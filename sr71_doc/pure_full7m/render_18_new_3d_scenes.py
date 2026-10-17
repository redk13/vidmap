import bpy, os, sys, math
from mathutils import Vector, Euler

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
    shard_id = int(args[0])
    out_dir  = os.path.abspath(args[1])
else:
    shard_id = 0
    out_dir  = "/var/tmp/cad_out"

os.makedirs(out_dir, exist_ok=True)

# Shard 0..17 renders Scene s9..s26 (18 brand-new unique 1080p 3D Studio sequences, 60 frames each)
scene_id = 9 + shard_id
N_FRAMES = 60

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SR71_GLB   = os.path.join(REPO_ROOT, "vidmap_ht", "models", "Blackbird.glb")
J58_GLB    = os.path.join(REPO_ROOT, "sr71_doc", "f110_engine", "f110_web.glb")
FONT_PATH  = os.path.join(REPO_ROOT, "sr71_doc", "fonts", "Oswald-Bold.ttf")

def init_cycles_fast_1080p():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 6
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.05
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = 'OPENIMAGEDENOISE'
    scn.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scn.cycles.denoising_prefilter = 'FAST'
    scn.cycles.max_bounces = 1
    scn.cycles.diffuse_bounces = 1
    scn.cycles.glossy_bounces = 1
    scn.cycles.transmission_bounces = 1
    scn.cycles.transparent_max_bounces = 1
    scn.render.use_persistent_data = True
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = 'PNG'
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - Medium High Contrast'

    world = bpy.data.worlds.new("StudioWorld")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.010, 0.013, 0.018, 1.0)
    bg.inputs[1].default_value = 0.70

    bpy.ops.mesh.primitive_plane_add(size=240.0, location=(0, 0, 0))
    fl = bpy.context.active_object
    m_fl = bpy.data.materials.new("FloorMat")
    m_fl.use_nodes = True
    b_fl = m_fl.node_tree.nodes.get("Principled BSDF")
    b_fl.inputs["Base Color"].default_value = (0.015, 0.018, 0.024, 1.0)
    b_fl.inputs["Metallic"].default_value = 0.15
    b_fl.inputs["Roughness"].default_value = 0.28
    fl.data.materials.append(m_fl)

    def add_area(name, loc, rot_deg, energy, size, col=(1.0, 0.98, 0.95)):
        ld = bpy.data.lights.new(name, type='AREA')
        ld.energy = energy
        ld.size = size
        ld.color = col
        lo = bpy.data.objects.new(name, ld)
        scn.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = tuple(math.radians(a) for a in rot_deg)

    add_area("KeyLight",  (0, -5, 11), (22, 0, 0),   2400.0, 11.0, (1.0, 0.98, 0.95))
    add_area("RimLight",  (-8, 8, 7),  (-32, -28, 0),1600.0, 8.0,  (0.75, 0.88, 1.0))
    add_area("FillLight", (8, -7, 5),  (42, 28, 0),  1100.0, 9.0,  (1.0, 0.93, 0.85))
    return scn

def load_sr71_model(scn, bank_deg=0.0):
    bpy.ops.import_scene.gltf(filepath=SR71_GLB)
    meshes = [o for o in scn.objects if o.type == 'MESH' and o.name != "Plane"]
    b_min = Vector((1e9, 1e9, 1e9))
    b_max = Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            b_min.x = min(b_min.x, w.x); b_min.y = min(b_min.y, w.y); b_min.z = min(b_min.z, w.z)
            b_max.x = max(b_max.x, w.x); b_max.y = max(b_max.y, w.y); b_max.z = max(b_max.z, w.z)
    span = max(b_max - b_min)
    sc = 15.0 / span
    cx, cy = (b_min.x + b_max.x) * 0.5, (b_min.y + b_max.y) * 0.5
    p = bpy.data.objects.new("SR71_Root", None)
    scn.collection.objects.link(p)
    for o in scn.objects:
        if o.parent is None and o not in (p,) and o.type != 'LIGHT' and o.name != "Plane":
            o.parent = p
    p.scale = (sc, sc, sc)
    p.location = (-cx * sc, -cy * sc, -b_min.z * sc + 0.05 + (1.4 if abs(bank_deg) > 1.0 else 0.0))
    if abs(bank_deg) > 0.1:
        p.rotation_euler = (0.0, math.radians(bank_deg), 0.0)
    return p

