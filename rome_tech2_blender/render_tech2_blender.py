import bpy
import bmesh
import math
import sys
import os
from mathutils import Vector, Euler

# Parse CLI args after "--"
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

start_frame = int(argv[0]) if len(argv) > 0 else 1
end_frame = int(argv[1]) if len(argv) > 1 else 600
asset_dir = os.path.abspath(argv[2]) if len(argv) > 2 else os.path.abspath("rome_ai_3d/assets")
out_dir = os.path.abspath(argv[3]) if len(argv) > 3 else "/tmp/tech2_frames"
os.makedirs(out_dir, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. CLEAN SCENE & CONFIGURE BLENDER 4.3 CYCLES (SHARP NOISE-FREE HYBRID)
# ---------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 6
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
# Disable OIDN denoiser so 1080p photorealistic textures stay 100% razor-sharp!
scene.cycles.use_denoising = False
scene.cycles.sample_clamp_direct = 3.0
scene.cycles.sample_clamp_indirect = 1.8
scene.cycles.max_bounces = 1
scene.cycles.diffuse_bounces = 1
scene.cycles.glossy_bounces = 1
scene.cycles.transmission_bounces = 0
scene.cycles.volume_bounces = 0

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.frame_start = start_frame
scene.frame_end = end_frame
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 95
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'

# Dark Obsidian Studio World
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.015, 0.02, 0.03, 1.0)
    bg_node.inputs[1].default_value = 0.5

# ---------------------------------------------------------------------------
# 2. LOAD RGB & DEPTH-ANYTHING-V2 IMAGES AND BUILD SMOOTHED DEPTH SAMPLER
# ---------------------------------------------------------------------------
W_PLANE = 16.0
H_PLANE = 9.0
GRID_W = 160
GRID_H = 90
DISP_SCALES = [1.85, 1.55, 1.75, 1.45, 1.95]

depth_grids = []
rgb_images = []
depth_images = []

active_shard_shot = (start_frame - 1) // 120
for i in range(1, 6):
    if (i - 1) != active_shard_shot:
        rgb_images.append(None)
        depth_images.append(None)
        depth_grids.append([[0.5] * GRID_W for _ in range(GRID_H)])
        continue
    rgb_path = os.path.join(asset_dir, f"rgb{i}.jpg")
    dep_path = os.path.join(asset_dir, f"depth{i}.png")
    img_rgb = bpy.data.images.load(rgb_path)
    img_dep = bpy.data.images.load(dep_path)
    img_dep.colorspace_settings.name = 'Non-Color'
    rgb_images.append(img_rgb)
    depth_images.append(img_dep)

    dw, dh = img_dep.size
    raw = list(img_dep.pixels)  # flat RGBA float array, bottom-to-top
    # Downsample to GRID_W x GRID_H (top-to-bottom v_img in [0,1])
    g = [[0.0] * GRID_W for _ in range(GRID_H)]
    for gy in range(GRID_H):
        v_img = gy / (GRID_H - 1)
        py = int((1.0 - v_img) * (dh - 1))
        row_offset = py * dw * 4
        for gx in range(GRID_W):
            u = gx / (GRID_W - 1)
            px = int(u * (dw - 1))
            g[gy][gx] = raw[row_offset + px * 4]

    # 2-pass 3x3 box blur on depth grid so 3D surface is silky smooth
    for _ in range(2):
        g2 = [[0.0] * GRID_W for _ in range(GRID_H)]
        for gy in range(GRID_H):
            y0 = max(0, gy - 1)
            y1 = min(GRID_H - 1, gy + 1)
            for gx in range(GRID_W):
                x0 = max(0, gx - 1)
                x1 = min(GRID_W - 1, gx + 1)
                s = 0.0
                c = 0
                for yy in range(y0, y1 + 1):
                    for xx in range(x0, x1 + 1):
                        s += g[yy][xx]
                        c += 1
                g2[gy][gx] = s / c
        g = g2
    depth_grids.append(g)

