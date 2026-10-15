import bpy
import bmesh
import math
import sys
import os
from mathutils import Vector, Euler

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
# 1. CLEAN SCENE & CONFIGURE BLENDER 4.3.2 CYCLES (ULTRA-FAST DIRECT 3D RAY)
# ---------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 4
scene.cycles.use_adaptive_sampling = False
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 0
scene.cycles.diffuse_bounces = 0
scene.cycles.glossy_bounces = 0

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

world = bpy.data.worlds.new("StudioWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.015, 0.02, 0.03, 1.0)
    bg_node.inputs[1].default_value = 0.5

# ---------------------------------------------------------------------------
# 2. TRUE CAMERA-PROJECTION UNPROJECTION GEOMETRY (Z_REF = 18.6667 FOR LENS=42)
# ---------------------------------------------------------------------------
W_PLANE = 16.0
H_PLANE = 9.0
Z_REF = 18.6667  # Exact distance where 16x9 plane fills 1920x1080 with 42mm lens (36mm sensor)
GRID_W = 160
GRID_H = 90
DISP_SCALES = [2.20, 1.80, 2.00, 1.65, 2.25]

active_shard_shot = (start_frame - 1) // 120
depth_grids = []
rgb_images = []
depth_images = []

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
    raw = list(img_dep.pixels)
    g = [[0.0] * GRID_W for _ in range(GRID_H)]
    for gy in range(GRID_H):
        v_img = gy / (GRID_H - 1)
        py = int((1.0 - v_img) * (dh - 1))
        row_offset = py * dw * 4
        for gx in range(GRID_W):
            u = gx / (GRID_W - 1)
            px = int(u * (dw - 1))
            g[gy][gx] = raw[row_offset + px * 4]

    for _ in range(2):
        g2 = [[0.0] * GRID_W for _ in range(GRID_H)]
        for gy in range(GRID_H):
            y0, y1 = max(0, gy - 1), min(GRID_H - 1, gy + 1)
            for gx in range(GRID_W):
                x0, x1 = max(0, gx - 1), min(GRID_W - 1, gx + 1)
                s, c = 0.0, 0
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

def map_pt3d(shot_idx, u, v_img, z_off=0.06):
    disp = DISP_SCALES[shot_idx]
    d = sample_depth(shot_idx, u, v_img)
    z_surf = (d - 0.45) * disp
    z = z_surf + z_off
    # Frustum unprojection so point at depth z_surf aligns 100% with image UV (u, v_img)!
    persp_scale = (Z_REF - z_surf) / Z_REF
    x = (u - 0.5) * W_PLANE * persp_scale
    y = (0.5 - v_img) * H_PLANE * persp_scale
    return Vector((x, y, z))

# ---------------------------------------------------------------------------
# 3. BUILD DISPLACED 3D DIORAMA MESH FOR ACTIVE SHOT
# ---------------------------------------------------------------------------
shot_collections = []
diorama_mats = []

for s_idx in range(5):
    col = bpy.data.collections.new(f"Shot_{s_idx+1}")
    scene.collection.children.link(col)
    shot_collections.append(col)
    if s_idx != active_shard_shot:
        diorama_mats.append(bpy.data.materials.new(f"DummyMat_{s_idx+1}"))
        continue

    mesh = bpy.data.meshes.new(f"DioramaMesh_{s_idx+1}")
    bm = bmesh.new()
    verts_grid = [[None] * GRID_W for _ in range(GRID_H)]
    disp = DISP_SCALES[s_idx]

    for gy in range(GRID_H):
        v_img = gy / (GRID_H - 1)
        for gx in range(GRID_W):
            u = gx / (GRID_W - 1)
            d = depth_grids[s_idx][gy][gx]
            z_surf = (d - 0.45) * disp
            persp_scale = (Z_REF - z_surf) / Z_REF
            x = (u - 0.5) * W_PLANE * persp_scale
            y = (0.5 - v_img) * H_PLANE * persp_scale
            verts_grid[gy][gx] = bm.verts.new((x, y, z_surf))

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

    n_emit.inputs["Strength"].default_value = 0.84
    n_bsdf.inputs["Roughness"].default_value = 0.30
    n_bsdf.inputs["Metallic"].default_value = 0.12
    n_bump.inputs["Strength"].default_value = 0.65
    n_bump.inputs["Distance"].default_value = 0.25

    nt.links.new(n_rgb.outputs["Color"], n_emit.inputs["Color"])
    nt.links.new(n_rgb.outputs["Color"], n_bsdf.inputs["Base Color"])
    nt.links.new(n_dep.outputs["Color"], n_bump.inputs["Height"])
    nt.links.new(n_bump.outputs["Normal"], n_bsdf.inputs["Normal"])

    if s_idx == 0:
        # Soft Additive 3D Holographic Cyan Scan Wave (preserves 100% of stone texture underneath!)
        n_texcoord = nt.nodes.new("ShaderNodeTexCoord")
        n_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        n_sub = nt.nodes.new("ShaderNodeMath")
        n_sub.operation = 'SUBTRACT'
        n_sub.name = "ScanCenterNode"
        n_sub.inputs[1].default_value = -6.0

        n_abs = nt.nodes.new("ShaderNodeMath")
        n_abs.operation = 'ABSOLUTE'

        # Smooth falloff: max(0, 1.0 - abs(X - scan_x) / 1.15)^2 * 0.65
        n_div = nt.nodes.new("ShaderNodeMath")
        n_div.operation = 'DIVIDE'
        n_div.inputs[1].default_value = 1.15

        n_inv = nt.nodes.new("ShaderNodeMath")
        n_inv.operation = 'SUBTRACT'
        n_inv.inputs[0].default_value = 1.0
        n_inv.use_clamp = True

        n_pow = nt.nodes.new("ShaderNodeMath")
        n_pow.operation = 'POWER'
        n_pow.inputs[1].default_value = 2.5

        n_mul = nt.nodes.new("ShaderNodeMath")
        n_mul.operation = 'MULTIPLY'
        n_mul.inputs[1].default_value = 0.65

        n_scan_emit = nt.nodes.new("ShaderNodeEmission")
        n_scan_emit.inputs["Color"].default_value = (0.0, 0.90, 1.0, 1.0)

        n_add_scan = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(n_texcoord.outputs["Object"], n_sep.inputs["Vector"])
        nt.links.new(n_sep.outputs["X"], n_sub.inputs[0])
        nt.links.new(n_sub.outputs["Value"], n_abs.inputs[0])
        nt.links.new(n_abs.outputs["Value"], n_div.inputs[0])
        nt.links.new(n_div.outputs["Value"], n_inv.inputs[1])
        nt.links.new(n_inv.outputs["Value"], n_pow.inputs[0])
        nt.links.new(n_pow.outputs["Value"], n_mul.inputs[0])
        nt.links.new(n_mul.outputs["Value"], n_scan_emit.inputs["Strength"])

        nt.links.new(n_emit.outputs["Emission"], n_add_scan.inputs[0])
        nt.links.new(n_scan_emit.outputs["Emission"], n_add_scan.inputs[1])
        nt.links.new(n_add_scan.outputs["Shader"], n_add.inputs[0])
    else:
        nt.links.new(n_emit.outputs["Emission"], n_add.inputs[0])

    nt.links.new(n_bsdf.outputs["BSDF"], n_add.inputs[1])
    nt.links.new(n_add.outputs["Shader"], n_out.inputs["Surface"])

    obj.data.materials.append(mat)
    diorama_mats.append(mat)

# ---------------------------------------------------------------------------
# 4. HELPERS FOR 3D NURBS TUBES, 3D POINTERS & 3D EXTRUDED TEXT
# ---------------------------------------------------------------------------
def make_emissive_mat(name, rgba, strength=1.8):
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

mat_cyan_core = make_emissive_mat("CyanCore", (0.82, 0.99, 1.0, 1.0), 2.5)
mat_cyan_glow = make_emissive_mat("CyanGlow", (0.0, 0.78, 1.0, 1.0), 1.4)
mat_gold_core = make_emissive_mat("GoldCore", (1.0, 0.96, 0.78, 1.0), 2.6)
mat_gold_glow = make_emissive_mat("GoldGlow", (1.0, 0.65, 0.05, 1.0), 1.5)
mat_white_text = make_emissive_mat("WhiteText3D", (0.98, 0.99, 1.0, 1.0), 1.35)
mat_gold_text = make_emissive_mat("GoldText3D", (1.0, 0.84, 0.25, 1.0), 1.55)
mat_cyan_text = make_emissive_mat("CyanText3D", (0.25, 0.92, 1.0, 1.0), 1.50)
mat_plate_dark = make_emissive_mat("DarkPlate3D", (0.02, 0.03, 0.05, 1.0), 0.12)

def create_3d_spline(col, name, pts, radius_core, radius_glow, mat_c, mat_g):
    c_data = bpy.data.curves.new(f"{name}_core", type='CURVE')
    c_data.dimensions = '3D'
    c_data.bevel_depth = radius_core
    c_data.bevel_resolution = 4
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

    g_data = bpy.data.curves.new(f"{name}_glow", type='CURVE')
    g_data.dimensions = '3D'
    g_data.bevel_depth = radius_glow
    g_data.bevel_resolution = 4
    sp_g = g_data.splines.new('NURBS')
    sp_g.points.add(len(pts) - 1)
    for idx, p in enumerate(pts):
        sp_g.points[idx].co = (p.x, p.y, p.z - 0.015, 1.0)
    sp_g.use_endpoint_u = True
    sp_g.order_u = min(4, len(pts))
    obj_g = bpy.data.objects.new(f"{name}_GlowObj", g_data)
    obj_g.data.materials.append(mat_g)
    col.objects.link(obj_g)
    return c_data, g_data

def create_3d_text_badge(col, name, text_str, loc, size=0.38, mat_txt=mat_white_text, with_plate=True, plate_w=None, plate_h=None):
    t_data = bpy.data.curves.new(name=name, type='FONT')
    t_data.body = text_str
    t_data.size = size
    t_data.extrude = 0.02
    t_data.bevel_depth = 0.004
    t_data.align_x = 'CENTER'
    t_data.align_y = 'CENTER'
    t_obj = bpy.data.objects.new(name, t_data)
    t_obj.location = loc
    t_obj.data.materials.append(mat_txt)
    col.objects.link(t_obj)

    if with_plate:
        pw = plate_w if plate_w else max(1.5, len(text_str) * size * 0.54)
        ph = plate_h if plate_h else size * 1.50
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= pw
            v.co.y *= ph
            v.co.z *= 0.015
        p_mesh = bpy.data.meshes.new(f"{name}_PlateMesh")
        bm.to_mesh(p_mesh)
        bm.free()
        p_obj = bpy.data.objects.new(f"{name}_Plate", p_mesh)
        p_obj.location = (loc.x, loc.y, loc.z - 0.025)
        p_obj.data.materials.append(mat_plate_dark)
        col.objects.link(p_obj)
        return t_obj, p_obj
    return t_obj, None

def add_3d_pointer(col, badge_loc, target_loc, mat_rod):
    c_data = bpy.data.curves.new("PtrRod", type='CURVE')
    c_data.dimensions = '3D'
    c_data.bevel_depth = 0.014
    c_data.bevel_resolution = 3
    sp = c_data.splines.new('POLY')
    sp.points.add(1)
    sp.points[0].co = (badge_loc.x, badge_loc.y - 0.22, badge_loc.z - 0.02, 1.0)
    sp.points[1].co = (target_loc.x, target_loc.y, target_loc.z + 0.03, 1.0)
    rod_obj = bpy.data.objects.new("PtrRodObj", c_data)
    rod_obj.data.materials.append(mat_rod)
    col.objects.link(rod_obj)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.06)
    sm = bpy.data.meshes.new("PtrDotMesh")
    bm.to_mesh(sm)
    bm.free()
    dot_obj = bpy.data.objects.new("PtrDotObj", sm)
    dot_obj.location = (target_loc.x, target_loc.y, target_loc.z + 0.04)
    dot_obj.data.materials.append(mat_rod)
    col.objects.link(dot_obj)