def load_j58_model(scn, cutaway=True):
    import sys as _sys
    _sys.path.insert(0, os.path.join(REPO_ROOT, "sr71_doc", "f110_engine"))
    import build_f110 as bf
    bf._add_wear = lambda *a, **kw: None
    mats = bf.build_materials()
    for m_obj in mats.values():
        if not m_obj or not m_obj.use_nodes:
            continue
        for nd in m_obj.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                r_in = nd.inputs.get("Roughness")
                if r_in and not r_in.is_linked and r_in.default_value < 0.22:
                    r_in.default_value = 0.22
    col = bpy.data.collections.new("F110")
    scn.collection.children.link(col)
    def _fast_bez(col, name, pts, radius, mat, bev_res=6):
        cd = bpy.data.curves.new(name, type='CURVE')
        cd.dimensions = '3D'; cd.bevel_depth = radius; cd.bevel_resolution = bev_res
        sp = cd.splines.new('BEZIER')
        sp.bezier_points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            bp = sp.bezier_points[i]; bp.co = p
            bp.handle_left_type = 'AUTO'; bp.handle_right_type = 'AUTO'
        ob = bpy.data.objects.new(name, cd); col.objects.link(ob)
        for s in cd.splines: s.use_smooth = True
        if mat: ob.data.materials.append(mat)
        return ob
    bf.bezier_tube = _fast_bez
    bf.build_inlet_section(col, mats)
    bf.build_fan_stage(col, mats)
    bf.build_hpc_stage(col, mats)
    bf.build_combustor(col, mats)
    bf.build_turbine(col, mats)
    bf.build_augmentor(col, mats)
    bf.build_nozzle(col, mats)
    bf.build_external_dressings(col, mats)
    if cutaway:
        bf.apply_section_cut(col, mats)
        cutter = bpy.data.objects.get("__section_cutter")
        if cutter:
            for o in list(col.objects):
                if o.type == 'MESH' and "Cutaway" in o.modifiers:
                    bpy.context.view_layer.objects.active = o
                    try:
                        bpy.ops.object.modifier_apply(modifier="Cutaway")
                    except Exception:
                        o.modifiers.remove(o.modifiers["Cutaway"])
            bpy.data.objects.remove(cutter, do_unlink=True)
    for o in col.objects:
        o.location.z += 1.25
    return col

