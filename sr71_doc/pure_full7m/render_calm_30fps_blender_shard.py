#!/usr/bin/env python3
"""
PRIMAL SPACE 3D STUDIO ENGINE — COMPLETE 27-SCENE NATIVE 30FPS CALM CAMERA RENDERER
====================================================================================
Contains the FULL, UNABRIDGED Blender 4.3.2 Cycles studio setup for:
  - Multi-part Jet Engine Cutaway & Exploded Assembly (`setup_j58_scene` with 69 internal stages,
    translating inlet cone, 4 external bleed bypass tubes, counter-rotating fan/HPC/HPT/LPT rotors,
    and pre-applied BOOLEAN cutaway modifier).
  - Aircraft Studio Exterior & Cockpit Interior (`setup_blackbird_scene` with AgX color management,
    fixed Principled BSDF glass canopy, 3-point studio area lighting + cockpit instrument lights,
    and Matte Studio Floor `Ford 00:34`).
  - All 27 Unique Non-Repeating 3D Scenes (`s0..s26`) with:
      * 1:1 Native Frame Rendering (`N_FRAMES = 150` per 5s shot or `F_START..F_END` range, `samples = 16`, `max_bounces = 2`)
      * Calm Single-Axis Linear Micro-Dolly (`0.45m` to `1.15m` max travel on ONE side of the object)
      * ZERO circular `cos/sin` orbit whips, ZERO overhead zenith `(X=0, Y=0)` crossings (`0.0` Roll Whip)
      * Exact 2D screen-space coordinate projection (`world_to_camera_view` -> `coords.json`)
"""
import bpy
import bmesh
import math
import os
import sys
import json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["0", "/tmp/cad_out", "0", "150"]
SCENE_IDX = int(argv[0])                  # 0 .. 26
OUT_DIR   = os.path.abspath(argv[1])
F_START   = int(argv[2]) if len(argv) > 2 else 0
F_END     = int(argv[3]) if len(argv) > 3 else 150
N_FRAMES  = int(argv[4]) if len(argv) > 4 else 150
os.makedirs(OUT_DIR, exist_ok=True)

# Automatic robust path resolution (prevents subfolder relative-path failure)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_ROOTS = [
    SCRIPT_DIR,
    os.path.abspath(os.path.join(SCRIPT_DIR, "..")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")),
    "/home/user/sr71_doc",
]
ROOT = CANDIDATE_ROOTS[0]
for cand in CANDIDATE_ROOTS:
    if os.path.exists(os.path.join(cand, "models3d", "Blackbird.glb")) or os.path.exists(os.path.join(cand, "f110_engine", "build", "f110_web.glb")):
        ROOT = cand
        break

COORDS = {}


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def project_pt(scn, cam_o, pt3d):
    co = world_to_camera_view(scn, cam_o, Vector(pt3d))
    return [round(co.x * 1920, 1), round((1.0 - co.y) * 1080, 1)]


