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

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 10
scene.cycles.use_denoising = False
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.fps = 30
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 95

scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'

# Full Blender Compositor Mastering Pipeline:
# 1. Diamond Sharpen Filter (restores 1080p micro-stone sharpness to Wan 2.2 AI video)
# 2. Color Balance (cinematic warm highlights & deep shadows)
# 3. Selective Fog Glow Glare (optical bloom on 3D water/laser tubes & sunlight)
scene.use_nodes = True
comp_tree = scene.node_tree
comp_tree.nodes.clear()
c_rl = comp_tree.nodes.new('CompositorNodeRLayers')

c_sharp = comp_tree.nodes.new('CompositorNodeFilter')
c_sharp.filter_type = 'SHARPEN_DIAMOND'
c_sharp.inputs['Fac'].default_value = 0.38

c_cb = comp_tree.nodes.new('CompositorNodeColorBalance')
c_cb.correction_method = 'LIFT_GAMMA_GAIN'
c_cb.lift = (0.97, 0.98, 1.0)
c_cb.gamma = (1.0, 1.0, 0.98)
c_cb.gain = (1.05, 1.03, 0.99)

c_glare = comp_tree.nodes.new('CompositorNodeGlare')
c_glare.glare_type = 'FOG_GLOW'
c_glare.quality = 'MEDIUM'
c_glare.threshold = 1.65
c_glare.size = 7

c_comp = comp_tree.nodes.new('CompositorNodeComposite')

comp_tree.links.new(c_rl.outputs['Image'], c_sharp.inputs['Image'])
comp_tree.links.new(c_sharp.outputs['Image'], c_cb.inputs['Image'])
comp_tree.links.new(c_cb.outputs['Image'], c_glare.inputs['Image'])
comp_tree.links.new(c_glare.outputs['Image'], c_comp.inputs['Image'])

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

world = bpy.data.worlds.new("RomeFull3DWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.035, 0.04, 0.05, 1.0)
bg_node.inputs[1].default_value = 0.55

Z_REF = 18.6667
cam_data = bpy.data.cameras.new("MainCam")
cam_data.lens = 42.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("MainCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# 3D Key Sun + Cool Rim Light + Moving 3D Point Light to sculpt the 3D Bump-Mapped Wan 2.2 Video Mesh
sun_data = bpy.data.lights.new(name="SunKey", type='SUN')
sun_data.energy = 1.55
sun_data.color = (1.0, 0.93, 0.80)
sun_obj = bpy.data.objects.new(name="SunKey", object_data=sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(40), math.radians(-28), math.radians(16)), 'XYZ')

rim_data = bpy.data.lights.new(name="RimLight", type='SUN')
rim_data.energy = 0.55
rim_data.color = (0.65, 0.82, 1.0)
rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_data)
scene.collection.objects.link(rim_obj)
rim_obj.rotation_euler = Euler((math.radians(-38), math.radians(34), math.radians(0)), 'XYZ')

pt_data = bpy.data.lights.new(name="FlowLight", type='POINT')
pt_data.energy = 0.0
pt_data.shadow_soft_size = 1.35
pt_obj = bpy.data.objects.new(name="FlowLight", object_data=pt_data)
scene.collection.objects.link(pt_obj)

def load_depth_array(idx, w, h):
    p = os.path.join(ASSETS_DIR, f"depth{idx}.png")
    im = Image.open(p).convert("L").resize((w, h), Image.Resampling.BILINEAR)
    px = list(im.getdata())
    return [px[r * w:(r + 1) * w] for r in range(h)]

gw, gh = 160, 90
d_arr = load_depth_array(shot_idx, gw + 1, gh + 1)
DISP_SCALES = {1: 2.1, 2: 2.2, 3: 1.9, 4: 1.8, 5: 2.1}
disp_scale = DISP_SCALES[shot_idx]

bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=gw, y_segments=gh, size=1.0)
uv_layer = bm.loops.layers.uv.new("UVMap")
for face in bm.faces:
    face.smooth = True
    for loop in face.loops:
        v = loop.vert
        u = (v.co.x + 1.0) * 0.5
        w = (v.co.y + 1.0) * 0.5
        loop[uv_layer].uv = (u, w)

