"""Renders 18 brand-new unique 1080p Pure-Blender 3D sequences (Scenes s9..s26, 60 frames each)
using the exact proven setup_blackbird_scene() and setup_j58_scene() from render_extra_cad_shard.py.
"""
import bpy, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["0", "/tmp/cad_out"]
SHARD_ID  = int(argv[0]) # 0..17
OUT_DIR   = os.path.abspath(argv[1])
os.makedirs(OUT_DIR, exist_ok=True)

SCENE_IDX = 9 + SHARD_ID # s9 .. s26
N_FRAMES  = 60

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)

def init_fast_cycles_1080p(exposure=0.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 6
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = 'OPENIMAGEDENOISE'
    scn.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scn.cycles.denoising_prefilter = 'FAST'
    scn.cycles.max_bounces = 1
    scn.cycles.diffuse_bounces = 1
    scn.cycles.glossy_bounces = 1
    scn.cycles.transparent_max_bounces = 1
    scn.cycles.sample_clamp_direct = 5.0
    scn.cycles.sample_clamp_indirect = 2.5
    scn.render.use_persistent_data = True
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
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
    palette = {
        "titanium":        ((0.46, 0.48, 0.51), 0.90, 0.24),
        "casing_alloy":    ((0.28, 0.30, 0.33), 0.86, 0.32),
        "hot_nickel":      ((0.28, 0.23, 0.19), 0.84, 0.30),
        "thermal_barrier": ((0.74, 0.71, 0.65), 0.08, 0.58),
        "steel":           ((0.62, 0.63, 0.65), 0.94, 0.18),
    }
    out = {}
    for name, (rgb, met, rough) in palette.items():
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Metallic"].default_value = met
        bsdf.inputs["Roughness"].default_value = rough
        out[name] = m
    return out

def setup_blackbird_scene(cockpit_mode=False):
    scn = init_fast_cycles_1080p(exposure=0.0)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "models3d", "Blackbird.glb"))
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
    scale_f = 8.0 / max(size.x, size.y, size.z, 0.001)
    z_min_s = (min_v.z - center.z) * scale_f

    for o in objs:
        o.location = (o.location - center) * scale_f
        o.location.z -= z_min_s
        o.scale = (scale_f, scale_f, scale_f)
        for p in o.data.polygons: p.use_smooth = True

    for m in bpy.data.materials:
        if not m.use_nodes: continue
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
                glass.inputs["Roughness"].default_value = 0.08
            nt.links.new(glass.outputs["BSDF"], out.inputs["Surface"])
        elif "texture.png" in m.name:
            for n in nt.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs["Metallic"].default_value = 0.62
                    n.inputs["Roughness"].default_value = 0.28

    bpy.ops.mesh.primitive_plane_add(size=100.0, location=(0, 0, -0.01))
    floor = bpy.context.active_object
    fmat = bpy.data.materials.new("Floor2"); fmat.use_nodes = True
    fbsdf = fmat.node_tree.nodes.get("Principled BSDF")
    fbsdf.inputs["Base Color"].default_value = (0.038, 0.044, 0.054, 1.0)
    fbsdf.inputs["Roughness"].default_value = 0.38; fbsdf.inputs["Metallic"].default_value = 0.18
    floor.data.materials.append(fmat)

    def add_light(name, loc, target, energy, size_l, col=(1,1,1)):
        ld = bpy.data.lights.new(name, type='AREA')
        ld.energy = energy; ld.size = size_l; ld.color = col
        lo = bpy.data.objects.new(name, ld); scn.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

    add_light("Key",  (4.5, -5.5, 4.8), (0, 0, 0.5), 950.0, 5.5, (1.0, 0.98, 0.95))
    add_light("Fill", (-5.0, -4.0, 3.2), (0, 0, 0.5), 550.0, 6.0, (0.85, 0.92, 1.0))
    add_light("Rim",  (0.0, 5.5, 4.2), (0, 0, 0.5), 780.0, 5.0, (0.95, 0.98, 1.0))

    if cockpit_mode:
        for lx, ly, lz, en in [(0.0, -2.58, 0.68, 2.5), (-0.12, -2.55, 0.65, 1.2), (0.12, -2.55, 0.65, 1.2)]:
            pld = bpy.data.lights.new("PanelLight", type='POINT')
            pld.energy = en; pld.shadow_soft_size = 0.06; pld.color = (1.0, 0.94, 0.86)
            plo = bpy.data.objects.new("PanelLight", pld)
            scn.collection.objects.link(plo); plo.location = (lx, ly, lz)

    cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 50.0; cam_d.clip_start = 0.01
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o); scn.camera = cam_o
    return scn, cam_o, cam_d