def create_point_light(col, name, color_rgb, energy=220.0, radius=0.8):
    l_data = bpy.data.lights.new(name=name, type='POINT')
    l_data.color = color_rgb
    l_data.energy = energy
    l_data.shadow_soft_size = radius
    l_obj = bpy.data.objects.new(name=name, object_data=l_data)
    col.objects.link(l_obj)
    return l_obj

# ---------------------------------------------------------------------------
# 5. BUILD ACTIVE SHOT 3D OBJECTS (EXACT FRUSTUM-UNPROJECTED 3D ANCHORS)
# ---------------------------------------------------------------------------
if active_shard_shot == 0:
    s1_specus_uv = [
        (0.04, 0.525), (0.18, 0.455), (0.35, 0.380),
        (0.55, 0.295), (0.75, 0.205), (0.93, 0.130)
    ]
    s1_pts = [map_pt3d(0, u, v, z_off=0.05) for (u, v) in s1_specus_uv]
    s1_c, s1_g = create_3d_spline(shot_collections[0], "S1_Specus", s1_pts, 0.038, 0.085, mat_cyan_core, mat_cyan_glow)
    s1_light = create_point_light(shot_collections[0], "S1_ScanLight", (0.0, 0.9, 1.0), energy=220.0, radius=1.2)
    s_sub, s_sub_p = create_3d_text_badge(
        shot_collections[0], "S1_Sub",
        "Roman aqueducts carried fresh water 100 km across valleys",
        Vector((0.0, -3.55, 1.2)), size=0.31, mat_txt=mat_white_text, plate_w=10.5, plate_h=0.54
    )

