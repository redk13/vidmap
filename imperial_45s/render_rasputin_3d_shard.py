#!/usr/bin/env python3
"""
Hybrid Masterpiece 3D Pipeline in Blender 4.3 Cycles (30.00 fps):
- Scenes 0, 1, 2, 4: High-Density 3D Depth-Displaced Camera Projection Meshes built from
  the approved hyper-detailed 3D keyframes (rasputin_kf_1, 2, 3, 5.jpg) + animated 3D camera
  (Orbit / Dolly / 3D Split / Top-Down Crane Pull-Up), 3D world-locked extruded typography,
  animated 3D footsteps, flickering 3D candle lights, and real 3D Webley .455 Revolver mesh.
- Scene 3 (Frames 900..1199): 100% Real GIS Geography (Natural Earth 50m GeoJSON of Imperial
  Russia, Baltic Sea, Gulf of Finland & 1916 Eastern Front) rendered in Blender 4.3 Cycles
  as sculpted volcanic obsidian 3D relief terrain on a white perspective wireframe grid,
  with glowing molten crimson Eastern Front borders, royal cobalt-blue Russian borders,
  and a towering golden laser beacon at Petrograd (59.93°N, 30.33°E).
"""
import os
import sys
import math
import json
import random

import bpy
import bmesh
import mathutils
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else ["0", "1", "/tmp/ras_frames"]
START_FRAME = int(argv[0])
END_FRAME = int(argv[1])
OUT_DIR = argv[2]
PREVIEW_MODE = "--preview" in argv