def sample_depth(shot_idx, u, v_img):
    u = max(0.0, min(1.0, u))
    v_img = max(0.0, min(1.0, v_img))
    g = depth_grids[shot_idx]
    gx = min(GRID_W - 1, max(0, int(round(u * (GRID_W - 1)))))
    gy = min(GRID_H - 1, max(0, int(round(v_img * (GRID_H - 1)))))
    return g[gy][gx]

def map_pt3d(shot_idx, u, v_img, disp_scale=None, z_off=0.08):
    if disp_scale is None:
        disp_scale = DISP_SCALES[shot_idx]
    x = (u - 0.5) * W_PLANE
    y = (0.5 - v_img) * H_PLANE
    d = sample_depth(shot_idx, u, v_img)
    z = (d - 0.45) * disp_scale + z_off
    return Vector((x, y, z))

# ---------------------------------------------------------------------------
# 3. BUILD 5 DISPLACED 3D DIORAMA MESHES WITH THICK CUTAWAY PEDESTAL WALLS
# ---------------------------------------------------------------------------
shot_collections = []
diorama_mats = []

active_shard_shot = (start_frame - 1) // 120
for s_idx in range(5):
    if s_idx != active_shard_shot:
        col = bpy.data.collections.new(f"Shot_{s_idx+1}")
        scene.collection.children.link(col)
        shot_collections.append(col)
        diorama_mats.append(bpy.data.materials.new(f"DummyMat_{s_idx+1}"))
        continue
    col = bpy.data.collections.new(f"Shot_{s_idx+1}")
    scene.collection.children.link(col)
    shot_collections.append(col)

    mesh = bpy.data.meshes.new(f"DioramaMesh_{s_idx+1}")
    bm = bmesh.new()

    verts_grid = [[None] * GRID_W for _ in range(GRID_H)]
    disp = DISP_SCALES[s_idx]
    for gy in range(GRID_H):
        v_img = gy / (GRID_H - 1)
        y = (0.5 - v_img) * H_PLANE
        for gx in range(GRID_W):
            u = gx / (GRID_W - 1)
            x = (u - 0.5) * W_PLANE
            d = depth_grids[s_idx][gy][gx]
            z = (d - 0.45) * disp
            v = bm.verts.new((x, y, z))
            verts_grid[gy][gx] = v

    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    for gy in range(GRID_H - 1):
        v0_uv = 1.0 - (gy / (GRID_H - 1))
        v1_uv = 1.0 - ((gy + 1) / (GRID_H - 1))
        for gx in range(GRID_W - 1):
            u0_uv = gx / (GRID_W - 1)
            u1_uv = (gx + 1) / (GRID_W - 1)
            f = bm.faces.new((
                verts_grid[gy][gx],
                verts_grid[gy][gx + 1],
                verts_grid[gy + 1][gx + 1],
                verts_grid[gy + 1][gx]
            ))
            f.smooth = True
            f.loops[0][uv_layer].uv = (u0_uv, v0_uv)
            f.loops[1][uv_layer].uv = (u1_uv, v0_uv)
            f.loops[2][uv_layer].uv = (u1_uv, v1_uv)
            f.loops[3][uv_layer].uv = (u0_uv, v1_uv)

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(f"Diorama_{s_idx+1}", mesh)
    col.objects.link(obj)

    # Create Hybrid Sharp Photorealistic + Physical Normal Relighting Material
    mat = bpy.data.materials.new(f"DioramaMat_{s_idx+1}")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    n_out = nt.nodes.new("ShaderNodeOutputMaterial")
    n_add = nt.nodes.new("ShaderNodeAddShader")
    n_emit = nt.nodes.new("ShaderNodeEmission")
    n_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    n_rgb = nt.nodes.new("ShaderNodeTexImage")
    n_dep = nt.nodes.new("ShaderNodeTexImage")
    n_bump = nt.nodes.new("ShaderNodeBump")

    n_rgb.image = rgb_images[s_idx]
    n_rgb.extension = 'EXTEND'
    n_dep.image = depth_images[s_idx]
    n_dep.extension = 'EXTEND'

    # Unsharp 0.78 base emission keeps 1080p photorealistic detail 100% crisp,
    # while Principled BSDF + Bump catches dynamic 3D lights & specular highlights!
    n_emit.inputs["Strength"].default_value = 0.78
    n_bsdf.inputs["Roughness"].default_value = 0.32
    n_bsdf.inputs["Metallic"].default_value = 0.10
    n_bump.inputs["Strength"].default_value = 0.65
    n_bump.inputs["Distance"].default_value = 0.25

    nt.links.new(n_rgb.outputs["Color"], n_emit.inputs["Color"])
    nt.links.new(n_rgb.outputs["Color"], n_bsdf.inputs["Base Color"])
    nt.links.new(n_dep.outputs["Color"], n_bump.inputs["Height"])
    nt.links.new(n_bump.outputs["Normal"], n_bsdf.inputs["Normal"])

    if s_idx == 0:
        # Shot 1: Add 3D Holographic Cyan Laser Scan Wave driven by Object X/Y/Z!
        n_texcoord = nt.nodes.new("ShaderNodeTexCoord")
        n_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        n_sub = nt.nodes.new("ShaderNodeMath")
        n_sub.operation = 'SUBTRACT'
        n_sub.name = "ScanCenterNode"
        n_sub.inputs[1].default_value = -6.0  # animated per frame!

        n_abs = nt.nodes.new("ShaderNodeMath")
        n_abs.operation = 'ABSOLUTE'

        n_lt = nt.nodes.new("ShaderNodeMath")
        n_lt.operation = 'LESS_THAN'
        n_lt.inputs[1].default_value = 0.65

        n_scan_emit = nt.nodes.new("ShaderNodeEmission")
        n_scan_emit.inputs["Color"].default_value = (0.0, 0.92, 1.0, 1.0)
        n_scan_emit.inputs["Strength"].default_value = 0.85

        n_mix_scan = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(n_texcoord.outputs["Object"], n_sep.inputs["Vector"])
        nt.links.new(n_sep.outputs["X"], n_sub.inputs[0])
        nt.links.new(n_sub.outputs["Value"], n_abs.inputs[0])
        nt.links.new(n_abs.outputs["Value"], n_lt.inputs[0])
        nt.links.new(n_lt.outputs["Value"], n_mix_scan.inputs["Fac"])
        nt.links.new(n_emit.outputs["Emission"], n_mix_scan.inputs[1])
        nt.links.new(n_scan_emit.outputs["Emission"], n_mix_scan.inputs[2])
        nt.links.new(n_mix_scan.outputs["Shader"], n_add.inputs[0])
    else:
        nt.links.new(n_emit.outputs["Emission"], n_add.inputs[0])

    nt.links.new(n_bsdf.outputs["BSDF"], n_add.inputs[1])
    nt.links.new(n_add.outputs["Shader"], n_out.inputs["Surface"])

    obj.data.materials.append(mat)
    diorama_mats.append(mat)