elif active_shard_shot == 1:
    s2_marcia_uv = [
        (0.325, 0.565), (0.390, 0.595), (0.470, 0.625),
        (0.555, 0.640), (0.640, 0.620), (0.720, 0.555),
        (0.805, 0.460), (0.875, 0.375), (0.930, 0.300)
    ]
    s2_pts = [map_pt3d(1, u, v, z_off=0.06) for (u, v) in s2_marcia_uv]
    s2_c, s2_g = create_3d_spline(shot_collections[1], "S2_Marcia", s2_pts, 0.045, 0.105, mat_gold_core, mat_gold_glow)
    s2_light = create_point_light(shot_collections[1], "S2_MarciaLight", (1.0, 0.65, 0.1), energy=260.0, radius=1.0)

    p_marcia_lbl = map_pt3d(1, 0.56, 0.50, z_off=0.25)
    create_3d_text_badge(shot_collections[1], "S2_MarciaLbl", "Aqua Marcia", p_marcia_lbl, size=0.42, mat_txt=mat_gold_text)

    p_pop_lbl = map_pt3d(1, 0.18, 0.52, z_off=0.25)
    s2_lbl_pop, _ = create_3d_text_badge(shot_collections[1], "S2_PopLbl", "1,000,000", p_pop_lbl, size=0.38, mat_txt=mat_white_text, plate_w=2.5, plate_h=0.60)
    add_3d_pointer(shot_collections[1], p_pop_lbl, map_pt3d(1, 0.325, 0.565, z_off=0.06), mat_white_text)

    s2_lbl_km, s2_plate_km = create_3d_text_badge(shot_collections[1], "S2_KmLbl", "90 km (55 mi)", s2_pts[-1] + Vector((-0.6, 0.45, 0.25)), size=0.35, mat_txt=mat_gold_text, plate_w=2.8, plate_h=0.58)
    s_sub, s_sub_p = create_3d_text_badge(
        shot_collections[1], "S2_Sub",
        "The Aqua Marcia spanned 90 km, supplying 1,000,000 citizens",
        Vector((0.0, -3.55, 1.2)), size=0.31, mat_txt=mat_gold_text, plate_w=10.8, plate_h=0.54
    )

