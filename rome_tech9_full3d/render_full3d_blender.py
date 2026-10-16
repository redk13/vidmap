import bpy
import bmesh
import math
import os
import sys
import json
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw, ImageFont

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = []

shot_idx = int(args[0])
f_sub_start = int(args[1])
f_sub_end = int(args[2])
frames_dir = os.path.abspath(args[3])
tracked_json = os.path.abspath(args[4])
out_dir = os.path.abspath(args[5])
os.makedirs(out_dir, exist_ok=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../rome_ai_3d/assets"))

with open(tracked_json) as f:
    TRACKED = json.load(f)

SHOT_RANGES = {
    1: (1, 130, 0.0, 4.35),
    2: (131, 248, 4.35, 8.25),
    3: (249, 353, 8.25, 11.75),
    4: (354, 474, 11.75, 15.80),
    5: (475, 600, 15.80, 20.00),
}
f_start, f_end, t0, t1 = SHOT_RANGES[shot_idx]

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
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 96

scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'

# Selective High-Threshold Optical Glare in Blender Compositor:
# Threshold = 1.85 so the 1080p video mesh (Emission = 1.0) NEVER gets fogged or blurred,
# while the 3D NURBS tubes (Emission = 2.4..4.0) get true optical bloom!
scene.use_nodes = True
comp_tree = scene.node_tree
comp_tree.nodes.clear()
c_rl = comp_tree.nodes.new('CompositorNodeRLayers')

c_glare = comp_tree.nodes.new('CompositorNodeGlare')
c_glare.glare_type = 'FOG_GLOW'
c_glare.quality = 'HIGH'
c_glare.threshold = 1.85
c_glare.size = 7
c_glare.mix = -0.50

c_comp = comp_tree.nodes.new('CompositorNodeComposite')
comp_tree.links.new(c_rl.outputs['Image'], c_glare.inputs['Image'])
comp_tree.links.new(c_glare.outputs['Image'], c_comp.inputs['Image'])

# Pure zero-haze studio world (Strength = 0.0 so zero gray fog reflects onto dark areas!)
world = bpy.data.worlds.new("ZeroHazeWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
    bg_node.inputs[1].default_value = 0.0

W_PLANE = 16.0
H_PLANE = 9.0
Z_REF = 18.6667
GRID_W = 180
GRID_H = 102
DISP_SCALES = {1: 2.30, 2: 2.00, 3: 2.25, 4: 1.90, 5: 2.35}
disp_scale = DISP_SCALES[shot_idx]

cam_data = bpy.data.cameras.new("MainCam")
cam_data.lens = 42.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("MainCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = Vector((0.0, 0.0, Z_REF))
cam_obj.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')

# Moving 3D Point Light that illuminates the 3D stone arches right under the flowing water/laser
pt_data = bpy.data.lights.new(name="FlowLight", type='POINT')
pt_data.energy = 240.0
pt_data.shadow_soft_size = 1.15
pt_obj = bpy.data.objects.new(name="FlowLight", object_data=pt_data)
scene.collection.objects.link(pt_obj)

dep_path = os.path.join(ASSETS_DIR, f"depth{shot_idx}.png")
img_dep = bpy.data.images.load(dep_path)
img_dep.colorspace_settings.name = 'Non-Color'
dw, dh = img_dep.size
raw_dep = list(img_dep.pixels)

depth_grid = [[0.0] * GRID_W for _ in range(GRID_H)]
for gy in range(GRID_H):
    v_img = gy / (GRID_H - 1)
    py = int((1.0 - v_img) * (dh - 1))
    row_offset = py * dw * 4
    for gx in range(GRID_W):
        u = gx / (GRID_W - 1)
        px = int(u * (dw - 1))
        depth_grid[gy][gx] = raw_dep[row_offset + px * 4]

for _ in range(2):
    g2 = [[0.0] * GRID_W for _ in range(GRID_H)]
    for gy in range(GRID_H):
        y0, y1 = max(0, gy - 1), min(GRID_H - 1, gy + 1)
        for gx in range(GRID_W):
            x0, x1 = max(0, gx - 1), min(GRID_W - 1, gx + 1)
            s_val, c_val = 0.0, 0
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    s_val += depth_grid[yy][xx]
                    c_val += 1
            g2[gy][gx] = s_val / c_val
    depth_grid = g2

def sample_depth(u, v_img):
    u = max(0.0, min(1.0, u))
    v_img = max(0.0, min(1.0, v_img))
    gx = min(GRID_W - 1, max(0, int(round(u * (GRID_W - 1)))))
    gy = min(GRID_H - 1, max(0, int(round(v_img * (GRID_H - 1)))))
    return depth_grid[gy][gx]

def uv_to_3d(u, v_img, z_off=0.16):
    d = sample_depth(u, v_img)
    z_surf = (d - 0.45) * disp_scale
    z = z_surf + z_off
    persp_scale = (Z_REF - z_surf) / Z_REF
    x = (u - 0.5) * W_PLANE * persp_scale
    y = (0.5 - v_img) * H_PLANE * persp_scale
    return Vector((x, y, z))

# Build perspective-calibrated 3D Displaced Mesh
mesh = bpy.data.meshes.new("WanTrue1080Mesh")
bm = bmesh.new()
verts_grid = [[None] * GRID_W for _ in range(GRID_H)]

for gy in range(GRID_H):
    v_img = gy / (GRID_H - 1)
    for gx in range(GRID_W):
        u = gx / (GRID_W - 1)
        d = depth_grid[gy][gx]
        z_surf = (d - 0.45) * disp_scale
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

vid_obj = bpy.data.objects.new("WanTrue1080Obj", mesh)
scene.collection.objects.link(vid_obj)

# Pure un-fogged 1080p Shader:
# 1. Emission (Strength = 0.96) preserves 100% of the razor-sharp 1080p stone texture & deep blacks
# 2. Principled BSDF (with clean depth-based normal, NOT noisy RGB bump!) catches ONLY the local 3D Point Light
# 3. In Shot 1, Depth-Masked 3D Holographic Cyan Scan Wave wraps across the foreground aqueduct arches
mat_vid = bpy.data.materials.new(name="MatWanTrue1080")
mat_vid.use_nodes = True
nt = mat_vid.node_tree
nt.nodes.clear()

n_out = nt.nodes.new("ShaderNodeOutputMaterial")
n_add = nt.nodes.new("ShaderNodeAddShader")
n_emit = nt.nodes.new("ShaderNodeEmission")
n_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
n_rgb = nt.nodes.new("ShaderNodeTexImage")
n_dep = nt.nodes.new("ShaderNodeTexImage")
n_bump = nt.nodes.new("ShaderNodeBump")

first_img_path = os.path.join(frames_dir, f"wan_frame_{f_sub_start:04d}.jpg")
n_rgb.image = bpy.data.images.load(first_img_path)
n_rgb.extension = 'EXTEND'
n_dep.image = img_dep
n_dep.extension = 'EXTEND'

n_emit.inputs["Strength"].default_value = 0.96
n_bsdf.inputs["Roughness"].default_value = 0.32
n_bsdf.inputs["Metallic"].default_value = 0.10
# Bump comes from smooth Depth-Anything-V2 map (NEVER from RGB video pixels -> zero grain!)
n_bump.inputs["Strength"].default_value = 0.45
n_bump.inputs["Distance"].default_value = 0.22

nt.links.new(n_rgb.outputs["Color"], n_emit.inputs["Color"])
nt.links.new(n_rgb.outputs["Color"], n_bsdf.inputs["Base Color"])
nt.links.new(n_dep.outputs["Color"], n_bump.inputs["Height"])
nt.links.new(n_bump.outputs["Normal"], n_bsdf.inputs["Normal"])

if shot_idx == 1:
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
    n_div.inputs[1].default_value = 1.05

    n_inv = nt.nodes.new("ShaderNodeMath")
    n_inv.operation = 'SUBTRACT'
    n_inv.inputs[0].default_value = 1.0
    n_inv.use_clamp = True

    n_pow = nt.nodes.new("ShaderNodeMath")
    n_pow.operation = 'POWER'
    n_pow.inputs[1].default_value = 3.0

    n_dep_mask = nt.nodes.new("ShaderNodeMapRange")
    n_dep_mask.inputs["From Min"].default_value = 0.34
    n_dep_mask.inputs["From Max"].default_value = 0.46
    n_dep_mask.inputs["To Min"].default_value = 0.0
    n_dep_mask.inputs["To Max"].default_value = 0.75
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
mesh.materials.append(mat_vid)

# Dual-Layer 3D NURBS Core + Glow Tubes
def make_emissive_mat(name, rgba, strength=3.2):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    out = t.nodes.new("ShaderNodeOutputMaterial")
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba
    em.inputs["Strength"].default_value = strength
    t.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

mat_cyan_core = make_emissive_mat("CyanCore", (0.85, 0.99, 1.0, 1.0), 3.8)
mat_cyan_glow = make_emissive_mat("CyanGlow", (0.0, 0.80, 1.0, 1.0), 2.3)
mat_gold_core = make_emissive_mat("GoldCore", (1.0, 0.96, 0.78, 1.0), 4.0)
mat_gold_glow = make_emissive_mat("GoldGlow", (1.0, 0.65, 0.05, 1.0), 2.4)

init_sp = TRACKED[str(f_start)]["spline"]
init_pts = [uv_to_3d(u, v, 0.16) for u, v in init_sp]

RADII = {
    1: (0.032, 0.078),
    2: (0.040, 0.098),
    3: (0.042, 0.105),
    4: (0.034, 0.086),
    5: (0.044, 0.110),
}
r_core, r_glow = RADII[shot_idx]
mat_c = mat_gold_core if shot_idx in [2, 4] else mat_cyan_core
mat_g = mat_gold_glow if shot_idx in [2, 4] else mat_cyan_glow

c_data = bpy.data.curves.new("SplineCore", type='CURVE')
c_data.dimensions = '3D'
c_data.resolution_u = 24
c_data.bevel_depth = r_core
c_data.bevel_resolution = 6
c_data.use_fill_caps = True
sp_c = c_data.splines.new('NURBS')
sp_c.points.add(len(init_pts) - 1)
for idx, p in enumerate(init_pts):
    sp_c.points[idx].co = (p.x, p.y, p.z, 1.0)
sp_c.use_endpoint_u = True
sp_c.order_u = min(4, len(init_pts))
obj_c = bpy.data.objects.new("SplineCoreObj", c_data)
obj_c.data.materials.append(mat_c)
scene.collection.objects.link(obj_c)

g_data = bpy.data.curves.new("SplineGlow", type='CURVE')
g_data.dimensions = '3D'
g_data.resolution_u = 24
g_data.bevel_depth = r_glow
g_data.bevel_resolution = 6
g_data.use_fill_caps = True
sp_g = g_data.splines.new('NURBS')
sp_g.points.add(len(init_pts) - 1)
for idx, p in enumerate(init_pts):
    sp_g.points[idx].co = (p.x, p.y, p.z - 0.01, 1.0)
sp_g.use_endpoint_u = True
sp_g.order_u = min(4, len(init_pts))
obj_g = bpy.data.objects.new("SplineGlowObj", g_data)
obj_g.data.materials.append(mat_g)
scene.collection.objects.link(obj_g)

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / max(1e-6, b - a)))
    return t * t * (3.0 - 2.0 * t)

def eval_pts(pts, u):
    u = max(0.0, min(1.0, u))
    f = u * (len(pts) - 1)
    i0 = int(f)
    i1 = min(len(pts) - 1, i0 + 1)
    return pts[i0].lerp(pts[i1], f - i0)

def proj2d(pt3d):
    co = world_to_camera_view(scene, cam_obj, pt3d)
    return (co.x * 1920.0, (1.0 - co.y) * 1080.0)

def load_font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

SERIF_BOLD_ITALIC = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"]
SANS_MED = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
SANS_BOLD_IT = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]