def build_3d_cockpit(scn):
    def make_mat(name, col, met=0.1, rough=0.45, emit=None, emit_s=0.0):
        m = bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (*col, 1.0)
        b.inputs["Metallic"].default_value = met
        b.inputs["Roughness"].default_value = rough
        if emit:
            b.inputs["Emission Color"].default_value = (*emit, 1.0)
            b.inputs["Emission Strength"].default_value = emit_s
        return m

    m_panel = make_mat("PanelGrey", (0.14, 0.15, 0.16), 0.15, 0.58)
    m_dark  = make_mat("BezelBlk",  (0.03, 0.035, 0.04), 0.45, 0.32)
    m_dial  = make_mat("DialFace",  (0.05, 0.055, 0.065), 0.1, 0.4)
    m_white = make_mat("TickWhite", (0.95, 0.96, 0.98), 0.0, 0.2, (0.95, 0.96, 0.98), 1.8)
    m_amber = make_mat("NeedleAmb", (1.0, 0.65, 0.15),  0.0, 0.2, (1.0, 0.65, 0.15), 2.5)
    m_green = make_mat("RadarGrn",  (0.15, 0.95, 0.45), 0.0, 0.2, (0.15, 0.95, 0.45), 2.2)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.0))
    pnl = bpy.context.active_object; pnl.scale = (4.2, 0.15, 2.6); pnl.data.materials.append(m_panel)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.95, -0.55, 1.25))
    lcon = bpy.context.active_object; lcon.scale = (0.65, 1.2, 0.45); lcon.data.materials.append(m_panel)
    for tx in (-2.08, -1.82):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.45, location=(tx, -0.45, 1.62))
        st = bpy.context.active_object; st.rotation_euler = (math.radians(-22), 0, 0); st.data.materials.append(m_dark)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.14, location=(tx, -0.36, 1.82))
        hd = bpy.context.active_object; hd.rotation_euler = (0, math.radians(90), 0); hd.data.materials.append(m_white if tx < -1.9 else m_amber)

    gauges = [
        (-0.55, 2.25, 0.23, "MACH", "3.22", 140),
        ( 0.55, 2.28, 0.22, "ALT",  "85000", 110),
        (-0.55, 1.72, 0.22, "CLIMB","0.0",   90),
        ( 0.55, 1.78, 0.22, "KEAS", "410",   125),
        ( 0.92, 1.68, 0.15, "EGT L","840",   135),
        ( 1.24, 1.68, 0.15, "EGT R","842",   138),
        ( 1.68, 1.72, 0.22, "JP-7", "48500", 85),
    ]
    needles = []
    for (gx, gz, gr, lbl, sub, ang) in gauges:
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=gr, depth=0.06, location=(gx, -0.09, gz))
        bz = bpy.context.active_object; bz.rotation_euler = (math.radians(90), 0, 0); bz.data.materials.append(m_dark)
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=gr*0.88, depth=0.05, location=(gx, -0.10, gz))
        fc = bpy.context.active_object; fc.rotation_euler = (math.radians(90), 0, 0); fc.data.materials.append(m_dial)
        for t_i in range(12):
            ta = math.radians(t_i * 30)
            tx = gx + math.sin(ta) * (gr * 0.74); tz = gz + math.cos(ta) * (gr * 0.74)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(tx, -0.128, tz))
            tk = bpy.context.active_object; tk.scale = (0.008, 0.005, gr * 0.11); tk.rotation_euler = (0, -ta, 0); tk.data.materials.append(m_white)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gx, -0.132, gz))
        nd = bpy.context.active_object; nd.scale = (0.010, 0.005, gr * 0.68); nd.rotation_euler = (0, -math.radians(ang), 0)
        nd.data.materials.append(m_amber if "EGT" in lbl else m_white)
        needles.append((nd, ang))

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.10, 1.18))
    rd = bpy.context.active_object; rd.scale = (0.58, 0.06, 0.58); rd.data.materials.append(m_dark)
    for r_ring in (0.08, 0.16, 0.23):
        bpy.ops.mesh.primitive_torus_add(major_radius=r_ring, minor_radius=0.004, location=(0.0, -0.132, 1.18), rotation=(math.radians(90), 0, 0))
        rg = bpy.context.active_object; rg.data.materials.append(m_green)
    return needles

scn = init_cycles_fast_1080p()
cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 52.0
cam = bpy.data.objects.new("Cam", cam_d)
scn.collection.objects.link(cam)
scn.camera = cam
tgt = bpy.data.objects.new("Target", None)
scn.collection.objects.link(tgt)
ttc = cam.constraints.new(type='TRACK_TO')
ttc.target = tgt
ttc.track_axis = 'TRACK_NEGATIVE_Z'
ttc.up_axis = 'UP_Y'

j58_col = None
cockpit_needles = None

if scene_id in (9, 10, 11, 13, 14, 17, 20, 21, 23, 24, 25, 26):
    bank = 26.0 if scene_id == 21 else 0.0
    load_sr71_model(scn, bank_deg=bank)
elif scene_id in (12, 15, 16, 22):
    j58_col = load_j58_model(scn, cutaway=(scene_id != 22))
elif scene_id in (18, 19):
    cockpit_needles = build_3d_cockpit(scn)

