import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw, ImageFont

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = []

start_frame = int(args[0]) if len(args) > 0 else 1
end_frame = int(args[1]) if len(args) > 1 else 600
out_dir = os.path.abspath(args[2]) if len(args) > 2 else os.path.abspath("./frames_tech6")
os.makedirs(out_dir, exist_ok=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../rome_ai_3d/assets"))

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.fps = 30
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 94

scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'Medium High Contrast'

scene.use_nodes = True
comp_tree = scene.node_tree
comp_tree.nodes.clear()
c_rl = comp_tree.nodes.new('CompositorNodeRLayers')
c_glare = comp_tree.nodes.new('CompositorNodeGlare')
c_glare.glare_type = 'FOG_GLOW'
c_glare.quality = 'MEDIUM'
c_glare.threshold = 1.80
c_glare.size = 6
c_comp = comp_tree.nodes.new('CompositorNodeComposite')
comp_tree.links.new(c_rl.outputs['Image'], c_glare.inputs['Image'])
comp_tree.links.new(c_glare.outputs['Image'], c_comp.inputs['Image'])

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

world = bpy.data.worlds.new("RomeDioramaWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.055, 0.06, 0.075, 1.0)
bg_node.inputs[1].default_value = 0.85

cam_data = bpy.data.cameras.new("OrbitCam")
cam_data.lens = 38.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("OrbitCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

sun_data = bpy.data.lights.new(name="SunKey", type='SUN')
sun_data.energy = 1.8
sun_data.color = (1.0, 0.94, 0.82)
sun_obj = bpy.data.objects.new(name="SunKey", object_data=sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(42), math.radians(-30), math.radians(18)), 'XYZ')

rim_data = bpy.data.lights.new(name="RimLight", type='SUN')
rim_data.energy = 0.75
rim_data.color = (0.65, 0.82, 1.0)
rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_data)
scene.collection.objects.link(rim_obj)
rim_obj.rotation_euler = Euler((math.radians(-45), math.radians(40), math.radians(0)), 'XYZ')

pt_data = bpy.data.lights.new(name="FlowLight", type='POINT')
pt_data.energy = 0.0
pt_data.shadow_soft_size = 1.4
pt_obj = bpy.data.objects.new(name="FlowLight", object_data=pt_data)
scene.collection.objects.link(pt_obj)

# Studio architectural pedestal base material
mat_plinth = bpy.data.materials.new(name="MatPlinth")
mat_plinth.use_nodes = True
bsdf_p = mat_plinth.node_tree.nodes.get("Principled BSDF")
bsdf_p.inputs['Base Color'].default_value = (0.14, 0.12, 0.10, 1.0)
bsdf_p.inputs['Roughness'].default_value = 0.45

# Travertine 3D arch block material
mat_trav = bpy.data.materials.new(name="MatTravertine3D")
mat_trav.use_nodes = True
bsdf_t = mat_trav.node_tree.nodes.get("Principled BSDF")
bsdf_t.inputs['Base Color'].default_value = (0.76, 0.69, 0.56, 1.0)
bsdf_t.inputs['Roughness'].default_value = 0.55

def load_depth_array(idx, w, h):
    p = os.path.join(ASSETS_DIR, f"depth{idx}.png")
    im = Image.open(p).convert("L").resize((w, h), Image.Resampling.BILINEAR)
    px = list(im.getdata())
    return [px[r * w:(r + 1) * w] for r in range(h)]

def build_volumetric_360_diorama(idx):
    """
    Reconstructs a closed 3D volumetric diorama mesh + 3D architectural plinth + 3D extruded arches
    so the Blender camera can orbit in a wide 3D arc around the miniature 3D island!
    """
    root = bpy.data.objects.new(f"Diorama360_{idx}", None)
    scene.collection.objects.link(root)

    gw, gh = 200, 112
    d_arr = load_depth_array(idx, gw + 1, gh + 1)

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

    # Displace into a true 3D tabletop relief block (X in [-7.2, 7.2], Y in [-4.05, 4.05], Z height from depth)
    for v in bm.verts:
        u = max(0.0, min(1.0, (v.co.x + 1.0) * 0.5))
        w = max(0.0, min(1.0, (v.co.y + 1.0) * 0.5))
        ix = min(gw, int(u * gw))
        iy = min(gh, int((1.0 - w) * gh))
        d_norm = d_arr[iy][ix] / 255.0
        v.co.x = v.co.x * 7.2
        v.co.y = v.co.y * 4.05
        v.co.z = (d_norm - 0.25) * 3.8

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"VolMesh_{idx}")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(f"VolObj_{idx}", mesh)
    obj.parent = root
    scene.collection.objects.link(obj)

    # Give the 3D relief a solid volumetric slab thickness via Solidify modifier
    sol = obj.modifiers.new(name="VolSlab", type='SOLIDIFY')
    sol.thickness = 1.85
    sol.offset = -1.0

    # Build a dark museum display plinth underneath the 3D diorama block so orbiting reveals a clean 3D pedestal
    bm_base = bmesh.new()
    bmesh.ops.create_cube(bm_base, size=1.0)
    for v in bm_base.verts:
        v.co.x *= 14.8
        v.co.y *= 8.4
        v.co.z = v.co.z * 1.4 - 2.1
    m_base = bpy.data.meshes.new(f"Plinth_{idx}")
    bm_base.to_mesh(m_base)
    bm_base.free()
    m_base.materials.append(mat_plinth)
    o_base = bpy.data.objects.new(f"Plinth_{idx}", m_base)
    o_base.parent = root
    scene.collection.objects.link(o_base)

    # Material for the 3D volumetric surface
    mat = bpy.data.materials.new(name=f"MatVol_{idx}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    add_sh = nodes.new('ShaderNodeAddShader')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.58
    em = nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 0.68
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(ASSETS_DIR, f"rgb{idx}.jpg"))
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(tex.outputs['Color'], em.inputs['Color'])
    links.new(bsdf.outputs['BSDF'], add_sh.inputs[0])
    links.new(em.outputs['Emission'], add_sh.inputs[1])
    links.new(add_sh.outputs['Shader'], out.inputs['Surface'])
    mesh.materials.append(mat)
    mesh.materials.append(mat_plinth)
    sol.material_offset = 1

    return root, d_arr, (gw, gh)