for v in bm.verts:
    u = max(0.0, min(1.0, (v.co.x + 1.0) * 0.5))
    w = max(0.0, min(1.0, (v.co.y + 1.0) * 0.5))
    ix = min(gw, int(u * gw))
    iy = min(gh, int((1.0 - w) * gh))
    d_norm = d_arr[iy][ix] / 255.0
    z_surf = (d_norm - 0.35) * disp_scale
    p_scale = (Z_REF - z_surf) / Z_REF
    v.co.x = v.co.x * 8.0 * p_scale
    v.co.y = v.co.y * 4.5 * p_scale
    v.co.z = z_surf

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
mesh = bpy.data.meshes.new("WanFull3DMesh")
bm.to_mesh(mesh)
bm.free()
vid_obj = bpy.data.objects.new("WanFull3DObj", mesh)
scene.collection.objects.link(vid_obj)

# Material with 3D Micro-Bump Normal Map generated from the Wan 2.2 Video Texture + Principled BSDF Specular & Roughness!
mat_vid = bpy.data.materials.new(name="MatWanFull3D")
mat_vid.use_nodes = True
nodes = mat_vid.node_tree.nodes
links = mat_vid.node_tree.links
nodes.clear()

out_node = nodes.new('ShaderNodeOutputMaterial')
add_sh = nodes.new('ShaderNodeAddShader')
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Roughness'].default_value = 0.52
bsdf.inputs['Specular IOR Level'].default_value = 0.55

em = nodes.new('ShaderNodeEmission')
em.inputs['Strength'].default_value = 0.65

tex_node = nodes.new('ShaderNodeTexImage')
first_img_path = os.path.join(frames_dir, f"wan_frame_{f_sub_start:04d}.jpg")
tex_node.image = bpy.data.images.load(first_img_path)

rgb_to_bw = nodes.new('ShaderNodeRGBToBW')
bump_node = nodes.new('ShaderNodeBump')
bump_node.inputs['Strength'].default_value = 0.58
bump_node.inputs['Distance'].default_value = 0.08

links.new(tex_node.outputs['Color'], rgb_to_bw.inputs['Color'])
links.new(rgb_to_bw.outputs['Val'], bump_node.inputs['Height'])
links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
links.new(tex_node.outputs['Color'], em.inputs['Color'])
links.new(bsdf.outputs['BSDF'], add_sh.inputs[0])
links.new(em.outputs['Emission'], add_sh.inputs[1])
links.new(add_sh.outputs['Shader'], out_node.inputs['Surface'])
mesh.materials.append(mat_vid)

def make_emission_mat(name, color, strength=3.8):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    l = mat.node_tree.links
    n.clear()
    o = n.new('ShaderNodeOutputMaterial')
    e = n.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1.0)
    e.inputs['Strength'].default_value = strength
    l.new(e.outputs['Emission'], o.inputs['Surface'])
    return mat

mat_cyan = make_emission_mat("MatCyanFlow", (0.0, 0.92, 1.0), 3.8)
mat_gold = make_emission_mat("MatGoldFlow", (1.0, 0.80, 0.14), 3.8)

def uv_to_3d(u, v_top, z_off=0.18):
    ix = min(gw, max(0, int(u * gw)))
    iy = min(gh, max(0, int(v_top * gh)))
    d_norm = d_arr[iy][ix] / 255.0
    z_surf = (d_norm - 0.35) * disp_scale + z_off
    p_scale = (Z_REF - z_surf) / Z_REF
    x = (u - 0.5) * 16.0 * p_scale
    y = (0.5 - v_top) * 9.0 * p_scale
    return Vector((x, y, z_surf))

init_sp = TRACKED[str(f_start)]["spline"]
init_pts = [uv_to_3d(u, v, 0.18) for u, v in init_sp]

curve_data = bpy.data.curves.new(name="TrackedTube", type='CURVE')
curve_data.dimensions = '3D'
curve_data.resolution_u = 24
curve_data.bevel_depth = 0.090 if shot_idx != 4 else 0.068
curve_data.bevel_resolution = 8
curve_data.use_fill_caps = True
spline = curve_data.splines.new('NURBS')
spline.points.add(len(init_pts) - 1)
for i, p in enumerate(init_pts):
    spline.points[i].co = (p.x, p.y, p.z, 1.0)
