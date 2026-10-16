import bpy, sys, os, math, json
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
seq_id = int(args[0])       # 1, 2, 3, or 4
f_start = int(args[1])      # 1..75 or 76..150
f_end   = int(args[2])
out_dir = os.path.abspath(args[3])
os.makedirs(out_dir, exist_ok=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

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
scn.render.image_settings.quality = 95
scn.view_settings.view_transform = 'AgX'
scn.view_settings.look = 'AgX - Medium High Contrast'

if seq_id in [1, 2, 3]:
    glb_path = os.path.join(DOC_ROOT, "models3d", "Blackbird.glb")
else:
    glb_path = os.path.join(DOC_ROOT, "f110_engine", "engine", "f110_web.glb")

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
target_len = 10.0 if seq_id in [1, 2, 3] else 7.5
scale_f = target_len / max(size.x, size.y, size.z, 0.001)
for o in objs:
    o.location = (o.location - center) * scale_f
    o.scale = (scale_f, scale_f, scale_f)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

scan_nodes = []
wire_col = (0.25, 0.86, 1.0, 1.0) if seq_id in [1, 3] else (1.0, 0.72, 0.18, 1.0)

for o in objs:
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        out_n = nt.nodes.get("Material Output")
        if not bsdf or not out_n: continue
        if seq_id == 4:
            bsdf.inputs["Base Color"].default_value = (0.58, 0.62, 0.68, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.85
            bsdf.inputs["Roughness"].default_value = 0.26
        elif "texture" in m.name.lower() or "defaultwhite" == m.name.lower():
            bsdf.inputs["Metallic"].default_value = 0.52
            bsdf.inputs["Roughness"].default_value = 0.34
        else:
            continue

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tex_coord.outputs["Object"], sep_xyz.inputs["Vector"])

        sub_n = nt.nodes.new("ShaderNodeMath"); sub_n.operation = 'SUBTRACT'; sub_n.inputs[1].default_value = -3.5
        scan_nodes.append(sub_n)
        abs_n = nt.nodes.new("ShaderNodeMath"); abs_n.operation = 'ABSOLUTE'
        map_n = nt.nodes.new("ShaderNodeMapRange")
        map_n.inputs["From Min"].default_value = 0.0
        map_n.inputs["From Max"].default_value = 1.45
        map_n.inputs["To Min"].default_value = 1.0
        map_n.inputs["To Max"].default_value = 0.0

        wire_n = nt.nodes.new("ShaderNodeWireframe")
        wire_n.use_pixel_size = True
        wire_n.inputs["Size"].default_value = 1.15

        mul_n = nt.nodes.new("ShaderNodeMath"); mul_n.operation = 'MULTIPLY'
        axis_out = sep_xyz.outputs["Y"] if seq_id in [1, 2, 3] else sep_xyz.outputs["X"]
        nt.links.new(axis_out, sub_n.inputs[0])
        nt.links.new(sub_n.outputs["Value"], abs_n.inputs[0])
        nt.links.new(abs_n.outputs["Value"], map_n.inputs["Value"])
        nt.links.new(map_n.outputs["Result"], mul_n.inputs[0])
        nt.links.new(wire_n.outputs["Fac"], mul_n.inputs[1])

        emit_n = nt.nodes.new("ShaderNodeEmission")
        emit_n.inputs["Color"].default_value = wire_col
        emit_n.inputs["Strength"].default_value = 2.6

        mix_s = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mul_n.outputs["Value"], mix_s.inputs["Fac"])
        nt.links.new(bsdf.outputs["BSDF"], mix_s.inputs[1])
        nt.links.new(emit_n.outputs["Emission"], mix_s.inputs[2])
        nt.links.new(mix_s.outputs["Shader"], out_n.inputs["Surface"])