def setup_j58_scene():
    scn = init_fast_cycles_1080p(exposure=-0.55)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "f110_engine", "build", "f110_web.glb"))
    objs = [o for o in scn.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    lib = build_clean_alloys()

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.9, -0.82, 0.12))
    cutter = bpy.context.active_object
    cutter.scale = (9.0, 1.64, 2.2)

    CUT_PATTERNS = ("casing_", "flange_", "inlet_case", "inlet_lip",
                    "bypass_inner_wall", "augmentor_liner", "combustor_liner_outer",
                    "nozzle_ext_flaps", "nozzle_seals", "splitter", "mixer")

    rotor_objs = []
    for o in objs:
        nm = o.name.lower()
        for p in o.data.polygons: p.use_smooth = True
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

        if any(pat in nm for pat in CUT_PATTERNS):
            mod = o.modifiers.new("Cutaway", "BOOLEAN")
            mod.operation = "DIFFERENCE"
            mod.solver = "FAST"
            mod.object = cutter
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier="Cutaway")

    bpy.data.objects.remove(cutter, do_unlink=True)

    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.36, radius2=0.0, depth=1.65,
                                    location=(-1.45, 0, 0), rotation=(0, math.radians(-90), 0))
    spike = bpy.context.active_object
    for p in spike.data.polygons: p.use_smooth = True
    spike.data.materials.append(lib["casing_alloy"])

    for ang_deg in [65, 115, 245, 295]:
        ang = math.radians(ang_deg)
        curve_d = bpy.data.curves.new(f"Bleed_{ang_deg}", type='CURVE')
        curve_d.dimensions = '3D'; curve_d.bevel_depth = 0.052; curve_d.bevel_resolution = 8
        sp = curve_d.splines.new('POLY')
        pts = [(0.25, 0.58*math.cos(ang), 0.58*math.sin(ang)),
               (0.45, 0.74*math.cos(ang), 0.74*math.sin(ang)),
               (2.85, 0.74*math.cos(ang), 0.74*math.sin(ang)),
               (3.40, 0.52*math.cos(ang), 0.52*math.sin(ang))]
        sp.points.add(len(pts)-1)
        for idx, pt in enumerate(pts): sp.points[idx].co = (*pt, 1.0)
        co = bpy.data.objects.new(f"Bleed_{ang_deg}", curve_d)
        scn.collection.objects.link(co)
        co.data.materials.append(lib["hot_nickel"])

    bpy.ops.mesh.primitive_plane_add(size=80.0, location=(1.8, 0, -0.82))
    floor = bpy.context.active_object
    fmat = bpy.data.materials.new("Floor"); fmat.use_nodes = True
    fbsdf = fmat.node_tree.nodes.get("Principled BSDF")
    fbsdf.inputs["Base Color"].default_value = (0.032, 0.036, 0.044, 1.0)
    fbsdf.inputs["Roughness"].default_value = 0.42; fbsdf.inputs["Metallic"].default_value = 0.15
    floor.data.materials.append(fmat)

    def area_light(name, loc, rot, energy, size):
        d = bpy.data.lights.new(name, type="AREA")
        d.energy = energy; d.size = size; d.shape = "RECTANGLE"; d.size_y = size * 0.55
        o = bpy.data.objects.new(name, d); o.location = loc; o.rotation_euler = rot
        scn.collection.objects.link(o)

    X_MID = 1.9
    area_light("key",  (X_MID - 3.0, -8.5, 6.5), (math.radians(50), 0, math.radians(-26)), 2900, 9.0)
    area_light("fill", (X_MID + 2.0, 7.5, -2.4), (math.radians(-62), 0, math.radians(152)), 1100, 11.0)
    area_light("rim",  (X_MID + 8.0, 4.0, 4.2),  (math.radians(64), 0, math.radians(116)), 2600, 5.0)
    area_light("bore", (X_MID - 0.4, -4.2, 1.2), (math.radians(74), 0, 0), 1500, 8.0)

    cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 65.0
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o); scn.camera = cam_o
    return scn, cam_o, cam_d, spike, rotor_objs