def make_emission_mat(name, color, strength=3.4):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    em = nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1.0)
    em.inputs['Strength'].default_value = strength
    links.new(em.outputs['Emission'], out.inputs['Surface'])
    return mat

mat_cyan = make_emission_mat("MatCyanFlow", (0.0, 0.92, 1.0), 3.6)
mat_gold = make_emission_mat("MatGoldFlow", (1.0, 0.80, 0.14), 3.6)

roots = {}
depths = {}
for i in range(1, 6):
    r, d_arr, dims = build_volumetric_360_diorama(i)
    roots[i] = r
    depths[i] = (d_arr, dims)

def map_pt3d(idx, u, v_top, z_off=0.20):
    d_arr, (gw, gh) = depths[idx]
    ix = min(gw, max(0, int(u * gw)))
    iy = min(gh, max(0, int(v_top * gh)))
    d_norm = d_arr[iy][ix] / 255.0
    z_surf = (d_norm - 0.25) * 3.8 + z_off
    x = (u - 0.5) * 14.4
    y = (0.5 - v_top) * 8.1
    return Vector((x, y, z_surf))

def create_curve_tube(name, pts, bevel_depth, mat):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 24
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = 8
    curve_data.use_fill_caps = True
    spline = curve_data.splines.new('NURBS')
    spline.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        spline.points[i].co = (p.x, p.y, p.z, 1.0)
    spline.use_endpoint_u = True
    spline.order_u = min(4, len(pts))
    obj = bpy.data.objects.new(name, curve_data)
    obj.data.materials.append(mat)
    scene.collection.objects.link(obj)
    return obj

s1_pts = [map_pt3d(1, u, v, 0.18) for u, v in [
    (0.00, 0.595), (0.18, 0.535), (0.35, 0.472), (0.52, 0.412), (0.68, 0.355), (0.87, 0.285)
]]
tube_s1 = create_curve_tube("SpecusS1", s1_pts, 0.085, mat_cyan)

s2_pts = [map_pt3d(2, u, v, 0.20) for u, v in [
    (0.245, 0.615), (0.33, 0.635), (0.43, 0.655), (0.53, 0.640), (0.63, 0.585), (0.72, 0.505), (0.80, 0.415)
]]
tube_s2 = create_curve_tube("MarciaS2", s2_pts, 0.095, mat_gold)

s3_pts = [map_pt3d(3, u, v, 0.18) for u, v in [
    (0.81, 0.545), (0.68, 0.525), (0.52, 0.500), (0.36, 0.478), (0.20, 0.452), (0.08, 0.435)
]]
tube_s3 = create_curve_tube("CutawayS3", s3_pts, 0.095, mat_cyan)

s4_pts = [map_pt3d(4, u, v, 0.18) for u, v in [
    (0.04, 0.525), (0.25, 0.468), (0.48, 0.402), (0.72, 0.330), (0.95, 0.255)
]]
tube_s4 = create_curve_tube("LaserS4", s4_pts, 0.065, mat_gold)

