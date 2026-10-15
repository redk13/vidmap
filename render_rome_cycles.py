import bpy
import bmesh
import math
import os
import sys
import json
import numpy as np
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw, ImageFont

# Parse CLI args after "--"
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

MODE = "--preview"
START_FRAME = 0
END_FRAME = 450
OUT_DIR = "/var/tmp/rome_cycles_frames"
RES_X, RES_Y = 1920, 1080
SAMPLES = 12

i = 0
while i < len(argv):
    if argv[i] == "--preview":
        MODE = "--preview"; i += 1
    elif argv[i] == "--shard":
        MODE = "--shard"; i += 1
    elif argv[i] == "--start":
        START_FRAME = int(argv[i+1]); i += 2
    elif argv[i] == "--end":
        END_FRAME = int(argv[i+1]); i += 2
    elif argv[i] == "--out-dir":
        OUT_DIR = argv[i+1]; i += 2
    elif argv[i] == "--res":
        RES_X, RES_Y = map(int, argv[i+1].split("x")); i += 2
    elif argv[i] == "--samples":
        SAMPLES = int(argv[i+1]); i += 2
    else:
        i += 1

os.makedirs(OUT_DIR, exist_ok=True)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(SCRIPT_DIR, "assets")

# Load real SRTM elevation array for accurate 3D spline height placement in Shot 2
SRTM_ELEV = np.load(os.path.join(ASSET_DIR, "rome_srtm_elev.npy"))

def get_srtm_z(x_world, y_world, size_x=48.0, size_y=30.0, disp_scale=5.2):
    # Map Blender world (x_world in [-size_x/2..size_x/2], y_world in [-size_y/2..size_y/2]) to SRTM pixel
    u = np.clip((x_world / size_x) + 0.5, 0.0, 0.999)
    v = np.clip(0.5 - (y_world / size_y), 0.0, 0.999)
    px = int(u * (SRTM_ELEV.shape[1] - 1))
    py = int(v * (SRTM_ELEV.shape[0] - 1))
    norm_h = np.clip(SRTM_ELEV[py, px], 0.0, 1450.0) / 1450.0
    return float(norm_h * disp_scale)

def configure_cycles_scene(sc):
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.sample_clamp_indirect = 4.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.use_auto_tile = True
    sc.cycles.tile_size = 256
    try:
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        sc.cycles.denoising_prefilter = 'FAST'
    except Exception:
        sc.cycles.use_denoising = False

    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        sc.view_settings.view_transform = 'Filmic'

    sc.render.resolution_x = RES_X
    sc.render.resolution_y = RES_Y
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 94

    # Enable Blender Compositor with Optical Fog-Glow Bloom!
    sc.use_nodes = True
    ct = sc.node_tree
    ct.nodes.clear()
    rl = ct.nodes.new('CompositorNodeRLayers')
    glare = ct.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.threshold = 1.15
    glare.size = 7
    comp = ct.nodes.new('CompositorNodeComposite')
    ct.links.new(rl.outputs['Image'], glare.inputs['Image'])
    ct.links.new(glare.outputs['Image'], comp.inputs['Image'])

