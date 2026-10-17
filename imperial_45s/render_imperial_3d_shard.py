import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
else:
    args = ["0"]

SHARD_ID = int(args[0])

# 20 Parallel 3D Shards (45 frames each = 900 3D frames total across the 48.0s timeline)
SHARD_3D_RANGES = [
    (0,   45),   # Shard 0:  Scene 0 (0.0s - 1.5s)
    (45,  90),   # Shard 1:  Scene 0 (1.5s - 3.0s)
    (90,  135),  # Shard 2:  Scene 0 (3.0s - 4.5s)
    (135, 180),  # Shard 3:  Scene 0 (4.5s - 6.0s)
    (180, 225),  # Shard 4:  Scene 1 (6.0s - 7.5s)
    (225, 270),  # Shard 5:  Scene 1 (7.5s - 9.0s)
    (270, 315),  # Shard 6:  Scene 1 (9.0s - 10.5s)
    (315, 360),  # Shard 7:  Scene 1 (10.5s - 12.0s)
    (540, 585),  # Shard 8:  Scene 3A (18.0s - 19.5s)
    (585, 630),  # Shard 9:  Scene 3A (19.5s - 21.0s)
    (900, 945),  # Shard 10: Scene 5 (30.0s - 31.5s)
    (945, 990),  # Shard 11: Scene 5 (31.5s - 33.0s)
    (990, 1035), # Shard 12: Scene 5 (33.0s - 34.5s)
    (1035, 1080),# Shard 13: Scene 5 (34.5s - 36.0s)
    (1170, 1215),# Shard 14: Scene 6B (39.0s - 40.5s)
    (1215, 1260),# Shard 15: Scene 6B (40.5s - 42.0s)
    (1260, 1305),# Shard 16: Scene 7 (42.0s - 43.5s)
    (1305, 1350),# Shard 17: Scene 7 (43.5s - 45.0s)
    (1350, 1395),# Shard 18: Scene 7 (45.0s - 46.5s)
    (1395, 1440),# Shard 19: Scene 7 (46.5s - 48.0s)
]

START_FRAME, END_FRAME = SHARD_3D_RANGES[SHARD_ID]

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(ROOT, "assets")
FONT_DIR = os.path.join(ROOT, "fonts")
OUT_DIR = f"/tmp/imperial_shard_{SHARD_ID:02d}"
os.makedirs(OUT_DIR, exist_ok=True)

