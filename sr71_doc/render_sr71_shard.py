#!/usr/bin/env python3
"""
Primal Space Flagship 3D Documentary Shard Renderer (1920x1080 @ 30fps)
Total Duration: 427.0s (7m 07s) across 20 Parallel Shards (shard 0..19)
Each shard renders 2 distinct scenes (~10.67s each = ~21.35s per shard) = 40 distinct scenes total.
Combines:
  1. Blender 4.3.2 High-Poly 3D Renders (Real SR-71 .obj + 99-Part 2,044-Airfoil J58 Cutaway .glb + OpenImageDenoise)
  2. Real Moving NASA/USAF Archival Videos (v_takeoff.webm, v_refuel.webm, v_flight.webm, v_trainer.webm)
  3. Primal Space Geopolitical Maps (Natural Earth GeoJSON #12151f & #c83228) & Cream Engineering Charts (#ebe8df)
  4. Official SR-71 Flight Manual Animated Aerodynamic Shockwave Vector Diagrams & 2.5D Archival Parallax
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

def get_font(sz, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

# 40 Distinct Scenes across the 8 Chapters (2 scenes per shard for Shards 0..19)
SCENES = [
    # Chapter 1 (00:00 - 00:53): The 85,000-Foot Missile Chase & The Leaking Hangar Paradox
    {"id": 0,  "type": "bl_sr71_missile", "title": "85,000 FEET — SOVIET SA-2 MISSILE LOCK (1968)", "sub": "Standard Evasive Procedure: Push Throttles to Mach 3.2"},
    {"id": 1,  "type": "vid_takeoff",     "title": "2,200 MPH — FASTER THAN A RIFLE BULLET",        "sub": "NASA / USAF Archival Footage: Full Afterburner Shock Diamonds", "vid": "v_takeoff.webm", "ss": 2.0},
    {"id": 2,  "type": "bl_sr71_leak",    "title": "THE HANGAR PARADOX — BUILT TO LEAK FUEL",       "sub": "Cold Titanium Airframe Leaves Deliberate Expansion Gaps on the Ground"},
    {"id": 3,  "type": "arch_parallax",   "title": "LOCKHEED SKUNK WORKS — THE UNTOLD ENGINEERING", "sub": "How Engineers Built a Titanium Spy Plane to Conquer Mach 3.2", "img": "sunset.jpg"},

    # Chapter 2 (00:53 - 01:44): The Thermal Barrier & Why Aluminum Melts at Mach 3
    {"id": 4,  "type": "bl_sr71_thermal", "title": "THE THERMAL BARRIER — 600°F TO 950°F SKIN HEAT","sub": "Aerodynamic Stagnation Compression Slams Air Molecules Against Titanium"},
    {"id": 5,  "type": "chart_alloy",     "title": "ALUMINUM 2024-T4 VS. TITANIUM BETA-120",        "sub": "Structural Yield Strength Collapse Above 300°F vs. Mach 3.2 Heat"},
    {"id": 6,  "type": "arch_parallax",   "title": "CLARENCE 'KELLY' JOHNSON — PROJECT OXCART (1958)", "sub": "Designing an Untouchable Reconnaissance Aircraft for the CIA", "img": "kelly.jpg"},
    {"id": 7,  "type": "vid_flight",      "title": "HIGH-ALTITUDE SUPERSONIC FLIGHT ENVELOPE",      "sub": "NASA Dryden Flight Research Center — Cruising Above California", "vid": "v_flight.webm", "ss": 1.0},

    # Chapter 3 (01:44 - 02:41): The CIA Titanium Heist From the Soviet Union
    {"id": 8,  "type": "map_cia_ussr",    "title": "OPERATION OXCART — THE SOVIET TITANIUM HEIST",  "sub": "How CIA Shell Companies Bought Raw Rutile Ore Directly From Moscow"},
    {"id": 9,  "type": "bl_j58_hero",     "title": "93% TITANIUM BETA-120 ALLOY STRUCTURE",         "sub": "Half the Weight of Steel — Withstanding Temperatures Above 1,000°F"},
    {"id": 10, "type": "arch_parallax",   "title": "SECRET TRANSPORT FROM BURBANK TO AREA 51",      "sub": "Declassified CIA Photo: Prototype Article 121 Moved in Sealed Crates", "img": "crate.jpg"},
    {"id": 11, "type": "arch_parallax",   "title": "MACHINING TITANIUM WITH TITANIUM TOOLS",        "sub": "Standard Cadmium-Plated Steel Tools Caused Instant Metal Embrittlement", "img": "a12_hangar.jpg"},

    # Chapter 4 (02:41 - 03:36): Thermal Expansion, Corrugated Wings & Mid-Air Sealing
    {"id": 12, "type": "bl_sr71_expand",  "title": "THERMAL EXPANSION — +3.5 INCHES IN FLIGHT",     "sub": "107.4-Foot Fuselage Expands Several Inches at Mach 3.2 Cruising Temp"},
    {"id": 13, "type": "arch_parallax",   "title": "CHORDWISE CORRUGATED TITANIUM WING SKINS",      "sub": "Accordion-Style Washboard Grooves Prevent Thermal Buckling", "img": "cockpit.jpg"},
    {"id": 14, "type": "bl_sr71_xray",    "title": "X-RAY CUTAWAY — SIX INTERNAL FUSELAGE FUEL TANKS", "sub": "Deliberate Expansion Seams Seal Tight Only Above Mach 2.0"},
    {"id": 15, "type": "vid_refuel",      "title": "MID-AIR REFUELING — KC-135Q STRATOTANKER",      "sub": "Topping Up the Tanks Immediately After Takeoff Before Supersonic Climb", "vid": "v_refuel.webm", "ss": 2.0},

    # Chapter 5 (03:36 - 04:28): JP-7 Fuel Coolant Loop & Triethylborane (TEB) Green Fire
    {"id": 16, "type": "chart_jp7",       "title": "JP-7 LOW-VOLATILITY SUPERSONIC FUEL",           "sub": "High Flashpoint (140°F) Extinguishes Open Flame & Resists Boiling at Mach 3"},
    {"id": 17, "type": "bl_sr71_coolant", "title": "FUEL AS LIQUID COOLANT — THERMAL HEAT SINK",    "sub": "Circulating JP-7 Under the 600°F Skin & Cockpit Before Entering the Engines"},
    {"id": 18, "type": "bl_j58_teb",      "title": "TRIETHYLBORANE (TEB) — PYROPHORIC GREEN IGNITION", "sub": "Explodes Into Apple-Green Fire on Contact With Oxygen (16 Shots Per Engine)"},
    {"id": 19, "type": "arch_parallax",   "title": "PRATT & WHITNEY J58 — FULL AFTERBURNER TEST",   "sub": "32,500 Pounds of Thrust With Glowing Supersonic Shock Diamonds", "img": "j58_fire.jpg"},

    # Chapter 6 (04:28 - 05:20): Inside the Pratt & Whitney J58 & The Sliding Inlet Spike
    {"id": 20, "type": "bl_j58_cutaway",  "title": "INSIDE THE PRATT & WHITNEY J58 TURBO-RAMJET",   "sub": "3D Section Cutaway: 9-Stage Axial Compressor, Combustor & Afterburner"},
    {"id": 21, "type": "bl_j58_exploded", "title": "99 SUB-ASSEMBLIES & 2,044 NACA AIRFOIL BLADES", "sub": "Why Supersonic Shockwaves Destroy Conventional Jet Turbines"},
    {"id": 22, "type": "bl_j58_spike",    "title": "THE SLIDING CONICAL INLET SPIKE — 26 INCHES",   "sub": "Retracts 1.6 Inches Per 0.1 Mach Above Mach 1.6 to Trap the Shockwave"},
    {"id": 23, "type": "diag_flight_man", "title": "OFFICIAL FLIGHT MANUAL — SHOCKWAVE CAPTURE",    "sub": "Multiple Oblique Shock Reflections Slow Mach 3.2 Air to Subsonic Mach 0.4", "mach_stage": 3},

    # Chapter 7 (05:20 - 06:15): The 6 Bleed Tubes & How the Inlet Produces 80% of Thrust
    {"id": 24, "type": "diag_flight_man", "title": "COMPRESSOR BOTTLENECK AT MACH 3.0",             "sub": "40:1 Ram Compression Overwhelms the 9-Stage Axial Core", "mach_stage": 4},
    {"id": 25, "type": "bl_j58_bleed",    "title": "THE SIX EXTERNAL BYPASS BLEED TUBES",           "sub": "20% of Compressed Air Bypasses Stage 4 Directly Into the Afterburner"},
    {"id": 26, "type": "bl_j58_ramjet",   "title": "CONTINUOUS-BLEED HYBRID TURBO-RAMJET CYCLE",    "sub": "Bypass Air + Vaporized JP-7 Ignite at 3,200°F in the Ejector Nozzle"},
    {"id": 27, "type": "chart_thrust",    "title": "THE MACH 3.2 THRUST PARADOX — 80% FROM INLET",  "sub": "Inlet Cone Pressure Rebound: 58–80% | Afterburner: 25% | Turbine Core: 17%"},

    # Chapter 8 (06:15 - 07:07): The Violent "Unstart" Phenomenon & Untouchable Legacy
    {"id": 28, "type": "bl_j58_unstart",  "title": "SUPERSONIC HAZARD — INLET UNSTART",             "sub": "Shockwave Pops Violently Out the Nacelle Like a Supersonic Gunshot"},
    {"id": 29, "type": "vid_trainer",     "title": "DIGITAL AUTOMATIC INLET CONTROL (DAFICS)",      "sub": "Auto-Recapturing the Shockwave in Fractions of a Second", "vid": "v_trainer.webm", "ss": 2.0},
    {"id": 30, "type": "vid_takeoff",     "title": "4,000+ MISSILES FIRED — ZERO SHOT DOWN",        "sub": "24 Years of Service & 3,551 Operational Sorties Without a Single Loss", "vid": "v_takeoff.webm", "ss": 10.0},
    {"id": 31, "type": "bl_sr71_finale",  "title": "A MONUMENT TO SLIDE RULES, TITANIUM & FIRE",    "sub": "The Lockheed SR-71 Blackbird — Forever Untouchable at Mach 3.2"},
]

# Pad to 40 scenes (each shard 0..19 renders 2 scenes: scene_idx = shard*2 and shard*2+1)
EXTRAS = [
    {"id": 32, "type": "arch_parallax",   "title": "U-2 TO OXCART — EVOLUTION OF RECONNAISSANCE",   "sub": "From Subsonic High-Altitude Gliders to Mach 3.2 Titanium Cruisers", "img": "u2_flight.jpg"},
    {"id": 33, "type": "diag_flight_man", "title": "SUBSONIC VS. SUPERSONIC INLET GEOMETRY",        "sub": "Spike Locked Forward Below Mach 1.6 for Maximum Subsonic Mass Flow", "mach_stage": 1},
    {"id": 34, "type": "diag_flight_man", "title": "TRANSITION THROUGH MACH 2.5",                   "sub": "Centerbody Bleed Doors & Forward Bypass Regulate Throat Pressure", "mach_stage": 2},
    {"id": 35, "type": "vid_flight",      "title": "STRATOSPHERIC CRUISE AT 85,000 FEET",           "sub": "Viewing 100,000 Square Miles of Earth Per Hour From the Edge of Space", "vid": "v_flight.webm", "ss": 12.0},
    {"id": 36, "type": "vid_refuel",      "title": "JP-7DEDICATED TANKER FLEET (KC-135Q)",          "sub": "Specialized Refueling Boom Operations Every 2,500 Miles", "vid": "v_refuel.webm", "ss": 14.0},
    {"id": 37, "type": "arch_parallax",   "title": "PRESSURIZED SPACESUITS AT 85,000 FEET",         "sub": "Crew Wore Full Apollo-Style Pressure Suits Inside the 600°F Cockpit", "img": "crew.jpg"},
    {"id": 38, "type": "bl_j58_front",    "title": "FRONT QUARTER VIEW — TITANIUM FAN & SPIKE",     "sub": "4,630mm Length · 99 Precision Assemblies · 2,044 Airfoils"},
    {"id": 39, "type": "bl_sr71_xray",    "title": "COMPLETE INTERNAL ARCHITECTURE REVIEW",         "sub": "Titanium Beta-120 Chine Structure, 6 Fuel Cells & Twin J58 Nacelles"},
]

# Interleave cleanly into 40 chronological scenes (5 scenes per chapter x 8 chapters = 40 scenes)
ORDERED_40 = [
    SCENES[0], SCENES[1], SCENES[2], SCENES[3], EXTRAS[0],   # Ch 1 (5 scenes)
    SCENES[4], SCENES[5], SCENES[6], SCENES[7], EXTRAS[5],   # Ch 2 (5 scenes)
    SCENES[8], SCENES[9], SCENES[10], SCENES[11], EXTRAS[6], # Ch 3 (5 scenes)
    SCENES[12], SCENES[13], SCENES[14], SCENES[15], EXTRAS[4], # Ch 4 (5 scenes)
    SCENES[16], SCENES[17], SCENES[18], SCENES[19], EXTRAS[1], # Ch 5 (5 scenes)
    SCENES[20], SCENES[21], SCENES[22], SCENES[23], EXTRAS[2], # Ch 6 (5 scenes)
    SCENES[24], SCENES[25], SCENES[26], SCENES[27], EXTRAS[3], # Ch 7 (5 scenes)
    SCENES[28], SCENES[29], SCENES[30], EXTRAS[7], SCENES[31], # Ch 8 (5 scenes)
]
print("Configured 40 scenes across 8 chapters.")

def render_blender_turntable_frames(scene_type, out_dir, n_keyframes=16):
    """
    Renders n_keyframes (1920x1080) in Blender 4.3.2 using the real imported SR-71 (.obj)
    or the 99-part 2,044-airfoil J58 (.glb) cutaway with OpenImageDenoise + 3D projected pin coords!
    """
    os.makedirs(out_dir, exist_ok=True)
    bl_script = os.path.join(out_dir, "run_bl.py")
    with open(bl_script, "w") as f:
        f.write(f"""