# ==============================================================================
# PROCEDURAL 3D CYCLES SHADER NODE MATERIALS
# ==============================================================================
def make_travertine_shader(name="RomanTravertine", warm_tint=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.62

    tex_coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Rotation'].default_value = (math.radians(90.0), 0.0, 0.0)
    mapping.inputs['Scale'].default_value = (1.6, 1.6, 1.6)

    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.offset = 0.5
    brick.squash = 1.0
    brick.inputs['Scale'].default_value = 2.6
    brick.inputs['Mortar Size'].default_value = 0.018
    brick.inputs['Mortar Smooth'].default_value = 0.1
    brick.inputs['Color1'].default_value = (0.82 * warm_tint, 0.71 * warm_tint, 0.55, 1.0)
    brick.inputs['Color2'].default_value = (0.71 * warm_tint, 0.59 * warm_tint, 0.44, 1.0)
    brick.inputs['Mortar'].default_value = (0.28, 0.22, 0.16, 1.0)

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 14.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.65

    mix_col = nt.nodes.new('ShaderNodeMix')
    mix_col.data_type = 'RGBA'
    mix_col.inputs['Factor'].default_value = 0.22

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.42
    bump.inputs['Distance'].default_value = 0.06

    nt.links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], brick.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
    nt.links.new(brick.outputs['Color'], mix_col.inputs[6])
    nt.links.new(noise.outputs['Color'], mix_col.inputs[7])
    nt.links.new(mix_col.outputs[2], bsdf.inputs['Base Color'])
    nt.links.new(brick.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_refractive_water_shader(name="RomanWater", emit_strength=1.6):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.02, 0.78, 0.98, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.06
    bsdf.inputs['IOR'].default_value = 1.333
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = 0.85
    if 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = (0.0, 0.82, 1.0, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emit_strength

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 25.0
    noise.inputs['Detail'].default_value = 5.0
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.18
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_emission_shader(name, color_rgba, strength=8.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = color_rgba
    emit.inputs['Strength'].default_value = strength
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return mat

def make_soil_strata_shader(name="GeologicalStrata", warm=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.88

    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    wave.inputs['Scale'].default_value = 2.2
    wave.inputs['Distortion'].default_value = 6.5
    wave.inputs['Detail'].default_value = 8.0

    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.inputs['Scale'].default_value = 18.0

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    if warm:
        ramp.color_ramp.elements[0].color = (0.28, 0.17, 0.10, 1.0)
        ramp.color_ramp.elements[1].color = (0.62, 0.43, 0.27, 1.0)
    else:
        ramp.color_ramp.elements[0].color = (0.14, 0.09, 0.06, 1.0)
        ramp.color_ramp.elements[1].color = (0.38, 0.27, 0.19, 1.0)

    mix_f = nt.nodes.new('ShaderNodeMix')
    mix_f.data_type = 'FLOAT'
    mix_f.inputs['Factor'].default_value = 0.45

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.58
    bump.inputs['Distance'].default_value = 0.08

    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
    nt.links.new(wave.outputs['Fac'], mix_f.inputs[2])
    nt.links.new(vor.outputs['Distance'], mix_f.inputs[3])
    nt.links.new(mix_f.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(mix_f.outputs[0], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# ==============================================================================
# 3D ARCHITECTURAL BUILDERS (TRUE B-MESH / BEVELED / ARCHED ROMAN STRUCTURES)
# ==============================================================================
def build_3d_roman_aqueduct(name, num_bays, bay_w, lower_h, upper_h, depth, mat_stone, mat_water=None):
    parent = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(parent)
    total_len = num_bays * bay_w
    start_x = -total_len / 2.0

    # Helper to create an arched wall tier using exact bmesh circular arch vaults
    def make_tier_mesh(t_name, n_bays, bw, th, td, z_base):
        bm = bmesh.new()
        arch_r = bw * 0.34
        spring_z = th * 0.55
        segs = 16
        for b in range(n_bays):
            x0 = start_x + b * bw
            x1 = x0 + bw
            cx = (x0 + x1) * 0.5
            # Left & right pier blocks up to spring_z
            for px0, px1 in [(x0, cx - arch_r), (cx + arch_r, x1)]:
                v = [
                    bm.verts.new((px0, -td/2, z_base)),
                    bm.verts.new((px1, -td/2, z_base)),
                    bm.verts.new((px1, -td/2, z_base + spring_z)),
                    bm.verts.new((px0, -td/2, z_base + spring_z)),
                    bm.verts.new((px0,  td/2, z_base)),
                    bm.verts.new((px1,  td/2, z_base)),
                    bm.verts.new((px1,  td/2, z_base + spring_z)),
                    bm.verts.new((px0,  td/2, z_base + spring_z)),
                ]
                for f in [(0,1,2,3), (5,4,7,6), (4,0,3,7), (1,5,6,2), (4,5,1,0)]:
                    bm.faces.new([v[k] for k in f])
            # Arch spandrel segments from spring_z to th
            for s in range(segs):
                a0 = math.pi - (s / float(segs)) * math.pi
                a1 = math.pi - ((s + 1) / float(segs)) * math.pi
                ax0, az0 = cx + math.cos(a0) * arch_r, z_base + spring_z + math.sin(a0) * arch_r
                ax1, az1 = cx + math.cos(a1) * arch_r, z_base + spring_z + math.sin(a1) * arch_r
                ox0 = x0 if s < segs // 2 else x1
                # Connect arch ring to top spandrel line (z = z_base + th)
                v = [
                    bm.verts.new((ax0, -td/2, az0)),
                    bm.verts.new((ax1, -td/2, az1)),
                    bm.verts.new((ax1, -td/2, z_base + th)),
                    bm.verts.new((ax0, -td/2, z_base + th)),
                    bm.verts.new((ax0,  td/2, az0)),
                    bm.verts.new((ax1,  td/2, az1)),
                    bm.verts.new((ax1,  td/2, z_base + th)),
                    bm.verts.new((ax0,  td/2, z_base + th)),
                ]
                for f in [(0,1,2,3), (5,4,7,6), (1,0,4,5), (3,2,6,7)]:
                    bm.faces.new([v[k] for k in f])
            # Fill left/right upper spandrel corners above piers
            for px0, px1 in [(x0, cx - arch_r), (cx + arch_r, x1)]:
                v = [
                    bm.verts.new((px0, -td/2, z_base + spring_z)),
                    bm.verts.new((px1, -td/2, z_base + spring_z)),
                    bm.verts.new((px1, -td/2, z_base + th)),
                    bm.verts.new((px0, -td/2, z_base + th)),
                    bm.verts.new((px0,  td/2, z_base + spring_z)),
                    bm.verts.new((px1,  td/2, z_base + spring_z)),
                    bm.verts.new((px1,  td/2, z_base + th)),
                    bm.verts.new((px0,  td/2, z_base + th)),
                ]
                for f in [(0,1,2,3), (5,4,7,6), (3,2,6,7), (4,0,3,7), (1,5,6,2)]:
                    bm.faces.new([v[k] for k in f])

        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(t_name)
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(t_name, me)
        bpy.context.collection.objects.link(obj)
        obj.parent = parent
        obj.data.materials.append(mat_stone)
        bev = obj.modifiers.new("Bevel", 'BEVEL')
        bev.width = 0.04
        bev.segments = 2
        return obj

    make_tier_mesh(f"{name}_Lower", num_bays, bay_w, lower_h, depth, 0.0)
    make_tier_mesh(f"{name}_Upper", num_bays * 2, bay_w * 0.5, upper_h, depth * 0.84, lower_h + 0.35)

    # Pier pilasters & plinths + mid cornice
    for i_p in range(num_bays + 1):
        px = start_x + i_p * bay_w
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, 0, lower_h * 0.48))
        pier = bpy.context.active_object
        pier.scale = (bay_w * 0.22, depth * 1.24, lower_h * 0.96)
        pier.parent = parent
        pier.data.materials.append(mat_stone)

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, 0, lower_h * 0.07))
        plinth = bpy.context.active_object
        plinth.scale = (bay_w * 0.34, depth * 1.36, lower_h * 0.14)
        plinth.parent = parent
        plinth.data.materials.append(mat_stone)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, lower_h + 0.18))
    cornice = bpy.context.active_object
    cornice.scale = (total_len + 0.5, depth * 1.32, 0.36)
    cornice.parent = parent
    cornice.data.materials.append(mat_stone)

    top_z = lower_h + 0.35 + upper_h
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, side * depth * 0.34, top_z + 0.28))
        wall = bpy.context.active_object
        wall.scale = (total_len + 0.4, depth * 0.16, 0.56)
        wall.parent = parent
        wall.data.materials.append(mat_stone)

    if mat_water is not None:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, top_z + 0.24))
        w_obj = bpy.context.active_object
        w_obj.scale = (total_len + 0.2, depth * 0.52, 0.34)
        w_obj.parent = parent
        w_obj.data.materials.append(mat_water)

    return parent

