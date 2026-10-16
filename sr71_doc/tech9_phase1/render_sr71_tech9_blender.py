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
DOC_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
FONT_BEBAS = os.path.join(DOC_ROOT, "fonts", "BebasNeue-Regular.ttf")

def f_bebas(sz):
    return ImageFont.truetype(FONT_BEBAS, sz)

def draw_tracked_text(draw, pos, text, font, fill, tracking=5):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((x, y), ch, font=font)
        x += (bbox[2] - bbox[0]) + tracking

def tracked_width(draw, text, font, tracking=5):
    w = 0
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        w += (bbox[2] - bbox[0]) + tracking
    return max(0, w - tracking)

def draw_primal_pointer(draw, px, py, dx, dy, text, color=(245, 247, 250, 255), sz=46):
    px = max(120, min(1800, int(px)))
    py = max(120, min(960, int(py)))
    r = 7
    draw.ellipse([px - r, py - r, px + r, py + r], fill=color)
    ex, ey = px + dx, py + dy
    nx = ex + (75 if dx >= 0 else -75)
    draw.line([(px, py), (ex, ey), (nx, ey)], fill=color, width=3)
    f = f_bebas(sz)
    tw = tracked_width(draw, text, f, tracking=5)
    tx = nx + 16 if dx >= 0 else nx - tw - 16
    ty = ey - sz // 2 - 2
    # Subtle soft drop shadow for legibility over bright highlights, zero boxes!
    draw_tracked_text(draw, (tx + 2, ty + 2), text, f, (0, 0, 0, 180), tracking=5)
    draw_tracked_text(draw, (tx, ty), text, f, color, tracking=5)

SHOT_RANGES = {
    1: (1,   150, 0.0,  5.0),
    2: (151, 300, 5.0,  10.0),
    3: (301, 450, 10.0, 15.0),
    4: (451, 600, 15.0, 20.0),
    5: (601, 750, 20.0, 25.0),
    6: (751, 900, 25.0, 30.0),
}
f_start, f_end, t0, t1 = SHOT_RANGES[shot_idx]

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / max(1e-6, b - a)))
    return t * t * (3.0 - 2.0 * t)