z_min = min(min((o.matrix_world @ Vector(v)).z for v in o.bound_box) for o in objs)
bpy.ops.mesh.primitive_plane_add(size=100.0, location=(0, 0, z_min - (0.02 if seq_id < 4 else 0.35)))
floor = bpy.context.active_object
fmat = bpy.data.materials.new("StudioFloor"); fmat.use_nodes = True
fbsdf = fmat.node_tree.nodes.get("Principled BSDF")
fbsdf.inputs["Base Color"].default_value = (0.19, 0.20, 0.22, 1.0)
fbsdf.inputs["Roughness"].default_value = 0.40
fbsdf.inputs["Metallic"].default_value = 0.12
floor.data.materials.append(fmat)

w = bpy.data.worlds.new("W"); w.use_nodes = True; scn.world = w
bg = w.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.21, 0.22, 0.24, 1.0); bg.inputs[1].default_value = 1.0

def add_area(nm, loc, energy, sz):
    ld = bpy.data.lights.new(nm, type='AREA'); ld.energy = energy; ld.size = sz
    lo = bpy.data.objects.new(nm, ld); lo.location = loc
    d = Vector((0,0,0)) - Vector(loc); lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scn.collection.objects.link(lo)

add_area("Key",  (8.0, -8.0, 9.0), 2300.0, 10.0)
add_area("Fill", (-8.0, -6.0, 6.0), 1150.0, 12.0)
add_area("Rim",  (0.0, 9.0, 7.0), 1650.0, 9.0)

cd = bpy.data.cameras.new("C"); cd.lens = 50.0
co = bpy.data.objects.new("C", cd); scn.collection.objects.link(co); scn.camera = co

if seq_id == 1:
    anc_3d = {"a1": Vector((0.0, -2.85, 0.22)), "a2": Vector((1.42, -0.95, -0.05))}
elif seq_id == 2:
    anc_3d = {"a1": Vector((0.0, -0.45, 0.18)), "a2": Vector((-1.55, 1.25, 0.05))}
elif seq_id == 3:
    anc_3d = {"a1": Vector((0.0, -3.65, 0.02)), "a2": Vector((0.0, -2.65, 0.26))}
else:
    anc_3d = {"a1": Vector((-1.6, 0.0, 0.45)), "a2": Vector((1.5, 0.0, 0.35))}

coords_out = {}
for f in range(f_start, f_end + 1):
    u = (f - 1) / 149.0
    su = 0.5 - 0.5 * math.cos(u * math.pi)
    if seq_id == 1:
        ang = math.radians(118.0 + 36.0 * su)
        dist = 8.4 - 0.85 * su
        zh = 2.35 - 0.35 * su
        target = Vector((0.0, -0.55, -0.08))
    elif seq_id == 2:
        ang = math.radians(72.0 + 34.0 * su)
        dist = 6.2 - 0.6 * su
        zh = 6.8 - 0.5 * su
        target = Vector((0.0, 0.0, 0.0))
    elif seq_id == 3:
        ang = math.radians(132.0 + 24.0 * su)
        dist = 5.4 - 0.65 * su
        zh = 1.45 - 0.20 * su
        target = Vector((0.0, -2.35, 0.05))
    else:
        ang = math.radians(-58.0 + 42.0 * su)
        dist = 7.2 - 0.7 * su
        zh = 2.2 - 0.3 * su
        target = Vector((0.0, 0.0, 0.0))

    co.location = (dist * math.cos(ang), dist * math.sin(ang), zh)
    d = target - co.location
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

    scan_v = -3.8 + 7.6 * u
    for sn in scan_nodes:
        sn.inputs[1].default_value = scan_v

    bpy.context.view_layer.update()
    c_dict = {}
    for k, pt in anc_3d.items():
        uv = world_to_camera_view(scn, co, pt)
        c_dict[k] = [round(uv.x * 1920.0, 2), round((1.0 - uv.y) * 1080.0, 2)]
    coords_out[str(f)] = c_dict

    scn.render.filepath = os.path.join(out_dir, f"cad_{seq_id}_{f:04d}.jpg")
    bpy.ops.render.render(write_still=True)

with open(os.path.join(out_dir, f"coords_{seq_id}_{f_start}_{f_end}.json"), "w") as fp:
    json.dump(coords_out, fp)
print(f"[CAD Seq {seq_id}] Rendered frames {f_start}..{f_end}")