# ==============================================================================
# HUD OVERLAY & SUBTITLE COMPOSITOR (Using Real Blender 3D Camera Matrix Projection)
# ==============================================================================
def get_font(size, bold=True, serif=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf" if (serif and bold) else
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf" if serif else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def proj_2d(sc, cam, vec3):
    co = world_to_camera_view(sc, cam, Vector(vec3))
    return (float(co.x * RES_X), float((1.0 - co.y) * RES_Y))

def draw_cinematic_subtitle(draw, before_txt, gold_txt, after_txt):
    f_reg = get_font(int(31 * RES_X / 1920), bold=False, serif=False)
    f_gld = get_font(int(32 * RES_X / 1920), bold=True, serif=True)
    b1 = draw.textbbox((0, 0), before_txt, font=f_reg)
    b2 = draw.textbbox((0, 0), gold_txt, font=f_gld)
    b3 = draw.textbbox((0, 0), after_txt, font=f_reg)
    w1, w2, w3 = b1[2] - b1[0], b2[2] - b2[0], b3[2] - b3[0]
    total_w = w1 + w2 + w3
    sx = (RES_X - total_w) // 2
    sy = RES_Y - int(76 * RES_Y / 1080)

    pad_x, pad_y = int(22 * RES_X / 1920), int(12 * RES_Y / 1080)
    draw.rounded_rectangle(
        [sx - pad_x, sy - pad_y, sx + total_w + pad_x, sy + int(42 * RES_Y / 1080)],
        radius=10, fill=(10, 12, 16, 155)
    )
    draw.text((sx, sy), before_txt, font=f_reg, fill=(255, 255, 255, 255))
    draw.text((sx + w1, sy), gold_txt, font=f_gld, fill=(248, 212, 72, 255))
    draw.text((sx + w1 + w2, sy), after_txt, font=f_reg, fill=(255, 255, 255, 255))

# ==============================================================================
# BUILD & RENDER EACH OF THE 5 SCENES IN BLENDER 4.3.2 CYCLES
# ==============================================================================
def render_frame_range(f_start, f_end):
    # Group requested frames by scene index (0..4, 90 frames = 3.0s each -> 450 frames = 15.0s)
    frames_to_do = [35, 145, 235, 305, 415] if MODE == "--preview" else list(range(f_start, f_end))

    for shot_idx in range(5):
        s_min = shot_idx * 90
        s_max = (shot_idx + 1) * 90
        shot_frames = [f for f in frames_to_do if s_min <= f < s_max]
        if not shot_frames:
            continue

        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        configure_cycles_scene(sc)

        if shot_idx == 0:
            # ------------------------------------------------------------------
            # SHOT 1 (Frames 0..89): Golden-Hour Ray-Traced Aqueduct in Real Valley
            # ------------------------------------------------------------------
            world = bpy.data.worlds.new("World1")
            sc.world = world
            world.use_nodes = True
            wn = world.node_tree.nodes
            wl = world.node_tree.links
            wn.clear()
            bg = wn.new('ShaderNodeBackground')
            bg.inputs['Strength'].default_value = 0.17
            sky = wn.new('ShaderNodeTexSky')
            sky.sky_type = 'NISHITA'
            sky.sun_elevation = math.radians(6.2)
            sky.sun_rotation = math.radians(58.0)
            sky.dust_density = 2.4
            sky.air_density = 1.4
            out_w = wn.new('ShaderNodeOutputWorld')
            wl.new(sky.outputs['Color'], bg.inputs['Color'])
            wl.new(bg.outputs['Background'], out_w.inputs['Surface'])

            mat_stone = make_travertine_shader("Stone1", warm_tint=1.05)
            mat_water = make_refractive_water_shader("Water1", emit_strength=1.8)
            build_3d_roman_aqueduct("Aq1", 18, 5.0, 10.2, 4.6, 2.4, mat_stone, mat_water)

            # Valley terrain mesh with vertex displacement
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=90, size=1.0, location=(0, 0, -1.8))
            terr = bpy.context.active_object
            terr.scale = (160.0, 120.0, 1.0)
            bpy.ops.object.transform_apply(scale=True)
            for v in terr.data.vertices:
                vx, vy = v.co.x, v.co.y
                valley_u = min(1.0, abs(vx) / 42.0) ** 1.85 * 19.5
                hills = math.sin(vx * 0.08) * math.cos(vy * 0.08) * 2.8 + math.sin(vx * 0.19 + vy * 0.15) * 1.2
                v.co.z = valley_u + hills - 2.2
            terr.data.update()
            bpy.ops.object.shade_smooth()
            mat_grass = bpy.data.materials.new("ValleyGrass")
            mat_grass.use_nodes = True
            gnt = mat_grass.node_tree
            gbsdf = gnt.nodes["Principled BSDF"]
            gbsdf.inputs["Roughness"].default_value = 0.90
            gn1 = gnt.nodes.new('ShaderNodeTexNoise')
            gn1.inputs['Scale'].default_value = 18.0
            gn1.inputs['Detail'].default_value = 10.0
            gramp = gnt.nodes.new('ShaderNodeValToRGB')
            gramp.color_ramp.elements[0].color = (0.08, 0.14, 0.04, 1.0)
            gramp.color_ramp.elements[1].color = (0.24, 0.31, 0.11, 1.0)
            gbump = gnt.nodes.new('ShaderNodeBump')
            gbump.inputs['Strength'].default_value = 0.55
            gnt.links.new(gn1.outputs['Fac'], gramp.inputs['Fac'])
            gnt.links.new(gramp.outputs['Color'], gbsdf.inputs['Base Color'])
            gnt.links.new(gn1.outputs['Fac'], gbump.inputs['Height'])
            gnt.links.new(gbump.outputs['Normal'], gbsdf.inputs['Normal'])
            terr.data.materials.append(mat_grass)

            # Glowing Cyan Holographic Laser Scan Plane (casts real cyan bounce light onto the arches!)
            mat_scan = make_emission_shader("CyanScan", (0.05, 0.92, 1.0, 1.0), strength=14.0)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-20, 0, 7.5))
            scan_obj = bpy.context.active_object
            scan_obj.scale = (0.16, 4.2, 16.5)
            scan_obj.data.materials.append(mat_scan)

            # Scatter organic 3D Mediterranean trees on the valley slopes
            mat_foliage = bpy.data.materials.new("CypressLeaf")
            mat_foliage.use_nodes = True
            mat_foliage.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.19, 0.06, 1.0)
            mat_foliage.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.82
            for idx_t in range(65):
                tx = ((idx_t * 37) % 110) - 55.0
                ty = ((idx_t * 53) % 80) - 40.0
                if abs(ty) < 6.5 or (ty < -2.0 and -32.0 < tx < 14.0):
                    continue
                tz = min(1.0, abs(tx) / 42.0) ** 1.85 * 19.5 + math.sin(tx * 0.08) * math.cos(ty * 0.08) * 2.8 - 2.4
                if tz > 0.5:
                    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.1, location=(tx, ty, tz + 1.8))
                    tr = bpy.context.active_object
                    tr.scale = (0.75, 0.75, 1.85)
                    tr.data.materials.append(mat_foliage)

            bpy.ops.object.camera_add()
            cam = bpy.context.active_object
            sc.camera = cam
            cam.data.lens = 38.0
            cam.data.dof.use_dof = True
            cam.data.dof.aperture_fstop = 4.0
            cam.data.dof.focus_distance = 24.0

            for f in shot_frames:
                u = (f - s_min) / 89.0
                su = u * u * (3 - 2 * u)
                cam.location = (-26.0 + su * 20.0, -19.5 + su * 4.5, 6.8 + su * 4.2)
                direction = Vector((4.0 + su * 10.0, 0.0, 8.2)) - cam.location
                cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
                scan_obj.location.x = -26.0 + u * 52.0

                raw_fp = os.path.join(OUT_DIR, f"raw_{f:04d}.jpg")
                sc.render.filepath = raw_fp
                bpy.ops.render.render(write_still=True)

                im = Image.open(raw_fp).convert("RGBA")
                ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)
                if u < 0.5:
                    draw_cinematic_subtitle(dr, "From the innovative ", "aqueducts", " engineered across Roman valleys")
                else:
                    draw_cinematic_subtitle(dr, "that brought fresh water nearly ", "100 km", " straight into the city")
                Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(OUT_DIR, f"frame_{f:04d}.jpg"), quality=94)
                os.remove(raw_fp)

        elif shot_idx == 1:
            # ------------------------------------------------------------------
            # SHOT 2 (Frames 90..179): Real SRTM Satellite DEM of Rome & Aqua Marcia
            # ------------------------------------------------------------------
            world = bpy.data.worlds.new("World2")
            sc.world = world
            world.use_nodes = True
            world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.015, 0.018, 0.022, 1.0)
            world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

            # Dramatic raking directional rim light across the real SRTM mountains
            bpy.ops.object.light_add(type='SUN', location=(-25, 25, 30))
            sun2 = bpy.context.active_object
            sun2.data.energy = 3.2
            sun2.data.angle = math.radians(8.0)
            sun2.rotation_euler = (math.radians(52), math.radians(-28), math.radians(35))

            # High-Res Subdivided Mesh Displaced by Real Rome SRTM Heightmap!
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=320, y_subdivisions=200, size=1.0, location=(0, 0, 0))
            dem_obj = bpy.context.active_object
            dem_obj.scale = (48.0, 30.0, 1.0)
            bpy.ops.object.transform_apply(scale=True)
            bpy.ops.object.shade_smooth()

            # Displace vertices directly from SRTM_ELEV for exact 3D mountain coordinates
            for v in dem_obj.data.vertices:
                v.co.z = get_srtm_z(v.co.x, v.co.y, 48.0, 30.0, 5.2)
            dem_obj.data.update()

            # Material using our baked SRTM obsidian relief + glowing river/lake emission texture
            mat_dem = bpy.data.materials.new("RomeSRTMMat")
            mat_dem.use_nodes = True
            nt = mat_dem.node_tree
            nt.nodes.clear()
            out_m = nt.nodes.new('ShaderNodeOutputMaterial')
            bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
            bsdf.inputs['Roughness'].default_value = 0.72

            tc = nt.nodes.new('ShaderNodeTexCoord')
            tex_alb = nt.nodes.new('ShaderNodeTexImage')
            tex_alb.image = bpy.data.images.load(os.path.join(ASSET_DIR, "rome_srtm_composite_albedo.png"))
            tex_emi = nt.nodes.new('ShaderNodeTexImage')
            tex_emi.image = bpy.data.images.load(os.path.join(ASSET_DIR, "rome_srtm_emission.png"))

            nt.links.new(tc.outputs['Generated'], tex_alb.inputs['Vector'])
            nt.links.new(tc.outputs['Generated'], tex_emi.inputs['Vector'])
            nt.links.new(tex_alb.outputs['Color'], bsdf.inputs['Base Color'])
            if 'Emission Color' in bsdf.inputs:
                nt.links.new(tex_emi.outputs['Color'], bsdf.inputs['Emission Color'])
                bsdf.inputs['Emission Strength'].default_value = 3.5
            nt.links.new(bsdf.outputs['BSDF'], out_m.inputs['Surface'])
            dem_obj.data.materials.append(mat_dem)

            # 3D Animated Glowing Golden-Orange Spline for AQUA MARCIA (90 km / 55 miles)
            # Coordinates on the 48x30 SRTM plane from Rome (-8.0, 0.8) along the Aniene Valley to Subiaco (17.5, -2.5)
            marcia_xy = [
                (-8.0, 0.8), (-4.5, -0.8), (-0.5, -2.2), (3.8, -2.8),
                (7.8, -1.6), (11.2, 1.2), (14.5, 2.8), (17.5, 1.4), (20.2, -0.5)
            ]
            curve_data = bpy.data.curves.new('AquaMarciaCurve', type='CURVE')
            curve_data.dimensions = '3D'
            curve_data.bevel_depth = 0.16
            curve_data.bevel_resolution = 6
            spline = curve_data.splines.new('CATMULL_ROM' if False else 'POLY')
            # Interpolate 80 smooth points hugging the real SRTM elevation
            dense_pts = []
            for idx_seg in range(len(marcia_xy) - 1):
                x0, y0 = marcia_xy[idx_seg]
                x1, y1 = marcia_xy[idx_seg + 1]
                for sub in range(12):
                    t_s = sub / 12.0
                    px = x0 + (x1 - x0) * t_s
                    py = y0 + (y1 - y0) * t_s
                    pz = get_srtm_z(px, py, 48.0, 30.0, 5.2) + 0.18
                    dense_pts.append((px, py, pz))
            spline.points.add(len(dense_pts) - 1)
            for idx_p, (px, py, pz) in enumerate(dense_pts):
                spline.points[idx_p].co = (px, py, pz, 1.0)

            marcia_obj = bpy.data.objects.new('AquaMarciaObj', curve_data)
            bpy.context.collection.objects.link(marcia_obj)
            mat_marcia = make_emission_shader("MarciaGlow", (1.0, 0.65, 0.06, 1.0), strength=16.0)
            marcia_obj.data.materials.append(mat_marcia)

            bpy.ops.object.camera_add()
            cam = bpy.context.active_object
            sc.camera = cam
            cam.data.lens = 40.0

            for f in shot_frames:
                u = (f - s_min) / 89.0
                su = u * u * (3 - 2 * u)
                cam.location = (-2.5 + su * 5.5, -24.5 + su * 4.5, 22.0 - su * 5.0)
                direction = Vector((2.5 + su * 3.5, 0.5, 1.2)) - cam.location
                cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
                bpy.context.view_layer.update()

                draw_frac = min(1.0, max(0.12, (u - 0.03) / 0.80))
                curve_data.bevel_factor_end = draw_frac

                raw_fp = os.path.join(OUT_DIR, f"raw_{f:04d}.jpg")
                sc.render.filepath = raw_fp
                bpy.ops.render.render(write_still=True)

                # Project exact 3D SRTM coordinates to 2D pixels via world_to_camera_view
                p_rome = proj_2d(sc, cam, (-8.0, 0.8, get_srtm_z(-8.0, 0.8) + 0.3))
                p_pop  = proj_2d(sc, cam, (-15.5, 3.8, 1.5))
                p_title = proj_2d(sc, cam, (2.2, -1.2, get_srtm_z(2.2, -1.2) + 1.4))
                tip_i = min(len(dense_pts) - 1, int(draw_frac * (len(dense_pts) - 1)))
                p_tip = proj_2d(sc, cam, dense_pts[tip_i])

                im = Image.open(raw_fp).convert("RGBA")
                ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)

                # Chapter bar top-left
                dr.rounded_rectangle([42, 28, 380, 40], radius=6, fill=(255, 255, 255, 65))
                dr.rounded_rectangle([42, 28, int(130 + u * 110), 40], radius=6, fill=(255, 255, 255, 240))

                # Rome population pointer
                pop_x = max(int(175 * RES_X / 1920), int(p_pop[0]))
                pop_y = int(p_pop[1])
                dr.line([(pop_x + 70, pop_y + 12), (int(p_rome[0]), int(p_rome[1]))], fill=(255, 255, 255, 220), width=2)
                f_pop = get_font(int(36 * RES_X / 1920), bold=True, serif=True)
                pop_val = f"{int(750000 + min(1.0, u * 1.3) * 250000):,}"
                dr.text((pop_x - 65, pop_y - 22), pop_val, font=f_pop, fill=(255, 255, 255, 255))

                # Glowing "Aqua Marcia" title & live km counter
                f_title = get_font(int(52 * RES_X / 1920), bold=True, serif=True)
                dr.text((int(p_title[0]) - 140, int(p_title[1]) - 30), "Aqua Marcia", font=f_title, fill=(255, 190, 35, 255))

                km_v = max(14, int(round(draw_frac * 90)))
                mi_v = max(9, int(round(draw_frac * 55)))
                tx_k = min(RES_X - int(220 * RES_X / 1920), int(p_tip[0]) + 35)
                ty_k = int(p_tip[1]) + 15
                dr.line([(int(p_tip[0]), int(p_tip[1])), (tx_k - 8, ty_k + 12)], fill=(255, 255, 255, 230), width=2)
                f_km = get_font(int(46 * RES_X / 1920), bold=True, serif=True)
                f_mi = get_font(int(26 * RES_X / 1920), bold=True, serif=True)
                dr.text((tx_k, ty_k - 18), f"{km_v} km", font=f_km, fill=(255, 255, 255, 255))
                dr.text((tx_k + 8, ty_k + 32), f"{mi_v} miles", font=f_mi, fill=(220, 230, 242, 255))

                draw_cinematic_subtitle(dr, "The ", "Aqua Marcia", " carried pure mountain spring water over 90 kilometers")
                Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(OUT_DIR, f"frame_{f:04d}.jpg"), quality=94)
                os.remove(raw_fp)

        elif shot_idx == 2:
            # ------------------------------------------------------------------
            # SHOT 3 (Frames 180..269): Dark-Grid 3D Geological Cutaway
            # (Water source -> Underground Mountain Tunnel -> 3D Bridge -> Rome)
            # ------------------------------------------------------------------
            world = bpy.data.worlds.new("World3")
            sc.world = world
            world.use_nodes = True
            world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.018, 0.020, 0.025, 1.0)
            world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8

            bpy.ops.object.light_add(type='AREA', location=(4, -18, 22))
            lt3 = bpy.context.active_object
            lt3.data.energy = 1800.0
            lt3.data.size = 18.0
            lt3.rotation_euler = (math.radians(42), 0, 0)

            def prof_z3(x):
                if x < -14: return 0.5 + math.sin((x + 24) * 0.15) * 0.22
                if x < 4:
                    u = (x - (-5.0)) / 9.0
                    return -4.2 + u * u * 4.7
                if x < 17:
                    u = (x - 10.5) / 6.5
                    return 0.5 + (1.0 - u * u) * 5.2
                u = min(1.0, (x - 17.0) / 9.5)
                return 2.6 - math.sin(u * math.pi) * 2.2

            # Build 3D extruded geological block via bmesh
            bm = bmesh.new()
            xs = np.linspace(-35.0, 35.0, 180)
            front_v, back_v = [], []
            for x in xs:
                z_top = prof_z3(float(x))
                v_f0 = bm.verts.new((float(x), -2.2, -14.0))
                v_f1 = bm.verts.new((float(x), -2.2, z_top))
                v_b0 = bm.verts.new((float(x),  2.2, -14.0))
                v_b1 = bm.verts.new((float(x),  2.2, z_top))
                front_v.append((v_f0, v_f1))
                back_v.append((v_b0, v_b1))
            for k in range(len(xs) - 1):
                bm.faces.new([front_v[k][0], front_v[k+1][0], front_v[k+1][1], front_v[k][1]])
                bm.faces.new([back_v[k+1][0], back_v[k][0], back_v[k][1], back_v[k+1][1]])
                bm.faces.new([front_v[k][1], front_v[k+1][1], back_v[k+1][1], back_v[k][1]])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me3 = bpy.data.meshes.new("GeoCut3")
            bm.to_mesh(me3)
            bm.free()
            geo_obj3 = bpy.data.objects.new("GeoCut3", me3)
            bpy.context.collection.objects.link(geo_obj3)
            geo_obj3.data.materials.append(make_soil_strata_shader("Soil3", warm=False))

            # Glowing White Top Contour Curve
            c_top = bpy.data.curves.new("TopContour3", type='CURVE')
            c_top.dimensions = '3D'
            c_top.bevel_depth = 0.09
            sp_t = c_top.splines.new('POLY')
            sp_t.points.add(len(xs) - 1)
            for k, x in enumerate(xs):
                sp_t.points[k].co = (float(x), -2.25, prof_z3(float(x)) + 0.06, 1.0)
            top_obj = bpy.data.objects.new("TopContour3", c_top)
            bpy.context.collection.objects.link(top_obj)
            top_obj.data.materials.append(make_emission_shader("WhiteLine3", (1.0, 1.0, 1.0, 1.0), strength=4.5))

            # Right Mountain Lake ("Water source")
            mat_lake3 = make_refractive_water_shader("Lake3", emit_strength=2.4)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(25.5, 0.0, 1.35))
            lake3 = bpy.context.active_object
            lake3.scale = (16.5, 4.1, 1.8)
            lake3.data.materials.append(mat_lake3)

            # Valley White Marble Arched Aqueduct Bridge
            mat_white3 = make_travertine_shader("MarbleBridge3", warm_tint=1.12)
            br3 = build_3d_roman_aqueduct("Br3", 9, 1.85, 2.4, 1.2, 1.4, mat_white3, None)
            br3.location = (-5.0, -0.5, -2.5)

            # Left Classical Roman Temple ("Rome")
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-21.5, -0.5, 0.9))
            t_base = bpy.context.active_object
            t_base.scale = (6.8, 3.2, 0.7)
            t_base.data.materials.append(mat_white3)
            for c_i in range(6):
                bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=2.4, location=(-24.1 + c_i * 1.04, -1.6, 2.4))
                col = bpy.context.active_object
                col.data.materials.append(mat_white3)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-21.5, -0.5, 3.95))
            t_top = bpy.context.active_object
            t_top.scale = (6.6, 3.0, 0.85)
            t_top.data.materials.append(mat_white3)

            # Animated Glowing Cyan Water Flow Channel (Water source -> Tunnel -> Bridge -> Rome)
            f_curve = bpy.data.curves.new("Flow3", type='CURVE')
            f_curve.dimensions = '3D'
            f_curve.bevel_depth = 0.22
            f_sp = f_curve.splines.new('POLY')
            f_pts = [(17.5, -2.35, 2.1), (10.5, -2.35, 1.65), (3.5, -2.35, 1.25), (-5.0, -2.35, 0.82), (-13.5, -2.35, 0.42), (-21.5, -2.35, 0.05)]
            f_sp.points.add(len(f_pts) - 1)
            for k, pt in enumerate(f_pts):
                f_sp.points[k].co = (pt[0], pt[1], pt[2], 1.0)
            f_obj = bpy.data.objects.new("Flow3", f_curve)
            bpy.context.collection.objects.link(f_obj)
            f_obj.data.materials.append(make_emission_shader("CyanFlow3", (0.0, 0.92, 1.0, 1.0), strength=12.0))

            bpy.ops.object.camera_add()
            cam = bpy.context.active_object
            sc.camera = cam
            cam.data.lens = 38.0

            for f in shot_frames:
                u = (f - s_min) / 89.0
                su = u * u * (3 - 2 * u)
                cam.location = (5.0 - su * 6.5, -38.0 - su * 8.0, 4.8 + su * 1.2)
                direction = Vector((3.0 - su * 4.5, 0.0, 0.5)) - cam.location
                cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
                bpy.context.view_layer.update()

                f_curve.bevel_factor_end = min(1.0, max(0.08, (u - 0.04) / 0.78))

                raw_fp = os.path.join(OUT_DIR, f"raw_{f:04d}.jpg")
                sc.render.filepath = raw_fp
                bpy.ops.render.render(write_still=True)

                p_src = proj_2d(sc, cam, (23.5, -1.5, 5.2))
                p_rom = proj_2d(sc, cam, (-21.5, -1.5, 6.2))

                im = Image.open(raw_fp).convert("RGBA")
                ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)
                f_lbl = get_font(int(42 * RES_X / 1920), bold=True, serif=True)
                sx = min(RES_X - int(180 * RES_X / 1920), int(p_src[0]))
                dr.text((sx - 60, int(p_src[1]) - 42), "Water", font=f_lbl, fill=(255, 255, 255, 255))
                dr.text((sx - 65, int(p_src[1]) + 4), "source", font=f_lbl, fill=(255, 255, 255, 255))
                if u > 0.15:
                    rx_l = max(int(140 * RES_X / 1920), int(p_rom[0]))
                    dr.text((rx_l - 55, int(p_rom[1]) - 20), "Rome", font=f_lbl, fill=(255, 255, 255, 255))

                draw_cinematic_subtitle(dr, "Tapping high ", "mountain springs", ", tunnels and bridges guided water by gravity alone")
                Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(OUT_DIR, f"frame_{f:04d}.jpg"), quality=94)
                os.remove(raw_fp)

        elif shot_idx == 3:
            # ------------------------------------------------------------------
            # SHOT 4 (Frames 270..359): Clean White Studio — 3D Ray-Traced Slope (0.09° - 0.17°)
            # ------------------------------------------------------------------
            world = bpy.data.worlds.new("World4")
            sc.world = world
            world.use_nodes = True
            world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.78, 0.76, 0.72, 1.0)
            world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.05

            bpy.ops.object.light_add(type='SUN', location=(20, -25, 35))
            sun4 = bpy.context.active_object
            sun4.data.energy = 2.8
            sun4.data.angle = math.radians(12.0)
            sun4.rotation_euler = (math.radians(48), math.radians(18), math.radians(-25))

            # Clean Tiled Architectural Studio Floor
            bpy.ops.mesh.primitive_plane_add(size=240.0, location=(0, 0, 0))
            fl4 = bpy.context.active_object
            mat_fl4 = bpy.data.materials.new("StudioFloor4")
            mat_fl4.use_nodes = True
            nt4 = mat_fl4.node_tree
            bsdf4 = nt4.nodes["Principled BSDF"]
            bsdf4.inputs["Roughness"].default_value = 0.42
            brick4 = nt4.nodes.new('ShaderNodeTexBrick')
            brick4.inputs['Scale'].default_value = 18.0
            brick4.inputs['Mortar Size'].default_value = 0.008
            brick4.inputs['Color1'].default_value = (0.88, 0.86, 0.82, 1.0)
            brick4.inputs['Color2'].default_value = (0.84, 0.82, 0.78, 1.0)
            brick4.inputs['Mortar'].default_value = (0.68, 0.66, 0.62, 1.0)
            nt4.links.new(brick4.outputs['Color'], bsdf4.inputs['Base Color'])
            fl4.data.materials.append(mat_fl4)

            mat_st4 = make_travertine_shader("Stone4", warm_tint=1.08)
            aq4 = build_3d_roman_aqueduct("Aq4", 26, 3.2, 4.4, 2.5, 1.8, mat_st4, None)
            aq4.location = (0, 4.0, -0.1)
            aq4.rotation_euler = (0, math.radians(0.75), 0)

            # Glowing Golden-Yellow Laser Beam along top channel (casts real golden bounce light!)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 4.0, 7.45))
            laser4 = bpy.context.active_object
            laser4.scale = (86.0, 2.1, 0.24)
            laser4.rotation_euler = (0, math.radians(0.75), 0)
            laser4.data.materials.append(make_emission_shader("GoldLaser4", (1.0, 0.78, 0.02, 1.0), strength=14.0))

            bpy.ops.object.camera_add()
            cam = bpy.context.active_object
            sc.camera = cam
            cam.data.lens = 40.0

            for f in shot_frames:
                u = (f - s_min) / 89.0
                su = u * u * (3 - 2 * u)
                cam.location = (-12.0 + su * 18.0, -22.0 + su * 2.5, 6.8 + su * 0.6)
                direction = Vector((-1.0 + su * 9.0, 4.0, 5.2)) - cam.location
                cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
                bpy.context.view_layer.update()

                raw_fp = os.path.join(OUT_DIR, f"raw_{f:04d}.jpg")
                sc.render.filepath = raw_fp
                bpy.ops.render.render(write_still=True)

                p_txt = proj_2d(sc, cam, (2.0 + su * 5.0, 4.0, 9.1))
                p_ln  = proj_2d(sc, cam, (5.5 + su * 5.0, 4.0, 7.5))

                im = Image.open(raw_fp).convert("RGBA")
                ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)

                if u < 0.52:
                    dr.line([(int(p_txt[0]) + 80, int(p_txt[1]) + 22), (int(p_ln[0]), int(p_ln[1]))], fill=(255, 255, 255, 240), width=3)
                    f_m1 = get_font(int(44 * RES_X / 1920), bold=True, serif=True)
                    f_m2 = get_font(int(26 * RES_X / 1920), bold=False, serif=False)
                    dr.text((int(p_txt[0]) - 210, int(p_txt[1]) - 36), "1.5–3 meters per km", font=f_m1, fill=(72, 68, 62, 255))
                    dr.text((int(p_txt[0]) - 115, int(p_txt[1]) + 16), "(8–16 feet per mile)", font=f_m2, fill=(105, 100, 92, 255))
                else:
                    f_deg = get_font(int(64 * RES_X / 1920), bold=True, serif=True)
                    dr.text((int(p_txt[0]) - 175, int(p_txt[1]) - 28), "0.09 – 0.17°", font=f_deg, fill=(82, 78, 72, 255))

                draw_cinematic_subtitle(dr, "Dropping just ", "1.5 to 3 meters", " per kilometer — a razor-thin 0.15° gradient")
                Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(OUT_DIR, f"frame_{f:04d}.jpg"), quality=94)
                os.remove(raw_fp)

        elif shot_idx == 4:
            # ------------------------------------------------------------------
            # SHOT 5 (Frames 360..449): 3D Deep Valley Cutaway & Glowing Cyan Inverted Siphon
            # ------------------------------------------------------------------
            world = bpy.data.worlds.new("World5")
            sc.world = world
            world.use_nodes = True
            world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.68, 0.67, 0.64, 1.0)
            world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.95

            bpy.ops.object.light_add(type='SUN', location=(18, -26, 36))
            sun5 = bpy.context.active_object
            sun5.data.energy = 3.0
            sun5.data.angle = math.radians(8.0)
            sun5.rotation_euler = (math.radians(46), math.radians(15), math.radians(-20))

            def val_z5(x):
                if abs(x) >= 13.5: return 6.5
                u = abs(x) / 13.5
                return -6.5 + (u ** 2.15) * 13.0

            bm = bmesh.new()
            xs5 = np.linspace(-29.0, 29.0, 160)
            fv5, bv5 = [], []
            for x in xs5:
                zt = val_z5(float(x))
                v_f0 = bm.verts.new((float(x), -4.5, -13.0))
                v_f1 = bm.verts.new((float(x), -4.5, zt))
                v_b0 = bm.verts.new((float(x),  4.5, -13.0))
                v_b1 = bm.verts.new((float(x),  4.5, zt))
                fv5.append((v_f0, v_f1))
                bv5.append((v_b0, v_b1))
            for k in range(len(xs5) - 1):
                bm.faces.new([fv5[k][0], fv5[k+1][0], fv5[k+1][1], fv5[k][1]])
                bm.faces.new([bv5[k+1][0], bv5[k][0], bv5[k][1], bv5[k+1][1]])
                bm.faces.new([fv5[k][1], fv5[k+1][1], bv5[k+1][1], bv5[k][1]])
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me5 = bpy.data.meshes.new("ValleyCut5")
            bm.to_mesh(me5)
            bm.free()
            cut5 = bpy.data.objects.new("ValleyCut5", me5)
            bpy.context.collection.objects.link(cut5)
            cut5.data.materials.append(make_soil_strata_shader("WarmRock5", warm=True))

            # Row of 3D Mediterranean Cypress Trees along the upper grass ridge
            mat_leaf5 = bpy.data.materials.new("Leaf5")
            mat_leaf5.use_nodes = True
            mat_leaf5.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.11, 0.22, 0.07, 1.0)
            mat_leaf5.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
            for idx_c in range(22):
                tx = -25.0 + idx_c * 2.35
                ty = 1.8 + (idx_c % 2) * 0.9
                for p_i, (dz, r_s) in enumerate([(7.4, 0.95), (8.4, 0.88), (9.3, 0.72), (10.1, 0.52)]):
                    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r_s, location=(tx + ((p_i%2)-0.5)*0.18, ty, dz))
                    cy = bpy.context.active_object
                    cy.scale = (1.05, 0.95, 1.25)
                    cy.data.materials.append(mat_leaf5)

            # 3D Two-Tier Stone Siphon Bridge at the bottom of the 50m valley
            mat_st5 = make_travertine_shader("Stone5", warm_tint=1.06)
            sb5 = build_3d_roman_aqueduct("SiphonBr5", 6, 3.1, 4.2, 3.2, 2.2, mat_st5, None)
            sb5.location = (0, -0.5, -4.6)

            # 3D Concrete "Header tank" filled with refractive cyan water on left rim
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-16.8, -3.2, 7.15))
            htank = bpy.context.active_object
            htank.scale = (4.2, 2.0, 1.1)
            htank.data.materials.append(mat_st5)

            # Glowing Cyan Pressurized U-Pipe Inverted Siphon Conduit along the front cutaway
            s_curve = bpy.data.curves.new("SiphonFlow5", type='CURVE')
            s_curve.dimensions = '3D'
            s_curve.bevel_depth = 0.30
            s_sp = s_curve.splines.new('POLY')
            xs_s = np.linspace(-25.0, 25.0, 100)
            s_sp.points.add(len(xs_s) - 1)
            for k, x in enumerate(xs_s):
                if x < -13.5: sz = 6.85
                elif x > 13.5: sz = 6.45
                else:
                    u_v = abs(float(x)) / 13.5
                    sz = max(-0.35, -3.1 + (u_v ** 2.0) * 9.8)
                s_sp.points[k].co = (float(x), -4.75, sz, 1.0)
            s_obj = bpy.data.objects.new("SiphonFlow5", s_curve)
            bpy.context.collection.objects.link(s_obj)
            s_obj.data.materials.append(make_emission_shader("CyanSiphon5", (0.0, 0.92, 1.0, 1.0), strength=14.0))

            bpy.ops.object.camera_add()
            cam = bpy.context.active_object
            sc.camera = cam
            cam.data.lens = 38.0

            for f in shot_frames:
                u = (f - s_min) / 89.0
                su = u * u * (3 - 2 * u)
                cam.location = (0.0 - su * 2.0, -40.5 + su * 5.0, 5.2 - su * 0.8)
                direction = Vector((-0.8 - su * 1.0, 0.0, 0.8)) - cam.location
                cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
                bpy.context.view_layer.update()

                s_curve.bevel_factor_end = min(1.0, max(0.12, (u - 0.04) / 0.76))

                raw_fp = os.path.join(OUT_DIR, f"raw_{f:04d}.jpg")
                sc.render.filepath = raw_fp
                bpy.ops.render.render(write_still=True)

                p_top = proj_2d(sc, cam, (0.0, -2.0, 6.2))
                p_bot = proj_2d(sc, cam, (0.0, -2.0, -6.2))
                p_tnk = proj_2d(sc, cam, (-16.8, -3.2, 9.2))

                im = Image.open(raw_fp).convert("RGBA")
                ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)

                # Vertical yellow laser height line ("50 m / 164 ft")
                dr.line([(int(p_top[0]), int(p_top[1])), (int(p_bot[0]), int(p_bot[1]))], fill=(255, 215, 0, 235), width=3)
                f_50 = get_font(int(40 * RES_X / 1920), bold=True, serif=True)
                f_ft = get_font(int(24 * RES_X / 1920), bold=False, serif=False)
                dr.text((int(p_top[0]) - 52, int(p_top[1]) - 52), "50 m", font=f_50, fill=(255, 255, 255, 255))
                dr.text((int(p_top[0]) - 45, int(p_top[1]) - 8), "(164 ft)", font=f_ft, fill=(255, 255, 255, 255))

                f_ht = get_font(int(34 * RES_X / 1920), bold=True, serif=True)
                dr.text((max(80, int(p_tnk[0]) - 95), max(45, int(p_tnk[1]) - 20)), "Header tank", font=f_ht, fill=(255, 255, 255, 255))

                draw_cinematic_subtitle(dr, "Across valleys deeper than ", "50 meters", ", pressurized inverted siphons forced water uphill")
                Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(OUT_DIR, f"frame_{f:04d}.jpg"), quality=94)
                os.remove(raw_fp)

render_frame_range(START_FRAME, END_FRAME)
print("BLENDER 4.3.2 CYCLES RENDER COMPLETE!")