s5_pts = [map_pt3d(5, u, v, 0.22) for u, v in [
    (0.11, 0.475), (0.16, 0.505), (0.23, 0.675), (0.31, 0.855), (0.40, 0.935),
    (0.49, 0.940), (0.58, 0.855), (0.66, 0.695), (0.74, 0.530), (0.80, 0.495)
]]
tube_s5 = create_curve_tube("SiphonS5", s5_pts, 0.095, mat_cyan)

all_tubes = [tube_s1, tube_s2, tube_s3, tube_s4, tube_s5]

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

def project_uv(idx, u, v_top, z_off=0.24):
    pt3d = map_pt3d(idx, u, v_top, z_off)
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

def composite_3d_hud(img_path, active_idx, u, t):
    im = Image.open(img_path).convert("RGBA")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    f_title = get_font(FONT_SERIF_ITALIC, 44)
    f_med = get_font(FONT_SERIF_ITALIC, 38)
    f_sub = get_font(FONT_SANS_BOLD, 25)
    f_small = get_font(FONT_SANS_BOLD, 22)

    if active_idx == 2:
        a_lbl = int(255 * smoothstep(0.05, 0.22, u))
        if a_lbl > 5:
            mx, my = project_uv(2, 0.56, 0.45, 0.25)
            draw_stroked_text(draw, mx, my, "Aqua Marcia", f_title, (255, 255, 255, a_lbl), (0, 0, 0, a_lbl), 5)
            p_rome = project_uv(2, 0.245, 0.615, 0.20)
            p_pop = (p_rome[0] - 235, p_rome[1] - 35)
            draw.line([p_pop, p_rome], fill=(255, 255, 255, int(a_lbl * 0.85)), width=3)
            draw.ellipse([p_rome[0]-5, p_rome[1]-5, p_rome[0]+5, p_rome[1]+5], fill=(255, 220, 100, a_lbl))
            pop_val = int(min(1.0, max(0.0, (u - 0.05) / 0.65)) * 1000000)
            draw_stroked_text(draw, p_pop[0] - 85, p_pop[1], f"{pop_val:,}", f_med, (255, 255, 255, a_lbl), (0, 0, 0, a_lbl), 4)
            f_prog = smoothstep(0.04, 0.90, u)
            pt_tip = lerp_pts(s2_pts, f_prog)
            co_tip = world_to_camera_view(scene, cam_obj, pt_tip)
            tx, ty = int(co_tip.x * 1920), int((1.0 - co_tip.y) * 1080) - 48
            km = int(round(f_prog * 90))
            mi = int(round(f_prog * 55))
            draw_stroked_text(draw, tx, ty, f"{km} km", f_med, (255, 240, 150, a_lbl), (0, 0, 0, a_lbl), 4)
            draw_stroked_text(draw, tx, ty + 34, f"{mi} miles", f_small, (230, 230, 230, a_lbl), (0, 0, 0, a_lbl), 3)

    elif active_idx == 3:
        a_src = int(255 * smoothstep(0.04, 0.22, u))
        if a_src > 5:
            sx, sy = project_uv(3, 0.80, 0.34, 0.25)
            draw_stroked_text(draw, sx, sy, "Water", f_title, (255, 255, 255, a_src), (0, 0, 0, a_src), 5)
            draw_stroked_text(draw, sx, sy + 44, "source", f_title, (255, 255, 255, a_src), (0, 0, 0, a_src), 5)
        a_rm = int(255 * smoothstep(0.18, 0.38, u))
        if a_rm > 5:
            rx, ry = project_uv(3, 0.14, 0.17, 0.30)
            ry = max(68, ry)
            draw_stroked_text(draw, rx, ry, "Rome", f_title, (255, 255, 255, a_rm), (0, 0, 0, a_rm), 5)

    elif active_idx == 4:
        pL = project_uv(4, 0.08, 0.39, 0.20)
        pR = project_uv(4, 0.86, 0.15, 0.20)
        draw_dashed_line(draw, pL, pR, (255, 255, 255, 225), width=3, dash=12, gap=8)
        mx, my = project_uv(4, 0.44, 0.22, 0.24)
        if u < 0.55:
            a1 = int(255 * smoothstep(0.05, 0.20, u) * (1.0 - smoothstep(0.45, 0.55, u)))
            if a1 > 5:
                draw_stroked_text(draw, mx, my, "1.5–3 meters per km", f_title, (255, 255, 255, a1), (0, 0, 0, a1), 5)
                draw_stroked_text(draw, mx, my + 42, "(8–16 feet per mile)", f_small, (235, 235, 235, a1), (0, 0, 0, a1), 3)
        else:
            a2 = int(255 * smoothstep(0.50, 0.65, u))
            if a2 > 5:
                draw_stroked_text(draw, mx, my + 10, "0.09 – 0.17°", get_font(FONT_SERIF_ITALIC, 48), (255, 255, 255, a2), (0, 0, 0, a2), 5)

    elif active_idx == 5:
        a_ht = int(255 * smoothstep(0.05, 0.22, u))
        if a_ht > 5:
            hx, hy = project_uv(5, 0.15, 0.30, 0.25)
            p_tank = project_uv(5, 0.12, 0.46, 0.22)
            draw.line([(hx, hy + 24), p_tank], fill=(255, 255, 255, int(a_ht * 0.85)), width=3)
            draw_stroked_text(draw, hx, hy, "Header tank", f_med, (255, 255, 255, a_ht), (0, 0, 0, a_ht), 4)
        a_50 = int(255 * smoothstep(0.22, 0.42, u))
        if a_50 > 5:
            p_top = project_uv(5, 0.46, 0.48, 0.22)
            p_bot = project_uv(5, 0.46, 0.90, 0.22)
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
    out.save(img_path, quality=94)