# ---------------------------------------------------------------------------
# 4. HELPER FUNCTIONS FOR REAL 3D BLENDER TUBES, LIGHTS & 3D EXTRUDED TEXT
# ---------------------------------------------------------------------------
def make_emissive_mat(name, rgba, strength=3.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

mat_cyan_core = make_emissive_mat("CyanCore", (0.78, 0.98, 1.0, 1.0), 4.2)
mat_cyan_glow = make_emissive_mat("CyanGlow", (0.0, 0.82, 1.0, 1.0), 2.2)
mat_gold_core = make_emissive_mat("GoldCore", (1.0, 0.95, 0.75, 1.0), 4.5)
mat_gold_glow = make_emissive_mat("GoldGlow", (1.0, 0.65, 0.05, 1.0), 2.4)
mat_white_text = make_emissive_mat("WhiteText3D", (0.98, 0.99, 1.0, 1.0), 1.65)
mat_gold_text = make_emissive_mat("GoldText3D", (1.0, 0.84, 0.25, 1.0), 1.95)
mat_cyan_text = make_emissive_mat("CyanText3D", (0.25, 0.92, 1.0, 1.0), 1.85)
mat_plate_dark = make_emissive_mat("DarkPlate3D", (0.02, 0.03, 0.05, 1.0), 0.15)

def create_3d_spline(col, name, pts, radius_core, radius_glow, mat_c, mat_g):
    # Core curve
    c_data = bpy.data.curves.new(f"{name}_core", type='CURVE')
    c_data.dimensions = '3D'
    c_data.bevel_depth = radius_core
    c_data.bevel_resolution = 6
    c_data.use_fill_caps = True
    sp = c_data.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for idx, p in enumerate(pts):
        sp.points[idx].co = (p.x, p.y, p.z, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(pts))
    obj_c = bpy.data.objects.new(f"{name}_CoreObj", c_data)
    obj_c.data.materials.append(mat_c)
    col.objects.link(obj_c)

    # Outer halo curve
    g_data = bpy.data.curves.new(f"{name}_glow", type='CURVE')
    g_data.dimensions = '3D'
    g_data.bevel_depth = radius_glow
    g_data.bevel_resolution = 6
    sp_g = g_data.splines.new('NURBS')
    sp_g.points.add(len(pts) - 1)
    for idx, p in enumerate(pts):
        sp_g.points[idx].co = (p.x, p.y, p.z - 0.01, 1.0)
    sp_g.use_endpoint_u = True
    sp_g.order_u = min(4, len(pts))
    obj_g = bpy.data.objects.new(f"{name}_GlowObj", g_data)
    obj_g.data.materials.append(mat_g)
    col.objects.link(obj_g)
    return c_data, g_data

def create_3d_text_badge(col, name, text_str, loc, size=0.42, mat_txt=mat_white_text, with_plate=True, plate_w=None, plate_h=None):
    # Real 3D extruded text in Blender
    t_data = bpy.data.curves.new(name=name, type='FONT')
    t_data.body = text_str
    t_data.size = size
    t_data.extrude = 0.025
    t_data.bevel_depth = 0.005
    t_data.align_x = 'CENTER'
    t_data.align_y = 'CENTER'
    t_obj = bpy.data.objects.new(name, t_data)
    t_obj.location = loc
    t_obj.data.materials.append(mat_txt)
    col.objects.link(t_obj)

    if with_plate:
        pw = plate_w if plate_w else max(1.6, len(text_str) * size * 0.56)
        ph = plate_h if plate_h else size * 1.55
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= pw
            v.co.y *= ph
            v.co.z *= 0.02
        p_mesh = bpy.data.meshes.new(f"{name}_PlateMesh")
        bm.to_mesh(p_mesh)
        bm.free()
        p_obj = bpy.data.objects.new(f"{name}_Plate", p_mesh)
        p_obj.location = (loc.x, loc.y, loc.z - 0.03)
        p_obj.data.materials.append(mat_plate_dark)
        col.objects.link(p_obj)
        # Rim around plate
        return t_obj, p_obj
    return t_obj, None


def add_3d_pointer(col, badge_loc, target_loc, mat_rod):
    c_data = bpy.data.curves.new("PtrRod", type='CURVE')
    c_data.dimensions = '3D'
    c_data.bevel_depth = 0.018
    c_data.bevel_resolution = 4
    sp = c_data.splines.new('POLY')
    sp.points.add(1)
    sp.points[0].co = (badge_loc.x, badge_loc.y - 0.25, badge_loc.z - 0.02, 1.0)
    sp.points[1].co = (target_loc.x, target_loc.y, target_loc.z + 0.04, 1.0)
    rod_obj = bpy.data.objects.new("PtrRodObj", c_data)
    rod_obj.data.materials.append(mat_rod)
    col.objects.link(rod_obj)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.075)
    sm = bpy.data.meshes.new("PtrDotMesh")
    bm.to_mesh(sm)
    bm.free()
    dot_obj = bpy.data.objects.new("PtrDotObj", sm)
    dot_obj.location = (target_loc.x, target_loc.y, target_loc.z + 0.05)
    dot_obj.data.materials.append(mat_rod)
    col.objects.link(dot_obj)

