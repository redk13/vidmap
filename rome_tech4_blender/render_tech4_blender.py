import bpy
import bmesh
import math
import sys
import os
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw, ImageFont

argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

start_frame = int(argv[0]) if len(argv) > 0 else 1
end_frame = int(argv[1]) if len(argv) > 1 else 600
asset_dir = os.path.abspath(argv[2]) if len(argv) > 2 else os.path.abspath("rome_ai_3d/assets")
out_dir = os.path.abspath(argv[3]) if len(argv) > 3 else "/tmp/tech4_frames"
os.makedirs(out_dir, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. CONFIGURE BLENDER 4.3.2 CYCLES + SELECTIVE COMPOSITOR GLARE BLOOM
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

# Selective High-Threshold Optical Glare in Blender Compositor (threshold=1.85)
scene.use_nodes = True
c_tree = scene.node_tree
c_tree.nodes.clear()
c_rl = c_tree.nodes.new("CompositorNodeRLayers")
c_glare = c_tree.nodes.new("CompositorNodeGlare")
c_glare.glare_type = 'FOG_GLOW'
c_glare.quality = 'HIGH'
c_glare.threshold = 1.85
c_glare.size = 7
c_glare.mix = -0.50
c_out = c_tree.nodes.new("CompositorNodeComposite")
c_tree.links.new(c_rl.outputs["Image"], c_glare.inputs["Image"])
c_tree.links.new(c_glare.outputs["Image"], c_out.inputs["Image"])

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
Z_REF = 18.6667
GRID_W = 180
GRID_H = 102
DISP_SCALES = [2.40, 2.00, 2.35, 1.95, 2.45]

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

def map_pt3d(shot_idx, u, v_img, z_off=0.14):
    disp = DISP_SCALES[shot_idx]
    d = sample_depth(shot_idx, u, v_img)
    z_surf = (d - 0.45) * disp
    z = z_surf + z_off
    persp_scale = (Z_REF - z_surf) / Z_REF
    x = (u - 0.5) * W_PLANE * persp_scale
    y = (0.5 - v_img) * H_PLANE * persp_scale
    return Vector((x, y, z))

# ---------------------------------------------------------------------------
# 3. BUILD DISPLACED 3D DIORAMA MESH + DEPTH-MASKED HOLOGRAPHIC SCAN SHADER
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

    n_emit.inputs["Strength"].default_value = 0.85
    n_bsdf.inputs["Roughness"].default_value = 0.28
    n_bsdf.inputs["Metallic"].default_value = 0.14
    n_bump.inputs["Strength"].default_value = 0.75
    n_bump.inputs["Distance"].default_value = 0.28

    nt.links.new(n_rgb.outputs["Color"], n_emit.inputs["Color"])
    nt.links.new(n_rgb.outputs["Color"], n_bsdf.inputs["Base Color"])
    nt.links.new(n_dep.outputs["Color"], n_bump.inputs["Height"])
    nt.links.new(n_bump.outputs["Normal"], n_bsdf.inputs["Normal"])

    if s_idx == 0:
        # Depth-Masked 3D Holographic Cyan Scan Wave (wraps ONLY around foreground/midground aqueduct arches, not sky!)
        n_texcoord = nt.nodes.new("ShaderNodeTexCoord")
        n_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        n_sub = nt.nodes.new("ShaderNodeMath")
        n_sub.operation = 'SUBTRACT'
        n_sub.name = "ScanCenterNode"
        n_sub.inputs[1].default_value = -6.0

        n_abs = nt.nodes.new("ShaderNodeMath")
        n_abs.operation = 'ABSOLUTE'

        n_div = nt.nodes.new("ShaderNodeMath")
        n_div.operation = 'DIVIDE'
        n_div.inputs[1].default_value = 1.10

        n_inv = nt.nodes.new("ShaderNodeMath")
        n_inv.operation = 'SUBTRACT'
        n_inv.inputs[0].default_value = 1.0
        n_inv.use_clamp = True

        n_pow = nt.nodes.new("ShaderNodeMath")
        n_pow.operation = 'POWER'
        n_pow.inputs[1].default_value = 3.0

        # Mask by Depth > 0.34 so the sky (depth < 0.30) is NEVER tinted cyan!
        n_dep_mask = nt.nodes.new("ShaderNodeMapRange")
        n_dep_mask.inputs["From Min"].default_value = 0.32
        n_dep_mask.inputs["From Max"].default_value = 0.45
        n_dep_mask.inputs["To Min"].default_value = 0.0
        n_dep_mask.inputs["To Max"].default_value = 0.95
        n_dep_mask.clamp = True

        n_mul = nt.nodes.new("ShaderNodeMath")
        n_mul.operation = 'MULTIPLY'

        n_scan_emit = nt.nodes.new("ShaderNodeEmission")
        n_scan_emit.inputs["Color"].default_value = (0.0, 0.92, 1.0, 1.0)

        n_add_scan = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(n_texcoord.outputs["Object"], n_sep.inputs["Vector"])
        nt.links.new(n_sep.outputs["X"], n_sub.inputs[0])
        nt.links.new(n_sub.outputs["Value"], n_abs.inputs[0])
        nt.links.new(n_abs.outputs["Value"], n_div.inputs[0])
        nt.links.new(n_div.outputs["Value"], n_inv.inputs[1])
        nt.links.new(n_inv.outputs["Value"], n_pow.inputs[0])
        nt.links.new(n_dep.outputs["Color"], n_dep_mask.inputs["Value"])
        nt.links.new(n_pow.outputs["Value"], n_mul.inputs[0])
        nt.links.new(n_dep_mask.outputs["Result"], n_mul.inputs[1])
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
# 4. CALIBRATED 3D BLENDER NURBS TUBES & 3D POINT LIGHTS
# ---------------------------------------------------------------------------
def make_emissive_mat(name, rgba, strength=3.2):
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

mat_cyan_core = make_emissive_mat("CyanCore", (0.85, 0.99, 1.0, 1.0), 3.8)
mat_cyan_glow = make_emissive_mat("CyanGlow", (0.0, 0.80, 1.0, 1.0), 2.3)
mat_gold_core = make_emissive_mat("GoldCore", (1.0, 0.96, 0.78, 1.0), 4.0)
mat_gold_glow = make_emissive_mat("GoldGlow", (1.0, 0.65, 0.05, 1.0), 2.4)

def create_3d_spline(col, name, pts, radius_core, radius_glow, mat_c, mat_g):
    c_data = bpy.data.curves.new(f"{name}_core", type='CURVE')
    c_data.dimensions = '3D'
    c_data.bevel_depth = radius_core
    c_data.bevel_resolution = 5
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
    g_data.bevel_resolution = 5
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

def create_point_light(col, name, color_rgb, energy=260.0, radius=0.9):
    l_data = bpy.data.lights.new(name=name, type='POINT')
    l_data.color = color_rgb
    l_data.energy = energy
    l_data.shadow_soft_size = radius
    l_obj = bpy.data.objects.new(name=name, object_data=l_data)
    col.objects.link(l_obj)
    return l_obj

# Exact UV-Calibrated 3D Splines (from uv_calibration_grid.jpg)
if active_shard_shot == 0:
    s1_uv = [(0.00, 0.595), (0.18, 0.530), (0.36, 0.468), (0.54, 0.405), (0.72, 0.342), (0.87, 0.285)]
    s1_pts = [map_pt3d(0, u, v, z_off=0.16) for (u, v) in s1_uv]
    s1_c, s1_g = create_3d_spline(shot_collections[0], "S1_Specus", s1_pts, 0.032, 0.078, mat_cyan_core, mat_cyan_glow)
    s1_light = create_point_light(shot_collections[0], "S1_Light", (0.0, 0.9, 1.0), energy=260.0, radius=1.2)

elif active_shard_shot == 1:
    s2_uv = [
        (0.485, 0.482), (0.545, 0.505), (0.615, 0.518), (0.685, 0.492),
        (0.745, 0.435), (0.805, 0.368), (0.865, 0.295), (0.915, 0.235)
    ]
    s2_pts = [map_pt3d(1, u, v, z_off=0.18) for (u, v) in s2_uv]
    s2_c, s2_g = create_3d_spline(shot_collections[1], "S2_Marcia", s2_pts, 0.042, 0.105, mat_gold_core, mat_gold_glow)
    s2_light = create_point_light(shot_collections[1], "S2_Light", (1.0, 0.65, 0.1), energy=290.0, radius=1.0)

elif active_shard_shot == 2:
    s3_uv = [
        (0.775, 0.490), (0.715, 0.480), (0.655, 0.465), (0.540, 0.438),
        (0.410, 0.408), (0.280, 0.376), (0.160, 0.346), (0.085, 0.328)
    ]
    s3_pts = [map_pt3d(2, u, v, z_off=0.18) for (u, v) in s3_uv]
    s3_c, s3_g = create_3d_spline(shot_collections[2], "S3_Flow", s3_pts, 0.045, 0.115, mat_cyan_core, mat_cyan_glow)
    s3_light = create_point_light(shot_collections[2], "S3_Light", (0.0, 0.9, 1.0), energy=290.0, radius=1.1)

elif active_shard_shot == 3:
    s4_uv = [(0.10, 0.432), (0.30, 0.372), (0.52, 0.305), (0.75, 0.235), (0.98, 0.162)]
    s4_pts = [map_pt3d(3, u, v, z_off=0.16) for (u, v) in s4_uv]
    s4_c, s4_g = create_3d_spline(shot_collections[3], "S4_Laser", s4_pts, 0.036, 0.092, mat_gold_core, mat_gold_glow)
    s4_light = create_point_light(shot_collections[3], "S4_Light", (1.0, 0.8, 0.15), energy=260.0, radius=1.1)

elif active_shard_shot == 4:
    s5_uv = [
        (0.245, 0.408), (0.295, 0.425), (0.335, 0.565), (0.380, 0.725),
        (0.430, 0.835), (0.478, 0.862), (0.528, 0.835), (0.580, 0.725),
        (0.640, 0.575), (0.705, 0.440), (0.785, 0.435)
    ]
    s5_pts = [map_pt3d(4, u, v, z_off=0.20) for (u, v) in s5_uv]
    s5_c, s5_g = create_3d_spline(shot_collections[4], "S5_Siphon", s5_pts, 0.048, 0.120, mat_cyan_core, mat_cyan_glow)
    s5_light = create_point_light(shot_collections[4], "S5_Light", (0.0, 0.9, 1.0), energy=290.0, radius=1.1)

# ---------------------------------------------------------------------------
# 5. CAMERA SETUP + BLENDER 3D CAMERA-MATRIX TYPOGRAPHY PROJECTION
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

def proj2d(pt3d):
    co = world_to_camera_view(scene, cam_obj, pt3d)
    return (co.x * 1920.0, (1.0 - co.y) * 1080.0)

def load_font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

SERIF_BOLD_ITALIC = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"]
SANS_MED = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
SANS_BOLD_IT = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]