spline.use_endpoint_u = True
spline.order_u = min(4, len(init_pts))
tube_obj = bpy.data.objects.new("TrackedTubeObj", curve_data)
tube_obj.data.materials.append(mat_gold if shot_idx in [2, 4] else mat_cyan)
scene.collection.objects.link(tube_obj)

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / max(1e-6, b - a)))
    return t * t * (3.0 - 2.0 * t)

def lerp_pts(pts, f):
    f = max(0.0, min(1.0, f)) * (len(pts) - 1)
    i0 = int(f)
    i1 = min(len(pts) - 1, i0 + 1)
    return pts[i0].lerp(pts[i1], f - i0)

FONT_SERIF_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def project_uv(u, v_top, z_off=0.22):
    pt3d = uv_to_3d(u, v_top, z_off)
    co_2d = world_to_camera_view(scene, cam_obj, pt3d)
    return int(co_2d.x * 1920), int((1.0 - co_2d.y) * 1080)

def draw_stroked_text(draw, x, y, text, font, fill=(255, 255, 255, 255), stroke=(0, 0, 0, 230), sw=4, anchor="mm"):
    draw.text((x, y), text, font=font, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)

def draw_dashed_line(draw, p1, p2, color=(255, 255, 255, 230), width=3, dash=10, gap=7):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1:
        return
    ux, uy = dx / dist, dy / dist
    cur = 0.0
    while cur < dist:
        nx = min(dist, cur + dash)
        draw.line([(x1 + ux * cur, y1 + uy * cur), (x1 + ux * nx, y1 + uy * nx)], fill=color, width=width)
        cur += dash + gap

# Pre-build a subtle cinematic vignette mask to hide any outer AI border flicker
vignette = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
v_draw = ImageDraw.Draw(vignette)
for b in range(28):
    alpha = int(115 * ((28 - b) / 28.0) ** 2)
    v_draw.rectangle([b, b, 1919 - b, 1079 - b], outline=(6, 8, 12, alpha), width=1)