elif active_shard_shot == 2:
    s3_flow_uv = [
        (0.84, 0.51), (0.75, 0.49), (0.63, 0.45),
        (0.48, 0.39), (0.31, 0.33), (0.17, 0.27), (0.10, 0.24)
    ]
    s3_pts = [map_pt3d(2, u, v, z_off=0.06) for (u, v) in s3_flow_uv]
    s3_c, s3_g = create_3d_spline(shot_collections[2], "S3_Flow", s3_pts, 0.052, 0.115, mat_cyan_core, mat_cyan_glow)
    s3_light = create_point_light(shot_collections[2], "S3_FlowLight", (0.0, 0.9, 1.0), energy=260.0, radius=1.1)

    p_ws = map_pt3d(2, 0.80, 0.28, z_off=0.25)
    create_3d_text_badge(shot_collections[2], "S3_WS", "Water source", p_ws, size=0.38, mat_txt=mat_cyan_text, plate_w=2.8, plate_h=0.60)
    add_3d_pointer(shot_collections[2], p_ws, map_pt3d(2, 0.84, 0.51, z_off=0.06), mat_cyan_text)

    p_rome = map_pt3d(2, 0.16, 0.16, z_off=0.25)
    create_3d_text_badge(shot_collections[2], "S3_Rome", "Rome", p_rome, size=0.40, mat_txt=mat_white_text, plate_w=1.8, plate_h=0.60)
    add_3d_pointer(shot_collections[2], p_rome, map_pt3d(2, 0.10, 0.24, z_off=0.06), mat_white_text)

    s_sub, s_sub_p = create_3d_text_badge(
        shot_collections[2], "S3_Sub",
        "From mountain springs, stone bridges guided water by gravity alone",
        Vector((0.0, -3.55, 1.2)), size=0.31, mat_txt=mat_white_text, plate_w=11.2, plate_h=0.54
    )