f_serif_44 = load_font(SERIF_BOLD_ITALIC, 44)
f_serif_38 = load_font(SERIF_BOLD_ITALIC, 38)
f_serif_58 = load_font(SERIF_BOLD_ITALIC, 58)
f_sans_26  = load_font(SANS_MED, 26)
f_sub_reg  = load_font(SANS_MED, 31)
f_sub_gold = load_font(SANS_BOLD_IT, 32)

def draw_shadow_text(draw, xy, txt, font, fill=(255, 255, 255, 255), shadow=(0, 0, 0, 230)):
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
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=10, fill=(10, 12, 16, 220), outline=(255, 215, 90, 95), width=1)
    cx = 960 - tot / 2
    cy = 1023
    draw.text((cx, cy), pre, font=f_sub_reg, fill=(245, 247, 250, 255), anchor="lm")
    draw.text((cx + w1, cy), gold, font=f_sub_gold, fill=(255, 212, 75, 255), anchor="lm")
    draw.text((cx + w1 + w2, cy), post, font=f_sub_reg, fill=(245, 247, 250, 255), anchor="lm")

for f in range(f_sub_start, f_sub_end + 1):
    t = (f - 1) / 30.0
    u = max(0.0, min(1.0, (t - t0) / max(1e-6, t1 - t0)))

    cur_img_path = os.path.join(frames_dir, f"wan_frame_{f:04d}.jpg")
    bpy.data.images.remove(n_rgb.image)
    n_rgb.image = bpy.data.images.load(cur_img_path)
    n_rgb.extension = 'EXTEND'

    f_data = TRACKED[str(f)]
    cur_pts = [uv_to_3d(u_p, v_p, 0.16) for u_p, v_p in f_data["spline"]]
    for i, p in enumerate(cur_pts):
        sp_c.points[i].co = (p.x, p.y, p.z, 1.0)
        sp_g.points[i].co = (p.x, p.y, p.z - 0.01, 1.0)

    if shot_idx == 1:
        scan_x = -7.8 + u * 16.0
        scan_node = mat_vid.node_tree.nodes.get("ScanCenterNode")
        if scan_node:
            scan_node.inputs[1].default_value = scan_x
        prog = smoothstep(0.04, 0.92, u)
        pt_data.color = (0.0, 0.90, 1.0)
    elif shot_idx == 2:
        prog = smoothstep(0.06, 0.88, u)
        pt_data.color = (1.0, 0.68, 0.12)
    elif shot_idx == 3:
        prog = smoothstep(0.06, 0.88, u)
        pt_data.color = (0.0, 0.90, 1.0)
    elif shot_idx == 4:
        prog = smoothstep(0.05, 0.88, u)
        pt_data.color = (1.0, 0.80, 0.15)
    else:
        prog = smoothstep(0.06, 0.90, u)
        pt_data.color = (0.0, 0.90, 1.0)

    c_data.bevel_factor_end = prog
    g_data.bevel_factor_end = prog
    tip = eval_pts(cur_pts, prog)
    pt_obj.location = tip + Vector((0, 0, 0.55))

    bpy.context.view_layer.update()
    out_jpg = os.path.join(out_dir, f"frame_{f:04d}.jpg")
    scene.render.filepath = out_jpg
    bpy.ops.render.render(write_still=True)

    im = Image.open(out_jpg).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    anc = f_data["anchors"]

    if shot_idx == 1:
        if u < 0.52:
            draw_subtitle_bar(dr, "Roman ", "aqueducts", " carried fresh water")
        else:
            draw_subtitle_bar(dr, "", "100 kilometers", " across valleys into the city")

    elif shot_idx == 2:
        p_col = proj2d(uv_to_3d(*anc["rome"], 0.16))
        p_pop = proj2d(uv_to_3d(*anc["pop"], 0.16))
        p_mar = proj2d(uv_to_3d(*anc["marcia"], 0.22))
        p_tip = proj2d(tip)

        dr.line([p_pop[0] + 95, p_pop[1], p_col[0], p_col[1]], fill=(255, 255, 255, 220), width=2)
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

    elif shot_idx == 3:
        p_ws = proj2d(uv_to_3d(*anc["source"], 0.18))
        p_rm = proj2d(uv_to_3d(*anc["rome"], 0.18))
        draw_shadow_text(dr, (p_ws[0], p_ws[1] - 20), "Water", f_serif_44, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, (p_ws[0], p_ws[1] + 22), "source", f_serif_44, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, (p_rm[0], max(85, p_rm[1])), "Rome", f_serif_44, fill=(255, 255, 255, 255))
        draw_subtitle_bar(dr, "From ", "mountain springs", ", stone bridges guided water by gravity alone")

    elif shot_idx == 4:
        p_txt = proj2d(uv_to_3d(*anc["mid"], 0.16))
        p_lin = proj2d(uv_to_3d(*anc["lin"], 0.16))
        if u < 0.52:
            dr.line([p_txt[0] + 75, p_txt[1] + 22, p_lin[0], p_lin[1]], fill=(255, 255, 255, 225), width=3)
            dr.text((p_txt[0], p_txt[1] - 12), "1.5–3 meters per km", font=f_serif_44, fill=(58, 54, 48, 255), anchor="mm")
            dr.text((p_txt[0], p_txt[1] + 26), "(8–16 feet per mile)", font=f_sans_26, fill=(90, 85, 78, 255), anchor="mm")
        else:
            dr.text((p_txt[0], p_txt[1] + 8), "0.09 – 0.17°", font=f_serif_58, fill=(68, 64, 58, 255), anchor="mm")
        draw_subtitle_bar(dr, "Aqueducts dropped just ", "1.5 to 3 meters", " per kilometer (0.09–0.17°)")

    elif shot_idx == 5:
        p_top = proj2d(uv_to_3d(*anc["top50"], 0.20))
        p_bot = proj2d(uv_to_3d(*anc["bot50"], 0.20))
        p_tnk = proj2d(uv_to_3d(*anc["ht_lbl"], 0.20))
        y_cur = p_top[1]
        while y_cur < p_bot[1]:
            dr.line([p_top[0], y_cur, p_top[0], min(p_bot[1], y_cur + 9)], fill=(255, 214, 0, 240), width=3)
            y_cur += 15
        draw_shadow_text(dr, (p_top[0], p_top[1] - 28), "50 m", f_serif_44, fill=(255, 255, 255, 255))
        draw_shadow_text(dr, (p_top[0], p_top[1] + 6), "(164 ft)", f_sans_26, fill=(240, 240, 240, 255))
        draw_shadow_text(dr, p_tnk, "Header tank", f_serif_38, fill=(255, 255, 255, 255))
        draw_subtitle_bar(dr, "Across deep valleys, pressurized siphons drove water ", "50 meters", " uphill")

    final_rgb = Image.alpha_composite(im, ov).convert("RGB")
    final_rgb.save(out_jpg, quality=96)