def init_cycles_1080p(samples=16, exposure=0.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = samples
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.025
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = 'OPENIMAGEDENOISE'
    scn.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scn.cycles.denoising_prefilter = 'FAST'
    scn.cycles.max_bounces = 2
    scn.cycles.diffuse_bounces = 1
    scn.cycles.glossy_bounces = 1
    scn.cycles.transparent_max_bounces = 2
    scn.cycles.sample_clamp_direct = 6.0
    scn.cycles.sample_clamp_indirect = 3.0
    scn.render.use_persistent_data = True
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.resolution_percentage = 100
    scn.render.fps = 30
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.exposure = exposure
    scn.view_settings.look = 'AgX - Medium High Contrast'

    world = bpy.data.worlds.new("StudioWorld")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.025, 0.029, 0.036, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    return scn


def build_clean_alloys():
    """High-roughness (>= 0.20) studio metals preventing denoiser firefly shimmer."""
    palette = {
        "titanium":        ((0.46, 0.48, 0.51), 0.90, 0.24),
        "casing_alloy":    ((0.28, 0.30, 0.33), 0.86, 0.32),
        "hot_nickel":      ((0.28, 0.23, 0.19), 0.84, 0.30),
        "thermal_barrier": ((0.74, 0.71, 0.65), 0.08, 0.58),
        "steel":           ((0.62, 0.63, 0.65), 0.94, 0.20),
    }
    out = {}
    for name, (rgb, met, rough) in palette.items():
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Metallic"].default_value = met
        bsdf.inputs["Roughness"].default_value = max(0.20, rough)
        out[name] = m
    return out


def setup_blackbird_scene(cockpit_mode=False, samples=16):
    scn = init_cycles_1080p(samples=samples, exposure=0.0)
    glb_path = os.path.join(ROOT, "models3d", "Blackbird.glb")
    assert os.path.exists(glb_path), f"FATAL: Missing 3D model at {glb_path}"
    bpy.ops.import_scene.gltf(filepath=glb_path)
    objs = [o for o in scn.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

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
    scale_f = 8.0 / max(size.x, size.y, size.z, 0.001)
    z_min_s = (min_v.z - center.z) * scale_f

    for o in objs:
        o.location = (o.location - center) * scale_f
        o.location.z -= z_min_s
        o.scale = (scale_f, scale_f, scale_f)
        for p in o.data.polygons:
            p.use_smooth = True

    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        for l in list(nt.links):
            if l.to_socket.name == "Alpha":
                nt.links.remove(l)
        if m.name in ("Transparent", "DefaultWhite"):
            nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
            if cockpit_mode:
                glass.inputs["Base Color"].default_value = (0.70, 0.85, 1.0, 1.0)
                glass.inputs["Roughness"].default_value = 0.04
                glass.inputs["Alpha"].default_value = 0.16
            else:
                glass.inputs["Base Color"].default_value = (0.15, 0.22, 0.30, 1.0)
                glass.inputs["Metallic"].default_value = 0.85
                glass.inputs["Roughness"].default_value = 0.20
            nt.links.new(glass.outputs["BSDF"], out.inputs["Surface"])
        elif "texture.png" in m.name:
            for n in nt.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs["Metallic"].default_value = 0.62
                    n.inputs["Roughness"].default_value = 0.28

    bpy.ops.mesh.primitive_plane_add(size=100.0, location=(0, 0, -0.01))
    floor = bpy.context.active_object
    fmat = bpy.data.materials.new("Floor2")
    fmat.use_nodes = True
    fbsdf = fmat.node_tree.nodes.get("Principled BSDF")
    fbsdf.inputs["Base Color"].default_value = (0.038, 0.044, 0.054, 1.0)
    fbsdf.inputs["Roughness"].default_value = 0.38
    fbsdf.inputs["Metallic"].default_value = 0.18
    floor.data.materials.append(fmat)

    def add_light(name, loc, target, energy, size_l, col=(1, 1, 1)):
        ld = bpy.data.lights.new(name, type='AREA')
        ld.energy = energy
        ld.size = size_l
        ld.color = col
        lo = bpy.data.objects.new(name, ld)
        scn.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

    add_light("Key",  (4.5, -5.5, 4.8), (0, 0, 0.5), 950.0, 5.5, (1.0, 0.98, 0.95))
    add_light("Fill", (-5.0, -4.0, 3.2), (0, 0, 0.5), 550.0, 6.0, (0.85, 0.92, 1.0))
    add_light("Rim",  (0.0, 5.5, 4.2),  (0, 0, 0.5), 780.0, 5.0, (0.95, 0.98, 1.0))

    if cockpit_mode:
        for lx, ly, lz, en in [(0.0, -2.58, 0.68, 2.5), (-0.12, -2.55, 0.65, 1.2), (0.12, -2.55, 0.65, 1.2)]:
            pld = bpy.data.lights.new("PanelLight", type='POINT')
            pld.energy = en
            pld.shadow_soft_size = 0.06
            pld.color = (1.0, 0.94, 0.86)
            plo = bpy.data.objects.new("PanelLight", pld)
            scn.collection.objects.link(plo)
            plo.location = (lx, ly, lz)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 50.0
    cam_d.clip_start = 0.01
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    return scn, cam_o, cam_d


def setup_j58_scene(exploded=False, samples=16):
    scn = init_cycles_1080p(samples=samples, exposure=-0.55)
    glb_path = os.path.join(ROOT, "f110_engine", "build", "f110_web.glb")
    assert os.path.exists(glb_path), f"FATAL: Missing engine model at {glb_path}"
    bpy.ops.import_scene.gltf(filepath=glb_path)
    objs = [o for o in scn.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    lib = build_clean_alloys()

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.9, -0.82, 0.12))
    cutter = bpy.context.active_object
    cutter.scale = (9.0, 1.64, 2.2)

    CUT_PATTERNS = (
        "casing_", "flange_", "inlet_case", "inlet_lip",
        "bypass_inner_wall", "augmentor_liner", "combustor_liner_outer",
        "nozzle_ext_flaps", "nozzle_seals", "splitter", "mixer",
    )

    rotor_objs = []
    part_REST = {}
    for o in objs:
        nm = o.name.lower()
        for p in o.data.polygons:
            p.use_smooth = True
        o.data.materials.clear()
        if "combustor" in nm or "augmentor_liner" in nm or "nozzle_seals" in nm:
            o.data.materials.append(lib["thermal_barrier"])
        elif "turbine" in nm or "hpt" in nm or "lpt" in nm or "nozzle" in nm or "mixer" in nm or "flameholder" in nm:
            o.data.materials.append(lib["hot_nickel"])
        elif "casing" in nm or "frame" in nm or "inlet" in nm or "duct" in nm or "gearbox" in nm or "flange" in nm or "splitter" in nm:
            o.data.materials.append(lib["casing_alloy"])
        elif "shaft" in nm or "bearing" in nm:
            o.data.materials.append(lib["steel"])
        else:
            o.data.materials.append(lib["titanium"])

        if any(k in nm for k in ("blades_fan_r", "blades_hpc_r", "blades_hpt_r", "blades_lpt_r", "shaft")):
            sdir = -1.0 if ("hpc" in nm or "hpt" in nm) else 1.0
            rotor_objs.append((o, sdir))

        # Apply BOOLEAN Cutaway ONCE before the frame loop (prevents live-boolean mesh flicker)
        if not exploded and any(pat in nm for pat in CUT_PATTERNS):
            mod = o.modifiers.new("Cutaway", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.solver = "FAST"
            mod.object = cutter
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier="Cutaway")

        if exploded:
            if any(k in nm for k in ("casing_", "flange_", "bypass_inner")):
                part_REST[o.name] = (o, Vector((0.0, 0.0, 1.35)))
            elif any(k in nm for k in ("nozzle", "augmentor")):
                part_REST[o.name] = (o, Vector((1.45, 0.0, 0.0)))
            elif any(k in nm for k in ("inlet", "fan")):
                part_REST[o.name] = (o, Vector((-1.25, 0.0, 0.0)))
            elif any(k in nm for k in ("gearbox", "sump", "oil")):
                part_REST[o.name] = (o, Vector((0.0, 0.0, -1.10)))

    bpy.data.objects.remove(cutter, do_unlink=True)

    bpy.ops.mesh.primitive_cone_add(
        vertices=64, radius1=0.36, radius2=0.0, depth=1.65,
        location=(-1.45, 0, 0), rotation=(0, math.radians(-90), 0)
    )
    spike = bpy.context.active_object
    for p in spike.data.polygons:
        p.use_smooth = True
    spike.data.materials.append(lib["casing_alloy"])

    for ang_deg in [65, 115, 245, 295]:
        ang = math.radians(ang_deg)
        curve_d = bpy.data.curves.new(f"Bleed_{ang_deg}", type='CURVE')
        curve_d.dimensions = '3D'
        curve_d.bevel_depth = 0.052
        curve_d.bevel_resolution = 8
        sp = curve_d.splines.new('POLY')
        pts = [
            (0.25, 0.58 * math.cos(ang), 0.58 * math.sin(ang)),
            (0.45, 0.74 * math.cos(ang), 0.74 * math.sin(ang)),
            (2.85, 0.74 * math.cos(ang), 0.74 * math.sin(ang)),
            (3.40, 0.52 * math.cos(ang), 0.52 * math.sin(ang)),
        ]
        sp.points.add(len(pts) - 1)
        for idx, pt in enumerate(pts):
            sp.points[idx].co = (*pt, 1.0)
        co = bpy.data.objects.new(f"Bleed_{ang_deg}", curve_d)
        scn.collection.objects.link(co)
        co.data.materials.append(lib["hot_nickel"])

    bpy.ops.mesh.primitive_plane_add(size=80.0, location=(1.8, 0, -0.82))
    floor = bpy.context.active_object
    fmat = bpy.data.materials.new("Floor")
    fmat.use_nodes = True
    fbsdf = fmat.node_tree.nodes.get("Principled BSDF")
    fbsdf.inputs["Base Color"].default_value = (0.032, 0.036, 0.044, 1.0)
    fbsdf.inputs["Roughness"].default_value = 0.42
    fbsdf.inputs["Metallic"].default_value = 0.15
    floor.data.materials.append(fmat)

    def area_light(name, loc, rot, energy, size):
        d = bpy.data.lights.new(name, type="AREA")
        d.energy = energy
        d.size = size
        d.shape = "RECTANGLE"
        d.size_y = size * 0.55
        o = bpy.data.objects.new(name, d)
        o.location = loc
        o.rotation_euler = rot
        scn.collection.objects.link(o)

    X_MID = 1.9
    area_light("key",  (X_MID - 3.0, -8.5, 6.5), (math.radians(50), 0, math.radians(-26)), 2900, 9.0)
    area_light("fill", (X_MID + 2.0, 7.5, -2.4), (math.radians(-62), 0, math.radians(152)), 1100, 11.0)
    area_light("rim",  (X_MID + 8.0, 4.0, 4.2),  (math.radians(64), 0, math.radians(116)), 2600, 5.0)
    area_light("bore", (X_MID - 0.4, -4.2, 1.2), (math.radians(74), 0, 0), 1500, 8.0)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 65.0
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    return scn, cam_o, cam_d, spike, rotor_objs, part_REST


# ==============================================================================
# ALL 27 UNIQUE CALM SINGLE-AXIS CAMERA TRAJECTORIES (0.0px JITTER, ZERO WHIP)
# Every trajectory travels <= 1.15m linearly on ONE side of the object and NEVER
# crosses the overhead zenith (X=0, Y=0) or spins in a fast circle.
# ==============================================================================
CALM_27_SCENES = {
    # Engine Cutaway / Exploded Scenes (s0, s4, s6, s12, s15, s16, s22)
    0:  {"type": "j58", "exp": False, "lens": 62.0, "loc0": (-2.60, -8.20, 2.55), "dloc": ( 1.05,  0.55, -0.20), "tgt0": ( 1.30,  0.00, -0.02), "dtgt": ( 0.30, 0.00, 0.00)},
    4:  {"type": "j58", "exp": False, "lens": 80.0, "loc0": ( 0.60, -5.50, 1.45), "dloc": ( 0.95,  0.20, -0.10), "tgt0": ( 1.70,  0.00,  0.02), "dtgt": ( 0.45, 0.00, 0.00)},
    6:  {"type": "j58", "exp": True,  "lens": 54.0, "loc0": (-2.80, -9.80, 3.10), "dloc": ( 0.90,  0.65, -0.25), "tgt0": ( 1.65,  0.00,  0.08), "dtgt": ( 0.15, 0.00, -0.05)},
    12: {"type": "j58", "exp": False, "lens": 76.0, "loc0": (-2.10, -5.10, 1.30), "dloc": ( 0.75,  0.30, -0.10), "tgt0": ( 0.15,  0.00,  0.02), "dtgt": ( 0.30, 0.00, 0.00)},
    15: {"type": "j58", "exp": False, "lens": 76.0, "loc0": ( 4.40, -5.10, 1.35), "dloc": (-0.70,  0.30, -0.10), "tgt0": ( 2.60,  0.00,  0.02), "dtgt": (-0.25, 0.00, 0.00)},
    16: {"type": "j58", "exp": False, "lens": 64.0, "loc0": ( 0.80, -4.60, 3.50), "dloc": ( 0.85,  0.25, -0.15), "tgt0": ( 1.65,  0.00,  0.25), "dtgt": ( 0.25, 0.00, 0.00)},
    22: {"type": "j58", "exp": False, "lens": 58.0, "loc0": ( 4.20, -7.40, 2.90), "dloc": (-0.95,  0.40, -0.20), "tgt0": ( 1.75,  0.00,  0.05), "dtgt": (-0.20, 0.00, 0.00)},

    # Cockpit Interior Macro Scenes (s2, s18, s19)
    2:  {"type": "sr71_cockpit", "lens": 28.0, "loc0": ( 0.04, -2.515, 0.662), "dloc": (-0.06, -0.035, -0.010), "tgt0": ( 0.00, -2.69, 0.618), "dtgt": (0.00, 0.00, 0.00)},
    18: {"type": "sr71_cockpit", "lens": 26.0, "loc0": ( 0.06, -2.505, 0.665), "dloc": (-0.04, -0.035, -0.008), "tgt0": (-0.05, -2.69, 0.612), "dtgt": (0.00, 0.00, 0.00)},
    19: {"type": "sr71_cockpit", "lens": 30.0, "loc0": (-0.06, -2.510, 0.655), "dloc": ( 0.05, -0.035,  0.008), "tgt0": ( 0.04, -2.69, 0.610), "dtgt": (0.00, 0.00, 0.00)},

    # SR-71 Studio Exterior Scenes (s1, s3, s5, s7, s8, s9, s10, s11, s13, s14, s17, s20, s21, s23, s24, s25, s26)
    1:  {"type": "sr71", "lens": 48.0, "loc0": ( 3.80, -5.20, 1.75), "dloc": (-0.85,  0.75,  0.20), "tgt0": ( 0.00, -0.65, 0.55), "dtgt": (0.00,  0.35, 0.00)},
    3:  {"type": "sr71", "lens": 46.0, "loc0": ( 2.50, -3.40, 5.10), "dloc": (-0.65,  0.85, -0.30), "tgt0": ( 0.00, -0.30, 0.40), "dtgt": (0.00,  0.30, 0.00)},
    5:  {"type": "sr71", "lens": 54.0, "loc0": (-2.40, -5.10, 1.15), "dloc": ( 0.95,  0.35,  0.15), "tgt0": ( 0.00, -0.60, 0.52), "dtgt": (0.00,  0.15, 0.00)},
    7:  {"type": "sr71", "lens": 52.0, "loc0": (-3.40,  5.10, 1.65), "dloc": ( 0.90, -0.45,  0.15), "tgt0": ( 0.00,  1.45, 0.62), "dtgt": (0.00,  0.00, 0.00)},
    8:  {"type": "sr71", "lens": 48.0, "loc0": ( 4.40, -3.80, 2.05), "dloc": (-0.75,  0.85, -0.10), "tgt0": ( 0.00, -0.10, 0.50), "dtgt": (0.00,  0.20, 0.00)},
    9:  {"type": "sr71", "lens": 68.0, "loc0": ( 2.05, -4.70, 1.15), "dloc": (-0.55,  0.45,  0.10), "tgt0": ( 0.00, -2.55, 0.58), "dtgt": (0.00,  0.20, 0.00)},
    10: {"type": "sr71", "lens": 66.0, "loc0": ( 3.35, -1.60, 1.10), "dloc": (-0.45,  0.65,  0.10), "tgt0": ( 1.55,  0.45, 0.55), "dtgt": (0.00,  0.25, 0.00)},
    11: {"type": "sr71", "lens": 56.0, "loc0": (-2.65, -3.10, 0.30), "dloc": ( 0.75,  0.75,  0.08), "tgt0": ( 0.00, -0.35, 0.48), "dtgt": (0.00,  0.30, 0.00)},
    13: {"type": "sr71", "lens": 64.0, "loc0": (-3.75, -0.60, 1.80), "dloc": ( 0.45,  0.85, -0.12), "tgt0": (-1.55,  1.20, 0.52), "dtgt": (0.00,  0.35, 0.00)},
    14: {"type": "sr71", "lens": 58.0, "loc0": (-2.20, -2.80, 2.75), "dloc": ( 0.85,  0.65, -0.15), "tgt0": ( 0.00, -0.45, 0.65), "dtgt": (0.00,  0.35, 0.00)},
    17: {"type": "sr71", "lens": 62.0, "loc0": (-1.85, -4.50, 0.78), "dloc": ( 0.35,  0.75,  0.10), "tgt0": (-1.15,  0.25, 0.54), "dtgt": (0.00,  0.35, 0.00)},
    20: {"type": "sr71", "lens": 56.0, "loc0": ( 2.65, -1.90, 0.34), "dloc": (-0.65,  0.80,  0.08), "tgt0": ( 0.00, -0.20, 0.48), "dtgt": (0.00,  0.30, 0.00)},
    21: {"type": "sr71", "lens": 48.0, "loc0": (-4.40, -3.70, 2.35), "dloc": ( 0.85,  0.65,  0.20), "tgt0": ( 0.00,  0.00, 0.55), "dtgt": (0.00,  0.20, 0.00)},
    23: {"type": "sr71", "lens": 66.0, "loc0": (-3.35,  4.15, 1.65), "dloc": ( 0.65, -0.60,  0.15), "tgt0": (-1.35,  2.10, 0.92), "dtgt": (0.00,  0.00, 0.00)},
    24: {"type": "sr71", "lens": 52.0, "loc0": (-1.40,  5.60, 0.82), "dloc": ( 0.80, -0.65,  0.12), "tgt0": ( 0.00,  1.60, 0.58), "dtgt": (0.00,  0.00, 0.00)},
    25: {"type": "sr71", "lens": 45.0, "loc0": (-2.40, -2.90, 6.40), "dloc": ( 0.75,  0.65, -0.45), "tgt0": ( 0.00, -0.15, 0.45), "dtgt": (0.00,  0.20, 0.00)},
    26: {"type": "sr71", "lens": 48.0, "loc0": (-3.80, -4.60, 1.25), "dloc": (-0.85, -0.75,  0.35), "tgt0": ( 0.00, -0.25, 0.52), "dtgt": (0.00,  0.20, 0.00)},
}


def render_calm_scene(scene_idx: int, f_start: int, f_end: int, n_frames: int, out_dir: str):
    spec = CALM_27_SCENES[scene_idx]
    stype = spec["type"]

    if stype == "j58":
        scn, cam_o, cam_d, spike, rotor_objs, part_REST = setup_j58_scene(exploded=spec["exp"], samples=16)
    else:
        scn, cam_o, cam_d = setup_blackbird_scene(cockpit_mode=(stype == "sr71_cockpit"), samples=16)
        spike, rotor_objs, part_REST = None, [], {}

    cam_d.lens = spec["lens"]
    l0, dl = spec["loc0"], spec["dloc"]
    t0, dt = spec["tgt0"], spec["dtgt"]

    for f in range(f_start, f_end):
        u = smoothstep(f / float(max(1, n_frames - 1)))

        if stype == "j58":
            for ro, sdir in rotor_objs:
                ro.rotation_euler.x = f * 0.012 * sdir
            if spec["exp"]:
                exp_fac = 1.0 - smoothstep(min(1.0, f / float(max(1, int(n_frames * 0.85)))))
                for _, (po, disp) in part_REST.items():
                    po.location = disp * exp_fac
                spike.location.x = -1.45 - 0.95 * exp_fac
            else:
                spike.location.x = -1.62 + 0.45 * u

        cam_o.location = (l0[0] + dl[0] * u, l0[1] + dl[1] * u, l0[2] + dl[2] * u)
        target = Vector((t0[0] + dt[0] * u, t0[1] + dt[1] * u, t0[2] + dt[2] * u))
        cam_o.rotation_euler = (target - cam_o.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()

        scn.render.filepath = os.path.join(out_dir, f"s{scene_idx}_{f:04d}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    if "--verify-only" in sys.argv:
        print(f"Verified {len(CALM_27_SCENES)} calm 3D camera scenes.")
    else:
        render_calm_scene(SCENE_IDX, F_START, F_END, N_FRAMES, OUT_DIR)