elif active_shard_shot == 3:
    s4_laser_uv = [
        (0.04, 0.545), (0.25, 0.455), (0.50, 0.355),
        (0.75, 0.250), (0.95, 0.155)
    ]
    s4_pts = [map_pt3d(3, u, v, z_off=0.06) for (u, v) in s4_laser_uv]
    s4_c, s4_g = create_3d_spline(shot_collections[3], "S4_Laser", s4_pts, 0.040, 0.095, mat_gold_core, mat_gold_glow)
    s4_light = create_point_light(shot_collections[3], "S4_LaserLight", (1.0, 0.8, 0.15), energy=240.0, radius=1.1)

    p_slope = map_pt3d(3, 0.44, 0.22, z_off=0.25)
    s4_lbl_slope, _ = create_3d_text_badge(shot_collections[3], "S4_SlopeLbl", "1.5-3 meters per km", p_slope, size=0.42, mat_txt=mat_gold_text, plate_w=4.6, plate_h=0.66)
    add_3d_pointer(shot_collections[3], p_slope, map_pt3d(3, 0.50, 0.355, z_off=0.06), mat_gold_text)

    s_sub, s_sub_p = create_3d_text_badge(
        shot_collections[3], "S4_Sub",
        "Aqueducts dropped just 1.5 to 3 meters per kilometer (0.09-0.17 deg)",
        Vector((0.0, -3.55, 1.2)), size=0.31, mat_txt=mat_gold_text, plate_w=11.5, plate_h=0.54
    )

elif active_shard_shot == 4:
    s5_siphon_uv = [
        (0.13, 0.47), (0.16, 0.55), (0.20, 0.67),
        (0.25, 0.80), (0.32, 0.88), (0.45, 0.90),
        (0.58, 0.88), (0.66, 0.78), (0.73, 0.64), (0.80, 0.52)
    ]
    s5_pts = [map_pt3d(4, u, v, z_off=0.06) for (u, v) in s5_siphon_uv]
    s5_c, s5_g = create_3d_spline(shot_collections[4], "S5_Siphon", s5_pts, 0.052, 0.115, mat_cyan_core, mat_cyan_glow)
    s5_light = create_point_light(shot_collections[4], "S5_SiphonLight", (0.0, 0.9, 1.0), energy=260.0, radius=1.1)

    p_ht = map_pt3d(4, 0.18, 0.32, z_off=0.25)
    create_3d_text_badge(shot_collections[4], "S5_HT", "Header tank", p_ht, size=0.38, mat_txt=mat_white_text, plate_w=2.8, plate_h=0.60)
    add_3d_pointer(shot_collections[4], p_ht, map_pt3d(4, 0.13, 0.47, z_off=0.06), mat_white_text)

    p_50m = map_pt3d(4, 0.46, 0.36, z_off=0.25)
    create_3d_text_badge(shot_collections[4], "S5_50M", "50 m (164 ft)", p_50m, size=0.40, mat_txt=mat_cyan_text, plate_w=2.9, plate_h=0.62)
    add_3d_pointer(shot_collections[4], p_50m, map_pt3d(4, 0.45, 0.90, z_off=0.06), mat_cyan_text)

    s_sub, s_sub_p = create_3d_text_badge(
        shot_collections[4], "S5_Sub",
        "Across deep valleys, pressurized siphons drove water 50 meters uphill",
        Vector((0.0, -3.55, 1.2)), size=0.31, mat_txt=mat_cyan_text, plate_w=11.5, plate_h=0.54
    )