f_serif_44 = load_font(SERIF_BOLD_ITALIC, 44)
f_serif_38 = load_font(SERIF_BOLD_ITALIC, 38)
f_serif_58 = load_font(SERIF_BOLD_ITALIC, 58)
f_sans_26  = load_font(SANS_MED, 26)
f_sub_reg  = load_font(SANS_MED, 31)
f_sub_gold = load_font(SANS_BOLD_IT, 32)

def draw_shadow_text(draw, xy, txt, font, fill=(255, 255, 255, 255), shadow=(0, 0, 0, 220)):
    x, y = xy
    for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 3)]:
        draw.text((x + ox, y + oy), txt, font=font, fill=shadow, anchor="mm")
    draw.text((x, y), txt, font=font, fill=fill, anchor="mm")

def draw_subtitle_bar(draw, pre, gold, post):
    w1 = draw.textlength(pre, font=f_sub_reg)
    w2 = draw.textlength(gold, font=f_sub_gold)
    w3 = draw.textlength(post, font=f_sub_reg)
    tot = w1 + w2 + w3
    pad_x = 26
    bx0, by0 = 960 - tot / 2 - pad_x, 995
    bx1, by1 = 960 + tot / 2 + pad_x, 1051
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=10, fill=(10, 12, 16, 215), outline=(255, 215, 90, 90), width=1)
    cx = 960 - tot / 2
    cy = 1023
    draw.text((cx, cy), pre, font=f_sub_reg, fill=(242, 244, 248, 255), anchor="lm")
    draw.text((cx + w1, cy), gold, font=f_sub_gold, fill=(255, 212, 75, 255), anchor="lm")
    draw.text((cx + w1 + w2, cy), post, font=f_sub_reg, fill=(242, 244, 248, 255), anchor="lm")

