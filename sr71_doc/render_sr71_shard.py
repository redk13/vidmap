#!/usr/bin/env python3
"""
Primal Space Exact-Style 1080p @ 30fps Documentary Renderer (20 Parallel Shards, 427.0s / 7m 07s)
100% Authentic Primal Space Visual Grammar:
  - ZERO HUD banners, ZERO cyan boxes, ZERO DejaVuSans, ZERO blurry video borders!
  - Fonts: BebasNeue-Regular.ttf & Oswald-Bold.ttf with custom letter-spacing (tracking).
  - 3D Assets: Microsoft TRELLIS (PBR .glb + 3D Gaussian Radiance Field) + Tencent Hunyuan3D-2 (144k & 476k faces)
               + 2,044-Airfoil J58 Cutaway on Ford 00:34 Radial Spotlight Studio Floors.
  - Maps: Exact "CIA 00:22" style (#14171f Navy + #c62820 Crimson, zero grid lines, white dot + condensed tracked label).
  - Charts: Exact "Ford 00:46" style (radial-vignetted cream #eeeae0, thin line + dots + Oswald numbers + faint bottom ticks).
  - Archival: Exact "Cable 00:58" 4:3 rounded film gate on pure #000000 black OR "CIA 00:46" full-bleed 16:9 moving video.
"""
import os, sys, math, json, subprocess, shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FF = "ffmpeg"

ROOT = os.path.dirname(os.path.abspath(__file__))
FPS = 30
W, H = 1920, 1080
TOTAL_DUR = 427.0
N_SHARDS = 20

F_BEBAS  = os.path.join(ROOT, "fonts", "BebasNeue-Regular.ttf")
F_OSWALD = os.path.join(ROOT, "fonts", "Oswald-Bold.ttf")

def f_bebas(sz): return ImageFont.truetype(F_BEBAS, sz)
def f_oswald(sz): return ImageFont.truetype(F_OSWALD, sz)

def draw_tracked_text(draw, xy, text, font, fill, tracking=5):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((x, y), ch, font=font)
        x += (bbox[2] - bbox[0]) + tracking

def draw_frameless_callout(draw, pt_target, pt_elbow, pt_end, label, color=(242, 242, 242), sz=48):
    tx, ty = pt_target
    ex, ey = pt_elbow
    nx, ny = pt_end
    draw.ellipse([tx-8, ty-8, tx+8, ty+8], fill=color)
    draw.line([(tx, ty), (ex, ey), (nx, ny)], fill=color, width=3)
    draw_tracked_text(draw, (nx + 16, ny - int(sz*0.58)), label, f_bebas(sz), color, tracking=4)

def make_studio_backdrop(w=1920, h=1080, center_rgb=(76, 80, 88), edge_rgb=(18, 20, 26)):
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt(((xx - w*0.5)/(w*0.58))**2 + ((yy - h*0.50)/(h*0.54))**2)
    halo = np.clip(1.0 - 0.68 * (dist**1.4), 0.15, 1.0)
    bg = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        bg[:, :, c] = center_rgb[c] * halo + edge_rgb[c] * (1.0 - halo)
    return np.clip(bg, 0, 255).astype(np.uint8)

def make_cream_backdrop(w=1920, h=1080):
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt(((xx - w*0.5)/(w*0.65))**2 + ((yy - h*0.5)/(h*0.65))**2)
    vig = np.clip(1.0 - 0.14 * (dist**1.6), 0.82, 1.0)
    base_col = np.array([238, 234, 224], dtype=np.float32)
    return np.clip(base_col[None, None, :] * vig[:, :, None], 0, 255).astype(np.uint8)

STUDIO_BG_DARK = make_studio_backdrop(W, H, (76, 80, 88), (18, 20, 26))
CREAM_BG       = make_cream_backdrop(W, H)