def create_point_light(col, name, color_rgb, energy=180.0, radius=0.6):
    l_data = bpy.data.lights.new(name=name, type='POINT')
    l_data.color = color_rgb
    l_data.energy = energy
    l_data.shadow_soft_size = radius
    l_obj = bpy.data.objects.new(name=name, object_data=l_data)
    col.objects.link(l_obj)
    return l_obj

# ---------------------------------------------------------------------------
# 5. POPULATE 3D SPLINES, 3D LIGHTS & 3D EXTRUDED TEXT FOR ALL 5 SHOTS
# ---------------------------------------------------------------------------

# --- SHOT 1 (0-4s): Golden-Hour Aqueduct + 3D Cyan Specus Stream + Scan Light ---
s1_specus_uv = [
    (0.02, 0.525), (0.18, 0.455), (0.35, 0.380),
    (0.55, 0.295), (0.75, 0.205), (0.95, 0.125)
]
s1_pts = [map_pt3d(0, u, v, z_off=0.06) for (u, v) in s1_specus_uv]
s1_c, s1_g = create_3d_spline(shot_collections[0], "S1_Specus", s1_pts, 0.045, 0.10, mat_cyan_core, mat_cyan_glow)
s1_light = create_point_light(shot_collections[0], "S1_ScanLight", (0.0, 0.9, 1.0), energy=220.0, radius=1.2)
s1_sub, _ = create_3d_text_badge(
    shot_collections[0], "S1_Sub",
    "Roman aqueducts carried fresh water 100 km across valleys",
    Vector((0.0, -3.55, 0.85)), size=0.33, mat_txt=mat_white_text, plate_w=10.8, plate_h=0.58
)