def init_cycles_1080p(samples=16, bg_rgb=(0.008, 0.009, 0.012), exposure=-0.35):
    """Proven fast Cycles 1080p setup (16 samples + FAST OIDN prefilter + 2 bounces + persistent BVH)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 10
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = 'OPENIMAGEDENOISE'
    scn.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    scn.cycles.denoising_prefilter = 'FAST'
    scn.cycles.max_bounces = 1
    scn.cycles.diffuse_bounces = 0
    scn.cycles.glossy_bounces = 1
    scn.cycles.transparent_max_bounces = 2
    scn.cycles.sample_clamp_direct = 6.0
    scn.cycles.sample_clamp_indirect = 3.0
    scn.render.use_persistent_data = True
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.resolution_percentage = 100
    scn.render.fps = 30
    scn.render.image_settings.file_format = 'PNG'
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - Medium High Contrast'
    scn.view_settings.exposure = exposure

    world = bpy.data.worlds.new("World")
    scn.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (bg_rgb[0], bg_rgb[1], bg_rgb[2], 1.0)
        bg.inputs[1].default_value = 1.0
    return scn

def make_pbr_mat(name, base_rgb, roughness=0.4, metallic=0.0, emission_rgb=None, emission_str=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (base_rgb[0], base_rgb[1], base_rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission_rgb and emission_str > 0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (emission_rgb[0], emission_rgb[1], emission_rgb[2], 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_str
    return mat

def make_checkered_marble_mat():
    mat = bpy.data.materials.new("CuriaCheckeredMarble")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.16

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    checker = nt.nodes.new("ShaderNodeTexChecker")
    checker.inputs["Scale"].default_value = 14.0
    checker.inputs["Color1"].default_value = (0.48, 0.36, 0.18, 1.0)
    checker.inputs["Color2"].default_value = (0.06, 0.07, 0.09, 1.0)
    nt.links.new(tex_coord.outputs["Generated"], checker.inputs["Vector"])
    nt.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def load_vertex_color_glb(glb_name, target_height=1.80, location=(0, 0, 0), rot_z_deg=0.0, decimate_ratio=1.0):
    path = os.path.join(ASSET_DIR, glb_name)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new_objs = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new_objs if o.type == 'MESH']
    if not meshes:
        return None

    bpy.ops.object.select_all(action='DESELECT')
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    for o in new_objs:
        if o != obj and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if decimate_ratio < 0.99:
        mod = obj.modifiers.new("FastDec", 'DECIMATE')
        mod.ratio = decimate_ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.shade_smooth()

    mat = bpy.data.materials.new(f"VC_{glb_name}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.62

    attr_node = nt.nodes.new("ShaderNodeVertexColor")
    if obj.data.color_attributes:
        attr_node.layer_name = obj.data.color_attributes[0].name
    gam_node = nt.nodes.new("ShaderNodeGamma")
    gam_node.inputs["Gamma"].default_value = 1.85
    nt.links.new(attr_node.outputs["Color"], gam_node.inputs["Color"])
    nt.links.new(gam_node.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
         nt.links.new(gam_node.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 0.18
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    zs = [v.z for v in verts]
    span_z = max(0.001, max(zs) - min(zs))
    s = target_height / span_z
    obj.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)

    verts2 = [v.co for v in obj.data.vertices]
    cx = 0.5 * (min(v.x for v in verts2) + max(v.x for v in verts2))
    cy = 0.5 * (min(v.y for v in verts2) + max(v.y for v in verts2))
    min_z = min(v.z for v in verts2)
    for v in obj.data.vertices:
        v.co.x -= cx
        v.co.y -= cy
        v.co.z -= min_z
    obj.data.update()

    obj.location = location
    obj.rotation_euler = (0.0, 0.0, math.radians(rot_z_deg))
    return obj

def append_blend_meshes(blend_name, target_size=1.8, location=(0, 0, 0), rot_euler=(0, 0, 0)):
    bpath = os.path.join(ASSET_DIR, blend_name)
    with bpy.data.libraries.load(bpath, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects
    meshes = []
    for o in data_to.objects:
        if o is not None and o.type == 'MESH':
            bpy.context.collection.objects.link(o)
            meshes.append(o)
    if not meshes:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    verts = [v.co for v in obj.data.vertices]
    span = max(
        max(v.x for v in verts) - min(v.x for v in verts),
        max(v.y for v in verts) - min(v.y for v in verts),
        max(v.z for v in verts) - min(v.z for v in verts),
        0.001
    )
    s = target_size / span
    obj.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    verts2 = [v.co for v in obj.data.vertices]
    cx = 0.5 * (min(v.x for v in verts2) + max(v.x for v in verts2))
    cy = 0.5 * (min(v.y for v in verts2) + max(v.y for v in verts2))
    min_z = min(v.z for v in verts2)
    for v in obj.data.vertices:
        v.co.x -= cx
        v.co.y -= cy
        v.co.z -= min_z
    obj.data.update()
    obj.location = location
    obj.rotation_euler = rot_euler
    return obj

def add_area_light(name, loc, energy, size, color=(1.0, 0.95, 0.88), target=(0, 0, 1.0)):
    ld = bpy.data.lights.new(name, type='AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = loc
    direction = Vector(target) - Vector(loc)
    lo.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return lo

def build_curia_interior_set(include_standing_caesar=True, include_throne_caesar=False, crime_scene=False):
    mat_checker = make_checkered_marble_mat()
    mat_trav = make_pbr_mat("Travertine", (0.28, 0.25, 0.21), roughness=0.36)
    mat_wood = make_pbr_mat("WalnutBench", (0.16, 0.10, 0.06), roughness=0.42)
    mat_col = make_pbr_mat("FlutedMarble", (0.34, 0.31, 0.27), roughness=0.32)
    mat_wall = make_pbr_mat("CuriaWall", (0.24, 0.22, 0.20), roughness=0.55)
    mat_gold = make_pbr_mat("RomanGold", (0.85, 0.66, 0.22), roughness=0.22, metallic=0.88)

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0.0))
    aisle = bpy.context.active_object
    aisle.scale = (3.6, 16.0, 1.0)
    aisle.data.materials.append(mat_checker)

    bpy.ops.mesh.primitive_plane_add(size=22.0, location=(0, 0, -0.01))
    flr = bpy.context.active_object
    flr.data.materials.append(mat_trav)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 5.5, 0.28))
    trib = bpy.context.active_object
    trib.scale = (9.5, 3.6, 0.56)
    trib.data.materials.append(mat_trav)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 7.6, 4.5))
    bwall = bpy.context.active_object
    bwall.scale = (16.0, 0.5, 9.0)
    bwall.data.materials.append(mat_wall)

    for cx in [-5.6, -3.4, -1.6, 1.6, 3.4, 5.6]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.38, depth=7.5, location=(cx, 6.8, 3.75))
        col_o = bpy.context.active_object
        col_o.data.materials.append(mat_col)
        bpy.ops.mesh.primitive_cube_add(size=0.95, location=(cx, 6.8, 0.35))
        base_o = bpy.context.active_object
        base_o.data.materials.append(mat_trav)

    for side in (-1, 1):
        for tier in range(3):
            bx = side * (2.45 + tier * 0.92)
            bz = 0.22 + tier * 0.26
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, -0.5, bz * 0.5))
            step_o = bpy.context.active_object
            step_o.scale = (0.88, 10.5, bz)
            step_o.data.materials.append(mat_trav)
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, -0.5, bz + 0.22))
            bench_o = bpy.context.active_object
            bench_o.scale = (0.55, 9.8, 0.44)
            bench_o.data.materials.append(mat_wood)

    sen_seat = load_vertex_color_glb("senator_seated_clean.glb", target_height=1.42, location=(0, 0, -20), decimate_ratio=0.25)
    sen_stand = load_vertex_color_glb("senator_standing_clean.glb", target_height=1.76, location=(0, 0, -20), decimate_ratio=0.25)
    sen_seat.hide_render = True
    sen_stand.hide_render = True

    def place_instance(proto, loc, rot_z_deg, scale_mult=1.0):
        inst = proto.copy()
        inst.data = proto.data
        inst.hide_render = False
        bpy.context.collection.objects.link(inst)
        inst.location = loc
        inst.rotation_euler = (0.0, 0.0, math.radians(rot_z_deg))
        inst.scale = (scale_mult, scale_mult, scale_mult)
        return inst

    if not crime_scene:
        for side in (-1, 1):
            face_yaw = 90.0 if side == -1 else -90.0
            for tier in range(3):
                bx = side * (2.42 + tier * 0.92)
                bz = 0.20 + tier * 0.26
                for y_pos in [-4.2, -2.7, -1.2, 0.3, 1.8, 3.2]:
                    yaw_jit = ((int(abs(y_pos * 10) + tier * 7) % 15) - 7.5)
                    if (tier == 0 and y_pos in (-1.2, 1.8)):
                        place_instance(sen_stand, (bx - side * 0.35, y_pos, bz), face_yaw + yaw_jit)
                    else:
                        place_instance(sen_seat, (bx, y_pos, bz), face_yaw + yaw_jit)

    if include_standing_caesar:
        load_vertex_color_glb("caesar_standing_clean.glb", target_height=1.86, location=(0.0, 1.2, 0.0), rot_z_deg=0.0, decimate_ratio=0.65)

    if include_throne_caesar:
        load_vertex_color_glb("caesar_throne_clean.glb", target_height=1.68, location=(-1.4, 4.4, 0.56), rot_z_deg=-25.0, decimate_ratio=0.65)
        for lx, ly, yaw in [(-3.0, 4.8, -35), (-2.3, 5.2, -25), (-1.5, 5.5, -15), (-3.5, 4.1, -45)]:
            place_instance(sen_stand, (lx, ly, 0.56), yaw)
        for lx, ly, yaw in [(-0.1, 4.9, 10), (0.6, 4.6, 20), (1.3, 5.0, 15), (0.2, 5.5, 5)]:
            place_instance(sen_stand, (lx, ly, 0.56), yaw)

    if crime_scene:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.4, 1.25))
        ped = bpy.context.active_object
        ped.scale = (1.35, 1.35, 1.40)
        ped.data.materials.append(mat_trav)
        pompey_st = load_vertex_color_glb("senator_standing_clean.glb", target_height=2.45, location=(0.0, 5.4, 1.95), rot_z_deg=0.0, decimate_ratio=0.5)
        pompey_st.data.materials.clear()
        pompey_st.data.materials.append(mat_col)

        mat_blood = make_pbr_mat("BloodPool", (0.22, 0.004, 0.006), roughness=0.04, emission_rgb=(0.25, 0.005, 0.008), emission_str=0.35)
        for bx, by, rx, ry in [(0.0, 2.8, 1.35, 1.05), (0.55, 2.4, 0.65, 0.52), (-0.6, 3.1, 0.58, 0.48), (1.4, 1.8, 0.18, 0.12), (1.8, 1.2, 0.16, 0.11)]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1.0, depth=0.012, location=(bx, by, 0.008))
            bp = bpy.context.active_object
            bp.scale = (rx, ry, 1.0)
            bp.data.materials.append(mat_blood)

        load_vertex_color_glb("caesar_fallen_clean.glb", target_height=0.72, location=(0.0, 2.8, 0.01), rot_z_deg=18.0, decimate_ratio=0.55)

        bpy.ops.mesh.primitive_cube_add(size=0.65, location=(1.35, 3.65, 0.32), rotation=(0.4, 1.1, 0.5))
        chair_o = bpy.context.active_object
        chair_o.data.materials.append(mat_gold)

        ring_pts = [(-2.1, 3.6, -60), (-2.3, 2.2, -85), (-1.8, 1.0, -120), (-0.7, 0.6, -155), (0.8, 0.7, 155), (1.9, 1.3, 120), (2.3, 2.6, 85), (2.0, 3.9, 55)]
        for rx, ry, yaw in ring_pts:
            place_instance(sen_stand, (rx, ry, 0.0), yaw)

    add_area_light("SunKey", (-4.5, -3.5, 7.2), 210.0, 3.5, (1.0, 0.92, 0.78), (0.0, 2.0, 0.8))
    add_area_light("CoolFill", (5.5, -2.0, 5.5), 55.0, 4.5, (0.72, 0.82, 1.0), (0.0, 2.0, 1.0))
    add_area_light("TribunalSpot", (0.0, 1.5, 6.8), 125.0, 2.8, (1.0, 0.95, 0.86), (0.0, 4.5, 0.8))


def build_scene1_pompey_complex_cutaway():
    mat_stone = make_pbr_mat("PorticoStone", (0.32, 0.29, 0.24), roughness=0.38)
    mat_roof = make_pbr_mat("TerracottaRoof", (0.52, 0.26, 0.18), roughness=0.48)
    mat_grass = make_pbr_mat("GardenGrass", (0.14, 0.28, 0.14), roughness=0.65)
    mat_city = make_pbr_mat("DarkCityBlocks", (0.10, 0.11, 0.14), roughness=0.55)
    mat_white_emit = make_pbr_mat("White3DText", (0.98, 0.98, 1.0), roughness=0.2, emission_rgb=(0.98, 0.98, 1.0), emission_str=1.6)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.35))
    plat = bpy.context.active_object
    plat.scale = (18.0, 11.0, 0.7)
    plat.data.materials.append(mat_stone)

    for gx in [-3.8, 0.2]:
        for gy in [-1.8, 1.8]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gx, gy, 0.04))
            g = bpy.context.active_object
            g.scale = (3.2, 2.4, 0.08)
            g.data.materials.append(mat_grass)

    for side_y in (-4.4, 4.4):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.5, side_y, 1.35))
        r = bpy.context.active_object
        r.scale = (13.0, 1.4, 0.25)
        r.data.materials.append(mat_roof)
        for cx in [x * 0.95 for x in range(-8, 6)]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.11, depth=1.25, location=(cx, side_y - (0.55 if side_y > 0 else -0.55), 0.62))
            c = bpy.context.active_object
            c.data.materials.append(mat_stone)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.4, 0.0, 1.45))
    curia = bpy.context.active_object
    curia.scale = (3.4, 4.2, 2.9)
    curia.data.materials.append(mat_stone)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.4, 0.0, 3.05))
    croof = bpy.context.active_object
    croof.scale = (3.6, 4.4, 0.35)
    croof.data.materials.append(mat_roof)

    for bx, by, sx, sy, sz in [
        (-4.0, -7.2, 2.2, 1.8, 1.1), (-1.2, -7.4, 2.4, 2.0, 1.4), (1.8, -7.1, 2.0, 1.7, 0.9), (4.6, -7.3, 2.5, 1.9, 1.3),
        (-4.2, 7.2, 2.3, 1.9, 1.2), (-1.0, 7.3, 2.5, 1.8, 1.5), (2.2, 7.1, 2.1, 1.8, 1.0), (5.0, 7.4, 2.4, 2.0, 1.3)
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, sz * 0.5 - 0.3))
        b = bpy.context.active_object
        b.scale = (sx, sy, sz)
        b.data.materials.append(mat_city)

    font_p = os.path.join(FONT_DIR, "Montserrat-Bold.ttf")
    f_obj = bpy.data.fonts.load(font_p) if os.path.exists(font_p) else None

    def make_3d_text(txt, size, extrude, loc, rot_euler):
        cu = bpy.data.curves.new(name=f"Txt_{txt}", type='FONT')
        cu.body = txt
        cu.size = size
        cu.extrude = extrude
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        if f_obj:
            cu.font = f_obj
        to = bpy.data.objects.new(f"Txt_{txt}", cu)
        bpy.context.collection.objects.link(to)
        to.location = loc
        to.rotation_euler = rot_euler
        to.data.materials.append(mat_white_emit)
        return to

    make_3d_text("CURIA", 0.95, 0.08, (6.4, 0.0, 3.32), (0.0, 0.0, math.radians(-90)))
    make_3d_text("PORTICO OF POMPEY", 0.68, 0.05, (-1.8, 0.0, 0.14), (0.0, 0.0, 0.0))
    make_3d_text("GLADIATORS", 0.82, 0.07, (-6.2, 0.0, 1.55), (math.radians(35), 0.0, math.radians(-25)))

    for i in range(14):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.11, location=(-5.0 + i * 0.72, 0.0, 0.12))
        dot = bpy.context.active_object
        dot.data.materials.append(mat_white_emit)

    add_area_light("ComplexKey", (-8.0, -9.0, 12.0), 320.0, 5.0, (1.0, 0.93, 0.82), (0, 0, 0))
    add_area_light("ComplexRim", (9.0, 8.0, 9.0), 110.0, 4.5, (0.55, 0.72, 1.0), (0, 0, 0))


def build_scene3a_sliced_marble_bust():
    bust = append_blend_meshes("marble_bust_01.blend", target_size=2.25, location=(0.0, 0.0, 0.35), rot_euler=(0, 0, 0))
    if bust:
        slice_piece = bust.copy()
        slice_piece.data = bust.data.copy()
        bpy.context.collection.objects.link(slice_piece)
        slice_piece.location = (0.18, -0.06, 0.48)
        slice_piece.rotation_euler = (0.08, 0.18, -0.12)

    mat_core = make_pbr_mat("CrimsonCore", (0.85, 0.06, 0.10), roughness=0.25, emission_rgb=(0.95, 0.08, 0.14), emission_str=1.2)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.44, location=(0.06, -0.08, 1.62))
    core = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    core.data.materials.append(mat_core)

    append_blend_meshes("dagger.blend", target_size=1.35, location=(-0.18, 0.05, 2.35), rot_euler=(0.0, math.radians(155), 0.0))

    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.15, depth=0.02, location=(0.0, 0.0, 0.02))
    disc = bpy.context.active_object
    disc.scale = (1.2, 0.45, 1.0)
    disc.data.materials.append(mat_core)

    curve_data = bpy.data.curves.new('CrimsonRibbon', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.022
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(2)
    pts = [(-3.2, 0.8, 0.6), (0.0, 0.6, 1.45), (3.2, 0.8, 2.15)]
    for i, p in enumerate(pts):
        spline.bezier_points[i].co = p
        spline.bezier_points[i].handle_left_type = 'AUTO'
        spline.bezier_points[i].handle_right_type = 'AUTO'
    rib = bpy.data.objects.new('CrimsonRibbon', curve_data)
    bpy.context.collection.objects.link(rib)
    rib.data.materials.append(mat_core)

    add_area_light("BustKey", (-2.6, -2.8, 2.8), 95.0, 1.8, (1.0, 0.98, 0.96), (0, 0, 1.4))
    add_area_light("BustCrimsonRim", (2.4, 1.5, 2.2), 80.0, 1.6, (1.0, 0.12, 0.16), (0, 0, 1.4))


def build_scene6b_stab_tableau():
    load_vertex_color_glb("stab_tableau_clean.glb", target_height=1.95, location=(0.0, 0.0, 0.0), rot_z_deg=0.0, decimate_ratio=0.55)
    sen_stand = load_vertex_color_glb("senator_standing_clean.glb", target_height=1.82, location=(0, 0, -20), decimate_ratio=0.25)
    sen_stand.hide_render = True
    for sx, sy, yaw in [(-2.4, 2.2, -25), (-1.4, 2.5, -12), (-0.5, 2.7, 0), (0.5, 2.7, 5), (1.4, 2.5, 15), (2.4, 2.2, 25)]:
        inst = sen_stand.copy()
        inst.data = sen_stand.data
        inst.hide_render = False
        bpy.context.collection.objects.link(inst)
        inst.location = (sx, sy, 0.0)
        inst.rotation_euler = (0, 0, math.radians(yaw))

    add_area_light("StabKey", (-1.5, -2.5, 3.2), 110.0, 1.4, (1.0, 0.92, 0.80), (0, 0, 1.1))
    add_area_light("StabRim", (1.8, 1.8, 2.8), 65.0, 1.8, (0.95, 0.22, 0.22), (0, 0, 1.2))


def set_calm_camera(cam_o, start_loc, end_loc, target_vec, u, lens=38.0):
    cam_o.data.lens = lens
    t = 3 * u * u - 2 * u * u * u
    loc = Vector(start_loc).lerp(Vector(end_loc), t)
    cam_o.location = loc
    direction = Vector(target_vec) - loc
    cam_o.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


SCENE_ID = START_FRAME // 180

if SCENE_ID == 0:
    scn = init_cycles_1080p(samples=16, bg_rgb=(0.015, 0.014, 0.012), exposure=-0.35)
    build_curia_interior_set(include_standing_caesar=True, include_throne_caesar=False, crime_scene=False)
    cam_d = bpy.data.cameras.new("Cam")
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    for f in range(START_FRAME, END_FRAME):
        u = (f - 0) / 180.0
        set_calm_camera(cam_o, (0.0, -3.2, 2.45), (0.0, -5.4, 3.65), (0.0, 1.2, 1.15), u, lens=36.0)
        scn.frame_set(f)
        scn.render.filepath = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

elif SCENE_ID == 1:
    scn = init_cycles_1080p(samples=16, bg_rgb=(0.005, 0.006, 0.009), exposure=-0.35)
    build_scene1_pompey_complex_cutaway()
    cam_d = bpy.data.cameras.new("Cam")
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    for f in range(START_FRAME, END_FRAME):
        u = (f - 180) / 180.0
        set_calm_camera(cam_o, (-9.5, -10.5, 7.8), (-6.8, -7.8, 5.8), (1.2, 0.0, 0.8), u, lens=35.0)
        scn.frame_set(f)
        scn.render.filepath = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

elif SCENE_ID == 3:
    scn = init_cycles_1080p(samples=16, bg_rgb=(0.004, 0.004, 0.006), exposure=-0.25)
    build_scene3a_sliced_marble_bust()
    cam_d = bpy.data.cameras.new("Cam")
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    for f in range(START_FRAME, END_FRAME):
        u = (f - 540) / 90.0
        set_calm_camera(cam_o, (-0.35, -3.45, 1.45), (0.35, -3.15, 1.55), (0.0, 0.0, 1.35), u, lens=45.0)
        scn.frame_set(f)
        scn.render.filepath = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

elif SCENE_ID == 5:
    scn = init_cycles_1080p(samples=16, bg_rgb=(0.012, 0.012, 0.015), exposure=-0.35)
    build_curia_interior_set(include_standing_caesar=False, include_throne_caesar=True, crime_scene=False)
    cam_d = bpy.data.cameras.new("Cam")
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    for f in range(START_FRAME, END_FRAME):
        u = (f - 900) / 180.0
        set_calm_camera(cam_o, (-2.6, 0.4, 2.35), (-1.4, 0.8, 2.50), (0.2, 4.2, 1.45), u, lens=34.0)
        scn.frame_set(f)
        scn.render.filepath = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

elif SCENE_ID == 6:
    scn = init_cycles_1080p(samples=16, bg_rgb=(0.003, 0.003, 0.005), exposure=-0.25)
    build_scene6b_stab_tableau()
    cam_d = bpy.data.cameras.new("Cam")
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    for f in range(START_FRAME, END_FRAME):
        u = (f - 1170) / 90.0
        set_calm_camera(cam_o, (-0.25, -2.95, 1.18), (0.15, -2.55, 1.24), (0.0, 0.0, 1.12), u, lens=42.0)
        scn.frame_set(f)
        scn.render.filepath = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

elif SCENE_ID == 7:
    scn = init_cycles_1080p(samples=16, bg_rgb=(0.010, 0.010, 0.012), exposure=-0.35)
    build_curia_interior_set(include_standing_caesar=False, include_throne_caesar=False, crime_scene=True)
    cam_d = bpy.data.cameras.new("Cam")
    cam_o = bpy.data.objects.new("Cam", cam_d)
    scn.collection.objects.link(cam_o)
    scn.camera = cam_o
    for f in range(START_FRAME, END_FRAME):
        u = (f - 1260) / 180.0
        set_calm_camera(cam_o, (0.0, -0.2, 5.2), (0.0, -0.8, 6.4), (0.0, 3.0, 0.4), u, lens=35.0)
        scn.frame_set(f)
        scn.render.filepath = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

print(f"Fast Cycles pass complete for shard {SHARD_ID} (frames {START_FRAME}..{END_FRAME-1})")