for f in range(start_frame, end_frame + 1):
    t = (f - 1) / 30.0
    if t < 4.35:
        active_idx = 1
        u = t / 4.35
    elif t < 8.25:
        active_idx = 2
        u = (t - 4.35) / (8.25 - 4.35)
    elif t < 11.75:
        active_idx = 3
        u = (t - 8.25) / (11.75 - 8.25)
    elif t < 15.80:
        active_idx = 4
        u = (t - 11.75) / (15.80 - 11.75)
    else:
        active_idx = 5
        u = (t - 15.80) / (20.0 - 15.80)
    u = max(0.0, min(1.0, u))
    ease = u * u * (3.0 - 2.0 * u)

    for i, r in roots.items():
        r.hide_render = (i != active_idx)
    for tb in all_tubes:
        tb.hide_render = True

    # True 3D spherical orbit around the 3D volumetric tabletop diorama (40-degree orbital sweep!)
    azim = math.radians(-22.0 + ease * 44.0)
    elev = math.radians(18.0 - ease * 8.0)
    radius = 15.6 - ease * 2.2

    cx = radius * math.sin(azim) * math.cos(elev)
    cy = -radius * math.sin(elev)
    cz = radius * math.cos(azim) * math.cos(elev)
    cam_pos = Vector((cx, cy, cz))
    look_t = Vector((0.0, 0.0, 0.25))

    if active_idx == 1:
        tube_s1.hide_render = False
        f_prog = smoothstep(0.10, 0.88, u)
        tube_s1.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s1_pts, f_prog) + Vector((0, 0, 0.45))
        pt_data.color = (0.0, 0.90, 1.0)
        pt_data.energy = 85.0 if f_prog > 0.01 else 0.0
    elif active_idx == 2:
        tube_s2.hide_render = False
        f_prog = smoothstep(0.04, 0.90, u)
        tube_s2.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s2_pts, f_prog) + Vector((0, 0, 0.55))
        pt_data.color = (1.0, 0.78, 0.15)
        pt_data.energy = 115.0
    elif active_idx == 3:
        tube_s3.hide_render = False
        f_prog = smoothstep(0.06, 0.90, u)
        tube_s3.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s3_pts, f_prog) + Vector((0, 0, 0.55))
        pt_data.color = (0.0, 0.92, 1.0)
        pt_data.energy = 95.0
    elif active_idx == 4:
        tube_s4.hide_render = False
        f_prog = smoothstep(0.04, 0.85, u)
        tube_s4.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s4_pts, f_prog) + Vector((0, 0, 0.45))
        pt_data.color = (1.0, 0.82, 0.18)
        pt_data.energy = 90.0
    else:
        tube_s5.hide_render = False
        f_prog = smoothstep(0.05, 0.92, u)
        tube_s5.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s5_pts, f_prog) + Vector((0, 0, 0.55))
        pt_data.color = (0.0, 0.92, 1.0)
        pt_data.energy = 105.0

    cam_obj.location = cam_pos
    dx = look_t.x - cam_pos.x
    dy = look_t.y - cam_pos.y
    dz = cam_pos.z - look_t.z
    rx = math.atan2(dy, dz)
    ry = -math.atan2(dx, dz)
    cam_obj.rotation_euler = Euler((rx, ry, 0.0), 'XYZ')

    bpy.context.view_layer.update()
    out_file = os.path.join(out_dir, f"frame_{f:04d}.jpg")
    scene.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    composite_3d_hud(out_file, active_idx, u, t)