# --- SHOT 2 (4-8s): 3D Dark Obsidian Map + Aqua Marcia 90 km + Dynamic Mountain Light ---
s2_marcia_uv = [
    (0.325, 0.565), (0.390, 0.595), (0.470, 0.625),
    (0.555, 0.640), (0.640, 0.620), (0.720, 0.555),
    (0.805, 0.460), (0.885, 0.365), (0.960, 0.270)
]
s2_pts = [map_pt3d(1, u, v, z_off=0.08) for (u, v) in s2_marcia_uv]
s2_c, s2_g = create_3d_spline(shot_collections[1], "S2_Marcia", s2_pts, 0.055, 0.13, mat_gold_core, mat_gold_glow)
s2_light = create_point_light(shot_collections[1], "S2_MarciaLight", (1.0, 0.65, 0.1), energy=260.0, radius=1.0)

p_marcia_lbl = map_pt3d(1, 0.56, 0.52, z_off=0.35)
s2_lbl_marcia, _ = create_3d_text_badge(shot_collections[1], "S2_MarciaLbl", "Aqua Marcia", p_marcia_lbl, size=0.48, mat_txt=mat_gold_text)

p_pop_lbl = map_pt3d(1, 0.15, 0.53, z_off=0.35)
s2_lbl_pop, _ = create_3d_text_badge(shot_collections[1], "S2_PopLbl", "1,000,000", p_pop_lbl, size=0.44, mat_txt=mat_white_text, plate_w=2.8, plate_h=0.68)
add_3d_pointer(shot_collections[1], p_pop_lbl, map_pt3d(1, 0.325, 0.565, z_off=0.08), mat_white_text)