os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, SCRIPT_DIR)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def configure_cycles(samples_override=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples_override if samples_override else (10 if PREVIEW_MODE else 18)
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.denoising_prefilter = "FAST"
    scene.cycles.use_persistent_data = True
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 1
    scene.cycles.transmission_bounces = 1
    scene.cycles.transparent_max_bounces = 2
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    return scene


def setup_world(col=(0.003, 0.004, 0.007), strength=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*col, 1.0)
    bg.inputs[1].default_value = strength


def make_pbr_mat(name, color, rough=0.28, metal=0.0, coat=0.0, emit_col=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if "Coat Weight" in bsdf.inputs and coat > 0:
            bsdf.inputs["Coat Weight"].default_value = coat
            bsdf.inputs["Coat Roughness"].default_value = 0.08
        if emit_col and emit_str > 0.0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (*emit_col, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emit_str
    return m


def make_obsidian_terrain_mat(name, c1, c2, rough=0.26, coat=0.45, scale=7.5, bump_str=0.55):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.12
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 12.0
    noise.inputs["Roughness"].default_value = 0.72
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale * 1.4
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.35
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (*c1, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (*c2, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_str
    bump.inputs["Distance"].default_value = 0.15
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], mix.inputs[2])
    nt.links.new(vor.outputs["Distance"], mix.inputs[3])
    nt.links.new(mix.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(mix.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def create_3d_depth_stage(img_filename, name="DepthStage", width=16.0, height=9.0, nx=192, ny=108, depth_amp=0.85, mode="room"):
    """
    Build a high-density 3D Depth-Displaced Mesh from a Masterpiece Keyframe image,
    with UV coordinates and a hybrid Emission + Principled BSDF shader so real 3D Blender
    point lights, 3D extruded text, and 3D camera motion interact with the 3D surface!
    """
    img_path = os.path.join(ASSETS_DIR, img_filename)
    b_img_full = bpy.data.images.load(img_path)
    b_img = b_img_full.copy()
    b_img.scale(nx, ny)
    px = np.array(b_img.pixels[:], dtype=np.float32).reshape((ny, nx, 4))
    # Flip vertically so row 0 is top of image (matching v_norm = 0 at top)
    arr = px[::-1, :, :3]
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    bpy.data.images.remove(b_img)

    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    obj.rotation_mode = "XYZ"
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    verts_grid = []
    for j in range(ny):
        v_norm = j / float(ny - 1)  # 0 at top of image, 1 at bottom
        y_world = (0.5 - v_norm) * height
        row_v = []
        for i in range(nx):
            u_norm = i / float(nx - 1)
            x_world = (u_norm - 0.5) * width
            l_val = float(lum[j, i])

            # Compute smooth 3D structural depth Z based on scene geometry mode
            if mode == "cutaway":
                # Isometric diorama: center-right palace rises forward in 3D, void stays back
                mask_palace = 1.0 if l_val > 0.04 else 0.0
                z_world = mask_palace * (0.35 + 0.55 * l_val + 0.35 * (1.0 - abs(u_norm - 0.58))) * depth_amp
            elif mode == "room":
                # Vaulted cellar perspective: edges & lower floor come forward toward camera, center recedes
                radial = ((u_norm - 0.5) * 1.6) ** 2 + ((v_norm - 0.45) * 1.3) ** 2
                statue_boost = 0.42 * l_val if (0.20 < u_norm < 0.82 and v_norm > 0.32) else 0.0
                z_world = (radial * 0.55 + v_norm * 0.45 + statue_boost) * depth_amp
            elif mode == "topdown":
                # 90° top-down crime scene: floor at Z=0, statues at corners & fallen body in center rise in +Z
                corner_dist = min(
                    math.hypot(u_norm - 0.15, v_norm - 0.18),
                    math.hypot(u_norm - 0.84, v_norm - 0.18),
                    math.hypot(u_norm - 0.15, v_norm - 0.82),
                    math.hypot(u_norm - 0.85, v_norm - 0.82),
                )
                center_dist = math.hypot((u_norm - 0.50) * 1.2, (v_norm - 0.53) * 1.4)
                statue_h = 0.55 if corner_dist < 0.16 else (0.28 * l_val if center_dist < 0.22 else 0.0)
                z_world = (statue_h + 0.12 * l_val) * depth_amp
            else:
                z_world = l_val * depth_amp

            v = bm.verts.new((x_world, y_world, z_world))
            row_v.append((v, u_norm, 1.0 - v_norm))
        verts_grid.append(row_v)

    for j in range(ny - 1):
        for i in range(nx - 1):
            v00, u00, w00 = verts_grid[j][i]
            v10, u10, w10 = verts_grid[j][i + 1]
            v11, u11, w11 = verts_grid[j + 1][i + 1]
            v01, u01, w01 = verts_grid[j + 1][i]
            face = bm.faces.new((v00, v01, v11, v10))
            face.smooth = True
            uvs = [(u00, w00), (u01, w01), (u11, w11), (u10, w10)]
            for loop, uv in zip(face.loops, uvs):
                loop[uv_layer].uv = uv

    bm.to_mesh(mesh)
    bm.free()

    # Build Hybrid Projection Material (Preserves 100% of Masterpiece Keyframe fidelity + reacts to 3D lights)
    mat = bpy.data.materials.new(name + "_Mat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.28
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.35

    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = b_img_full
    tex.extension = "EXTEND"

    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 0.82

    mesh.materials.append(mat)
    return obj, mat, bsdf


def load_blend_asset(filename, name_prefix, target_height=None, mat=None):
    path = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        return None
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.objects = df.objects
    meshes = []
    for o in dt.objects:
        if o is not None and o.type == "MESH" and len(o.data.vertices) > 4:
            bpy.context.collection.objects.link(o)
            o.hide_render = False
            o.hide_viewport = False
            o.visible_camera = True
            meshes.append(o)
    if not meshes:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name_prefix
    obj.rotation_mode = "XYZ"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    verts = [v.co for v in obj.data.vertices]
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    dz = max(zs) - min(zs)
    span = max(max(xs) - min(xs), max(ys) - min(ys), dz) if "revolver" in filename else dz
    sc = (target_height / max(span, 1e-4)) if target_height else 1.0
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    min_z = min(zs)
    for v in obj.data.vertices:
        v.co.x = (v.co.x - cx) * sc
        v.co.y = (v.co.y - cy) * sc
        v.co.z = (v.co.z - min_z) * sc
    obj.data.update()
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj


def add_box(name, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "XYZ"
    o.scale = scale
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


def add_cyl(name, loc, r, depth, mat, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "XYZ"
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


def add_3d_text(text, loc, size, mat, rot=(0, 0, 0), extrude=0.045):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.active_object
    t.rotation_mode = "XYZ"
    t.data.body = text
    t.data.size = size
    t.data.extrude = extrude
    t.data.bevel_depth = 0.008
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    font_path = os.path.join(SCRIPT_DIR, "fonts", "Cinzel-Bold.ttf")
    if os.path.exists(font_path):
        t.data.font = bpy.data.fonts.load(font_path)
    t.data.materials.clear()
    t.data.materials.append(mat)
    return t


def add_point_light(name, loc, energy, radius=0.35, col=(1.0, 0.72, 0.35)):
    ld = bpy.data.lights.new(name, type="POINT")
    ld.energy = energy
    ld.shadow_soft_size = radius
    ld.color = col
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    bpy.context.collection.objects.link(lo)
    return lo


def add_spot_light(name, loc, rot_deg, energy, size=1.5, spot_deg=60.0, col=(1.0, 0.82, 0.55)):
    ld = bpy.data.lights.new(name, type="SPOT")
    ld.energy = energy
    ld.shadow_soft_size = size
    ld.spot_size = math.radians(spot_deg)
    ld.spot_blend = 0.6
    ld.color = col
    lo = bpy.data.objects.new(name, ld)
    lo.rotation_mode = "XYZ"
    lo.location = loc
    lo.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.collection.objects.link(lo)
    return lo


def add_camera(loc, rot_deg, lens=35.0):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    co = bpy.data.objects.new("Cam", cd)
    co.rotation_mode = "XYZ"
    co.location = loc
    co.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.collection.objects.link(co)
    bpy.context.scene.camera = co
    return co


# ==============================================================================
# SCENE 0 (Frames 0..299): 3D DEPTH-PROJECTED CUTAWAY OF YUSUPOV PALACE + 3D TEXT
# ==============================================================================
def build_scene_0():
    scene = configure_cycles(samples_override=8)
    setup_world((0.002, 0.003, 0.005), 1.0)

    stage, _, bsdf = create_3d_depth_stage(
        "rasputin_kf_1_cutaway.jpg", "YusupovCutaway3D", width=16.0, height=9.0, nx=192, ny=108, depth_amp=0.75, mode="cutaway"
    )

    mat_text_white = make_pbr_mat("TextWhite", (0.98, 0.96, 0.92), rough=0.15, emit_col=(0.98, 0.96, 0.92), emit_str=2.2)
    mat_text_gold = make_pbr_mat("TextGold", (1.0, 0.82, 0.35), rough=0.15, emit_col=(1.0, 0.82, 0.35), emit_str=2.6)
    mat_step_on = make_pbr_mat("StepRedOn", (1.0, 0.12, 0.15), rough=0.1, emit_col=(1.0, 0.14, 0.18), emit_str=6.5)
    mat_step_off = make_pbr_mat("StepRedOff", (0.18, 0.02, 0.03), rough=0.5, emit_col=(0.18, 0.02, 0.03), emit_str=0.05)

    # 3D World-Locked Extruded Typography Floating over the Cutaway Zones
    add_3d_text("MOIKA CANAL", (-3.8, -1.75, 0.65), 0.38, mat_text_white, rot=(0, 0, math.radians(-26.5)), extrude=0.035)
    add_3d_text("YUSUPOV PALACE", (-0.55, 2.55, 0.72), 0.40, mat_text_white, rot=(0, 0, math.radians(-14.0)), extrude=0.035)
    add_3d_text("GRAND DRAWING ROOM", (4.25, 2.25, 0.82), 0.32, mat_text_gold, rot=(0, 0, 0), extrude=0.03)
    add_3d_text("SOUNDPROOFED BASEMENT", (4.35, -3.55, 0.75), 0.33, mat_text_gold, rot=(0, 0, 0), extrude=0.03)

    # Animated 3D Glowing Crimson Footsteps descending the Spiral Staircase into the Basement
    stair_pts = [
        (3.65, 0.62, 0.75), (3.42, 0.45, 0.75), (3.20, 0.26, 0.74), (3.02, 0.05, 0.73),
        (3.15, -0.18, 0.72), (3.38, -0.36, 0.72), (3.62, -0.52, 0.72), (3.45, -0.78, 0.71),
        (3.22, -1.05, 0.70), (3.12, -1.35, 0.69), (3.32, -1.65, 0.68), (3.65, -1.88, 0.68),
    ]
    step_objs = []
    for idx_s, pt in enumerate(stair_pts):
        so = add_cyl(f"StairStepDot_{idx_s}", pt, 0.075, 0.04, mat_step_on, verts=20)
        step_objs.append(so)

    # 3D Point Lights over the Cutaway Chandelier, Basement Candelabra & Embankment Streetlamps
    l_draw = add_point_light("Chandelier3D", (4.05, 1.35, 1.45), 55.0, radius=0.4, col=(1.0, 0.78, 0.42))
    l_base = add_point_light("Basement3D", (4.45, -1.85, 1.35), 65.0, radius=0.35, col=(1.0, 0.68, 0.28))
    l_moon = add_point_light("CanalMoon3D", (-3.5, -1.0, 3.2), 45.0, radius=1.2, col=(0.45, 0.72, 1.0))

    cam = add_camera(loc=(0.0, 0.0, 11.4), rot_deg=(0.0, 0.0, 0.0), lens=35.0)

    def update_frame(f):
        u = smoothstep((f - 0.0) / 299.0)
        # Smooth 3D orbital crane push-in toward the right-side cutaway staircase & basement
        cam.location = (
            lerp(-0.35, 0.68, u),
            lerp(0.18, -0.32, u),
            lerp(11.55, 9.75, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(-1.2, 1.8, u)),
            math.radians(lerp(-2.2, 3.2, u)),
            math.radians(lerp(0.8, -0.8, u)),
        )
        l_base.data.energy = 65.0 + 18.0 * math.sin(f * 0.42)
        l_draw.data.energy = 55.0 + 10.0 * math.cos(f * 0.28)
        active = int(lerp(1, len(step_objs) + 1, clamp((f - 12.0) / 210.0)))
        for idx_s, so in enumerate(step_objs):
            so.data.materials[0] = mat_step_on if idx_s <= active else mat_step_off

    return scene, update_frame


# ==============================================================================
# SCENE 1 (Frames 300..599): 3D DEPTH-PROJECTED BASEMENT TABLEAU + CANDLE FLICKER
# ==============================================================================
def build_scene_1():
    scene = configure_cycles(samples_override=8)
    setup_world((0.003, 0.002, 0.005), 1.0)

    stage, _, _ = create_3d_depth_stage(
        "rasputin_kf_2_basement.jpg", "BasementTableau3D", width=16.0, height=9.0, nx=192, ny=108, depth_amp=1.05, mode="room"
    )

    # Real 3D flickering candle light right over the candelabra on the mahogany table + cold moonlight on the upper stairs
    candle_3d = add_point_light("CandelabraLight3D", (0.0, 0.15, 1.55), 85.0, radius=0.35, col=(1.0, 0.68, 0.25))
    stair_moon = add_point_light("StairMoonLight3D", (0.0, 1.65, 1.85), 40.0, radius=0.8, col=(0.42, 0.68, 1.0))

    # Subtle 3D floating golden dust motes in the cellar candlelight
    mat_mote = make_pbr_mat("CandleMote", (1.0, 0.82, 0.42), rough=0.1, emit_col=(1.0, 0.78, 0.35), emit_str=3.5)
    random.seed(1916)
    motes = []
    for m_i in range(28):
        mx = random.uniform(-4.5, 4.5)
        my = random.uniform(-2.5, 2.5)
        mz = random.uniform(0.65, 2.2)
        mo = add_cyl(f"Mote_{m_i}", (mx, my, mz), 0.018, 0.018, mat_mote, verts=8)
        motes.append((mo, mx, my, mz, random.uniform(0.0, 6.28)))

    cam = add_camera(loc=(0.0, 0.0, 11.4), rot_deg=(0.0, 0.0, 0.0), lens=35.0)

    def update_frame(f):
        u = smoothstep((f - 300.0) / 299.0)
        # Slow, tense 3D camera dolly-in + subtle pan between Rasputin and Prince Yusupov
        cam.location = (
            lerp(-0.22, 0.18, u),
            lerp(-0.12, 0.08, u),
            lerp(11.45, 9.65, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(0.8, -0.6, u)),
            math.radians(lerp(-1.8, 1.6, u)),
            0.0,
        )
        candle_3d.data.energy = 85.0 + 24.0 * math.sin(f * 0.55) + 12.0 * math.cos(f * 0.9)
        for mo, mx, my, mz, ph in motes:
            mo.location = (
                mx + 0.12 * math.sin(f * 0.03 + ph),
                my + 0.08 * (f - 300.0) * 0.01,
                mz + 0.08 * math.cos(f * 0.04 + ph),
            )

    return scene, update_frame


# ==============================================================================
# SCENE 2 (Frames 600..899): 3D SLICED MARBLE BUST + ANIMATED 3D LASER SEPARATION
# ==============================================================================
def build_scene_2():
    scene = configure_cycles(samples_override=8)
    setup_world((0.005, 0.001, 0.002), 1.0)

    # Create two 3D depth-projected meshes split along the 38° laser line so the upper-right bust half physically separates in 3D!
    stage_low, _, _ = create_3d_depth_stage(
        "rasputin_kf_3_sliced_bust.jpg", "BustLowerLeft3D", width=16.0, height=9.0, nx=160, ny=90, depth_amp=0.65, mode="cutaway"
    )
    stage_high = stage_low.copy()
    stage_high.data = stage_low.data.copy()
    stage_high.rotation_mode = "XYZ"
    bpy.context.collection.objects.link(stage_high)

    # Bisect stage_low and stage_high along the diagonal laser line: y - 0.62*x = 0.15
    plane_co = mathutils.Vector((0.35, 0.18, 0.0))
    plane_no = mathutils.Vector((0.52, 0.85, 0.0)).normalized()

    bm1 = bmesh.new()
    bm1.from_mesh(stage_low.data)
    bmesh.ops.bisect_plane(
        bm1, geom=bm1.verts[:] + bm1.edges[:] + bm1.faces[:], plane_co=plane_co, plane_no=plane_no, clear_outer=True, clear_inner=False
    )
    bm1.to_mesh(stage_low.data)
    bm1.free()

    bm2 = bmesh.new()
    bm2.from_mesh(stage_high.data)
    bmesh.ops.bisect_plane(
        bm2, geom=bm2.verts[:] + bm2.edges[:] + bm2.faces[:], plane_co=plane_co, plane_no=plane_no, clear_outer=False, clear_inner=True
    )
    bm2.to_mesh(stage_high.data)
    bm2.free()

    # Real 3D Glowing Crimson Laser Beam sweeping across the cut
    mat_laser = make_pbr_mat("Laser3D", (1.0, 0.08, 0.12), rough=0.05, emit_col=(1.0, 0.10, 0.14), emit_str=14.0)
    laser_3d = add_box("LaserBeam3D", (0.35, 0.18, 0.58), (18.5, 0.045, 0.045), mat_laser, rot=(0, 0, math.radians(31.5)))
    laser_light = add_point_light("LaserCoreLight", (0.85, 0.45, 1.4), 95.0, radius=0.45, col=(1.0, 0.08, 0.12))

    # Shift the bust group slightly right (+1.15m) so the Left Bento Noir Dossier Card has clean framing
    cam = add_camera(loc=(-1.05, 0.0, 11.2), rot_deg=(0.0, 0.0, 0.0), lens=35.0)

    def update_frame(f):
        u = smoothstep((f - 600.0) / 299.0)
        split_t = smoothstep((f - 615.0) / 160.0)
        # Physically separate the upper-right 3D bust half along the 38° laser trajectory!
        stage_high.location = (
            lerp(-0.08, 0.22, split_t),
            lerp(-0.05, 0.16, split_t),
            lerp(0.0, 0.28, split_t),
        )
        laser_3d.scale = (lerp(0.05, 1.05, smoothstep((f - 605.0) / 45.0)), 1.0, 1.0 + 0.35 * math.sin(f * 0.4))
        laser_light.data.energy = 95.0 + 35.0 * math.sin(f * 0.35)
        cam.location = (
            lerp(-1.15, -0.75, u),
            lerp(-0.10, 0.12, u),
            lerp(11.35, 9.85, u),
        )
        cam.rotation_euler = (0.0, math.radians(lerp(-1.5, 2.2, u)), 0.0)

    return scene, update_frame


# ==============================================================================
# SCENE 3 (Frames 900..1199): 100% REAL GIS GEOGRAPHY IN BLENDER 4.3 CYCLES
# ==============================================================================
def build_scene_3():
    """
    100% Real GIS Geographic Relief Map of Imperial Russia, Baltic Sea, Gulf of Finland
    and the 1916 Eastern Front built from Natural Earth 50m GeoJSON inside Blender 4.3 Cycles.
    """
    scene = configure_cycles(samples_override=12)
    setup_world((0.002, 0.003, 0.007), 1.0)

    mat_grid = make_pbr_mat("GridWire", (0.55, 0.65, 0.82), rough=0.2, emit_col=(0.55, 0.65, 0.82), emit_str=0.65)
    mat_ocean = make_pbr_mat("DarkBalticOcean", (0.008, 0.012, 0.022), rough=0.14, coat=0.8)
    mat_obsidian_russia = make_obsidian_terrain_mat(
        "ObsidianRussia", (0.035, 0.042, 0.065), (0.012, 0.016, 0.028), rough=0.24, coat=0.5, scale=8.5, bump_str=0.65
    )
    mat_obsidian_front = make_obsidian_terrain_mat(
        "ObsidianFront", (0.12, 0.025, 0.030), (0.035, 0.010, 0.012), rough=0.26, coat=0.45, scale=8.5, bump_str=0.68
    )
    mat_obsidian_neutral = make_obsidian_terrain_mat(
        "ObsidianNeutral", (0.028, 0.032, 0.042), (0.010, 0.012, 0.018), rough=0.32, coat=0.3, scale=8.0, bump_str=0.50
    )
    mat_blue_neon = make_pbr_mat("RussiaBlueNeon", (0.12, 0.45, 1.0), rough=0.1, emit_col=(0.15, 0.52, 1.0), emit_str=6.5)
    mat_red_neon = make_pbr_mat("FrontCrimsonNeon", (1.0, 0.10, 0.14), rough=0.1, emit_col=(1.0, 0.12, 0.16), emit_str=8.5)
    mat_gold_beacon = make_pbr_mat("PetrogradGoldBeacon", (1.0, 0.84, 0.28), rough=0.05, emit_col=(1.0, 0.82, 0.25), emit_str=18.0)

    # 1. Dark Ocean Floor + Crisp 3D White Perspective Wireframe Grid
    add_box("OceanFloor", (0.0, 0.0, -0.04), (24.0, 18.0, 0.04), mat_ocean)
    for gx in range(-16, 17, 1):
        add_box(f"GridX_{gx}", (gx * 0.65, 0.0, 0.0), (0.012, 16.0, 0.006), mat_grid)
    for gy in range(-12, 13, 1):
        add_box(f"GridY_{gy}", (0.0, gy * 0.65, 0.0), (21.0, 0.012, 0.006), mat_grid)

    def proj(lon, lat):
        x = (lon - 27.0) * 0.36 + 0.95
        y = (lat - 54.2) * 0.48
        return x, y

    # 2. Real GIS Country Polygons + Neon Glowing Borders from russia_eastern_front_50m.geojson
    geo_path = os.path.join(ASSETS_DIR, "russia_eastern_front_50m.geojson")
    if os.path.exists(geo_path):
        with open(geo_path, "r") as f:
            gdata = json.load(f)

        russian_empire = {"Russia", "Finland", "Estonia", "Latvia", "Belarus", "Ukraine"}
        eastern_front = {"Germany", "Poland", "Lithuania", "Austria", "Hungary", "Romania"}

        for feat in gdata.get("features", []):
            cname = feat.get("properties", {}).get("NAME", "")
            geom = feat.get("geometry", {})
            gtype = geom.get("type")
            coords = geom.get("coordinates", [])
            polys = coords if gtype == "MultiPolygon" else [coords]

            if cname in russian_empire:
                cmat = mat_obsidian_russia
                rmat = mat_blue_neon
                z_off = 0.06
                ext = 0.14
            elif cname in eastern_front:
                cmat = mat_obsidian_front
                rmat = mat_red_neon
                z_off = 0.09
                ext = 0.16
            else:
                cmat = mat_obsidian_neutral
                rmat = None
                z_off = 0.04
                ext = 0.10

            curve_data = bpy.data.curves.new(f"GIS_{cname}", type="CURVE")
            curve_data.dimensions = "2D"
            curve_data.fill_mode = "BOTH"
            curve_data.extrude = ext
            curve_data.bevel_depth = 0.015

            rim_data = bpy.data.curves.new(f"NeonRim_{cname}", type="CURVE") if rmat else None
            if rim_data:
                rim_data.dimensions = "2D"
                rim_data.fill_mode = "NONE"
                rim_data.bevel_depth = 0.032

            has_pts = False
            for poly in polys:
                if not poly:
                    continue
                ring = poly[0]
                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]
                if max(lons) < 10.0 or min(lons) > 49.0 or max(lats) < 42.5 or min(lats) > 66.5:
                    continue
                pts = []
                for pt in ring:
                    lon = min(max(pt[0], 11.0), 47.0)
                    lat = min(max(pt[1], 43.2), 64.8)
                    pts.append(proj(lon, lat))
                if len(pts) >= 4:
                    spline = curve_data.splines.new("POLY")
                    spline.points.add(len(pts) - 1)
                    for idx_p, (px_i, py_i) in enumerate(pts):
                        spline.points[idx_p].co = (px_i, py_i, 0.0, 1.0)
                    spline.use_cyclic_u = True
                    if rim_data:
                        rspline = rim_data.splines.new("POLY")
                        rspline.points.add(len(pts) - 1)
                        for idx_p, (px_i, py_i) in enumerate(pts):
                            rspline.points[idx_p].co = (px_i, py_i, 0.0, 1.0)
                        rspline.use_cyclic_u = True
                    has_pts = True

            if has_pts:
                cobj = bpy.data.objects.new(f"GISMesh_{cname}", curve_data)
                cobj.rotation_mode = "XYZ"
                cobj.location = (0.0, 0.0, z_off)
                cobj.data.materials.append(cmat)
                bpy.context.collection.objects.link(cobj)
                if rim_data:
                    robj = bpy.data.objects.new(f"GISRim_{cname}", rim_data)
                    robj.rotation_mode = "XYZ"
                    robj.location = (0.0, 0.0, z_off + ext + 0.016)
                    robj.data.materials.append(rmat)
                    bpy.context.collection.objects.link(robj)

    # 3. Sculpted 3D Mountain Ridges (Carpathian Arc, Western Front Trenches, Urals/Valdai Hills)
    random.seed(1916)
    mountain_clusters = [
        # Carpathians & Galicia Front
        (-1.4, -2.1, 0.55), (-1.1, -2.3, 0.62), (-0.7, -2.4, 0.52), (-0.3, -2.2, 0.48),
        # East Prussia / Masurian Lakes / Polish Front
        (-1.6, -0.4, 0.42), (-1.3, 0.1, 0.45), (-0.9, 0.5, 0.38),
        # Valdai Hills / Central Russian Upland
        (1.6, 0.8, 0.36), (2.2, 1.2, 0.40), (2.8, 0.4, 0.35), (3.4, -0.4, 0.38),
    ]
    for idx_m, (mx, my, mh) in enumerate(mountain_clusters):
        for sub in range(4):
            ox = mx + random.uniform(-0.35, 0.35)
            oy = my + random.uniform(-0.35, 0.35)
            oh = mh * random.uniform(0.65, 1.15)
            bpy.ops.mesh.primitive_cone_add(
                vertices=7, radius1=random.uniform(0.38, 0.65), radius2=0.03, depth=oh, location=(ox, oy, 0.22 + oh * 0.5)
            )
            mc = bpy.context.active_object
            mc.rotation_mode = "XYZ"
            mc.rotation_euler = (0, 0, random.uniform(0, 6.28))
            mc.data.materials.append(mat_obsidian_front if ox < 0.0 else mat_obsidian_russia)

    # 4. Towering Golden Laser Beacon at Real Coordinates of Petrograd (59.93°N, 30.33°E)
    px, py = proj(30.33, 59.93)
    pin_ring = add_cyl("PetrogradRing", (px, py, 0.24), 0.36, 0.04, mat_gold_beacon, verts=48)
    pin_beam = add_cyl("PetrogradLaserSpire", (px, py, 1.85), 0.048, 3.30, mat_gold_beacon, verts=24)

    # Converging Crimson Plot Trajectory Arrows toward Petrograd
    for sx, sy, rot_z in [(-1.1, 0.3, -32), (-0.3, -1.4, -15), (2.5, -0.6, 22)]:
        add_box(
            f"PlotArrow_{sx}",
            ((sx + px) * 0.5, (sy + py) * 0.5, 0.25),
            (0.06, math.hypot(px - sx, py - sy) * 0.78, 0.03),
            mat_red_neon,
            rot=(0, 0, math.radians(rot_z)),
        )

    # Dramatic War-Room Lighting (Golden Beacon Glow + Red Frontline Glow + Raking Rim Light)
    add_point_light("PetrogradGoldGlow", (px, py, 0.95), 240.0, radius=0.45, col=(1.0, 0.76, 0.22))
    add_point_light("EasternFrontRedGlow", (-0.9, -0.8, 0.95), 220.0, radius=0.85, col=(1.0, 0.12, 0.15))
    add_spot_light("MapRakingKey", (1.5, -6.5, 7.5), (42, 0, 10), 850.0, size=2.5, spot_deg=68.0, col=(0.68, 0.82, 1.0))

    cam = add_camera(loc=(0.2, -7.8, 6.4), rot_deg=(47.5, 0.0, 0.0), lens=32.0)

    def update_frame(f):
        u = smoothstep((f - 900.0) / 299.0)
        cam.location = (
            lerp(-0.35, 0.72, u),
            lerp(-8.15, -6.45, u),
            lerp(6.85, 5.35, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(46.0, 49.5, u)),
            0.0,
            math.radians(lerp(-4.0, 3.0, u)),
        )
        pulse = 1.0 + 0.22 * math.sin(f * 0.3)
        pin_ring.scale = (pulse, pulse, 1.0)

    return scene, update_frame


# ==============================================================================
# SCENE 4 (Frames 1200..1499): 90° TOP-DOWN FORENSIC CRIME SCENE + 3D REVOLVER
# ==============================================================================
def build_scene_4():
    scene = configure_cycles(samples_override=8)
    setup_world((0.002, 0.002, 0.004), 1.0)

    stage, _, _ = create_3d_depth_stage(
        "rasputin_kf_5_crimescene.jpg", "CrimeSceneTopDown3D", width=16.0, height=9.0, nx=192, ny=108, depth_amp=0.80, mode="topdown"
    )

    # Real 3D Webley .455 Revolver + 3 Spent Brass Bullet Casings on the Marble Tiles beside Rasputin's Right Hand!
    mat_gun_steel = make_pbr_mat("WebleySteel3D", (0.78, 0.80, 0.84), rough=0.16, metal=0.92, emit_col=(0.78, 0.80, 0.84), emit_str=0.35)
    mat_brass = make_pbr_mat("BrassShell3D", (1.0, 0.82, 0.28), rough=0.14, metal=0.94, emit_col=(1.0, 0.82, 0.28), emit_str=0.55)

    rev_obj = load_blend_asset("bk_revolver.blend", "CrimeRevolver3D", target_height=0.95, mat=mat_gun_steel)
    if rev_obj:
        rev_obj.location = (1.55, -0.45, 0.32)
        rev_obj.rotation_euler = (0.0, 0.0, math.radians(-38.0))

    for idx_s, (sx, sy) in enumerate([(1.15, -0.78), (1.88, -0.22), (1.42, -0.95)]):
        add_cyl(f"Shell3D_{idx_s}", (sx, sy, 0.28), 0.042, 0.12, mat_brass, verts=16, rot=(math.radians(90), 0, math.radians(idx_s * 52)))

    # Raking warm spotlight across the 3D crime scene
    spot_3d = add_point_light("ForensicSpot3D", (0.0, 0.2, 4.2), 75.0, radius=0.8, col=(1.0, 0.84, 0.55))

    cam = add_camera(loc=(0.0, 0.0, 10.2), rot_deg=(0.0, 0.0, 0.0), lens=35.0)

    def update_frame(f):
        u = smoothstep((f - 1200.0) / 299.0)
        # Dramatic 90° Top-Down Forensic Crane Pull-Up + Slow Counter-Clockwise Spiral
        cam.location = (
            lerp(-0.15, 0.05, u),
            lerp(-0.12, 0.05, u),
            lerp(8.85, 11.45, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(1.5, -0.5, u)),
            math.radians(lerp(-1.2, 0.8, u)),
            math.radians(lerp(-5.5, 4.5, u)),
        )
        spot_3d.data.energy = 75.0 + 12.0 * math.sin(f * 0.25)

    return scene, update_frame


# ==============================================================================
# MAIN RENDER LOOP ACROSS REQUESTED FRAME RANGE (START_FRAME .. END_FRAME)
# ==============================================================================
BUILDERS = {
    0: build_scene_0,
    1: build_scene_1,
    2: build_scene_2,
    3: build_scene_3,
    4: build_scene_4,
}

current_scene_id = None
scene_obj = None
updater_fn = None

for frame_idx in range(START_FRAME, END_FRAME + 1):
    sid = min(4, max(0, frame_idx // 300))
    if sid != current_scene_id:
        current_scene_id = sid
        scene_obj, updater_fn = BUILDERS[sid]()
    updater_fn(frame_idx)
    out_file = os.path.join(OUT_DIR, f"frame_{frame_idx:04d}.png")
    scene_obj.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print(f"Rendered Hybrid 3D frame {frame_idx:04d} (Scene {sid}) -> {out_file}")