for f in range(start_frame, end_frame + 1):
    t = (f - 1) / 30.0
    active_idx = active_shard_shot
    u = min(1.0, max(0.0, (t - active_idx * 4.0) / 4.0))

    for idx, col in enumerate(shot_collections):
        col.hide_render = (idx != active_idx)

    e = smoothstep(0.0, 1.0, u)

    if active_idx == 0:
        cam_obj.location = Vector((-0.65 + e * 1.30, -0.25 + e * 0.45, 17.3 - e * 1.45))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        scan_x = -7.8 + u * 16.0
        scan_node = diorama_mats[0].node_tree.nodes.get("ScanCenterNode")
        if scan_node:
            scan_node.inputs[1].default_value = scan_x
        prog = smoothstep(0.04, 0.92, u)
        s1_c.bevel_factor_end = prog
        s1_g.bevel_factor_end = prog
        tip = eval_pts(s1_pts, prog)
        s1_light.location = tip + Vector((0, 0, 0.55))

    elif active_idx == 1:
        cam_obj.location = Vector((0.55 - e * 1.10, -0.32 + e * 0.50, 17.3 - e * 1.40))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        prog = smoothstep(0.06, 0.88, u)
        s2_c.bevel_factor_end = prog
        s2_g.bevel_factor_end = prog
        tip = eval_pts(s2_pts, prog)
        s2_light.location = tip + Vector((0, 0, 0.55))

    elif active_idx == 2:
        cam_obj.location = Vector((0.60 - e * 1.20, -0.28 + e * 0.45, 17.3 - e * 1.35))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        prog = smoothstep(0.06, 0.88, u)
        s3_c.bevel_factor_end = prog
        s3_g.bevel_factor_end = prog
        tip = eval_pts(s3_pts, prog)
        s3_light.location = tip + Vector((0, 0, 0.55))

    elif active_idx == 3:
        cam_obj.location = Vector((-0.60 + e * 1.20, -0.20 + e * 0.36, 17.3 - e * 1.35))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        prog = smoothstep(0.05, 0.88, u)
        s4_c.bevel_factor_end = prog
        s4_g.bevel_factor_end = prog
        tip = eval_pts(s4_pts, prog)
        s4_light.location = tip + Vector((0, 0, 0.50))

    elif active_idx == 4:
        cam_obj.location = Vector((-0.55 + e * 1.10, -0.28 + e * 0.45, 17.3 - e * 1.35))
        look_at(cam_obj, Vector((0.0, 0.0, 0.0)))
        prog = smoothstep(0.06, 0.90, u)
        s5_c.bevel_factor_end = prog
        s5_g.bevel_factor_end = prog
        tip = eval_pts(s5_pts, prog)
        s5_light.location = tip + Vector((0, 0, 0.55))

    scene.frame_set(f)
    bpy.context.view_layer.update()
    out_jpg = os.path.join(out_dir, f"frame_{f:04d}.jpg")
    scene.render.filepath = out_jpg
    bpy.ops.render.render(write_still=True)

    # Project 3D coordinates through Blender's exact camera matrix (`world_to_camera_view`)
    im = Image.open(out_jpg).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)

    if active_idx == 0:
        if u < 0.52:
            draw_subtitle_bar(dr, "Roman ", "aqueducts", " carried fresh water")
        else:
            draw_subtitle_bar(dr, "", "100 kilometers", " across valleys into the city")

    elif active_idx == 1:
        p_col = proj2d(map_pt3d(1, 0.485, 0.482, z_off=0.15))
        p_pop = proj2d(map_pt3d(1, 0.220, 0.455, z_off=0.15))
        p_mar = proj2d(map_pt3d(1, 0.640, 0.415, z_off=0.22))
        p_tip = proj2d(tip)

        dr.line([p_pop[0] + 95, p_pop[1], p_col[0], p_col[1]], fill=(255, 255, 255, 215), width=2)
        pop_val = int(round(smoothstep(0.04, 0.55, u) * 1000000))
        draw_shadow_text(dr, p_pop, f"{pop_val:,}", f_serif_38, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, p_mar, "Aqua Marcia", f_serif_44, fill=(255, 216, 102, 255))

        km = int(round(prog * 90))
        mi = int(round(prog * 55))
        tx = min(1760, max(160, p_tip[0]))
        ty = max(95, p_tip[1] - 48)
        draw_shadow_text(dr, (tx, ty), f"{km} km", f_serif_38, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, (tx, ty + 32), f"{mi} miles", f_sans_26, fill=(225, 225, 225, 240))
        draw_subtitle_bar(dr, "The ", "Aqua Marcia", " spanned 90 km, supplying 1,000,000 citizens")

    elif active_idx == 2:
        p_ws = proj2d(map_pt3d(2, 0.785, 0.315, z_off=0.18))
        p_rm = proj2d(map_pt3d(2, 0.175, 0.135, z_off=0.18))
        draw_shadow_text(dr, (p_ws[0], p_ws[1] - 20), "Water", f_serif_44, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, (p_ws[0], p_ws[1] + 22), "source", f_serif_44, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, (p_rm[0], max(85, p_rm[1])), "Rome", f_serif_44, fill=(255, 255, 255, 255))
        draw_subtitle_bar(dr, "From ", "mountain springs", ", stone bridges guided water by gravity alone")

    elif active_idx == 3:
        p_txt = proj2d(map_pt3d(3, 0.44, 0.23, z_off=0.16))
        p_lin = proj2d(map_pt3d(3, 0.52, 0.305, z_off=0.16))
        if u < 0.52:
            dr.line([p_txt[0] + 75, p_txt[1] + 22, p_lin[0], p_lin[1]], fill=(255, 255, 255, 225), width=3)
            dr.text((p_txt[0], p_txt[1] - 12), "1.5–3 meters per km", font=f_serif_44, fill=(58, 54, 48, 255), anchor="mm")
            dr.text((p_txt[0], p_txt[1] + 26), "(8–16 feet per mile)", font=f_sans_26, fill=(90, 85, 78, 255), anchor="mm")
        else:
            dr.text((p_txt[0], p_txt[1] + 8), "0.09 – 0.17°", font=f_serif_58, fill=(68, 64, 58, 255), anchor="mm")
        draw_subtitle_bar(dr, "Aqueducts dropped just ", "1.5 to 3 meters", " per kilometer (0.09–0.17°)")

    elif active_idx == 4:
        p_top = proj2d(map_pt3d(4, 0.475, 0.415, z_off=0.20))
        p_bot = proj2d(map_pt3d(4, 0.475, 0.855, z_off=0.20))
        p_tnk = proj2d(map_pt3d(4, 0.245, 0.335, z_off=0.20))
        # Dashed vertical 50m measurement line
        y_cur = p_top[1]
        while y_cur < p_bot[1]:
            dr.line([p_top[0], y_cur, p_top[0], min(p_bot[1], y_cur + 9)], fill=(255, 214, 0, 240), width=3)
            y_cur += 15
        draw_shadow_text(dr, (p_top[0], p_top[1] - 28), "50 m", f_serif_44, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, (p_top[0], p_top[1] + 6), "(164 ft)", f_sans_26, fill=(240, 240, 240, 255))
        draw_shadow_text(dr, p_tnk, "Header tank", f_serif_38, fill=(255, 255, 255, 255))
        draw_subtitle_bar(dr, "Across deep valleys, pressurized siphons drove water ", "50 meters", " uphill")

    final_rgb = Image.alpha_composite(im, ov).convert("RGB")
    final_rgb.save(out_jpg, quality=95)

    if (f - start_frame) % 10 == 0 or f == end_frame:
        print(f"Rendered Blender Tech3 frame {f} ({start_frame}..{end_frame})")
