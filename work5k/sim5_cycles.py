# Blender 4.1 headless: shrinking-sphere crumple (TRUE BALL) + Cycles GPU render w/ alpha
import bpy, random, math, os, sys

OUT = os.environ.get('SHOT5_OUT', '/kaggle/working/vidmap_shot5')
TEXDIR = os.environ.get('SHOT5_TEX', OUT)
os.makedirs(os.path.join(OUT, 'frames'), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start = 1; sc.frame_end = 84

# ---------- sheets (max quality density) ----------
def make_sheet(name, sx, sy, cx, cy, cz, subx, suby, seed, tex):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subx, y_subdivisions=suby, size=1, location=(cx,cy,cz))
    ob = bpy.context.object; ob.name = name
    ob.scale = (sx, sy, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.uv.unwrap(method='ANGLE_BASED')  # grid unwrap ~ planar
    bpy.ops.object.mode_set(mode='OBJECT')
    random.seed(seed)
    for v in ob.data.vertices:
        v.co.z += (random.random()-0.5)*0.012
    m = ob.modifiers.new('cloth','CLOTH'); cs = m.settings
    cs.quality = 12; cs.mass = 0.25; cs.air_damping = 3.0
    cs.tension_stiffness = 30; cs.compression_stiffness = 18; cs.shear_stiffness = 25
    cs.bending_stiffness = 3.5
    cs.effector_weights.gravity = 0.0
    col = m.collision_settings
    col.use_self_collision = True; col.self_distance_min = 0.01
    col.distance_min = 0.012; col.collision_quality = 6
    ob.modifiers.new('colobj','COLLISION'); ob.collision.thickness_outer = 0.01
    m.point_cache.frame_start = 1; m.point_cache.frame_end = 84
    # material: paper PBR + translucency
    mat = bpy.data.materials.new(name+'_mat'); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']
    img = bpy.data.images.load(os.path.join(TEXDIR, tex))
    ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img
    nt.links.new(ti.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.65
    try: bsdf.inputs['Transmission Weight'].default_value = 0.0
    except: pass
    # bump from texture for micro paper grain
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25
    nt.links.new(ti.outputs['Color'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    mat.use_backface_culling = False
    ob.data.materials.append(mat)
    # planar UVs matching grid
    uvl = ob.data.uv_layers.active
    import mathutils
    xs = [v.co.x for v in ob.data.vertices]; ys = [v.co.y for v in ob.data.vertices]
    x0,x1,y0,y1 = min(xs),max(xs),min(ys),max(ys)
    for loop in ob.data.loops:
        co = ob.data.vertices[loop.vertex_index].co
        uvl.data[loop.index].uv = ((co.x-x0)/(x1-x0), (co.y-y0)/(y1-y0))
    return ob

paper = make_sheet('paper', 1.12, 0.5, 0, 0, 0.0, 110, 50, 11, 'crump-paper.png')
strip = make_sheet('strip', 0.813, 0.363, -0.28, 0.38, 0.06, 72, 32, 23, 'crump-strip.png')

# ---------- shrinking inverted icosphere (forces TRUE BALL) ----------
CTR = (0.0, 0.15, 0.03)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.95, location=CTR)
sph = bpy.context.object; sph.name = 'crusher'
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode='OBJECT')
sph.modifiers.new('col','COLLISION')
sph.collision.thickness_inner = 0.02; sph.collision.thickness_outer = 0.02
sph.hide_render = True
sph.scale = (1,1,1);      sph.keyframe_insert('scale', frame=4)
sph.scale = (0.60,)*3;    sph.keyframe_insert('scale', frame=30)
sph.scale = (0.30,)*3;    sph.keyframe_insert('scale', frame=56)
sph.scale = (0.175,)*3;   sph.keyframe_insert('scale', frame=76)
sph.scale = (0.175,)*3;   sph.keyframe_insert('scale', frame=84)

# mild turbulence for organic asymmetry
bpy.ops.object.effector_add(type='TURBULENCE', location=CTR)
tb = bpy.context.object; tb.field.strength = 5.0; tb.field.size = 0.3; tb.field.seed = 7

print('BAKING...', flush=True)
bpy.ops.ptcache.bake_all(bake=True)
print('BAKE DONE', flush=True)

# ---------- camera / lights (match three.js fov33 z=8 framing, world scale 4.6 handled in comp) ----------
cam_data = bpy.data.cameras.new('cam'); cam_data.angle = math.radians(33)
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
cam.location = (0, 0.1, 1.95); cam.rotation_euler = (0, 0, 0)
sc.camera = cam

key_d = bpy.data.lights.new('key','AREA'); key_d.energy = 60; key_d.size = 3.0
key = bpy.data.objects.new('key', key_d); sc.collection.objects.link(key)
key.location = (1.4, 1.6, 2.2); key.rotation_euler = (math.radians(-28), math.radians(28), 0)
fill_d = bpy.data.lights.new('fill','AREA'); fill_d.energy = 18; fill_d.size = 4.0
fill = bpy.data.objects.new('fill', fill_d); sc.collection.objects.link(fill)
fill.location = (-1.6, -0.4, 1.8); fill.rotation_euler = (math.radians(10), math.radians(-35), 0)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.35,0.38,0.42,1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35

# ---------- Cycles GPU ----------
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for dt in ('OPTIX','CUDA'):
    try:
        prefs.compute_device_type = dt
        prefs.get_devices()
        ok = any(d.type == dt for d in prefs.devices)
        if ok: break
    except Exception: ok = False
for d in prefs.devices: d.use = True
sc.cycles.device = 'GPU' if ok else 'CPU'
print('RENDER DEVICE:', prefs.compute_device_type if ok else 'CPU', flush=True)
sc.cycles.samples = 160
sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.render.resolution_x = 1920; sc.render.resolution_y = 1080
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'

for f in range(1, 85):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, 'frames', 'f%03d.png' % f)
    bpy.ops.render.render(write_still=True)
    print('FRAME', f, 'done', flush=True)
print('ALL DONE', flush=True)