# ==============================================================================
# SHOT 6: 100% Native 30fps Denoised Cycles on the 90,387-Vertex Multi-Part CAD
#         Blackbird.glb (Every single frame rendered natively in Blender — ZERO
#         Optical Flow warping, ZERO frame-skipping!)
# ==============================================================================
if shot_idx == 6:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 14
    scn.cycles.max_bounces = 3
    scn.cycles.transparent_max_bounces = 6
    scn.cycles.use_denoising = True
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.image_settings.file_format = 'JPEG'
    scn.render.image_settings.quality = 96
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - Medium High Contrast'

    glb_path = os.path.join(DOC_ROOT, "models3d", "Blackbird.glb")
    bpy.ops.import_scene.gltf(filepath=glb_path)
    objs = [o for o in scn.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    min_v = Vector((1e9, 1e9, 1e9)); max_v = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.bound_box:
            wv = o.matrix_world @ Vector(v)
            for i in range(3):
                min_v[i] = min(min_v[i], wv[i]); max_v[i] = max(max_v[i], wv[i])
    center = (min_v + max_v) * 0.5
    size = max_v - min_v
    scale_f = 10.0 / max(size.x, size.y, size.z, 0.001)
    for o in objs:
        o.location = (o.location - center) * scale_f
        o.scale = (scale_f, scale_f, scale_f)

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bb = objs[0]
    for m in bb.data.materials:
        if not m or not m.use_nodes: continue
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if not bsdf: continue
        if "texture" in m.name.lower() or "defaultwhite" == m.name.lower():
            bsdf.inputs["Metallic"].default_value = 0.52
            bsdf.inputs["Roughness"].default_value = 0.34

    z_min = min(v.co.z for v in bb.data.vertices)
    bpy.ops.mesh.primitive_plane_add(size=90.0, location=(0, 0, z_min))
    floor = bpy.context.active_object
    fmat = bpy.data.materials.new("StudioFloor")
    fmat.use_nodes = True
    fbsdf = fmat.node_tree.nodes.get("Principled BSDF")
    fbsdf.inputs["Base Color"].default_value = (0.22, 0.23, 0.25, 1.0)
    fbsdf.inputs["Roughness"].default_value = 0.42
    fbsdf.inputs["Metallic"].default_value = 0.10
    floor.data.materials.append(fmat)

    w = bpy.data.worlds.new("W"); w.use_nodes = True; scn.world = w
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.24, 0.25, 0.27, 1.0); bg.inputs[1].default_value = 1.0

    def add_area(nm, loc, energy, sz):
        ld = bpy.data.lights.new(nm, type='AREA'); ld.energy = energy; ld.size = sz
        lo = bpy.data.objects.new(nm, ld); lo.location = loc
        d = Vector((0,0,0)) - Vector(loc); lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        scn.collection.objects.link(lo)

    add_area("Key",  (8.0, -8.0, 9.0), 2200.0, 10.0)
    add_area("Fill", (-8.0, -6.0, 6.0), 1100.0, 12.0)
    add_area("Rim",  (0.0, 9.0, 7.0), 1600.0, 9.0)

    cd = bpy.data.cameras.new("C"); cd.lens = 50.0
    co = bpy.data.objects.new("C", cd); scn.collection.objects.link(co); scn.camera = co

    canopy_3d = Vector((0.0, -2.85, 0.22))
    spike_3d  = Vector((1.42, -0.95, -0.05))

    for f in range(f_sub_start, f_sub_end + 1):
        u = (f - f_start) / max(1, f_end - f_start)
        su = 0.5 - 0.5 * math.cos(u * math.pi)
        ang = math.radians(118.0 + 34.0 * su)
        dist = 8.4 - 0.8 * su
        zh = 2.4 - 0.35 * su
        co.location = (dist * math.cos(ang), dist * math.sin(ang), zh)
        d = Vector((0.0, -0.6, -0.1)) - co.location
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()

        out_jpg = os.path.join(out_dir, f"frame_{f:04d}.jpg")
        scn.render.filepath = out_jpg
        bpy.ops.render.render(write_still=True)

        im = Image.open(out_jpg).convert("RGBA")
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        if u > 0.12:
            uv_c = world_to_camera_view(scn, co, canopy_3d)
            draw_primal_pointer(dr, uv_c.x * 1920, (1.0 - uv_c.y) * 1080, 75, -145, "620°F QUARTZ WINDSHIELD")
        if u > 0.38:
            uv_s = world_to_camera_view(scn, co, spike_3d)
            draw_primal_pointer(dr, uv_s.x * 1920, (1.0 - uv_s.y) * 1080, -75, -155, "J58 CONICAL INLET SPIKE")
        Image.alpha_composite(im, ov).convert("RGB").save(out_jpg, quality=96)
    sys.exit(0)

# ==============================================================================
# SHOTS 1..5: Exact rome_tech9_full3d Architecture
#   - WanTrue1080Mesh (180x102 Perspective-Calibrated 3D Displaced Mesh from Depth-Anything-V2)
#   - ZeroHazeWorld (Strength=0.0) + Emission(0.96) + Principled BSDF with smooth depth normal
#   - CompositorNodeGlare (Threshold=1.85 so video never fogs while 3D NURBS tubes bloom)
#   - Dual-Layer 3D NURBS Core + Glow Tubes + Moving FlowLight
#   - Exact Primal Space Bebas Neue 3D-Projected Pointers (world_to_camera_view)
# ==============================================================================
with open(tracked_json) as f:
    TRACKED = json.load(f)

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
DISP_SCALES = {1: 2.25, 2: 2.15, 3: 2.05, 4: 2.20, 5: 2.15}
disp_scale = DISP_SCALES[shot_idx]