ORDERED_40 = [
    # Ch 1 (0..4)
    {"id": 0,  "type": "studio_sr71",  "big": "85,000 FEET", "sub": "MACH 3.2 CRUISE",     "call": ((1180, 410), (1260, 240), (1330, 240), "TWIN J58 AFTERBURNERS")},
    {"id": 1,  "type": "vid_full",     "vid": "v_takeoff.webm", "ss": 2.0, "label": "2,200 MPH"},
    {"id": 2,  "type": "trellis_gs",   "vid": "ai3d_models/ai3d_job_0/sr71_trellis_gaussian360.mp4", "big": "BUILT TO LEAK", "sub": "COLD TITANIUM SEAMS"},
    {"id": 3,  "type": "gate_43",      "img": "sunset.jpg",  "zoom": (1.0, 1.06)},
    {"id": 4,  "type": "gate_43",      "img": "u2_flight.jpg", "zoom": (1.06, 1.0)},

    # Ch 2 (5..9)
    {"id": 5,  "type": "studio_sr71_heat", "big": "950°F", "sub": "AERODYNAMIC FRICTION", "call": ((360, 740), (360, 520), (420, 520), "620°F QUARTZ WINDSHIELD")},
    {"id": 6,  "type": "ford_chart",   "pts": [("1,000°F", "TITANIUM BETA-120", 540, 340), ("600°F", "WINDSHIELD LIMIT", 1010, 610), ("300°F", "ALUMINUM FAILS", 1360, 750)], "ticks": ["MACH 1.2", "MACH 2.4", "MACH 3.2"]},
    {"id": 7,  "type": "gate_43",      "img": "kelly.jpg",   "zoom": (1.0, 1.07)},
    {"id": 8,  "type": "vid_full",     "vid": "v_flight.webm", "ss": 1.0, "label": "PROJECT OXCART"},
    {"id": 9,  "type": "gate_43",      "img": "crew.jpg",    "zoom": (1.05, 1.0)},

    # Ch 3 (10..14)
    {"id": 10, "type": "cia_map",      "mode": "urals"},
    {"id": 11, "type": "cia_map",      "mode": "route"},
    {"id": 12, "type": "hunyuan_3d",   "job": "ai3d_job_2", "big": "93% TITANIUM", "sub": "BETA-120 ALLOY"},
    {"id": 13, "type": "gate_43",      "img": "crate.jpg",   "zoom": (1.0, 1.06)},
    {"id": 14, "type": "gate_43",      "img": "a12_hangar.jpg", "zoom": (1.06, 1.0)},

    # Ch 4 (15..19)
    {"id": 15, "type": "studio_sr71",  "big": "+3.5 INCHES", "sub": "THERMAL EXPANSION", "call": ((980, 510), (1050, 310), (1120, 310), "CORRUGATED WING SKINS")},
    {"id": 16, "type": "gate_43",      "img": "cockpit.jpg", "zoom": (1.0, 1.06)},
    {"id": 17, "type": "bl_xray_clean","big": "6 FUEL TANKS", "sub": "SEAL ABOVE MACH 2.0"},
    {"id": 18, "type": "vid_full",     "vid": "v_refuel.webm", "ss": 2.0, "label": "KC-135Q REFUELING"},
    {"id": 19, "type": "vid_full",     "vid": "v_refuel.webm", "ss": 13.0, "label": ""},

    # Ch 5 (20..24)
    {"id": 20, "type": "ford_chart",   "pts": [("100°F", "JET-A FLASHPOINT", 540, 680), ("140°F", "JP-7 FLASHPOINT", 1010, 440), ("600°F", "HEAT SINK COOLANT", 1360, 290)], "ticks": ["GROUND", "MACH 2.0", "MACH 3.2"]},
    {"id": 21, "type": "bl_xray_clean","big": "JP-7 COOLANT", "sub": "FUEL ABSORBS SKIN HEAT"},
    {"id": 22, "type": "studio_j58",   "call1": "TEB PYROPHORIC IGNITER", "call2": "16 GREEN FIRE SHOTS"},
    {"id": 23, "type": "gate_43",      "img": "j58_fire.jpg", "zoom": (1.0, 1.07)},
    {"id": 24, "type": "trellis_gs",   "vid": "ai3d_models/ai3d_job_1/j58_trellis_gaussian360.mp4", "big": "32,500 LBF", "sub": "PRATT & WHITNEY J58"},

    # Ch 6 (25..29)
    {"id": 25, "type": "bl_j58_clean", "call": ((910, 490), (960, 220), (1030, 220), "9-STAGE AXIAL COMPRESSOR")},
    {"id": 26, "type": "hunyuan_3d",   "job": "ai3d_job_3", "big": "2,044 AIRFOILS", "sub": "99 SUB-ASSEMBLIES"},
    {"id": 27, "type": "studio_j58",   "call1": "SLIDING INLET SPIKE (26 IN)", "call2": "TRAPS SHOCKWAVE IN THROAT"},
    {"id": 28, "type": "diag_clean",   "mach_stage": 1, "big": "SUBSONIC", "sub": "SPIKE LOCKED FORWARD"},
    {"id": 29, "type": "diag_clean",   "mach_stage": 3, "big": "MACH 3.2", "sub": "SPIKE RETRACTED 26 INCHES"},

    # Ch 7 (30..34)
    {"id": 30, "type": "diag_clean",   "mach_stage": 2, "big": "MACH 2.5", "sub": "BYPASS DOORS OPEN"},
    {"id": 31, "type": "studio_j58",   "call1": "STAGE 4 COMPRESSOR BLEED", "call2": "6 EXTERNAL BYPASS TUBES"},
    {"id": 32, "type": "bl_j58_clean", "call": ((1140, 390), (1210, 190), (1280, 190), "3,200°F AFTERBURNER PLUME")},
    {"id": 33, "type": "ford_chart",   "pts": [("80%", "INLET CONE THRUST", 540, 290), ("25%", "AFTERBURNER", 1010, 590), ("17%", "TURBINE CORE", 1360, 690)], "ticks": ["INLET CONE", "AFTERBURNER", "TURBINE"]},
    {"id": 34, "type": "diag_clean",   "mach_stage": 4, "big": "80% THRUST", "sub": "INLET PRESSURE REBOUND"},

    # Ch 8 (35..39)
    {"id": 35, "type": "studio_j58",   "call1": "INLET UNSTART SHOCKWAVE", "call2": "VIOLent ASYMMETRIC YAW"},
    {"id": 36, "type": "vid_full",     "vid": "v_trainer.webm", "ss": 2.0, "label": "DAFICS AUTO-RESTART"},
    {"id": 37, "type": "vid_full",     "vid": "v_takeoff.webm", "ss": 10.0, "label": "4,000 MISSILES EVADED"},
    {"id": 38, "type": "vid_full",     "vid": "v_flight.webm",  "ss": 11.0, "label": "ZERO AIRCRAFT LOST"},
    {"id": 39, "type": "studio_sr71",  "big": "UNTOUCHABLE", "sub": "3,551 SORTIES · 0 LOST", "call": None},
]
print("Configured 40 exact Primal Space scenes.")