import sys, os, math, json, bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = {repr(ROOT)}
SCENE_TYPE = {repr(scene_type)}
OUT_DIR = {repr(out_dir)}
N_KF = {n_keyframes}

sys.path.insert(0, os.path.join(ROOT, "f110_engine"))
import engine.render as rnd
import engine.materials as mats

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.samples = 14
scn.cycles.use_adaptive_sampling = True
try:
    scn.cycles.use_denoising = True
except Exception:
    scn.cycles.use_denoising = False
scn.cycles.max_bounces = 2
scn.cycles.caustics_reflective = False
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'

def make_fresnel_mat(name, col_inner, col_edge, str_inner=0.5, str_edge=2.4, transparent=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs[0].default_value = 0.38
    if transparent:
        s1 = nt.nodes.new("ShaderNodeBsdfTransparent")
        s1.inputs[0].default_value = (0.72, 0.88, 1.0, 1.0)
    else:
        s1 = nt.nodes.new("ShaderNodeEmission")
        s1.inputs[0].default_value = col_inner
        s1.inputs[1].default_value = str_inner
    s2 = nt.nodes.new("ShaderNodeEmission")
    s2.inputs[0].default_value = col_edge
    s2.inputs[1].default_value = str_edge
    nt.links.new(lw.outputs["Facing"], mix.inputs["Fac"])
    nt.links.new(s1.outputs[0], mix.inputs[1])
    nt.links.new(s2.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m

if SCENE_TYPE.startswith("bl_sr71"):
    scn.cycles.max_bounces = 6
    scn.cycles.transparent_max_bounces = 12
    scn.cycles.transmission_bounces = 4
    scn.cycles.diffuse_bounces = 0
    scn.cycles.glossy_bounces = 0
    scn.cycles.use_denoising = False
    rnd.setup_world(0.18)
    for name, ener, col, rot in [
        ("Key", 4.5, (0.92, 0.96, 1.0), (42, -18, 25)),
        ("Rim", 3.8, (1.0, 0.72, 0.42), (-48, 32, -140)),
        ("Fill", 2.4, (0.65, 0.80, 1.0), (65, 20, -45)),
        ("Under", 1.6, (0.55, 0.70, 0.95), (-115, 10, 20)),
    ]:
        ld = bpy.data.lights.new(name, type='SUN')
        ld.energy = ener
        ld.angle = 0.0
        ld.color = col
        lo = bpy.data.objects.new(name, ld)
        scn.collection.objects.link(lo)
        lo.rotation_euler = tuple(math.radians(a) for a in rot)

    bpy.ops.wm.obj_import(filepath=os.path.join(ROOT, "models3d", "sr71_blend.obj"))
    objs = [o for o in scn.objects if o.type == 'MESH']
    for o in objs:
        for p in o.data.polygons: p.use_smooth = True
        mod = o.modifiers.new("Subsurf", type='SUBSURF')
        mod.levels = 2
        mod.render_levels = 2

    for m in bpy.data.materials:
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if "window" in m.name.lower():
                bsdf.inputs["Base Color"].default_value = (0.10, 0.55, 0.88, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.08
                bsdf.inputs["Emission Color"].default_value = (0.08, 0.45, 0.78, 1.0)
                bsdf.inputs["Emission Strength"].default_value = 1.2
            elif "booster" in m.name.lower() or "chrome" in m.name.lower():
                bsdf.inputs["Base Color"].default_value = (0.60, 0.65, 0.74, 1.0)
                bsdf.inputs["Metallic"].default_value = 0.92
                bsdf.inputs["Roughness"].default_value = 0.18
            else:
                bsdf.inputs["Base Color"].default_value = (0.085, 0.095, 0.125, 1.0)
                bsdf.inputs["Metallic"].default_value = 0.88
                bsdf.inputs["Roughness"].default_value = 0.24
                if SCENE_TYPE == "bl_sr71_thermal":
                    lw_th = m.node_tree.nodes.new("ShaderNodeLayerWeight")
                    lw_th.inputs[0].default_value = 0.38
                    m.node_tree.links.new(lw_th.outputs["Fresnel"], bsdf.inputs["Emission Strength"])
                    bsdf.inputs["Emission Color"].default_value = (1.0, 0.28, 0.04, 1.0)

    min_v = Vector((1e9, 1e9, 1e9))
    max_v = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.bound_box:
            wv = o.matrix_world @ Vector(v)
            for i in range(3):
                min_v[i] = min(min_v[i], wv[i])
                max_v[i] = max(max_v[i], wv[i])
    center = (min_v + max_v) * 0.5
    size = max_v - min_v
    fuse_z = min_v.z + size.z * 0.22

    plume_outer = make_fresnel_mat("PlumeOuter", (0.15, 0.55, 1.0, 1.0), (1.0, 0.50, 0.12, 1.0), str_inner=1.2, str_edge=3.2, transparent=True)
    plume_core  = make_fresnel_mat("PlumeCore",  (1.0, 0.65, 0.20, 1.0), (1.0, 0.90, 0.55, 1.0), str_inner=2.5, str_edge=4.5, transparent=True)
    for side in [-1.0, 1.0]:
        ny = center.y + side * 1.12
        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.16, radius2=0.01, depth=2.1, location=(max_v.x + 0.95, ny, fuse_z), rotation=(0, math.radians(90), 0))
        c_out = bpy.context.active_object
        for p in c_out.data.polygons: p.use_smooth = True
        c_out.data.materials.append(plume_outer)
        bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.09, radius2=0.005, depth=1.3, location=(max_v.x + 0.55, ny, fuse_z), rotation=(0, math.radians(90), 0))
        c_in = bpy.context.active_object
        for p in c_in.data.polygons: p.use_smooth = True
        c_in.data.materials.append(plume_core)

    if SCENE_TYPE in ("bl_sr71_xray", "bl_sr71_coolant", "bl_sr71_leak"):
        xray_mat = make_fresnel_mat("XRayHull", (0.06, 0.42, 0.78, 1.0), (0.20, 0.82, 1.0, 1.0), str_inner=0.6, str_edge=2.6, transparent=True)
        for o in objs:
            for i in range(len(o.data.materials)):
                o.data.materials[i] = xray_mat
        t_col = (0.05, 0.75, 1.0, 1.0) if SCENE_TYPE == "bl_sr71_coolant" else (1.0, 0.35, 0.05, 1.0)
        tank_mat = make_fresnel_mat("TankMat", t_col, (1.0, 0.80, 0.30, 1.0), str_inner=1.8, str_edge=3.5, transparent=False)
        for i in range(6):
            frac = -0.26 + i * 0.105
            tx = center.x + frac * size.x
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=size.y*0.048, depth=size.x*0.075, location=(tx, center.y, fuse_z), rotation=(0, math.radians(90), 0))
            tk = bpy.context.active_object
            for p in tk.data.polygons: p.use_smooth = True
            tk.scale = (1.0, 1.35, 0.65)
            tk.data.materials.append(tank_mat)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 42.0
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    max_dim = max(size.x, size.y, size.z)

    coords_log = []
    for kf in range(N_KF):
        u = kf / max(1, N_KF - 1)
        ang = math.radians(150.0 + u * 35.0)
        rad = max_dim * (0.96 - 0.10 * math.sin(u * math.pi))
        elev = max_dim * (0.34 + 0.10 * math.cos(u * math.pi))
        cam_o.location = center + Vector((rad * math.cos(ang), rad * math.sin(ang), elev))
        rnd.aim(cam_o, center)
        scn.render.filepath = os.path.join(OUT_DIR, f"kf_{{kf:03d}}.png")
        bpy.ops.render.render(write_still=True)

        # Project 3D nose, cockpit, engine spike, and tail to 2D screen space
        pts_3d = {{
            "nose": Vector((min_v.x + 0.4, center.y, fuse_z)),
            "cockpit": Vector((min_v.x + size.x*0.22, center.y, fuse_z + 0.25)),
            "spike": Vector((center.x + 0.2, center.y - 1.12, fuse_z)),
            "afterburner": Vector((max_v.x, center.y - 1.12, fuse_z)),
        }}
        proj = {{}}
        for k, v3 in pts_3d.items():
            co = world_to_camera_view(scn, cam_o, v3)
            proj[k] = [int(co.x * 1920), int((1.0 - co.y) * 1080)]
        coords_log.append(proj)

    with open(os.path.join(OUT_DIR, "coords.json"), "w") as f:
        json.dump(coords_log, f)