cam_data = bpy.data.cameras.new("MainCam")
cam_data.lens = 42.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("MainCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = Vector((0.0, 0.0, Z_REF))
cam_obj.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')

pt_data = bpy.data.lights.new(name="FlowLight", type='POINT')
pt_data.energy = 240.0
pt_data.shadow_soft_size = 1.15
pt_obj = bpy.data.objects.new(name="FlowLight", object_data=pt_data)
scene.collection.objects.link(pt_obj)

dep_path = os.path.join(frames_dir, f"depth{shot_idx}.png")
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
n_bsdf.inputs["Metallic"].default_value = 0.12
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

    n_abs = nt.nodes.new("ShaderNodeMath"); n_abs.operation = 'ABSOLUTE'
    n_div = nt.nodes.new("ShaderNodeMath"); n_div.operation = 'DIVIDE'; n_div.inputs[1].default_value = 1.05
    n_inv = nt.nodes.new("ShaderNodeMath"); n_inv.operation = 'SUBTRACT'; n_inv.inputs[0].default_value = 1.0; n_inv.use_clamp = True
    n_pow = nt.nodes.new("ShaderNodeMath"); n_pow.operation = 'POWER'; n_pow.inputs[1].default_value = 3.0

    n_dep_mask = nt.nodes.new("ShaderNodeMapRange")
    n_dep_mask.inputs["From Min"].default_value = 0.34
    n_dep_mask.inputs["From Max"].default_value = 0.48
    n_dep_mask.inputs["To Min"].default_value = 0.0
    n_dep_mask.inputs["To Max"].default_value = 0.65
    n_dep_mask.clamp = True

    n_mul = nt.nodes.new("ShaderNodeMath"); n_mul.operation = 'MULTIPLY'
    n_scan_emit = nt.nodes.new("ShaderNodeEmission")
    n_scan_emit.inputs["Color"].default_value = (0.0, 0.88, 1.0, 1.0)
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
mat_gold_glow = make_emissive_mat("GoldGlow", (1.0, 0.62, 0.05, 1.0), 2.4)

init_sp = TRACKED[str(f_start)]["spline"]
init_pts = [uv_to_3d(u, v, 0.16) for u, v in init_sp]

RADII = {
    1: (0.032, 0.078),
    2: (0.036, 0.088),
    3: (0.028, 0.068),
    4: (0.038, 0.094),
    5: (0.034, 0.082),
}
r_core, r_glow = RADII[shot_idx]
mat_c = mat_gold_core if shot_idx in [2, 3, 5] else mat_cyan_core
mat_g = mat_gold_glow if shot_idx in [2, 3, 5] else mat_cyan_glow

c_data = bpy.data.curves.new("SplineCore", type='CURVE')
c_data.dimensions = '3D'; c_data.resolution_u = 24; c_data.bevel_depth = r_core; c_data.bevel_resolution = 6; c_data.use_fill_caps = True
sp_c = c_data.splines.new('NURBS')
sp_c.points.add(len(init_pts) - 1)
for idx, p in enumerate(init_pts):
    sp_c.points[idx].co = (p.x, p.y, p.z, 1.0)
sp_c.use_endpoint_u = True; sp_c.order_u = min(4, len(init_pts))
obj_c = bpy.data.objects.new("SplineCoreObj", c_data); obj_c.data.materials.append(mat_c); scene.collection.objects.link(obj_c)

g_data = bpy.data.curves.new("SplineGlow", type='CURVE')
g_data.dimensions = '3D'; g_data.resolution_u = 24; g_data.bevel_depth = r_glow; g_data.bevel_resolution = 6; g_data.use_fill_caps = True
sp_g = g_data.splines.new('NURBS')
sp_g.points.add(len(init_pts) - 1)
for idx, p in enumerate(init_pts):
    sp_g.points[idx].co = (p.x, p.y, p.z - 0.01, 1.0)
sp_g.use_endpoint_u = True; sp_g.order_u = min(4, len(init_pts))
obj_g = bpy.data.objects.new("SplineGlowObj", g_data); obj_g.data.materials.append(mat_g); scene.collection.objects.link(obj_g)

def eval_pts(pts, u):
    u = max(0.0, min(1.0, u))
    f = u * (len(pts) - 1)
    i0 = int(f)
    i1 = min(len(pts) - 1, i0 + 1)
    return pts[i0].lerp(pts[i1], f - i0)

def proj2d(pt3d):
    co = world_to_camera_view(scene, cam_obj, pt3d)
    return (co.x * 1920.0, (1.0 - co.y) * 1080.0)

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
        prog = smoothstep(0.04, 0.90, u)
        pt_data.color = (0.0, 0.90, 1.0)
    elif shot_idx in [2, 3, 5]:
        prog = smoothstep(0.05, 0.90, u)
        pt_data.color = (1.0, 0.68, 0.12)
    else:
        prog = smoothstep(0.05, 0.90, u)
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
        if u > 0.10:
            p_n = proj2d(uv_to_3d(*anc["nose"], 0.18))
            draw_primal_pointer(dr, p_n[0], p_n[1], -65, -150, "950°F TITANIUM NOSE")
        if u > 0.35:
            p_i = proj2d(uv_to_3d(*anc["inlet"], 0.18))
            draw_primal_pointer(dr, p_i[0], p_i[1], 75, 130, "MACH 3.2 INLET CONE")
    elif shot_idx == 2:
        if u > 0.10:
            p_t = proj2d(uv_to_3d(*anc["tanks"], 0.18))
            draw_primal_pointer(dr, p_t[0], p_t[1], 75, -155, "6 INTERNAL JP-7 TANKS")
        if u > 0.40:
            p_e = proj2d(uv_to_3d(*anc["engine"], 0.18))
            draw_primal_pointer(dr, p_e[0], p_e[1], -75, 145, "FUEL-COOLED J58 CORE")
    elif shot_idx == 3:
        if u > 0.10:
            p_s = proj2d(uv_to_3d(*anc["seam"], 0.18))
            draw_primal_pointer(dr, p_s[0], p_s[1], 75, -145, "COLD TITANIUM EXPANSION GAPS")
        if u > 0.40:
            p_p = proj2d(uv_to_3d(*anc["puddle"], 0.18))
            draw_primal_pointer(dr, p_p[0], p_p[1], -75, -110, "JP-7 RUNWAY LEAK")
    elif shot_idx == 4:
        if u > 0.08:
            p_sp = proj2d(uv_to_3d(*anc["spike"], 0.18))
            draw_primal_pointer(dr, p_sp[0], p_sp[1], 65, -170, "26-INCH SLIDING SPIKE")
        if u > 0.30:
            p_tb = proj2d(uv_to_3d(*anc["tubes"], 0.18))
            draw_primal_pointer(dr, p_tb[0], p_tb[1], 65, -120, "6 BYPASS BLEED TUBES")
        if u > 0.55:
            p_ab = proj2d(uv_to_3d(*anc["ab"], 0.18))
            draw_primal_pointer(dr, p_ab[0], p_ab[1], 65, -175, "3,200°F AFTERBURNER")
    elif shot_idx == 5:
        if u > 0.12:
            p_cr = proj2d(uv_to_3d(*anc["crate"], 0.18))
            draw_primal_pointer(dr, p_cr[0], p_cr[1], 75, -145, "SOVIET TITANIUM SPONGE")
        if u > 0.40:
            p_ag = proj2d(uv_to_3d(*anc["agents"], 0.18))
            draw_primal_pointer(dr, p_ag[0], p_ag[1], 75, -140, "CIA SHELL COMPANY BUYERS")

    final_rgb = Image.alpha_composite(im, ov).convert("RGB")
    final_rgb.save(out_jpg, quality=96)