for f in range(N_FRAMES):
    u = f / float(N_FRAMES - 1)
    t = 0.5 - 0.5 * math.cos(math.pi * u)

    if scene_id == 9:
        cam_d.lens = 68.0
        cam.location = (-3.8 + 0.8 * t, -5.2 + 0.6 * t, 1.45 + 0.15 * t)
        tgt.location = (0.0, -3.4 + 0.4 * t, 0.95)
    elif scene_id == 10:
        cam_d.lens = 65.0
        cam.location = (4.6 - 0.5 * t, -2.2 + 1.1 * t, 1.65 + 0.15 * t)
        tgt.location = (2.1, 0.8 + 0.4 * t, 1.05)
    elif scene_id == 11:
        cam_d.lens = 58.0
        cam.location = (-3.6 + 1.2 * t, -2.4 + 1.4 * t, 0.48 + 0.12 * t)
        tgt.location = (0.0, -0.5 + 0.5 * t, 0.62)
    elif scene_id == 12:
        cam_d.lens = 68.0
        cam.location = (-1.65 + 0.45 * t, -2.15 + 0.25 * t, 1.45 + 0.10 * t)
        tgt.location = (-0.95 + 0.25 * t, 0.0, 1.25)
    elif scene_id == 13:
        cam_d.lens = 64.0
        cam.location = (-5.2 + 0.6 * t, 0.5 + 1.8 * t, 2.35 - 0.20 * t)
        tgt.location = (-2.2, 2.0 + 0.8 * t, 0.95)
    elif scene_id == 14:
        cam_d.lens = 60.0
        cam.location = (-2.4 + 4.8 * t, -2.8 + 1.2 * t, 3.6 - 0.3 * t)
        tgt.location = (0.0, -0.6 + 0.8 * t, 1.22)
    elif scene_id == 15:
        cam_d.lens = 66.0
        cam.location = (1.65 - 0.45 * t, -2.10 + 0.25 * t, 1.48 - 0.08 * t)
        tgt.location = (0.95 - 0.20 * t, 0.0, 1.25)
    elif scene_id == 16:
        cam_d.lens = 58.0
        cam.location = (-0.8 + 1.6 * t, -1.9 + 0.3 * t, 2.85 - 0.15 * t)
        tgt.location = (-0.1 + 0.3 * t, 0.0, 1.32)
    elif scene_id == 17:
        cam_d.lens = 62.0
        cam.location = (-2.2 + 0.4 * t, -6.2 + 1.2 * t, 1.15 + 0.15 * t)
        tgt.location = (-1.4, -0.5 + 0.8 * t, 1.02)
    elif scene_id == 18:
        cam_d.lens = 55.0
        cam.location = (-0.95 - 0.25 * t, -1.75 + 0.25 * t, 2.05 - 0.10 * t)
        tgt.location = (-1.65, -0.35, 1.65)
    elif scene_id == 19:
        cam_d.lens = 58.0
        cam.location = (0.45 - 0.90 * t, -1.65 + 0.22 * t, 1.48 + 0.08 * t)
        tgt.location = (0.0, -0.10, 1.32)
    elif scene_id == 20:
        cam_d.lens = 56.0
        cam.location = (3.8 - 1.2 * t, -1.8 + 1.6 * t, 0.55 + 0.15 * t)
        tgt.location = (0.0, 0.2 + 0.6 * t, 0.72)
    elif scene_id == 21:
        cam_d.lens = 48.0
        ang = math.radians(-50.0 + 45.0 * t)
        cam.location = (9.8 * math.cos(ang), 9.8 * math.sin(ang), 3.4 + 0.6 * t)
        tgt.location = (0.0, 0.0, 1.95)
    elif scene_id == 22:
        cam_d.lens = 54.0
        ang = math.radians(-125.0 + 70.0 * t)
        cam.location = (3.8 * math.cos(ang), 3.8 * math.sin(ang), 1.85 + 0.25 * math.sin(math.pi * t))
        tgt.location = (0.05, 0.0, 1.25)
    elif scene_id == 23:
        cam_d.lens = 65.0
        cam.location = (-4.5 + 0.8 * t, 4.8 - 0.9 * t, 2.45 + 0.25 * t)
        tgt.location = (-1.8, 3.2, 1.85)
    elif scene_id == 24:
        cam_d.lens = 52.0
        cam.location = (-0.8 + 1.6 * t, 8.6 - 1.4 * t, 1.28 + 0.20 * t)
        tgt.location = (0.0, 2.6, 1.12)
    elif scene_id == 25:
        cam_d.lens = 45.0
        cam.location = (-0.6 + 1.2 * t, -0.4 + 0.8 * t, 12.8 - 2.2 * t)
        tgt.location = (0.0, 0.0, 0.85)
    elif scene_id == 26:
        cam_d.lens = 48.0
        cam.location = (-5.5 - 3.5 * t, -6.2 - 3.2 * t, 1.65 + 1.45 * t)
        tgt.location = (0.0, -0.5 + 0.5 * t, 1.05)

    if j58_col is not None:
        rot = f * 0.045
        for o in j58_col.objects:
            if any(k in o.name for k in ("Fan", "HPC", "HPT", "LPT", "Spinner", "Disk", "Blades")):
                o.rotation_euler.x = rot
    if cockpit_needles is not None:
        for idx, (nd, base_a) in enumerate(cockpit_needles):
            nd.rotation_euler = (0, -math.radians(base_a + 5.0 * math.sin(u * math.pi + idx)), 0)

    scn.render.filepath = os.path.join(out_dir, f"s{scene_id}_{f:04d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[Shard {shard_id}] Rendered s{scene_id}_{f:04d}.png", flush=True)