else:
    # J58 2,044-Airfoil Engine Scenes (bl_j58_*)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "f110_engine", "build", "f110_web.glb"))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    lib = mats.build_all()
    for o in objs:
        nm = o.name.lower()
        if "combustor" in nm or "augmentor_liner" in nm or "nozzle_seals" in nm:
            mat = lib["thermal_barrier"]
        elif "turbine" in nm or "nozzle" in nm or "mixer" in nm or "flameholder" in nm:
            mat = lib["hot_nickel"]
        elif "casing" in nm or "frame" in nm or "inlet" in nm or "duct" in nm or "gearbox" in nm or "flange" in nm or "splitter" in nm:
            mat = lib["casing_alloy"]
        elif "shaft" in nm or "bearing" in nm:
            mat = lib["steel"]
        else:
            mat = lib["titanium"]
        o.data.materials.clear()
        o.data.materials.append(mat)

    bleed_col = (0.15, 0.95, 0.32, 1.0) if SCENE_TYPE == "bl_j58_teb" else (0.95, 0.28, 0.08, 1.0)
    bleed_mat = bpy.data.materials.new("J58_Bleed")
    bleed_mat.use_nodes = True
    bsdf = bleed_mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = bleed_col
    bsdf.inputs["Metallic"].default_value = 0.72
    bsdf.inputs["Roughness"].default_value = 0.22
    if "Emission Color" in bsdf.inputs and SCENE_TYPE in ("bl_j58_teb", "bl_j58_bleed", "bl_j58_ramjet"):
        bsdf.inputs["Emission Color"].default_value = bleed_col
        bsdf.inputs["Emission Strength"].default_value = 0.85

    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.38, radius2=0.0, depth=1.45, location=(-0.65, 0, 0), rotation=(0, math.radians(-90), 0))
    spk = bpy.context.active_object
    spk.name = "j58_inlet_spike"
    for p in spk.data.polygons: p.use_smooth = True
    spk.data.materials.append(lib["titanium"])

    for i in range(6):
        ang = math.radians(i * 60.0 + 30.0)
        cu = bpy.data.curves.new(f"j58_bleed_tube_{{i}}", type='CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = 0.042
        cu.bevel_resolution = 8
        sp = cu.splines.new('NURBS')
        pts = [
            (1.10, 0.48 * math.cos(ang), 0.48 * math.sin(ang)),
            (1.22, 0.68 * math.cos(ang), 0.68 * math.sin(ang)),
            (2.10, 0.68 * math.cos(ang), 0.68 * math.sin(ang)),
            (2.95, 0.68 * math.cos(ang), 0.68 * math.sin(ang)),
            (3.12, 0.52 * math.cos(ang), 0.52 * math.sin(ang)),
        ]
        sp.points.add(len(pts)-1)
        for pi, (px, py, pz) in enumerate(pts):
            sp.points[pi].co = (px, py, pz, 1.0)
        sp.use_endpoint_u = True
        obj_p = bpy.data.objects.new(f"j58_bleed_tube_{{i}}", cu)
        obj_p.data.materials.append(bleed_mat)
        scn.collection.objects.link(obj_p)

    rnd.setup_world(0.30)
    rnd.setup_lights()
    if SCENE_TYPE != "bl_j58_hero":
        rnd._add_section_cutter()
    rnd.area_light("bore", (rnd.X_MID - 0.4, -4.2, 1.2), (math.radians(74), 0, 0), 1800, 8.0)
    rnd.area_light("bore2", (rnd.X_MID + 1.2, -2.6, 3.4), (math.radians(38), 0, 0), 900, 6.0)
    cam_o = rnd.setup_camera((rnd.X_MID - 3.8, -11.6, 4.0), (rnd.X_MID - 0.25, 0, 0.0), lens=76)

    coords_log = []
    for kf in range(N_KF):
        u = kf / max(1, N_KF - 1)
        # Animate spike retraction (26 inches = 0.66m) and camera orbit!
        spk.location.x = -0.75 + u * 0.48
        # Rotate compressor & fan blades
        for o in objs:
            if "blades_" in o.name.lower():
                o.rotation_euler.x = u * math.pi * 4.0
        if SCENE_TYPE == "bl_j58_front":
            cam_o.location = (rnd.X_MID - 10.8 + u*1.5, -5.2 - u*2.5, 2.4 + u*1.0)
        elif SCENE_TYPE == "bl_j58_exploded":
            cam_o.location = (rnd.X_MID - 5.2 + u*2.8, -13.0, 4.4 - u*0.8)
        else:
            cam_o.location = (rnd.X_MID - 4.4 + u*2.6, -11.4 - 0.8*math.sin(u*math.pi), 3.8 + 0.6*math.cos(u*math.pi))
        rnd.aim(cam_o, (rnd.X_MID - 0.15, 0.0, 0.0))
        scn.render.filepath = os.path.join(OUT_DIR, f"kf_{{kf:03d}}.png")
        bpy.ops.render.render(write_still=True)

        pts_3d = {{
            "spike": Vector((spk.location.x, 0.0, 0.0)),
            "compressor": Vector((1.05, 0.0, 0.25)),
            "bleed": Vector((2.05, 0.0, 0.68)),
            "combustor": Vector((2.20, 0.0, 0.0)),
            "afterburner": Vector((3.40, 0.0, 0.0)),
        }}
        proj = {{}}
        for k, v3 in pts_3d.items():
            co = world_to_camera_view(scn, cam_o, v3)
            proj[k] = [int(co.x * 1920), int((1.0 - co.y) * 1080)]
        coords_log.append(proj)

    with open(os.path.join(OUT_DIR, "coords.json"), "w") as f:
        json.dump(coords_log, f)
""")
    bl_bin = os.environ.get("BLENDER_BIN", "blender")
    subprocess.run([bl_bin, "-b", "-P", bl_script], check=True)

def add_primal_hud(frame_bgr, title, sub, t_local, dur_scene, pin_pt=None, pin_label=None):
    """Draws clean Primal Space minimalist typography & 3D-tracked engineering callout pin."""
    img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    dr = ImageDraw.Draw(img, "RGBA")
    # Top-left minimalist title bar with subtle dark glass pill
    dr.rounded_rectangle([42, 36, 980, 128], radius=10, fill=(12, 15, 22, 205), outline=(70, 95, 135, 180), width=2)
    dr.rectangle([42, 36, 50, 128], fill=(0, 210, 255, 255))
    dr.text((68, 48), title, font=get_font(24, True), fill=(245, 248, 255, 255))
    dr.text((68, 84), sub, font=get_font(16, False), fill=(175, 195, 225, 255))

    # 3D-Projected Callout Pin if provided
    if pin_pt and pin_label:
        px, py = pin_pt
        if 80 < px < 1840 and 140 < py < 960:
            bx = min(1520, max(100, px + 70))
            by = max(160, min(920, py - 65))
            dr.line([(px, py), (bx, by)], fill=(0, 225, 255, 235), width=3)
            dr.ellipse([px-7, py-7, px+7, py+7], fill=(0, 225, 255, 255), outline=(255, 255, 255, 255), width=2)
            dr.rounded_rectangle([bx, by-22, bx+340, by+22], radius=6, fill=(14, 18, 28, 225), outline=(0, 225, 255, 220), width=2)
            dr.text((bx+14, by-11), pin_label, font=get_font(16, True), fill=(255, 255, 255, 255))

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def render_scene_frames(scene, n_frames, work_dir, write_frame_fn):
    stype = scene["type"]
    title = scene["title"]
    sub   = scene["sub"]
    dur   = n_frames / float(FPS)

    if stype.startswith("bl_"):
        bl_dir = os.path.join(work_dir, f"bl_{scene['id']}")
        n_kf = 16
        render_blender_turntable_frames(stype, bl_dir, n_keyframes=n_kf)
        kfs = []
        for k in range(n_kf):
            im = cv2.imread(os.path.join(bl_dir, f"kf_{k:03d}.png"))
            im = cv2.bilateralFilter(im, 5, 24, 24)
            kfs.append(im)
        with open(os.path.join(bl_dir, "coords.json")) as f:
            coords = json.load(f)

        pin_map = {
            "bl_sr71_missile": ("afterburner", "J58 FULL AFTERBURNER — MACH 3.2"),
            "bl_sr71_leak":    ("cockpit",     "ROOM TEMP: DELIBERATE TANK GAPS"),
            "bl_sr71_thermal": ("nose",        "STAGNATION TEMP: 620°F – 950°F"),
            "bl_sr71_expand":  ("cockpit",     "THERMAL EXPANSION: +3.5 INCHES"),
            "bl_sr71_xray":    ("cockpit",     "6 INTERNAL FUSELAGE FUEL TANKS"),
            "bl_sr71_coolant": ("spike",       "JP-7 FUEL CIRCULATES AS COOLANT"),
            "bl_sr71_finale":  ("afterburner", "0 AIRCRAFT LOST TO ENEMY MISSILES"),
            "bl_j58_hero":     ("spike",       "BETA-120 TITANIUM INLET CONE"),
            "bl_j58_teb":      ("combustor",   "TEB PYROPHORIC GREEN IGNITION"),
            "bl_j58_cutaway":  ("compressor",  "9-STAGE AXIAL FLOW COMPRESSOR"),
            "bl_j58_exploded": ("combustor",   "99 ASSEMBLIES · 2,044 AIRFOILS"),
            "bl_j58_spike":    ("spike",       "SPIKE RETRACTS 26 INCHES AT MACH 3.2"),
            "bl_j58_bleed":    ("bleed",       "6 EXTERNAL BYPASS BLEED TUBES"),
            "bl_j58_ramjet":   ("afterburner", "3,200°F HYBRID TURBO-RAMJET PLUME"),
            "bl_j58_unstart":  ("spike",       "SHOCKWAVE EXPULSION (UNSTART)"),
            "bl_j58_front":    ("spike",       "CONICAL SHOCKWAVE CAPTURE THROAT"),
        }
        pk, plbl = pin_map.get(stype, ("spike", "PRATT & WHITNEY J58"))

        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            pos = u * (n_kf - 1)
            idx0 = int(math.floor(pos))
            idx1 = min(n_kf - 1, idx0 + 1)
            frac = pos - idx0
            fr = cv2.addWeighted(kfs[idx0], 1.0 - frac, kfs[idx1], frac, 0)
            p0 = coords[idx0].get(pk, [960, 540])
            p1 = coords[idx1].get(pk, [960, 540])
            pt = (int(p0[0]*(1-frac) + p1[0]*frac), int(p0[1]*(1-frac) + p1[1]*frac))
            fr = add_primal_hud(fr, title, sub, f_i/FPS, dur, pin_pt=pt, pin_label=plbl)
            write_frame_fn(fr)

    elif stype.startswith("vid_"):
        vid_p = os.path.join(ROOT, "real_videos", scene["vid"])
        cap = cv2.VideoCapture(vid_p)
        v_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        v_tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 300
        start_f = int(scene.get("ss", 0.0) * v_fps)
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            cur_vf = (start_f + int(f_i * (v_fps / FPS))) % max(1, v_tot - 5)
            cap.set(cv2.CAP_PROP_POS_FRAMES, cur_vf)
            ret, raw = cap.read()
            if not ret or raw is None:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, raw = cap.read()
            bg = cv2.GaussianBlur(cv2.resize(raw, (W, H)), (51, 51), 0)
            bg = (bg.astype(np.float32) * 0.22).astype(np.uint8)
            fg = cv2.resize(raw, (1560, 860), interpolation=cv2.INTER_LINEAR)
            bg[155:1015, 180:1740] = fg
            cv2.rectangle(bg, (180, 155), (1740, 1015), (210, 220, 235), 2, cv2.LINE_AA)
            fr = add_primal_hud(bg, title, sub, f_i/FPS, dur)
            write_frame_fn(fr)
        cap.release()

    elif stype == "map_cia_ussr":
        with open(os.path.join(ROOT, "models3d", "world_countries.geojson")) as f:
            geo = json.load(f)
        USSR_ISO = {"RUS", "UKR", "BLR", "KAZ", "UZB", "TKM", "KGZ", "TJK", "GEO", "AZE", "ARM", "LTU", "LVA", "EST", "MDA"}
        base_map = Image.new("RGB", (W, H), (18, 21, 31))
        dr = ImageDraw.Draw(base_map)
        for gx in range(80, W, 90): dr.line([(gx, 0), (gx, H)], fill=(26, 31, 46), width=1)
        for gy in range(80, H, 90): dr.line([(0, gy), (W, gy)], fill=(26, 31, 46), width=1)
        def ll_xy(lon, lat):
            return (120.0 + (lon + 135.0)/290.0 * 1680.0, 960.0 - (lat - 8.0)/72.0 * 780.0)
        for feat in geo["features"]:
            iso = feat.get("properties", {}).get("ISO_A3") or feat.get("properties", {}).get("ADM0_A3") or ""
            fc = (200, 48, 38) if iso in USSR_ISO else (38, 45, 62)
            oc = (240, 90, 75) if iso in USSR_ISO else (62, 72, 96)
            geom = feat.get("geometry", {})
            polys = geom.get("coordinates", []) if geom.get("type") == "MultiPolygon" else [geom.get("coordinates", [])]
            for poly in polys:
                if not poly: continue
                pts = [ll_xy(pt[0], pt[1]) for pt in poly[0] if -145 <= pt[0] <= 165 and 5 <= pt[1] <= 82]
                if len(pts) >= 3: dr.polygon(pts, fill=fc, outline=oc)
        base_bgr = cv2.cvtColor(np.array(base_map), cv2.COLOR_RGB2BGR)
        nodes = [
            (ll_xy(60.0, 56.0),   "1. U.S.S.R. RUTILE ORE MINES (URALS)"),
            (ll_xy(8.5, 47.4),    "2. EUROPEAN FRONT COMPANIES (ZURICH)"),
            (ll_xy(-9.1, 38.7),   "3. THIRD-PARTY MARITIME TRANSIT"),
            (ll_xy(-118.3, 34.2), "4. LOCKHEED SKUNK WORKS (BURBANK, CA)"),
        ]
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            fr = base_bgr.copy()
            total_segs = len(nodes) - 1
            prog = u * total_segs
            for s_i in range(total_segs):
                pA = (int(nodes[s_i][0][0]), int(nodes[s_i][0][1]))
                pB = (int(nodes[s_i+1][0][0]), int(nodes[s_i+1][0][1]))
                seg_u = max(0.0, min(1.0, prog - s_i))
                if seg_u > 0:
                    pCur = (int(pA[0] + (pB[0]-pA[0])*seg_u), int(pA[1] + (pB[1]-pA[1])*seg_u))
                    cv2.line(fr, pA, pCur, (255, 255, 255), 4, cv2.LINE_AA)
            for idx, ((nx, ny), lbl) in enumerate(nodes):
                if prog >= idx - 0.1:
                    cv2.circle(fr, (int(nx), int(ny)), 10, (255, 255, 255), -1, cv2.LINE_AA)
                    cv2.circle(fr, (int(nx), int(ny)), 14, (40, 60, 220), 2, cv2.LINE_AA)
                    cv2.putText(fr, lbl, (max(40, min(1420, int(nx)-110)), int(ny)+34), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
            fr = add_primal_hud(fr, title, sub, f_i/FPS, dur)
            write_frame_fn(fr)

    elif stype.startswith("chart_"):
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            img = Image.new("RGB", (W, H), (235, 232, 223))
            dr = ImageDraw.Draw(img)
            ox, oy, aw, ah = 240, 880, 1440, 640
            dr.line([(ox, oy-ah), (ox, oy), (ox+aw, oy)], fill=(35, 35, 40), width=4)
            if stype == "chart_alloy":
                mx1, mx2 = ox + int(0.58*aw), ox + int(0.90*aw)
                dr.rectangle([mx1, oy-ah, mx2, oy], fill=(222, 206, 192))
                dr.text((mx1+20, oy-ah+20), "MACH 3.2 THERMAL ENVELOPE (600°F – 950°F)", font=get_font(20, True), fill=(185, 45, 35))
                for i, tl in enumerate(["0°F", "250°F", "500°F", "750°F", "1,000°F"]):
                    tx = ox + int(i * aw / 4)
                    dr.text((tx-28, oy+18), tl, font=get_font(20, True), fill=(45, 45, 50))
                n_pts = max(2, int(u * 40))
                al_all = [(ox + int(k/39*aw), oy - int(420 * (1.0 / (1.0 + math.exp((k-14)/3.2))))) for k in range(40)]
                ti_all = [(ox + int(k/39*aw), oy - int(580 - 140*(k/39)**2)) for k in range(40)]
                dr.line(al_all[:n_pts], fill=(200, 48, 38), width=7)
                dr.line(ti_all[:n_pts], fill=(25, 32, 45), width=7)
                dr.text((ox+60, oy-360), "ALUMINUM 2024-T4 (MELTS / STRUCTURAL COLLAPSE >300°F)", font=get_font(22, True), fill=(195, 45, 35))
                dr.text((ox+60, oy-620), "TITANIUM BETA-120 ALLOY (HOLDS STRENGTH PAST 1,000°F)", font=get_font(22, True), fill=(25, 32, 45))
            elif stype == "chart_thrust":
                bars = [
                    ("INLET CONE PRESSURE REBOUND", 0.58, (0, 140, 215), "58% – 80% OF TOTAL THRUST"),
                    ("AFTERBURNER EJECTOR NOZZLE",  0.25, (215, 85, 30), "25% OF TOTAL THRUST"),
                    ("9-STAGE AXIAL TURBINE CORE",  0.17, (65, 75, 95),  "ONLY 17% OF TOTAL THRUST"),
                ]
                for b_i, (blbl, bval, bcol, btxt) in enumerate(bars):
                    by = 320 + b_i * 185
                    bw = int(aw * bval * min(1.0, u * 1.35))
                    dr.rounded_rectangle([ox+40, by, ox+40+max(20, bw), by+110], radius=10, fill=bcol)
                    dr.text((ox+40, by-36), blbl, font=get_font(22, True), fill=(30, 30, 35))
                    dr.text((ox+60+bw, by+38), btxt, font=get_font(24, True), fill=bcol)
            else:
                # chart_jp7
                bars = [
                    ("STANDARD JET-A KEROSENE (FLASHPOINT 100°F)", 0.32, (200, 50, 40), "BOILS & VAPORIZES AT MACH 3"),
                    ("LOCKHEED JP-7 SUPERSONIC FUEL (FLASHPOINT 140°F)", 0.88, (25, 115, 185), "EXTINGUISHES OPEN FLAME + COOLS AIRFRAME"),
                ]
                for b_i, (blbl, bval, bcol, btxt) in enumerate(bars):
                    by = 360 + b_i * 230
                    bw = int(aw * bval * min(1.0, u * 1.35))
                    dr.rounded_rectangle([ox+40, by, ox+40+max(20, bw), by+125], radius=10, fill=bcol)
                    dr.text((ox+40, by-38), blbl, font=get_font(22, True), fill=(30, 30, 35))
                    dr.text((ox+60+bw, by+44), btxt, font=get_font(22, True), fill=bcol)
            fr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            fr = add_primal_hud(fr, title, sub, f_i/FPS, dur)
            write_frame_fn(fr)

    elif stype == "diag_flight_man":
        svg_im = cv2.imread(os.path.join(ROOT, "archival_photos", "j58_airflow_official.png"))
        sh, sw = svg_im.shape[:2]
        stg = scene.get("mach_stage", 3)
        y0 = int(sh * (stg * 0.20))
        y1 = min(sh, int(sh * ((stg + 1) * 0.20)))
        crop = svg_im[y0:y1, :]
        crop_rs = cv2.resize(crop, (1620, 480), interpolation=cv2.INTER_LINEAR)
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            fr = np.full((H, W, 3), (12, 14, 20), dtype=np.uint8)
            fr[320:800, 150:1770] = crop_rs
            # Animated supersonic airflow particles streaming through the J58 diagram
            for p_i in range(28):
                px = int(160 + ((p_i * 65 + u * 950) % 1580))
                py = 560 + int(115 * math.sin(p_i * 1.7 + u * 6.0))
                col = (0, 210, 255) if px < 880 else (40, 110, 255)
                cv2.arrowedLine(fr, (px, py), (px+28, py), col, 2, cv2.LINE_AA, tipLength=0.35)
            cv2.rectangle(fr, (150, 320), (1770, 800), (70, 160, 235), 2, cv2.LINE_AA)
            fr = add_primal_hud(fr, title, sub, f_i/FPS, dur)
            write_frame_fn(fr)

    else:
        # arch_parallax (2.5D depth parallax over authentic archival photography)
        im_p = os.path.join(ROOT, "archival_photos", scene.get("img", "sunset.jpg"))
        raw = cv2.imread(im_p)
        if raw is None:
            raw = np.full((720, 1280, 3), (30, 35, 45), dtype=np.uint8)
        bg_blur = cv2.GaussianBlur(cv2.resize(raw, (W, H)), (65, 65), 0)
        bg_blur = (bg_blur.astype(np.float32) * 0.25).astype(np.uint8)
        fg_base = cv2.resize(raw, (1540, 860), interpolation=cv2.INTER_CUBIC)
        for f_i in range(n_frames):
            u = f_i / max(1, n_frames - 1)
            fr = bg_blur.copy()
            # Smooth 2.5D camera dolly zoom (1.00 -> 1.07)
            sc = 1.0 + 0.065 * u
            cw, ch = int(1540 / sc), int(860 / sc)
            x0, y0 = (1540 - cw) // 2, (860 - ch) // 2
            zoomed = cv2.resize(fg_base[y0:y0+ch, x0:x0+cw], (1540, 860), interpolation=cv2.INTER_LINEAR)
            fr[155:1015, 190:1730] = zoomed
            cv2.rectangle(fr, (190, 155), (1730, 1015), (215, 220, 230), 2, cv2.LINE_AA)
            fr = add_primal_hud(fr, title, sub, f_i/FPS, dur)
            write_frame_fn(fr)

def render_shard(shard_idx, out_mp4):
    shard_dur = TOTAL_DUR / float(N_SHARDS) # 21.35s per shard
    n_shard_frames = int(round(shard_dur * FPS)) # 640 frames
    n_scene1 = n_shard_frames // 2
    n_scene2 = n_shard_frames - n_scene1

    sc1 = ORDERED_40[shard_idx * 2]
    sc2 = ORDERED_40[shard_idx * 2 + 1]
    work_dir = f"/tmp/sr71_shard_{shard_idx:02d}"
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

    def write_frame(bgr):
        proc.stdin.write(bgr.tobytes())

    print(f"[Shard {shard_idx:02d}] Rendering Scene {sc1['id']} ({sc1['type']}) - {n_scene1} frames...")
    render_scene_frames(sc1, n_scene1, work_dir, write_frame)
    print(f"[Shard {shard_idx:02d}] Rendering Scene {sc2['id']} ({sc2['type']}) - {n_scene2} frames...")
    render_scene_frames(sc2, n_scene2, work_dir, write_frame)

    proc.stdin.close()
    proc.wait()
    shutil.rmtree(work_dir, ignore_errors=True)
    print(f"[Shard {shard_idx:02d}] Completed -> {out_mp4} ({os.path.getsize(out_mp4)//1024} KB)")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        s_idx = int(sys.argv[1])
        o_mp4 = sys.argv[2]
        render_shard(s_idx, o_mp4)