def render_j58_cutaway_studio(out_dir, n_kf=20):
    os.makedirs(out_dir, exist_ok=True)
    bl_py = os.path.join(out_dir, "j58_bl.py")
    with open(bl_py, "w") as f:
        f.write(f"""
import sys, os, math, bpy
from mathutils import Vector
ROOT = {repr(ROOT)}
OUT_D = {repr(out_dir)}
N_KF = {n_kf}
sys.path.insert(0, os.path.join(ROOT, "f110_engine"))
import engine.render as rnd
import engine.materials as mats

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.samples = 14
scn.cycles.use_denoising = True
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080
scn.render.film_transparent = True
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'

bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "f110_engine", "build", "f110_web.glb"))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

objs = [o for o in bpy.data.objects if o.type == "MESH"]
lib = mats.build_all()
for o in objs:
    nm = o.name.lower()
    if "combustor" in nm or "augmentor_liner" in nm or "nozzle_seals" in nm: mat = lib["thermal_barrier"]
    elif "turbine" in nm or "nozzle" in nm or "mixer" in nm or "flameholder" in nm: mat = lib["hot_nickel"]
    elif "casing" in nm or "frame" in nm or "inlet" in nm or "duct" in nm or "gearbox" in nm or "flange" in nm or "splitter" in nm: mat = lib["casing_alloy"]
    elif "shaft" in nm or "bearing" in nm: mat = lib["steel"]
    else: mat = lib["titanium"]
    o.data.materials.clear()
    o.data.materials.append(mat)

bleed_mat = bpy.data.materials.new("J58_Bleed")
bleed_mat.use_nodes = True
bsdf = bleed_mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.72, 0.45, 0.28, 1.0)
bsdf.inputs["Metallic"].default_value = 0.85
bsdf.inputs["Roughness"].default_value = 0.22

bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.38, radius2=0.0, depth=1.45, location=(-0.65, 0, 0), rotation=(0, math.radians(-90), 0))
spk = bpy.context.active_object
for p in spk.data.polygons: p.use_smooth = True
spk.data.materials.append(lib["titanium"])

for i in range(6):
    ang = math.radians(i * 60.0 + 30.0)
    cu = bpy.data.curves.new(f"bleed_{{i}}", type='CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = 0.042; cu.bevel_resolution = 8
    sp = cu.splines.new('NURBS')
    pts = [(1.10, 0.48*math.cos(ang), 0.48*math.sin(ang)), (1.22, 0.68*math.cos(ang), 0.68*math.sin(ang)), (2.95, 0.68*math.cos(ang), 0.68*math.sin(ang)), (3.12, 0.52*math.cos(ang), 0.52*math.sin(ang))]
    sp.points.add(len(pts)-1)
    for pi, (px, py, pz) in enumerate(pts): sp.points[pi].co = (px, py, pz, 1.0)
    sp.use_endpoint_u = True
    obj_p = bpy.data.objects.new(f"bleed_{{i}}", cu)
    obj_p.data.materials.append(bleed_mat)
    scn.collection.objects.link(obj_p)

rnd.setup_world(0.32)
rnd.setup_lights()
rnd._add_section_cutter()
rnd.area_light("bore", (rnd.X_MID - 0.4, -4.2, 1.2), (math.radians(74), 0, 0), 1800, 8.0)
cam_o = rnd.setup_camera((rnd.X_MID - 3.8, -11.6, 3.8), (rnd.X_MID - 0.2, 0, 0.0), lens=78)

for kf in range(N_KF):
    u = kf / max(1, N_KF - 1)
    spk.location.x = -0.75 + u * 0.48
    for o in objs:
        if "blades_" in o.name.lower(): o.rotation_euler.x = u * math.pi * 4.0
    cam_o.location = (rnd.X_MID - 4.2 + u*2.2, -11.4 - 0.6*math.sin(u*math.pi), 3.6 + 0.4*math.cos(u*math.pi))
    rnd.aim(cam_o, (rnd.X_MID - 0.15, 0.0, 0.0))
    scn.render.filepath = os.path.join(OUT_D, f"kf_{{kf:03d}}.png")
    bpy.ops.render.render(write_still=True)
""")
    bl_bin = os.environ.get("BLENDER_BIN", "blender")
    subprocess.run([bl_bin, "-b", "-P", bl_py], check=True)