def composite_3d_hud(img_path, u, t, cur_pts, anchors):
    im = Image.open(img_path).convert("RGBA")
    im = Image.alpha_composite(im, vignette)
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    f_title = get_font(FONT_SERIF_ITALIC, 44)
    f_med = get_font(FONT_SERIF_ITALIC, 38)
    f_sub = get_font(FONT_SANS_BOLD, 25)
    f_small = get_font(FONT_SANS_BOLD, 22)

    if shot_idx == 2:
        a_lbl = int(255 * smoothstep(0.05, 0.22, u))
        if a_lbl > 5:
            mx, my = project_uv(*anchors["marcia"], 0.24)
            draw_stroked_text(draw, mx, my, "Aqua Marcia", f_title, (255, 255, 255, a_lbl), (0, 0, 0, a_lbl), 5)
            p_rome = project_uv(*anchors["rome"], 0.18)
            p_pop = (p_rome[0] - 255, p_rome[1] - 38)
            draw.line([p_pop, p_rome], fill=(255, 255, 255, int(a_lbl * 0.85)), width=3)
            draw.ellipse([p_rome[0]-5, p_rome[1]-5, p_rome[0]+5, p_rome[1]+5], fill=(255, 220, 100, a_lbl))
            pop_val = int(min(1.0, max(0.0, (u - 0.05) / 0.65)) * 1000000)
            draw_stroked_text(draw, p_pop[0] - 85, p_pop[1], f"{pop_val:,}", f_med, (255, 255, 255, a_lbl), (0, 0, 0, a_lbl), 4)
            f_prog = smoothstep(0.04, 0.90, u)
            pt_tip = lerp_pts(cur_pts, f_prog)
            co_tip = world_to_camera_view(scene, cam_obj, pt_tip)
            tx, ty = int(co_tip.x * 1920), int((1.0 - co_tip.y) * 1080) - 48
            km = int(round(f_prog * 90))
            mi = int(round(f_prog * 55))
            draw_stroked_text(draw, tx, ty, f"{km} km", f_med, (255, 240, 150, a_lbl), (0, 0, 0, a_lbl), 4)
            draw_stroked_text(draw, tx, ty + 34, f"{mi} miles", f_small, (230, 230, 230, a_lbl), (0, 0, 0, a_lbl), 3)

    elif shot_idx == 3:
        a_src = int(255 * smoothstep(0.04, 0.22, u))
        if a_src > 5:
            sx, sy = project_uv(*anchors["source"], 0.24)
            draw_stroked_text(draw, sx, sy, "Water", f_title, (255, 255, 255, a_src), (0, 0, 0, a_src), 5)
            draw_stroked_text(draw, sx, sy + 44, "source", f_title, (255, 255, 255, a_src), (0, 0, 0, a_src), 5)
        a_rm = int(255 * smoothstep(0.18, 0.38, u))
        if a_rm > 5:
            rx, ry = project_uv(*anchors["rome"], 0.28)
            ry = max(68, ry)
            draw_stroked_text(draw, rx, ry, "Rome", f_title, (255, 255, 255, a_rm), (0, 0, 0, a_rm), 5)

    elif shot_idx == 4:
        pL = project_uv(*anchors["pL"], 0.18)
        pR = project_uv(*anchors["pR"], 0.18)
        draw_dashed_line(draw, pL, pR, (255, 255, 255, 225), width=3, dash=12, gap=8)
        mx, my = project_uv(*anchors["mid"], 0.22)
        if u < 0.55:
            a1 = int(255 * smoothstep(0.05, 0.20, u) * (1.0 - smoothstep(0.45, 0.55, u)))
            if a1 > 5:
                draw_stroked_text(draw, mx, my, "1.5–3 meters per km", f_title, (255, 255, 255, a1), (0, 0, 0, a1), 5)
                draw_stroked_text(draw, mx, my + 42, "(8–16 feet per mile)", f_small, (235, 235, 235, a1), (0, 0, 0, a1), 3)
        else:
            a2 = int(255 * smoothstep(0.50, 0.65, u))
            if a2 > 5:
                draw_stroked_text(draw, mx, my + 10, "0.09 – 0.17°", get_font(FONT_SERIF_ITALIC, 48), (255, 255, 255, a2), (0, 0, 0, a2), 5)

    elif shot_idx == 5:
        a_ht = int(255 * smoothstep(0.05, 0.22, u))
        if a_ht > 5:
            hx, hy = project_uv(*anchors["ht_lbl"], 0.24)
            p_tank = project_uv(*anchors["ht_tank"], 0.18)
            draw.line([(hx, hy + 24), p_tank], fill=(255, 255, 255, int(a_ht * 0.85)), width=3)
            draw_stroked_text(draw, hx, hy, "Header tank", f_med, (255, 255, 255, a_ht), (0, 0, 0, a_ht), 4)
        a_50 = int(255 * smoothstep(0.22, 0.42, u))
        if a_50 > 5:
            p_top = project_uv(*anchors["top50"], 0.18)
            p_bot = project_uv(*anchors["bot50"], 0.18)
            draw_dashed_line(draw, p_top, p_bot, (255, 225, 80, a_50), width=3, dash=9, gap=6)
            draw_stroked_text(draw, p_top[0], p_top[1] - 46, "50 m", f_med, (255, 255, 255, a_50), (0, 0, 0, a_50), 4)
            draw_stroked_text(draw, p_top[0], p_top[1] - 14, "(164 ft)", f_small, (235, 235, 235, a_50), (0, 0, 0, a_50), 3)

    subs = [
        (0.15, 2.30, "Roman", "aqueducts", "carried fresh water"),
        (2.30, 4.35, "", "100 kilometers", "across valleys into the city"),
        (4.35, 8.25, "The", "Aqua Marcia", "spanned 90 km, supplying 1,000,000 citizens"),
        (8.25, 11.75, "From", "mountain springs,", "stone bridges guided water by gravity alone"),
        (11.75, 15.80, "Aqueducts dropped just", "1.5 to 3 meters", "per kilometer (0.09–0.17°)"),
        (15.80, 19.95, "Across deep valleys, pressurized siphons drove water", "50 meters", "uphill")
    ]
    for s0, s1, pre, hi, post in subs:
        if s0 <= t <= s1:
            parts = [(pre + " ", (255, 255, 255, 255)) if pre else ("", (255,255,255,255)),
                     (hi + " ", (255, 212, 64, 255)),
                     (post, (255, 255, 255, 255))]
            full_txt = (pre + " " if pre else "") + hi + (" " + post if post else "")
            bbox = draw.textbbox((0, 0), full_txt, font=f_sub)
            tw = bbox[2] - bbox[0]
            pad_x, pad_y = 24, 12
            bx0, by0 = 960 - tw // 2 - pad_x, 1018 - 18 - pad_y
            bx1, by1 = 960 + tw // 2 + pad_x, 1018 + 18 + pad_y
            draw.rounded_rectangle([bx0, by0, bx1, by1], radius=10, fill=(8, 10, 14, 195), outline=(255, 212, 64, 90), width=1)
            cur_x = 960 - tw // 2
            for txt_seg, col in parts:
                if not txt_seg:
                    continue
                f_use = get_font(FONT_SERIF_ITALIC, 26) if col[1] == 212 else f_sub
                draw.text((cur_x, 1018), txt_seg, font=f_use, fill=col, anchor="lm")
                seg_bb = draw.textbbox((0, 0), txt_seg, font=f_use)
                cur_x += (seg_bb[2] - seg_bb[0])
            break

    out = Image.alpha_composite(im, overlay).convert("RGB")
    out.save(img_path, quality=95)