s2_lbl_km, s2_plate_km = create_3d_text_badge(shot_collections[1], "S2_KmLbl", "90 km (55 mi)", s2_pts[-1] + Vector((0, 0.55, 0.35)), size=0.40, mat_txt=mat_gold_text, plate_w=3.1, plate_h=0.65)
s2_sub, _ = create_3d_text_badge(
    shot_collections[1], "S2_Sub",
    "The Aqua Marcia spanned 90 km, supplying 1,000,000 citizens",
    Vector((0.0, -3.55, 0.85)), size=0.33, mat_txt=mat_gold_text, plate_w=11.0, plate_h=0.58
)

# --- SHOT 3 (8-12s): 3D Geological Cutaway Diorama + Cyan Flow to Rome Temple ---
s3_flow_uv = [
    (0.86, 0.51), (0.76, 0.49), (0.64, 0.45),
    (0.48, 0.39), (0.31, 0.33), (0.16, 0.27), (0.08, 0.24)
]
s3_pts = [map_pt3d(2, u, v, z_off=0.09) for (u, v) in s3_flow_uv]
s3_c, s3_g = create_3d_spline(shot_collections[2], "S3_Flow", s3_pts, 0.065, 0.15, mat_cyan_core, mat_cyan_glow)
s3_light = create_point_light(shot_collections[2], "S3_FlowLight", (0.0, 0.9, 1.0), energy=260.0, radius=1.1)

p_ws = map_pt3d(2, 0.85, 0.28, z_off=0.35)
create_3d_text_badge(shot_collections[2], "S3_WS", "Water source", p_ws, size=0.44, mat_txt=mat_cyan_text, plate_w=3.2, plate_h=0.68)
add_3d_pointer(shot_collections[2], p_ws, map_pt3d(2, 0.86, 0.51, z_off=0.09), mat_cyan_text)

p_rome = map_pt3d(2, 0.13, 0.14, z_off=0.35)
create_3d_text_badge(shot_collections[2], "S3_Rome", "Rome", p_rome, size=0.46, mat_txt=mat_white_text, plate_w=2.0, plate_h=0.68)
add_3d_pointer(shot_collections[2], p_rome, map_pt3d(2, 0.08, 0.24, z_off=0.09), mat_white_text)

s3_sub, _ = create_3d_text_badge(
    shot_collections[2], "S3_Sub",
    "From mountain springs, stone bridges guided water by gravity alone",
    Vector((0.0, -3.55, 0.85)), size=0.33, mat_txt=mat_white_text, plate_w=11.4, plate_h=0.58
)

# --- SHOT 4 (12-16s): 3D Studio Aqueduct + Golden Laser Slope ---
s4_laser_uv = [
    (0.02, 0.545), (0.25, 0.455), (0.50, 0.355),
    (0.75, 0.250), (0.98, 0.145)
]
s4_pts = [map_pt3d(3, u, v, z_off=0.09) for (u, v) in s4_laser_uv]
s4_c, s4_g = create_3d_spline(shot_collections[3], "S4_Laser", s4_pts, 0.048, 0.12, mat_gold_core, mat_gold_glow)
s4_light = create_point_light(shot_collections[3], "S4_LaserLight", (1.0, 0.8, 0.15), energy=240.0, radius=1.1)

p_slope = map_pt3d(3, 0.44, 0.23, z_off=0.35)
s4_lbl_slope, _ = create_3d_text_badge(shot_collections[3], "S4_SlopeLbl", "1.5-3 meters per km", p_slope, size=0.48, mat_txt=mat_gold_text, plate_w=5.2, plate_h=0.75)
add_3d_pointer(shot_collections[3], p_slope, map_pt3d(3, 0.50, 0.355, z_off=0.09), mat_gold_text)