# ---------------------------------------------------------------------------
# 6. UPRIGHT 3D CAMERA ANIMATION (Z: 17.5 -> 16.1 FOR FULL 16:9 FRAMING)
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
    active_idx = active_shard_shot
    u = min(1.0, max(0.0, (t - active_idx * 4.0) / 4.0))

    for idx, col in enumerate(shot_collections):
        col.hide_render = (idx != active_idx)

    e = smoothstep(0.0, 1.0, u)

    if active_idx == 0:
        cam_obj.location = Vector((-0.55 + e * 1.10, -0.25 + e * 0.45, 17.5 - e * 1.35))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        scan_x = -7.5 + u * 15.5
        scan_node = diorama_mats[0].node_tree.nodes.get("ScanCenterNode")
        if scan_node:
            scan_node.inputs[1].default_value = scan_x
        prog = smoothstep(0.05, 0.92, u)
        s1_c.bevel_factor_end = prog
        s1_g.bevel_factor_end = prog
        tip = eval_pts(s1_pts, prog)
        s1_light.location = tip + Vector((0, 0, 0.55))

    elif active_idx == 1:
        cam_obj.location = Vector((0.45 - e * 0.90, -0.30 + e * 0.45, 17.5 - e * 1.30))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        prog = smoothstep(0.06, 0.88, u)
        s2_c.bevel_factor_end = prog
        s2_g.bevel_factor_end = prog
        tip = eval_pts(s2_pts, prog)
        s2_light.location = tip + Vector((0, 0, 0.50))
        km = int(round(prog * 90))
        mi = int(round(prog * 55))
        s2_lbl_km.data.body = f"{km} km ({mi} mi)"
        s2_lbl_km.location = Vector((min(4.8, max(-4.8, tip.x - 0.5)), min(3.2, tip.y + 0.55), tip.z + 0.25))
        if s2_plate_km:
            s2_plate_km.location = s2_lbl_km.location - Vector((0, 0, 0.025))
        pop_val = int(round(smoothstep(0.05, 0.55, u) * 1000000))
        s2_lbl_pop.data.body = f"{pop_val:,}"

    elif active_idx == 2:
        cam_obj.location = Vector((0.50 - e * 1.00, -0.25 + e * 0.40, 17.5 - e * 1.25))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        prog = smoothstep(0.08, 0.90, u)
        s3_c.bevel_factor_end = prog
        s3_g.bevel_factor_end = prog
        tip = eval_pts(s3_pts, prog)
        s3_light.location = tip + Vector((0, 0, 0.55))

    elif active_idx == 3:
        cam_obj.location = Vector((-0.50 + e * 1.00, -0.20 + e * 0.35, 17.5 - e * 1.25))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
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
        cam_obj.location = Vector((-0.45 + e * 0.90, -0.25 + e * 0.40, 17.5 - e * 1.25))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        prog = smoothstep(0.06, 0.92, u)
        s5_c.bevel_factor_end = prog
        s5_g.bevel_factor_end = prog
        tip = eval_pts(s5_pts, prog)
        s5_light.location = tip + Vector((0, 0, 0.55))

    scene.frame_set(f)
    scene.render.filepath = os.path.join(out_dir, f"frame_{f:04d}.jpg")
    bpy.ops.render.render(write_still=True)
    if (f - start_frame) % 10 == 0 or f == end_frame:
        print(f"Rendered Blender Tech1 frame {f} ({start_frame}..{end_frame})")