for f in range(f_sub_start, f_sub_end + 1):
    t = (f - 1) / 30.0
    u = max(0.0, min(1.0, (t - t0) / max(1e-6, t1 - t0)))
    ease = u * u * (3.0 - 2.0 * u)

    # Load current Wan 2.2 AI video frame into the 3D Bump-Mapped & Displaced Mesh
    cur_img_path = os.path.join(frames_dir, f"wan_frame_{f:04d}.jpg")
    bpy.data.images.remove(tex_node.image)
    tex_node.image = bpy.data.images.load(cur_img_path)

    # Update 3D NURBS spline coordinates from Lucas-Kanade Optical Flow tracking
    f_data = TRACKED[str(f)]
    cur_pts = [uv_to_3d(u_p, v_p, 0.18) for u_p, v_p in f_data["spline"]]
    for i, p in enumerate(cur_pts):
        spline.points[i].co = (p.x, p.y, p.z, 1.0)

    # Add smooth 3D camera parallax orbit in Blender ON TOP of the Wan 2.2 motion!
    cam_pos = Vector((-0.85 + ease * 1.70, -0.45 + ease * 0.80, 17.6 - ease * 1.4))
    look_t = Vector((0.15 * ease, 0.05 * ease, 0.0))
    cam_obj.location = cam_pos
    dx = look_t.x - cam_pos.x
    dy = look_t.y - cam_pos.y
    dz = cam_pos.z - look_t.z
    cam_obj.rotation_euler = Euler((math.atan2(dy, dz), -math.atan2(dx, dz), 0.0), 'XYZ')

    if shot_idx == 1:
        f_prog = smoothstep(0.08, 0.88, u)
        pt_data.color = (0.0, 0.90, 1.0)
        pt_data.energy = 85.0
    elif shot_idx == 2:
        f_prog = smoothstep(0.04, 0.90, u)
        pt_data.color = (1.0, 0.78, 0.15)
        pt_data.energy = 115.0
    elif shot_idx == 3:
        f_prog = smoothstep(0.06, 0.90, u)
        pt_data.color = (0.0, 0.92, 1.0)
        pt_data.energy = 95.0
    elif shot_idx == 4:
        f_prog = smoothstep(0.04, 0.85, u)
        pt_data.color = (1.0, 0.82, 0.18)
        pt_data.energy = 90.0
    else:
        f_prog = smoothstep(0.05, 0.92, u)
        pt_data.color = (0.0, 0.92, 1.0)
        pt_data.energy = 105.0

    tube_obj.data.bevel_factor_end = f_prog
    pt_obj.location = lerp_pts(cur_pts, f_prog) + Vector((0, 0, 0.50))

    bpy.context.view_layer.update()
    out_file = os.path.join(out_dir, f"frame_{f:04d}.jpg")
    scene.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    composite_3d_hud(out_file, u, t, cur_pts, f_data["anchors"])
