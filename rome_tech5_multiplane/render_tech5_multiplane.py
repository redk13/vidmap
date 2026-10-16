import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw, ImageFont, ImageFilter

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = []

start_frame = int(args[0]) if len(args) > 0 else 1
end_frame = int(args[1]) if len(args) > 1 else 600
out_dir = os.path.abspath(args[2]) if len(args) > 2 else os.path.abspath("./frames_tech5")
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
c_glare.threshold = 1.85
c_glare.size = 6
c_comp = comp_tree.nodes.new('CompositorNodeComposite')
comp_tree.links.new(c_rl.outputs['Image'], c_glare.inputs['Image'])
comp_tree.links.new(c_glare.outputs['Image'], c_comp.inputs['Image'])

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

world = bpy.data.worlds.new("RomeMultiplaneWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.04, 0.045, 0.06, 1.0)
bg_node.inputs[1].default_value = 0.55

cam_data = bpy.data.cameras.new("MainCam")
cam_data.lens = 40.0
cam_data.sensor_width = 36.0
cam_obj = bpy.data.objects.new("MainCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

sun_data = bpy.data.lights.new(name="SunKey", type='SUN')
sun_data.energy = 1.4
sun_data.color = (1.0, 0.93, 0.80)
sun_obj = bpy.data.objects.new(name="SunKey", object_data=sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(38), math.radians(-26), math.radians(15)), 'XYZ')

pt_data = bpy.data.lights.new(name="FlowLight", type='POINT')
pt_data.energy = 0.0
pt_data.shadow_soft_size = 1.4
pt_obj = bpy.data.objects.new(name="FlowLight", object_data=pt_data)
scene.collection.objects.link(pt_obj)

Z_REF = 17.7778

def load_depth_array(idx, w, h):
    p = os.path.join(ASSETS_DIR, f"depth{idx}.png")
    im = Image.open(p).convert("L").resize((w, h), Image.Resampling.BILINEAR)
    px = list(im.getdata())
    return [px[r * w:(r + 1) * w] for r in range(h)]

def build_multiplane_scene(idx):
    """
    Separates the image into 3 distinct 3D layers in Blender space:
    1. Far Background Sky & Mountains Plane (pushed deep back to Z = -6.5, scaled by frustum so it covers the background during wide camera motion)
    2. Midground Volumetric 3D Cutout Structure (Aqueduct / Arches / Ridges with Solidify 3D thickness and alpha-masked cutout holes where background shows through!)
    3. Foreground Terrain Plane (at Z = +2.2 with alpha mask for close foreground elements)
    """
    root = bpy.data.objects.new(f"MultiplaneRoot_{idx}", None)
    scene.collection.objects.link(root)

    rgb_path = os.path.join(ASSETS_DIR, f"rgb{idx}.jpg")
    rgb_im = Image.open(rgb_path).convert("RGB")
    W, H = rgb_im.size
    dep_im = Image.open(os.path.join(ASSETS_DIR, f"depth{idx}.png")).convert("L").resize((W, H), Image.Resampling.BILINEAR)

    # Create RGBA textures for Midground Cutout (with open arches/background removed) and Foreground Cutout
    mid_rgba = Image.new("RGBA", (W, H))
    fg_rgba = Image.new("RGBA", (W, H))
    bg_rgb = rgb_im.filter(ImageFilter.GaussianBlur(radius=3))

    rgb_px = rgb_im.load()
    dep_px = dep_im.load()
    mid_px = mid_rgba.load()
    fg_px = fg_rgba.load()

    for y in range(H):
        for x in range(W):
            d = dep_px[x, y] / 255.0
            r, g, b = rgb_px[x, y]
            # Sky / dark arch shadow openings or distant background stay on the Far Plane
            is_sky_or_far = d < 0.28
            # Also detect open arch shadow holes in shots 1, 3, 4, 5 so the camera sees through the arches!
            luma = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            is_arch_hole = (idx in [1, 3, 4, 5]) and (0.25 < y / H < 0.78) and (d < 0.46) and (luma < 0.22)
            if is_sky_or_far or is_arch_hole:
                mid_px[x, y] = (r, g, b, 0)
            else:
                mid_px[x, y] = (r, g, b, 255)

            if d > 0.72:
                fg_px[x, y] = (r, g, b, 255)
            else:
                fg_px[x, y] = (r, g, b, 0)

    bg_path = f"/tmp/mp_bg_{idx}.jpg"
    mid_path = f"/tmp/mp_mid_{idx}.png"
    fg_path = f"/tmp/mp_fg_{idx}.png"
    bg_rgb.save(bg_path, quality=92)
    mid_rgba.save(mid_path)
    fg_rgba.save(fg_path)

    # 1. Far Background Dome/Plane at Z = -6.0 (scaled 1.48x to allow wide 3D camera sweep)
    z_bg = -6.0
    scale_bg = (Z_REF - z_bg) / Z_REF * 1.18
    bm_bg = bmesh.new()
    bmesh.ops.create_grid(bm_bg, x_segments=64, y_segments=36, size=1.0)
    uv_bg = bm_bg.loops.layers.uv.new("UVMap")
    for face in bm_bg.faces:
        face.smooth = True
        for loop in face.loops:
            v = loop.vert
            u = (v.co.x + 1.0) * 0.5
            w_uv = (v.co.y + 1.0) * 0.5
            loop[uv_bg].uv = (u, w_uv)
    for v in bm_bg.verts:
        # Slight concave cylinder curve for panoramic wrap
        ang = v.co.x * 0.28
        v.co.x = v.co.x * 8.0 * scale_bg
        v.co.y = v.co.y * 4.5 * scale_bg
        v.co.z = z_bg + (v.co.x * v.co.x) * 0.015
    m_bg = bpy.data.meshes.new(f"BG_{idx}")
    bm_bg.to_mesh(m_bg)
    bm_bg.free()
    o_bg = bpy.data.objects.new(f"BG_{idx}", m_bg)
    o_bg.parent = root
    scene.collection.objects.link(o_bg)

    mat_bg = bpy.data.materials.new(name=f"MatBG_{idx}")
    mat_bg.use_nodes = True
    nt = mat_bg.node_tree
    nt.nodes.clear()
    n_out = nt.nodes.new('ShaderNodeOutputMaterial')
    n_em = nt.nodes.new('ShaderNodeEmission')
    n_tex = nt.nodes.new('ShaderNodeTexImage')
    n_tex.image = bpy.data.images.load(bg_path)
    n_em.inputs['Strength'].default_value = 0.95
    nt.links.new(n_tex.outputs['Color'], n_em.inputs['Color'])
    nt.links.new(n_em.outputs['Emission'], n_out.inputs['Surface'])
    m_bg.materials.append(mat_bg)

    # 2. Midground 3D Volumetric Cutout Mesh with Solidify 3D Thickness (Open Arches!)
    gw, gh = 220, 124
    d_arr = load_depth_array(idx, gw + 1, gh + 1)
    bm_mid = bmesh.new()
    bmesh.ops.create_grid(bm_mid, x_segments=gw, y_segments=gh, size=1.0)
    uv_mid = bm_mid.loops.layers.uv.new("UVMap")
    for face in bm_mid.faces:
        face.smooth = True
        for loop in face.loops:
            v = loop.vert
            u = (v.co.x + 1.0) * 0.5
            w_uv = (v.co.y + 1.0) * 0.5
            loop[uv_mid].uv = (u, w_uv)
    for v in bm_mid.verts:
        u = max(0.0, min(1.0, (v.co.x + 1.0) * 0.5))
        w_uv = max(0.0, min(1.0, (v.co.y + 1.0) * 0.5))
        ix = min(gw, int(u * gw))
        iy = min(gh, int((1.0 - w_uv) * gh))
        d_norm = d_arr[iy][ix] / 255.0
        z_surf = (d_norm - 0.35) * 3.8
        p_scale = (Z_REF - z_surf) / Z_REF
        v.co.x = v.co.x * 8.0 * p_scale
        v.co.y = v.co.y * 4.5 * p_scale
        v.co.z = z_surf
    bmesh.ops.recalc_face_normals(bm_mid, faces=bm_mid.faces)
    m_mid = bpy.data.meshes.new(f"MID_{idx}")
    bm_mid.to_mesh(m_mid)
    bm_mid.free()
    o_mid = bpy.data.objects.new(f"MID_{idx}", m_mid)
    o_mid.parent = root
    scene.collection.objects.link(o_mid)

    # Add true 3D architectural thickness via Blender Solidify Modifier!
    sol = o_mid.modifiers.new(name="ArchThickness", type='SOLIDIFY')
    sol.thickness = 0.55
    sol.offset = -1.0

    mat_mid = bpy.data.materials.new(name=f"MatMID_{idx}")
    mat_mid.use_nodes = True
    nt = mat_mid.node_tree
    nt.nodes.clear()
    n_out = nt.nodes.new('ShaderNodeOutputMaterial')
    n_mix_trans = nt.nodes.new('ShaderNodeMixShader')
    n_trans = nt.nodes.new('ShaderNodeBsdfTransparent')
    n_add = nt.nodes.new('ShaderNodeAddShader')
    n_bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    n_bsdf.inputs['Roughness'].default_value = 0.65
    n_em = nt.nodes.new('ShaderNodeEmission')
    n_em.inputs['Strength'].default_value = 0.72
    n_tex = nt.nodes.new('ShaderNodeTexImage')
    n_tex.image = bpy.data.images.load(mid_path)
    nt.links.new(n_tex.outputs['Color'], n_bsdf.inputs['Base Color'])
    nt.links.new(n_tex.outputs['Color'], n_em.inputs['Color'])
    nt.links.new(n_bsdf.outputs['BSDF'], n_add.inputs[0])
    nt.links.new(n_em.outputs['Emission'], n_add.inputs[1])
    nt.links.new(n_tex.outputs['Alpha'], n_mix_trans.inputs['Fac'])
    nt.links.new(n_trans.outputs['BSDF'], n_mix_trans.inputs[1])
    nt.links.new(n_add.outputs['Shader'], n_mix_trans.inputs[2])
    nt.links.new(n_mix_trans.outputs['Shader'], n_out.inputs['Surface'])
    m_mid.materials.append(mat_mid)

    # 3. Foreground Floating Layer at Z = +2.4 for strong foreground parallax separation
    bm_fg = bmesh.new()
    bmesh.ops.create_grid(bm_fg, x_segments=80, y_segments=45, size=1.0)
    uv_fg = bm_fg.loops.layers.uv.new("UVMap")
    for face in bm_fg.faces:
        face.smooth = True
        for loop in face.loops:
            v = loop.vert
            u = (v.co.x + 1.0) * 0.5
            w_uv = (v.co.y + 1.0) * 0.5
            loop[uv_fg].uv = (u, w_uv)
    z_fg = 2.4
    scale_fg = (Z_REF - z_fg) / Z_REF
    for v in bm_fg.verts:
        v.co.x = v.co.x * 8.0 * scale_fg
        v.co.y = v.co.y * 4.5 * scale_fg
        v.co.z = z_fg
    m_fg = bpy.data.meshes.new(f"FG_{idx}")
    bm_fg.to_mesh(m_fg)
    bm_fg.free()
    o_fg = bpy.data.objects.new(f"FG_{idx}", m_fg)
    o_fg.parent = root
    scene.collection.objects.link(o_fg)

    mat_fg = bpy.data.materials.new(name=f"MatFG_{idx}")
    mat_fg.use_nodes = True
    nt = mat_fg.node_tree
    nt.nodes.clear()
    n_out = nt.nodes.new('ShaderNodeOutputMaterial')
    n_mix_trans = nt.nodes.new('ShaderNodeMixShader')
    n_trans = nt.nodes.new('ShaderNodeBsdfTransparent')
    n_em = nt.nodes.new('ShaderNodeEmission')
    n_em.inputs['Strength'].default_value = 0.90
    n_tex = nt.nodes.new('ShaderNodeTexImage')
    n_tex.image = bpy.data.images.load(fg_path)
    nt.links.new(n_tex.outputs['Color'], n_em.inputs['Color'])
    nt.links.new(n_tex.outputs['Alpha'], n_mix_trans.inputs['Fac'])
    nt.links.new(n_trans.outputs['BSDF'], n_mix_trans.inputs[1])
    nt.links.new(n_em.outputs['Emission'], n_mix_trans.inputs[2])
    nt.links.new(n_mix_trans.outputs['Shader'], n_out.inputs['Surface'])
    m_fg.materials.append(mat_fg)

    return root, d_arr, (gw, gh)

def make_emission_mat(name, color, strength=3.2):
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
    r, d_arr, dims = build_multiplane_scene(i)
    roots[i] = r
    depths[i] = (d_arr, dims)

def map_pt3d(idx, u, v_top, z_off=0.18):
    d_arr, (gw, gh) = depths[idx]
    ix = min(gw, max(0, int(u * gw)))
    iy = min(gh, max(0, int(v_top * gh)))
    d_norm = d_arr[iy][ix] / 255.0
    z_surf = (d_norm - 0.35) * 3.8 + z_off
    p_scale = (Z_REF - z_surf) / Z_REF
    x = (u - 0.5) * 16.0 * p_scale
    y = (0.5 - v_top) * 9.0 * p_scale
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

s1_pts = [map_pt3d(1, u, v, 0.16) for u, v in [
    (0.00, 0.595), (0.18, 0.535), (0.35, 0.472), (0.52, 0.412), (0.68, 0.355), (0.87, 0.285)
]]
tube_s1 = create_curve_tube("SpecusS1", s1_pts, 0.085, mat_cyan)

s2_pts = [map_pt3d(2, u, v, 0.18) for u, v in [
    (0.245, 0.615), (0.33, 0.635), (0.43, 0.655), (0.53, 0.640), (0.63, 0.585), (0.72, 0.505), (0.80, 0.415)
]]
tube_s2 = create_curve_tube("MarciaS2", s2_pts, 0.095, mat_gold)

s3_pts = [map_pt3d(3, u, v, 0.16) for u, v in [
    (0.81, 0.545), (0.68, 0.525), (0.52, 0.500), (0.36, 0.478), (0.20, 0.452), (0.08, 0.435)
]]
tube_s3 = create_curve_tube("CutawayS3", s3_pts, 0.095, mat_cyan)

s4_pts = [map_pt3d(4, u, v, 0.16) for u, v in [
    (0.04, 0.525), (0.25, 0.468), (0.48, 0.402), (0.72, 0.330), (0.95, 0.255)
]]
tube_s4 = create_curve_tube("LaserS4", s4_pts, 0.065, mat_gold)

s5_pts = [map_pt3d(5, u, v, 0.20) for u, v in [
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

def project_uv(idx, u, v_top, z_off=0.22):
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
            p_rome = project_uv(2, 0.245, 0.615, 0.18)
            p_pop = (p_rome[0] - 255, p_rome[1] - 38)
            draw.line([p_pop, p_rome], fill=(255, 255, 255, int(a_lbl * 0.85)), width=3)
            draw.ellipse([p_rome[0]-5, p_rome[1]-5, p_rome[0]+5, p_rome[1]+5], fill=(255, 220, 100, a_lbl))
            pop_val = int(min(1.0, max(0.0, (u - 0.05) / 0.65)) * 1000000)
            draw_stroked_text(draw, p_pop[0] - 85, p_pop[1], f"{pop_val:,}", f_med, (255, 255, 255, a_lbl), (0, 0, 0, a_lbl), 4)
            f_prog = smoothstep(0.04, 0.90, u)
            pt_tip = lerp_pts(s2_pts, f_prog)
            co_tip = world_to_camera_view(scene, cam_obj, pt3d := pt_tip)
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
        pL = project_uv(4, 0.08, 0.39, 0.18)
        pR = project_uv(4, 0.86, 0.15, 0.18)
        draw_dashed_line(draw, pL, pR, (255, 255, 255, 225), width=3, dash=12, gap=8)
        mx, my = project_uv(4, 0.44, 0.22, 0.22)
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
            p_tank = project_uv(5, 0.12, 0.46, 0.20)
            draw.line([(hx, hy + 24), p_tank], fill=(255, 255, 255, int(a_ht * 0.85)), width=3)
            draw_stroked_text(draw, hx, hy, "Header tank", f_med, (255, 255, 255, a_ht), (0, 0, 0, a_ht), 4)
        a_50 = int(255 * smoothstep(0.22, 0.42, u))
        if a_50 > 5:
            p_top = project_uv(5, 0.46, 0.48, 0.20)
            p_bot = project_uv(5, 0.46, 0.90, 0.20)
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
        hide = (i != active_idx)
        r.hide_render = hide
        for ch in r.children:
            ch.hide_render = hide
    for tb in all_tubes:
        tb.hide_render = True

    # Wide 3D multi-plane camera movement so background mountains slide visibly behind the cutout 3D arches!
    if active_idx == 1:
        cam_pos = Vector((-2.4 + ease * 4.8, -0.95 + ease * 1.65, 15.6 - ease * 2.4))
        look_t = Vector((0.35 * ease, 0.10 * ease, 0.0))
        tube_s1.hide_render = False
        f_prog = smoothstep(0.10, 0.88, u)
        tube_s1.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s1_pts, f_prog) + Vector((0, 0, 0.45))
        pt_data.color = (0.0, 0.90, 1.0)
        pt_data.energy = 85.0 if f_prog > 0.01 else 0.0
    elif active_idx == 2:
        cam_pos = Vector((-1.95 + ease * 3.9, -1.55 + ease * 2.1, 15.2 - ease * 2.2))
        look_t = Vector((0.40 * ease, -0.15 + 0.30 * ease, 0.0))
        tube_s2.hide_render = False
        f_prog = smoothstep(0.04, 0.90, u)
        tube_s2.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s2_pts, f_prog) + Vector((0, 0, 0.55))
        pt_data.color = (1.0, 0.78, 0.15)
        pt_data.energy = 115.0
    elif active_idx == 3:
        cam_pos = Vector((2.25 - ease * 4.5, -1.15 + ease * 1.65, 15.6 - ease * 2.1))
        look_t = Vector((0.30 - 0.60 * ease, 0.08 * ease, 0.0))
        tube_s3.hide_render = False
        f_prog = smoothstep(0.06, 0.90, u)
        tube_s3.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s3_pts, f_prog) + Vector((0, 0, 0.55))
        pt_data.color = (0.0, 0.92, 1.0)
        pt_data.energy = 95.0
    elif active_idx == 4:
        cam_pos = Vector((-2.35 + ease * 4.7, -0.75 + ease * 1.45, 15.5 - ease * 2.1))
        look_t = Vector((0.35 * ease, 0.10 * ease, 0.0))
        tube_s4.hide_render = False
        f_prog = smoothstep(0.04, 0.85, u)
        tube_s4.data.bevel_factor_end = f_prog
        pt_obj.location = lerp_pts(s4_pts, f_prog) + Vector((0, 0, 0.45))
        pt_data.color = (1.0, 0.82, 0.18)
        pt_data.energy = 90.0
    else:
        cam_pos = Vector((-2.15 + ease * 4.3, -1.10 + ease * 1.75, 15.6 - ease * 2.1))
        look_t = Vector((0.15 * ease, -0.30 * ease, 0.0))
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