def render_xray_studio(out_dir, n_kf=20):
    os.makedirs(out_dir, exist_ok=True)
    bl_py = os.path.join(out_dir, "xray_bl.py")
    with open(bl_py, "w") as f:
        f.write(f"""
import sys, os, math, bpy
from mathutils import Vector
ROOT = {repr(ROOT)}
OUT_D = {repr(out_dir)}
N_KF = {n_kf}
sys.path.insert(0, os.path.join(ROOT, "f110_engine"))
import engine.render as rnd

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.samples = 14
scn.cycles.max_bounces = 6
scn.cycles.transparent_max_bounces = 12
scn.cycles.diffuse_bounces = 0
scn.cycles.glossy_bounces = 0
scn.cycles.use_denoising = False
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080
scn.render.film_transparent = True
scn.view_settings.view_transform = 'AgX'

def make_fresnel_mat(name, col_inner, col_edge, str_inner=0.6, str_edge=2.6, transparent=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader"); lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs[0].default_value = 0.36
    if transparent:
        s1 = nt.nodes.new("ShaderNodeBsdfTransparent"); s1.inputs[0].default_value = (0.76, 0.90, 1.0, 1.0)
    else:
        s1 = nt.nodes.new("ShaderNodeEmission"); s1.inputs[0].default_value = col_inner; s1.inputs[1].default_value = str_inner
    s2 = nt.nodes.new("ShaderNodeEmission"); s2.inputs[0].default_value = col_edge; s2.inputs[1].default_value = str_edge
    nt.links.new(lw.outputs["Facing"], mix.inputs["Fac"]); nt.links.new(s1.outputs[0], mix.inputs[1]); nt.links.new(s2.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m

bpy.ops.wm.obj_import(filepath=os.path.join(ROOT, "models3d", "sr71_blend.obj"))
objs = [o for o in scn.objects if o.type == 'MESH']
xray_mat = make_fresnel_mat("XRayHull", (0.06, 0.42, 0.78, 1.0), (0.20, 0.82, 1.0, 1.0), transparent=True)
for o in objs:
    for p in o.data.polygons: p.use_smooth = True
    mod = o.modifiers.new("Sub", type='SUBSURF'); mod.levels = 2; mod.render_levels = 2
    for i in range(len(o.data.materials)): o.data.materials[i] = xray_mat

min_v = Vector((1e9,1e9,1e9)); max_v = Vector((-1e9,-1e9,-1e9))
for o in objs:
    for v in o.bound_box:
        wv = o.matrix_world @ Vector(v)
        for i in range(3): min_v[i]=min(min_v[i],wv[i]); max_v[i]=max(max_v[i],wv[i])
center = (min_v + max_v)*0.5; size = max_v - min_v; fuse_z = min_v.z + size.z*0.22
tank_mat = make_fresnel_mat("Tank", (1.0, 0.35, 0.05, 1.0), (1.0, 0.80, 0.30, 1.0), str_inner=1.8, str_edge=3.5, transparent=False)
for i in range(6):
    tx = center.x + (-0.26 + i*0.105)*size.x
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=size.y*0.048, depth=size.x*0.075, location=(tx, center.y, fuse_z), rotation=(0, math.radians(90), 0))
    tk = bpy.context.active_object
    for p in tk.data.polygons: p.use_smooth = True
    tk.scale = (1.0, 1.35, 0.65); tk.data.materials.append(tank_mat)

cd = bpy.data.cameras.new("C"); cd.lens = 44.0; co = bpy.data.objects.new("C", cd); scn.collection.objects.link(co); scn.camera = co
md = max(size.x, size.y, size.z)
for kf in range(N_KF):
    u = kf / max(1, N_KF - 1)
    ang = math.radians(145.0 + u * 35.0)
    co.location = center + Vector((md*0.92*math.cos(ang), md*0.92*math.sin(ang), md*0.36))
    rnd.aim(co, center)
    scn.render.filepath = os.path.join(OUT_D, f"kf_{{kf:03d}}.png")
    bpy.ops.render.render(write_still=True)
""")
    bl_bin = os.environ.get("BLENDER_BIN", "blender")
    subprocess.run([bl_bin, "-b", "-P", bl_py], check=True)