s4_sub, _ = create_3d_text_badge(
    shot_collections[3], "S4_Sub",
    "Aqueducts dropped just 1.5 to 3 meters per kilometer (0.09-0.17 deg)",
    Vector((0.0, -3.55, 0.85)), size=0.33, mat_txt=mat_gold_text, plate_w=11.8, plate_h=0.58
)

# --- SHOT 5 (16-20s): 3D Valley Cutaway + Header Tank + Pressurized Cyan U-Siphon ---
s5_siphon_uv = [
    (0.11, 0.47), (0.15, 0.55), (0.19, 0.68),
    (0.24, 0.83), (0.30, 0.94), (0.45, 0.96),
    (0.60, 0.94), (0.67, 0.82), (0.74, 0.66), (0.81, 0.52)
]
s5_pts = [map_pt3d(4, u, v, z_off=0.09) for (u, v) in s5_siphon_uv]
s5_c, s5_g = create_3d_spline(shot_collections[4], "S5_Siphon", s5_pts, 0.065, 0.15, mat_cyan_core, mat_cyan_glow)
s5_light = create_point_light(shot_collections[4], "S5_SiphonLight", (0.0, 0.9, 1.0), energy=260.0, radius=1.1)

p_ht = map_pt3d(4, 0.14, 0.34, z_off=0.35)
create_3d_text_badge(shot_collections[4], "S5_HT", "Header tank", p_ht, size=0.42, mat_txt=mat_white_text, plate_w=3.1, plate_h=0.66)
add_3d_pointer(shot_collections[4], p_ht, map_pt3d(4, 0.11, 0.47, z_off=0.09), mat_white_text)

p_50m = map_pt3d(4, 0.47, 0.39, z_off=0.35)
create_3d_text_badge(shot_collections[4], "S5_50M", "50 m (164 ft)", p_50m, size=0.44, mat_txt=mat_cyan_text, plate_w=3.2, plate_h=0.68)
add_3d_pointer(shot_collections[4], p_50m, map_pt3d(4, 0.45, 0.96, z_off=0.09), mat_cyan_text)

s5_sub, _ = create_3d_text_badge(
    shot_collections[4], "S5_Sub",
    "Across deep valleys, pressurized siphons drove water 50 meters uphill",
    Vector((0.0, -3.55, 0.85)), size=0.33, mat_txt=mat_cyan_text, plate_w=11.8, plate_h=0.58
)