if SCENE_IDX in (9, 10, 11, 13, 14, 17, 18, 19, 20, 21, 23, 24, 25, 26):
    scn, cam_o, cam_d = setup_blackbird_scene(cockpit_mode=(SCENE_IDX in (18, 19)))
    for f in range(N_FRAMES):
        u = smoothstep(f / float(N_FRAMES - 1))
        if SCENE_IDX == 9:
            cam_d.lens = 68.0
            cam_o.location = (2.1 - 0.6 * u, -4.8 + 0.5 * u, 1.15 + 0.15 * u)
            target = Vector((0.0, -2.65 + 0.25 * u, 0.58))
        elif SCENE_IDX == 10:
            cam_d.lens = 66.0
            cam_o.location = (3.4 - 0.5 * u, -1.6 + 0.9 * u, 1.10 + 0.15 * u)
            target = Vector((1.55, 0.45 + 0.35 * u, 0.55))
        elif SCENE_IDX == 11:
            cam_d.lens = 56.0
            cam_o.location = (-2.8 + 1.2 * u, -3.2 + 1.6 * u, 0.28 + 0.12 * u)
            target = Vector((0.0, -0.4 + 0.6 * u, 0.48))
        elif SCENE_IDX == 13:
            cam_d.lens = 64.0
            cam_o.location = (-3.8 + 0.5 * u, -0.5 + 1.8 * u, 1.85 - 0.20 * u)
            target = Vector((-1.55, 1.2 + 0.6 * u, 0.52))
        elif SCENE_IDX == 14:
            cam_d.lens = 58.0
            cam_o.location = (-1.8 + 3.6 * u, -2.6 + 1.4 * u, 2.85 - 0.25 * u)
            target = Vector((0.0, -0.6 + 0.8 * u, 0.65))
        elif SCENE_IDX == 17:
            cam_d.lens = 62.0
            cam_o.location = (-1.85 + 0.35 * u, -4.6 + 1.1 * u, 0.78 + 0.12 * u)
            target = Vector((-1.15, 0.2 + 0.6 * u, 0.54))
        elif SCENE_IDX == 18:
            cam_d.lens = 26.0
            cam_o.location = (0.06 - 0.04 * u, -2.50 - 0.04 * u, 0.665 - 0.010 * u)
            target = Vector((-0.05, -2.69, 0.612))
        elif SCENE_IDX == 19:
            cam_d.lens = 30.0
            cam_o.location = (-0.06 + 0.05 * u, -2.51 - 0.04 * u, 0.655 + 0.010 * u)
            target = Vector((0.04, -2.69, 0.610))
        elif SCENE_IDX == 20:
            cam_d.lens = 56.0
            cam_o.location = (2.8 - 1.2 * u, -1.8 + 1.8 * u, 0.32 + 0.12 * u)
            target = Vector((0.0, -0.2 + 0.6 * u, 0.48))
        elif SCENE_IDX == 21:
            cam_d.lens = 48.0
            ang = math.radians(-140.0 + 55.0 * u)
            cam_o.location = (5.8 * math.cos(ang), 5.8 * math.sin(ang), 2.4 + 0.5 * u)
            target = Vector((0.0, 0.0, 0.55))
        elif SCENE_IDX == 23:
            cam_d.lens = 66.0
            cam_o.location = (-3.4 + 0.8 * u, 4.2 - 0.8 * u, 1.65 + 0.20 * u)
            target = Vector((-1.35, 2.1, 0.92))
        elif SCENE_IDX == 24:
            cam_d.lens = 52.0
            cam_o.location = (-0.6 + 1.2 * u, 5.8 - 0.9 * u, 0.82 + 0.15 * u)
            target = Vector((0.0, 1.6, 0.58))
        elif SCENE_IDX == 25:
            cam_d.lens = 45.0
            cam_o.location = (-0.4 + 0.8 * u, -0.4 + 0.8 * u, 7.8 - 1.4 * u)
            target = Vector((0.0, 0.0, 0.45))
        else:
            cam_d.lens = 48.0
            cam_o.location = (-3.6 - 2.2 * u, -4.4 - 2.2 * u, 1.15 + 1.05 * u)
            target = Vector((0.0, -0.3 + 0.3 * u, 0.52))

        cam_o.rotation_euler = (target - cam_o.location).to_track_quat('-Z', 'Y').to_euler()
        scn.render.filepath = os.path.join(OUT_DIR, f"s{SCENE_IDX}_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

elif SCENE_IDX in (12, 15, 16, 22):
    scn, cam_o, cam_d, spike, rotor_objs = setup_j58_scene()
    for f in range(N_FRAMES):
        u = smoothstep(f / float(N_FRAMES - 1))
        for ro, sdir in rotor_objs:
            ro.rotation_euler.x = f * 0.024 * sdir
        if SCENE_IDX == 12:
            cam_d.lens = 78.0
            cam_o.location = (-2.2 + 0.8 * u, -5.2 + 0.4 * u, 1.35 - 0.15 * u)
            target = Vector((0.15 + 0.45 * u, 0.0, 0.02))
        elif SCENE_IDX == 15:
            cam_d.lens = 76.0
            cam_o.location = (4.6 - 0.8 * u, -5.2 + 0.4 * u, 1.40 - 0.15 * u)
            target = Vector((2.65 - 0.35 * u, 0.0, 0.02))
        elif SCENE_IDX == 16:
            cam_d.lens = 62.0
            cam_o.location = (0.6 + 1.8 * u, -4.6 + 0.5 * u, 3.8 - 0.3 * u)
            target = Vector((1.65 + 0.35 * u, 0.0, 0.25))
        else:
            cam_d.lens = 56.0
            cam_o.location = (4.8 - 2.6 * u, -7.8 + 0.8 * u, 3.2 - 0.5 * u)
            target = Vector((1.75, 0.0, 0.05))

        cam_o.rotation_euler = (target - cam_o.location).to_track_quat('-Z', 'Y').to_euler()
        scn.render.filepath = os.path.join(OUT_DIR, f"s{SCENE_IDX}_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