def render_scene_frames(scene, n_frames, work_dir, write_frame_fn):
    stype = scene["type"]

    if stype in ("studio_sr71", "studio_sr71_heat"):
        ref = Image.open(os.path.join(ROOT, "ai3d_refs", "sr71_ref_studio.png")).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
        arr = np.array(ref).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        dist = np.sqrt(((xx - W*0.5)/(W*0.62))**2 + ((yy - H*0.52)/(H*0.58))**2)
        vig = np.clip(1.0 - 0.55 * (dist**1.5), 0.25, 1.0)
        lum = (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]) / 255.0
        bg_w = np.clip((lum - 0.35) / 0.35, 0.0, 1.0)
        dark_s = arr * 0.28 * vig[:, :, None]
        plane_l = arr * 0.96
        if stype == "studio_sr71_heat":
            # Subtle thermal glow on nose & nacelle spikes
            heat_d = np.sqrt(((xx - W*0.18)/(W*0.22))**2 + ((yy - H*0.72)/(H*0.22))**2)
            heat_m = np.clip(1.0 - heat_d, 0.0, 1.0) * (1.0 - bg_w)
            plane_l[:, :, 0] = np.clip(plane_l[:, :, 0] + heat_m * 210, 0, 255)
            plane_l[:, :, 1] = np.clip(plane_l[:, :, 1] + heat_m * 75, 0, 255)
        base_rgb = np.clip(dark_s * bg_w[:, :, None] + plane_l * (1.0 - bg_w[:, :, None]), 0, 255).astype(np.uint8)

        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            # Smooth 3% studio camera push-in
            sc = 1.0 + 0.038 * u
            cw, ch = int(W / sc), int(H / sc)
            x0, y0 = (W - cw)//2, (H - ch)//2
            cropped = cv2.resize(base_rgb[y0:y0+ch, x0:x0+cw], (W, H), interpolation=cv2.INTER_LINEAR)
            im = Image.fromarray(cropped)
            dr = ImageDraw.Draw(im)
            draw_tracked_text(dr, (150, 96),  scene["big"], f_bebas(136), (175, 182, 195), tracking=8)
            draw_tracked_text(dr, (156, 236), scene["sub"], f_bebas(54),  (115, 122, 135), tracking=6)
            if scene.get("call") and u > 0.18:
                pt_t, pt_e, pt_n, clbl = scene["call"]
                draw_frameless_callout(dr, pt_t, pt_e, pt_n, clbl, color=(235, 238, 245), sz=52)
            write_frame_fn(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

    elif stype == "studio_j58":
        ref = Image.open(os.path.join(ROOT, "ai3d_refs", "j58_ref_studio.png")).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
        arr = np.array(ref).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        dist = np.sqrt(((xx - W*0.5)/(W*0.65))**2 + ((yy - H*0.50)/(H*0.60))**2)
        vig = np.clip(1.0 - 0.22 * (dist**1.5), 0.72, 1.0)
        base_rgb = np.clip(arr * vig[:, :, None], 0, 255).astype(np.uint8)
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            sc = 1.0 + 0.04 * u
            cw, ch = int(W / sc), int(H / sc)
            x0, y0 = (W - cw)//2, (H - ch)//2
            cropped = cv2.resize(base_rgb[y0:y0+ch, x0:x0+cw], (W, H), interpolation=cv2.INTER_LINEAR)
            im = Image.fromarray(cropped)
            dr = ImageDraw.Draw(im)
            c_line = (36, 40, 46)
            draw_frameless_callout(dr, (182, 532), (182, 112), (270, 112), scene["call1"], color=c_line, sz=56)
            if u > 0.22:
                draw_frameless_callout(dr, (1095, 228), (1165, 112), (1245, 112), scene["call2"], color=c_line, sz=56)
            write_frame_fn(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

    elif stype == "trellis_gs":
        vp = os.path.join(ROOT, scene["vid"])
        cap = cv2.VideoCapture(vp)
        v_tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 100
        frames_gs = []
        while True:
            ret, fr = cap.read()
            if not ret: break
            # Left half of TRELLIS video is the 3D Gaussian Radiance Field, right half is the Normal Map
            frames_gs.append(fr)
        cap.release()
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            raw = frames_gs[f_i % len(frames_gs)]
            rh, rw = raw.shape[:2]
            # Place Gaussian Splatting & Normal Map cleanly on the dark studio floor
            canvas = STUDIO_BG_DARK.copy()
            im = Image.fromarray(canvas)
            dr = ImageDraw.Draw(im)
            draw_tracked_text(dr, (150, 96),  scene["big"], f_bebas(132), (215, 222, 235), tracking=8)
            draw_tracked_text(dr, (156, 232), scene["sub"], f_bebas(54),  (135, 142, 155), tracking=6)
            canvas = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
            rs = cv2.resize(raw, (1360, 680), interpolation=cv2.INTER_CUBIC)
            canvas[310:990, 280:1640] = rs
            write_frame_fn(canvas)

    elif stype == "hunyuan_3d":
        jdir = os.path.join(ROOT, "ai3d_models", scene["job"])
        im0 = cv2.imread(os.path.join(jdir, "render_angle_0.png"))
        im1 = cv2.imread(os.path.join(jdir, "render_angle_1.png"))
        im0 = cv2.resize(im0, (W, H), interpolation=cv2.INTER_CUBIC)
        im1 = cv2.resize(im1, (W, H), interpolation=cv2.INTER_CUBIC)
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            base = im0 if u < 0.5 else im1
            sub_u = (u * 2.0) if u < 0.5 else ((u - 0.5) * 2.0)
            sc = 1.0 + 0.045 * sub_u
            cw, ch = int(W / sc), int(H / sc)
            x0, y0 = (W - cw)//2, (H - ch)//2
            fr = cv2.resize(base[y0:y0+ch, x0:x0+cw], (W, H), interpolation=cv2.INTER_LINEAR)
            im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
            dr = ImageDraw.Draw(im)
            draw_tracked_text(dr, (150, 96),  scene["big"], f_bebas(132), (230, 235, 245), tracking=8)
            draw_tracked_text(dr, (156, 232), scene["sub"], f_bebas(54),  (150, 160, 175), tracking=6)
            write_frame_fn(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

    elif stype in ("bl_j58_clean", "bl_xray_clean"):
        bl_d = os.path.join(work_dir, f"bl_{scene['id']}")
        n_kf = 16
        if stype == "bl_j58_clean":
            render_j58_cutaway_studio(bl_d, n_kf=n_kf)
        else:
            render_xray_studio(bl_d, n_kf=n_kf)
        kfs = []
        for k in range(n_kf):
            rgba = Image.open(os.path.join(bl_d, f"kf_{k:03d}.png")).convert("RGBA")
            bg = Image.fromarray(STUDIO_BG_DARK).convert("RGBA")
            comp = Image.alpha_composite(bg, rgba).convert("RGB")
            kfs.append(np.array(comp))
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            pos = u * (n_kf - 1)
            i0 = int(math.floor(pos)); i1 = min(n_kf - 1, i0 + 1); frac = pos - i0
            rgb = cv2.addWeighted(kfs[i0], 1.0 - frac, kfs[i1], frac, 0)
            im = Image.fromarray(rgb)
            dr = ImageDraw.Draw(im)
            if scene.get("big"):
                draw_tracked_text(dr, (150, 96),  scene["big"], f_bebas(132), (225, 232, 242), tracking=8)
                draw_tracked_text(dr, (156, 232), scene["sub"], f_bebas(54),  (140, 150, 165), tracking=6)
            if scene.get("call") and u > 0.15:
                pt_t, pt_e, pt_n, clbl = scene["call"]
                draw_frameless_callout(dr, pt_t, pt_e, pt_n, clbl, color=(242, 242, 242), sz=52)
            write_frame_fn(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

    elif stype == "cia_map":
        with open(os.path.join(ROOT, "models3d", "world_countries.geojson")) as f:
            geo = json.load(f)
        USSR_ISO = {"RUS", "UKR", "BLR", "KAZ", "UZB", "TKM", "KGZ", "TJK", "GEO", "AZE", "ARM", "LTU", "LVA", "EST", "MDA"}
        base_map = Image.new("RGB", (W, H), (20, 23, 31))
        dr = ImageDraw.Draw(base_map)
        mode = scene["mode"]
        def ll_xy(lon, lat):
            if mode == "urals":
                return ((lon - 5.0) / 115.0 * W, H - (lat - 24.0) / 48.0 * H)
            return (120.0 + (lon + 135.0)/290.0 * 1680.0, 960.0 - (lat - 8.0)/72.0 * 780.0)
        for feat in geo["features"]:
            iso = feat.get("properties", {}).get("ISO_A3") or feat.get("properties", {}).get("ADM0_A3") or ""
            fc = (198, 40, 32) if iso in USSR_ISO else (35, 38, 48)
            geom = feat.get("geometry", {})
            polys = geom.get("coordinates", []) if geom.get("type") == "MultiPolygon" else [geom.get("coordinates", [])]
            for poly in polys:
                if not poly: continue
                pts = [ll_xy(pt[0], pt[1]) for pt in poly[0]]
                if len(pts) >= 3: dr.polygon(pts, fill=fc, outline=(20, 23, 31))
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            im = base_map.copy()
            d = ImageDraw.Draw(im)
            if mode == "urals":
                mx, my = [int(v) for v in ll_xy(59.9, 56.8)]
                d.ellipse([mx-16, my-16, mx+16, my+16], fill=(242, 242, 242))
                draw_tracked_text(d, (mx + 36, my - 52), "URALS", f_bebas(68), (242, 242, 242), tracking=5)
                draw_tracked_text(d, (mx + 36, my + 12), "TITANIUM MINE", f_bebas(68), (242, 242, 242), tracking=5)
            else:
                p1 = [int(v) for v in ll_xy(59.9, 56.8)]
                p2 = [int(v) for v in ll_xy(8.5, 47.4)]
                p3 = [int(v) for v in ll_xy(-118.3, 34.2)]
                d.line([tuple(p1), tuple(p2), tuple(p3)], fill=(242, 242, 242), width=5)
                for px, py, l1, l2 in [(p1[0], p1[1], "U.S.S.R.", "RUTILE ORE"), (p2[0], p2[1], "ZURICH", "CIA SHELL CO."), (p3[0], p3[1], "BURBANK", "SKUNK WORKS")]:
                    d.ellipse([px-13, py-13, px+13, py+13], fill=(242, 242, 242))
                    draw_tracked_text(d, (px + 24, py - 42), l1, f_bebas(48), (242, 242, 242), tracking=4)
                    draw_tracked_text(d, (px + 24, py + 6),  l2, f_bebas(48), (242, 242, 242), tracking=4)
            write_frame_fn(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

    elif stype == "ford_chart":
        pts_cfg = scene["pts"]
        ticks   = scene["ticks"]
        coords  = [(p[2], p[3]) for p in pts_cfg]
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            im = Image.fromarray(CREAM_BG.copy())
            dr = ImageDraw.Draw(im)
            # Bottom faint axis line & ticks (exact Ford 00:46 style)
            dr.line([(360, 940), (1560, 940)], fill=(210, 205, 194), width=3)
            for idx, tlbl in enumerate(ticks):
                tx = coords[idx][0]
                dr.line([(tx, 922), (tx, 940)], fill=(198, 193, 182), width=3)
                draw_tracked_text(dr, (tx - 72, 954), tlbl, f_bebas(52), (172, 167, 156), tracking=4)

            # Progressive line & dots
            dr.line(coords, fill=(28, 28, 28), width=7)
            for idx, (num_s, sub_s, px, py) in enumerate(pts_cfg):
                dr.ellipse([px-12, py-12, px+12, py+12], fill=(28, 28, 28))
                ncol = (195, 42, 32) if idx == 2 else (32, 32, 32)
                if idx == 0:
                    draw_tracked_text(dr, (px - 110, py - 142), num_s, f_oswald(72), ncol, tracking=2)
                    draw_tracked_text(dr, (px - 104, py - 58),  sub_s, f_bebas(42), (152, 147, 138), tracking=3)
                else:
                    draw_tracked_text(dr, (px + 34, py - 54), num_s, f_oswald(68), ncol, tracking=2)
                    draw_tracked_text(dr, (px + 225, py - 34), sub_s, f_bebas(42), (152, 147, 138), tracking=3)
            write_frame_fn(cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR))

    elif stype == "gate_43":
        # Exact "1. Cable 00:58" 4:3 rounded film gate centered on pure pitch-black #000000
        raw = Image.open(os.path.join(ROOT, "archival_photos", scene["img"])).convert("RGB")
        gw, gh = 1240, 920
        raw_rs = raw.resize((gw, gh), Image.Resampling.LANCZOS)
        mask = Image.new("L", (gw, gh), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, gw-1, gh-1], radius=54, fill=255)
        z0, z1 = scene.get("zoom", (1.0, 1.06))
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            sc = z0 + (z1 - z0) * u
            cw, ch = int(gw / sc), int(gh / sc)
            x0, y0 = (gw - cw)//2, (gh - ch)//2
            cropped = raw_rs.crop((x0, y0, x0+cw, y0+ch)).resize((gw, gh), Image.Resampling.BILINEAR)
            canvas = Image.new("RGB", (W, H), (0, 0, 0))
            canvas.paste(cropped, ((W - gw)//2, (H - gh)//2), mask)
            write_frame_fn(cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR))

    elif stype == "vid_full":
        # Exact "2. CIA 00:46 / 4. Fire 00:58" Full-Bleed 16:9 moving video (ZERO borders, ZERO HUD boxes!)
        vp = os.path.join(ROOT, "real_videos", scene["vid"])
        cap = cv2.VideoCapture(vp)
        v_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        v_tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300
        start_f = int(scene.get("ss", 0.0) * v_fps)
        lbl = scene.get("label", "")
        for f_i in range(n_frames):
            cur_vf = (start_f + int(f_i * (v_fps / FPS))) % max(1, v_tot - 5)
            cap.set(cv2.CAP_PROP_POS_FRAMES, cur_vf)
            ret, raw = cap.read()
            if not ret or raw is None:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, raw = cap.read()
            fr = cv2.resize(raw, (W, H), interpolation=cv2.INTER_CUBIC)
            if lbl:
                im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
                dr = ImageDraw.Draw(im)
                draw_tracked_text(dr, (130, 88), lbl, f_bebas(96), (242, 242, 242), tracking=6)
                fr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
            write_frame_fn(fr)
        cap.release()

    elif stype == "diag_clean":
        svg_im = cv2.imread(os.path.join(ROOT, "archival_photos", "j58_airflow_official.png"))
        sh, sw = svg_im.shape[:2]
        stg = scene.get("mach_stage", 3)
        y0 = int(sh * (stg * 0.20)); y1 = min(sh, int(sh * ((stg + 1) * 0.20)))
        crop_rs = cv2.resize(svg_im[y0:y1, :], (1640, 500), interpolation=cv2.INTER_CUBIC)
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            canvas = STUDIO_BG_DARK.copy()
            im = Image.fromarray(canvas)
            dr = ImageDraw.Draw(im)
            draw_tracked_text(dr, (140, 86),  scene["big"], f_bebas(124), (235, 240, 248), tracking=8)
            draw_tracked_text(dr, (146, 214), scene["sub"], f_bebas(52),  (145, 155, 170), tracking=6)
            fr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
            fr[380:880, 140:1780] = crop_rs
            write_frame_fn(fr)

def render_shard(shard_idx, out_mp4):
    shard_dur = TOTAL_DUR / float(N_SHARDS)
    n_shard_frames = int(round(shard_dur * FPS))
    n_sc1 = n_shard_frames // 2
    n_sc2 = n_shard_frames - n_sc1

    sc1 = ORDERED_40[shard_idx * 2]
    sc2 = ORDERED_40[shard_idx * 2 + 1]
    work_dir = f"/tmp/sr71_v2_shard_{shard_idx:02d}"
    os.makedirs(work_dir, exist_ok=True)

    cmd = [
        FF, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "bgr24", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "16",
        "-pix_fmt", "yuv420p",
        out_mp4
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    def write_frame(bgr): proc.stdin.write(bgr.tobytes())

    print(f"[Shard {shard_idx:02d}] Scene {sc1['id']} ({sc1['type']})...")
    render_scene_frames(sc1, n_sc1, work_dir, write_frame)
    print(f"[Shard {shard_idx:02d}] Scene {sc2['id']} ({sc2['type']})...")
    render_scene_frames(sc2, n_sc2, work_dir, write_frame)

    proc.stdin.close()
    proc.wait()
    shutil.rmtree(work_dir, ignore_errors=True)
    print(f"[Shard {shard_idx:02d}] Done -> {out_mp4}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        render_shard(int(sys.argv[1]), sys.argv[2])