# ---------------------------------------------------------------------------
# 6. CAMERA SETUP & FRAME-BY-FRAME 30FPS ANIMATION LOOP
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("MasterCam")
cam_data.lens = 42.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("MasterCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)

def eval_pts(pts, u):
    u = max(0.0, min(1.0, u))
    f = u * (len(pts) - 1)
    i0 = int(f)
    i1 = min(len(pts) - 1, i0 + 1)
    return pts[i0].lerp(pts[i1], f - i0)

def look_at(obj, target):
    dx = target.x - obj.location.x
    dy = target.y - obj.location.y
    dz = max(0.1, obj.location.z - target.z)
    rx = math.atan2(dy, dz)
    ry = -math.atan2(dx, dz)
    obj.rotation_euler = Euler((rx, ry, 0.0), 'XYZ')

for f in range(start_frame, end_frame + 1):
    t = (f - 1) / 30.0
    if t < 4.0:
        active_idx = 0
        u = t / 4.0
    elif t < 8.0:
        active_idx = 1
        u = (t - 4.0) / 4.0
    elif t < 12.0:
        active_idx = 2
        u = (t - 8.0) / 4.0
    elif t < 16.0:
        active_idx = 3
        u = (t - 12.0) / 4.0
    else:
        active_idx = 4
        u = min(1.0, (t - 16.0) / 4.0)

    # Toggle active collection
    for idx, col in enumerate(shot_collections):
        col.hide_render = (idx != active_idx)

    e = smoothstep(0.0, 1.0, u)

    if active_idx == 0:
        cam_obj.location = Vector((-0.55 + e * 1.10, -0.30 + e * 0.50, 12.5 - e * 1.35))
        look_at(cam_obj, Vector((0.0 + e * 0.25, 0.0 + e * 0.10, 0.2)))
        scan_x = -8.5 + u * 18.0
        scan_node = diorama_mats[0].node_tree.nodes.get("ScanCenterNode")
        if scan_node:
            scan_node.inputs[1].default_value = scan_x
        prog = smoothstep(0.05, 0.92, u)
        s1_c.bevel_factor_end = prog
        s1_g.bevel_factor_end = prog
        tip = eval_pts(s1_pts, prog)
        s1_light.location = tip + Vector((0, 0, 0.55))

    elif active_idx == 1:
        cam_obj.location = Vector((0.45 - e * 0.90, -0.50 + e * 0.55, 12.4 - e * 1.25))
        look_at(cam_obj, Vector((0.15 - e * 0.20, 0.0, 0.15)))
        prog = smoothstep(0.06, 0.88, u)
        s2_c.bevel_factor_end = prog
        s2_g.bevel_factor_end = prog
        tip = eval_pts(s2_pts, prog)
        s2_light.location = tip + Vector((0, 0, 0.50))
        km = int(round(prog * 90))
        mi = int(round(prog * 55))
        s2_lbl_km.data.body = f"{km} km ({mi} mi)"
        s2_lbl_km.location = tip + Vector((0.0, 0.58, 0.35))
        if s2_plate_km:
            s2_plate_km.location = s2_lbl_km.location - Vector((0, 0, 0.03))
        pop_val = int(round(smoothstep(0.05, 0.55, u) * 1000000))
        s2_lbl_pop.data.body = f"{pop_val:,}"

    elif active_idx == 2:
        cam_obj.location = Vector((0.55 - e * 1.15, -0.35 + e * 0.45, 12.4 - e * 1.20))
        look_at(cam_obj, Vector((0.15 - e * 0.35, 0.05, 0.20)))
        prog = smoothstep(0.08, 0.90, u)
        s3_c.bevel_factor_end = prog
        s3_g.bevel_factor_end = prog
        tip = eval_pts(s3_pts, prog)
        s3_light.location = tip + Vector((0, 0, 0.55))

    elif active_idx == 3:
        cam_obj.location = Vector((-0.50 + e * 1.05, -0.20 + e * 0.35, 12.5 - e * 1.20))
        look_at(cam_obj, Vector((0.0, 0.08, 0.15)))
        prog = smoothstep(0.05, 0.88, u)
        s4_c.bevel_factor_end = prog
        s4_g.bevel_factor_end = prog
        tip = eval_pts(s4_pts, prog)
        s4_light.location = tip + Vector((0, 0, 0.50))
        if u < 0.52:
            s4_lbl_slope.data.body = "1.5-3 meters per km"
        else:
            s4_lbl_slope.data.body = "0.09 - 0.17 deg"

    elif active_idx == 4:
        cam_obj.location = Vector((-0.45 + e * 0.90, -0.40 + e * 0.50, 12.4 - e * 1.25))
        look_at(cam_obj, Vector((0.0, -0.05, 0.15)))
        prog = smoothstep(0.06, 0.92, u)
        s5_c.bevel_factor_end = prog
        s5_g.bevel_factor_end = prog
        tip = eval_pts(s5_pts, prog)
        s5_light.location = tip + Vector((0, 0, 0.55))

    scene.frame_set(f)
    scene.render.filepath = os.path.join(out_dir, f"frame_{f:04d}.jpg")
    bpy.ops.render.render(write_still=True)
    if (f - start_frame) % 10 == 0 or f == end_frame:
        print(f"Rendered Blender Tech2 frame {f} ({start_frame}..{end_frame})")
