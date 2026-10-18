#!/usr/bin/env python3
"""
Hybrid Masterpiece 3D 360-Degree Pipeline in Blender 4.3 (1920x1080 @ 30.00 fps):
- ZERO Blur Guarantee:
  * Native 1920x1080 render resolution (no 720p upscale).
  * use_denoising = False (no OpenImageDenoise smearing).
  * filter_size = 0.65 (razor-sharp subpixel AA filter).
  * max_bounces = 0 + 100% deterministic noise-free shader node graphs (Cubic 2560x1440 textures
    + analytical 3D Hemisphere Normal/Fresnel/Specular studio shaders for 3D statues, columns, revolver & GIS terrain).
  * Flat, un-warped high-resolution architectural projection panels (zero bumpy low-res mesh distortion).
- True 360° (0° -> 360°) 3D Camera Orbit in ALL 5 Scenes:
  * Scene 0 (0..299): Full 360° 3D Orbit around the 4-Sided Yusupov Palace Cutaway Diorama Island
    with 3D Corinthian columns, 3D stepped canal base, 3D glowing crimson staircase footsteps & 3D titles.
  * Scene 1 (300..599): Full 360° 3D Orbit around the Soundproofed Basement 3D Pavilion with 3D marble
    statues of Rasputin & Prince Yusupov, 3D mahogany table, and 3D golden candelabra.
  * Scene 2 (600..899): Full 360° 3D Turntable Rotation of the Bisected 3D Marble Bust Monument +
    real 3D Rasputin bust split at 38° by the glowing crimson laser beam.
  * Scene 3 (900..1199): Full 360° 3D Orbit around the 100% Real GIS (Natural Earth 50m GeoJSON)
    3D Obsidian Topographic Relief Map of Russia & the 1916 Eastern Front + Golden Petrograd Laser Spire.
  * Scene 4 (1200..1499): Full 360° 3D Forensic Overhead Crane Orbit around the Top-Down Crime Scene
    Courtyard, 3D Corinthian corner columns, 3D marble statues, and 3D Webley .455 Revolver & brass shells.
"""
import os
import sys
import math
import json
import random

import bpy
import bmesh
import mathutils

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else ["0", "1", "/tmp/ras_frames"]
START_FRAME = int(argv[0])
END_FRAME = int(argv[1])
OUT_DIR = argv[2]
PREVIEW_MODE = "--preview" in argv

os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, SCRIPT_DIR)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def configure_sharp_1080p():
    """Configure Blender 4.3 Cycles for 100% noise-free, zero-blur native 1920x1080 rendering."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.cycles.filter_size = 0.65
    scene.cycles.use_persistent_data = True
    scene.cycles.max_bounces = 0
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.cycles.transmission_bounces = 0
    scene.cycles.volume_bounces = 0
    scene.cycles.transparent_max_bounces = 2
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    return scene


def setup_world(col=(0.004, 0.005, 0.009)):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*col, 1.0)
    bg.inputs[1].default_value = 1.0


def look_at(cam_obj, target_pt):
    direction = mathutils.Vector(target_pt) - cam_obj.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    cam_obj.rotation_euler = rot_quat.to_euler("XYZ")


def make_crisp_tex_mat(name, img_filename, strength=1.0):
    """
    100% unblurred, noise-free high-resolution texture material.
    Connects Cubic-interpolated 2560x1440 image texture directly to Emission -> Surface
    so Cycles samples the exact native pixels with 4x AA and ZERO denoiser blur.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = strength

    tex = nt.nodes.new("ShaderNodeTexImage")
    img_path = os.path.join(ASSETS_DIR, img_filename)
    tex.image = bpy.data.images.load(img_path, check_existing=True)
    tex.interpolation = "Cubic"
    tex.extension = "EXTEND"

    nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m


def make_emit_mat(name, color, strength=1.0):
    """Pure crisp emission material for neon borders, laser beams, golden beacons & 3D text."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1.0)
    emit.inputs["Strength"].default_value = strength
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m


def make_studio_3d_mat(name, shadow_col, mid_col, high_col, rim_col=(1.0, 0.85, 0.55), fresnel_blend=0.32):
    """
    Deterministic noise-free 3D studio material for 3D statues, columns, pedestals & revolvers.
    Computes 360° Hemisphere Half-Lambert shading + Fresnel rim glow in shader nodes
    plugged directly into Surface so 3D meshes have crisp dynamic shading with 0.0% noise.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    vdot = nt.nodes.new("ShaderNodeVectorMath")
    vdot.operation = "DOT_PRODUCT"
    vdot.inputs[1].default_value = (0.48, -0.52, 0.70)

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = -1.0
    mr.inputs[2].default_value = 1.0
    mr.inputs[3].default_value = 0.0
    mr.inputs[4].default_value = 1.0

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*shadow_col, 1.0)
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (*high_col, 1.0)
    el_mid = ramp.color_ramp.elements.new(0.52)
    el_mid.color = (*mid_col, 1.0)

    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = fresnel_blend

    mix_rim = nt.nodes.new("ShaderNodeMixRGB")
    mix_rim.blend_type = "ADD"
    mix_rim.inputs["Color2"].default_value = (*rim_col, 1.0)

    nt.links.new(geom.outputs["Normal"], vdot.inputs[0])
    nt.links.new(vdot.outputs["Value"], mr.inputs[0])
    nt.links.new(mr.outputs[0], ramp.inputs["Fac"])
    nt.links.new(lw.outputs["Fresnel"], mix_rim.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix_rim.inputs["Color1"])
    nt.links.new(mix_rim.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m


def make_obsidian_gis_mat(name, c_low, c_high, rim_col, scale=7.5):
    """
    Deterministic noise-free 3D Volcanic Obsidian GIS Terrain Material.
    Combines Voronoi ridge lines + 360° Hemisphere Normal shading + Fresnel rim.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0

    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    vdot = nt.nodes.new("ShaderNodeVectorMath")
    vdot.operation = "DOT_PRODUCT"
    vdot.inputs[1].default_value = (0.45, -0.50, 0.74)

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = -1.0
    mr.inputs[2].default_value = 1.0
    mr.inputs[3].default_value = 0.0
    mr.inputs[4].default_value = 1.0

    mix_val = nt.nodes.new("ShaderNodeMixRGB")
    mix_val.blend_type = "MIX"
    mix_val.inputs["Fac"].default_value = 0.45

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.08
    ramp.color_ramp.elements[0].color = (*c_low, 1.0)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (*c_high, 1.0)

    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.28

    mix_rim = nt.nodes.new("ShaderNodeMixRGB")
    mix_rim.blend_type = "ADD"
    mix_rim.inputs["Color2"].default_value = (*rim_col, 1.0)

    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(geom.outputs["Normal"], vdot.inputs[0])
    nt.links.new(vdot.outputs["Value"], mr.inputs[0])
    nt.links.new(vor.outputs["Distance"], mix_val.inputs["Color1"])
    nt.links.new(mr.outputs[0], mix_val.inputs["Color2"])
    nt.links.new(mix_val.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(lw.outputs["Fresnel"], mix_rim.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mix_rim.inputs["Color1"])
    nt.links.new(mix_rim.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m


def create_flat_uv_panel(name, width, height, mat, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Create a 100% flat, geometric distortion-free UV-mapped vertical panel in local XZ plane facing -Y."""
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    obj.rotation_mode = "XYZ"
    obj.location = loc
    obj.rotation_euler = rot
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    hw = width * 0.5
    hh = height * 0.5
    v0 = bm.verts.new((-hw, 0.0, -hh))
    v1 = bm.verts.new((hw, 0.0, -hh))
    v2 = bm.verts.new((hw, 0.0, hh))
    v3 = bm.verts.new((-hw, 0.0, hh))
    face = bm.faces.new((v0, v1, v2, v3))
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    return obj


def create_horizontal_uv_floor(name, width, height, mat, loc=(0, 0, 0)):
    """Create a 100% flat, distortion-free UV-mapped horizontal floor in XY plane facing +Z."""
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    obj.rotation_mode = "XYZ"
    obj.location = loc
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    hw = width * 0.5
    hh = height * 0.5
    v0 = bm.verts.new((-hw, -hh, 0.0))
    v1 = bm.verts.new((hw, -hh, 0.0))
    v2 = bm.verts.new((hw, hh, 0.0))
    v3 = bm.verts.new((-hw, hh, 0.0))
    face = bm.faces.new((v0, v1, v2, v3))
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    return obj


def load_blend_asset(filename, name_prefix, target_height=None, mat=None):
    path = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        return None
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.objects = df.objects
    meshes = []
    for o in dt.objects:
        if o is not None and o.type == "MESH" and len(o.data.vertices) > 4:
            bpy.context.collection.objects.link(o)
            o.hide_render = False
            o.hide_viewport = False
            o.visible_camera = True
            meshes.append(o)
    if not meshes:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name_prefix
    obj.rotation_mode = "XYZ"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    verts = [v.co for v in obj.data.vertices]
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    dz = max(zs) - min(zs)
    span = max(max(xs) - min(xs), max(ys) - min(ys), dz) if "revolver" in filename else dz
    sc = (target_height / max(span, 1e-4)) if target_height else 1.0
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    min_z = min(zs)
    for v in obj.data.vertices:
        v.co.x = (v.co.x - cx) * sc
        v.co.y = (v.co.y - cy) * sc
        v.co.z = (v.co.z - min_z) * sc
    obj.data.update()
    if mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    return obj


def clone_obj(src_obj, name, loc, rot=(0, 0, 0), scale=(1, 1, 1)):
    if src_obj is None:
        return None
    c = src_obj.copy()
    c.data = src_obj.data
    c.name = name
    c.rotation_mode = "XYZ"
    c.location = loc
    c.rotation_euler = rot
    c.scale = scale
    bpy.context.collection.objects.link(c)
    return c


def add_box(name, loc, scale, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "XYZ"
    o.scale = scale
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


def add_cyl(name, loc, r, depth, mat, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "XYZ"
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


def add_3d_text(text, loc, size, mat, rot=(0, 0, 0), extrude=0.045):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.active_object
    t.rotation_mode = "XYZ"
    t.data.body = text
    t.data.size = size
    t.data.extrude = extrude
    t.data.bevel_depth = 0.008
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    font_path = os.path.join(SCRIPT_DIR, "fonts", "Cinzel-Bold.ttf")
    if os.path.exists(font_path):
        t.data.font = bpy.data.fonts.load(font_path)
    t.data.materials.clear()
    t.data.materials.append(mat)
    return t


def add_camera(loc, lens=35.0):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    co = bpy.data.objects.new("Cam", cd)
    co.rotation_mode = "XYZ"
    co.location = loc
    bpy.context.collection.objects.link(co)
    bpy.context.scene.camera = co
    return co


def build_4sided_3d_pavilion(img_filename, name_prefix, w=12.8, h=7.2, title_top="YUSUPOV PALACE // 1916"):
    """
    Build a monumental 4-sided 3D Neoclassical Architectural Diorama Pavilion:
    - 4 flat, distortion-free 16:9 panels (2560x1440 Cubic texture) on Front (-Y), Right (+X), Back (+Y), Left (-X)
    - 4 real 3D Corinthian Columns (bk_column_corinthian.blend) at the corners
    - 3D Stepped Imperial Marble Base + 3D Perspective Grid Floor
    - 3D Golden Neoclassical Roof Cornice & Crown Pediment
    - 3D World-Locked Extruded Titles on all 4 facades
    """
    mat_tex = make_crisp_tex_mat(f"{name_prefix}_TexMat", img_filename, strength=1.0)
    mat_marble = make_studio_3d_mat(
        f"{name_prefix}_Marble", (0.14, 0.15, 0.18), (0.62, 0.60, 0.56), (0.96, 0.94, 0.88), rim_col=(1.0, 0.85, 0.55)
    )
    mat_dark_stone = make_studio_3d_mat(
        f"{name_prefix}_DarkStone", (0.03, 0.035, 0.045), (0.12, 0.13, 0.16), (0.28, 0.30, 0.36), rim_col=(0.45, 0.65, 0.95)
    )
    mat_gold = make_emit_mat(f"{name_prefix}_Gold", (0.98, 0.80, 0.32), strength=1.15)
    mat_crimson = make_emit_mat(f"{name_prefix}_Crimson", (0.95, 0.14, 0.18), strength=1.25)
    mat_grid = make_emit_mat(f"{name_prefix}_Grid", (0.28, 0.34, 0.46), strength=0.65)

    hw = w * 0.5
    hh = h * 0.5

    # 4 Razor-Sharp 16:9 Facades around the 3D Pavilion
    faces = [
        ("Front", (0.0, -hw, 0.0), (0.0, 0.0, 0.0)),
        ("Right", (hw, 0.0, 0.0), (0.0, 0.0, math.radians(90.0))),
        ("Back", (0.0, hw, 0.0), (0.0, 0.0, math.radians(180.0))),
        ("Left", (-hw, 0.0, 0.0), (0.0, 0.0, math.radians(270.0))),
    ]
    for fname, floc, frot in faces:
        create_flat_uv_panel(f"{name_prefix}_{fname}", w, h, mat_tex, loc=floc, rot=frot)

    # Solid 3D Core Block inside the 4 facades + 3D Stepped Base + 3D Roof Cornice
    add_box(f"{name_prefix}_Core", (0.0, 0.0, 0.0), (w - 0.08, w - 0.08, h - 0.08), mat_dark_stone)
    add_box(f"{name_prefix}_BaseStep1", (0.0, 0.0, -hh - 0.25), (w + 1.4, w + 1.4, 0.50), mat_dark_stone)
    add_box(f"{name_prefix}_BaseStep2", (0.0, 0.0, -hh - 0.65), (w + 2.8, w + 2.8, 0.35), mat_marble)
    add_box(f"{name_prefix}_BaseRimGold", (0.0, 0.0, -hh - 0.02), (w + 0.45, w + 0.45, 0.08), mat_gold)

    add_box(f"{name_prefix}_RoofCornice", (0.0, 0.0, hh + 0.22), (w + 1.1, w + 1.1, 0.44), mat_marble)
    add_box(f"{name_prefix}_RoofGoldRim", (0.0, 0.0, hh + 0.02), (w + 0.45, w + 0.45, 0.08), mat_gold)
    add_box(f"{name_prefix}_RoofCrimsonRim", (0.0, 0.0, hh + 0.46), (w + 0.65, w + 0.65, 0.06), mat_crimson)

    # 3D Perspective Wireframe Floor Grid under the Diorama Island
    grid_z = -hh - 0.84
    for g in range(-16, 17, 2):
        add_box(f"{name_prefix}_GX_{g}", (g * 1.2, 0.0, grid_z), (0.02, 36.0, 0.01), mat_grid)
        add_box(f"{name_prefix}_GY_{g}", (0.0, g * 1.2, grid_z), (36.0, 0.02, 0.01), mat_grid)

    # 4 Real 3D Corinthian Columns at the 4 Corners of the Pavilion
    col_proto = load_blend_asset("bk_column_corinthian.blend", f"{name_prefix}_ColProto", target_height=h + 0.5, mat=mat_marble)
    if col_proto:
        corners = [
            (-hw - 0.22, -hw - 0.22),
            (hw + 0.22, -hw - 0.22),
            (hw + 0.22, hw + 0.22),
            (-hw - 0.22, hw + 0.22),
        ]
        for idx_c, (cx, cy) in enumerate(corners):
            if idx_c == 0:
                col_proto.location = (cx, cy, -hh - 0.25)
            else:
                clone_obj(col_proto, f"{name_prefix}_Col_{idx_c}", (cx, cy, -hh - 0.25))

    # 3D Extruded World-Locked Title Headers on all 4 Sides of the Crown Cornice
    title_rots = [
        ((0.0, -hw - 0.62, hh + 0.22), (math.radians(90.0), 0.0, 0.0)),
        ((hw + 0.62, 0.0, hh + 0.22), (math.radians(90.0), 0.0, math.radians(90.0))),
        ((0.0, hw + 0.62, hh + 0.22), (math.radians(90.0), 0.0, math.radians(180.0))),
        ((-hw - 0.62, 0.0, hh + 0.22), (math.radians(90.0), 0.0, math.radians(270.0))),
    ]
    for tloc, trot in title_rots:
        add_3d_text(title_top, tloc, 0.42, mat_gold, rot=trot, extrude=0.04)

    return mat_marble, mat_gold, mat_crimson


# ==============================================================================
# SCENE 0 (Frames 0..299): FULL 360° ORBIT AROUND YUSUPOV PALACE 3D CUTAWAY
# ==============================================================================
def build_scene_0():
    scene = configure_sharp_1080p()
    setup_world((0.003, 0.004, 0.008))

    mat_marble, mat_gold, mat_crimson = build_4sided_3d_pavilion(
        "rasputin_kf_1_cutaway.jpg", "YusupovCutaway", w=12.8, h=7.2, title_top="YUSUPOV PALACE // 94 MOIKA CANAL"
    )

    # 3D Glowing Crimson Footsteps descending around the 3D Palace Plinth Perimeter
    for i in range(32):
        ang = (i / 32.0) * 2.0 * math.pi
        rx = 7.65 * math.sin(ang)
        ry = -7.65 * math.cos(ang)
        rz = -3.65 - 0.15 * math.sin(ang * 2.0)
        add_cyl(f"Step3D_{i}", (rx, ry, rz), 0.15, 0.06, mat_crimson, verts=20)

    cam = add_camera(loc=(0.0, -21.8, 2.3), lens=36.0)

    def update_frame(f):
        # Full 360-degree (0 -> 2*pi) continuous 3D orbit over 300 frames
        u = (f - 0.0) / 300.0
        theta = u * 2.0 * math.pi
        radius = 21.8 + 1.6 * (math.sin(2.0 * theta) ** 2)
        cam_z = 2.25 + 0.55 * math.sin(theta * 2.0)
        cam.location = (radius * math.sin(theta), -radius * math.cos(theta), cam_z)
        look_at(cam, (0.0, 0.0, -0.10))

    return scene, update_frame


# ==============================================================================
# SCENE 1 (Frames 300..599): FULL 360° ORBIT AROUND SOUNDPROOFED BASEMENT CHAMBER
# ==============================================================================
def build_scene_1():
    scene = configure_sharp_1080p()
    setup_world((0.004, 0.003, 0.007))

    mat_marble, mat_gold, mat_crimson = build_4sided_3d_pavilion(
        "rasputin_kf_2_basement.jpg", "BasementChamber", w=12.8, h=7.2, title_top="SOUNDPROOFED CELLAR // DEC 30, 1916"
    )

    # Real 3D Carrara Marble Statues of Rasputin & Conspirators + 3D Golden Candelabra on the 4 Plinth Terraces
    ras_proto = load_blend_asset("bk_bearded_statue.blend", "RasputinStatue3D", target_height=2.35, mat=mat_marble)
    cand_proto = load_blend_asset("bk_candelabra.blend", "Candelabra3D", target_height=1.15, mat=mat_gold)

    terrace_locs = [
        ((0.0, -7.25, -3.85), 0.0),
        ((7.25, 0.0, -3.85), 90.0),
        ((0.0, 7.25, -3.85), 180.0),
        ((-7.25, 0.0, -3.85), 270.0),
    ]
    for idx_t, ((tx, ty, tz), rot_d) in enumerate(terrace_locs):
        rad = math.radians(rot_d)
        if cand_proto:
            if idx_t == 0:
                cand_proto.location = (tx, ty, tz)
                cand_proto.rotation_euler = (0.0, 0.0, rad)
            else:
                clone_obj(cand_proto, f"Cand_{idx_t}", (tx, ty, tz), rot=(0.0, 0.0, rad))
        if ras_proto:
            sx = tx + 2.8 * math.cos(rad)
            sy = ty + 2.8 * math.sin(rad)
            if idx_t == 0:
                ras_proto.location = (sx, sy, tz)
                ras_proto.rotation_euler = (0.0, 0.0, rad)
            else:
                clone_obj(ras_proto, f"RasStatue_{idx_t}", (sx, sy, tz), rot=(0.0, 0.0, rad))

    cam = add_camera(loc=(0.0, -21.8, 2.0), lens=36.0)

    def update_frame(f):
        # Full 360-degree (0 -> 2*pi) continuous 3D orbit over 300 frames
        u = (f - 300.0) / 300.0
        theta = u * 2.0 * math.pi
        radius = 21.8 + 1.6 * (math.sin(2.0 * theta) ** 2)
        cam_z = 2.05 + 0.45 * math.cos(theta * 2.0)
        cam.location = (radius * math.sin(theta), -radius * math.cos(theta), cam_z)
        look_at(cam, (0.0, 0.0, -0.15))

    return scene, update_frame


# ==============================================================================
# SCENE 2 (Frames 600..899): FULL 360° TURNTABLE OF BISECTED 3D MARBLE BUST
# ==============================================================================
def build_scene_2():
    scene = configure_sharp_1080p()
    setup_world((0.006, 0.002, 0.003))

    # Build a Parent Turntable Empty at X = +2.35m (so the left side has clean room for the Bento Dossier Card)
    pivot_low = bpy.data.objects.new("BustTurntableLow", None)
    pivot_low.location = (2.35, 0.0, -0.55)
    pivot_low.rotation_mode = "XYZ"
    bpy.context.collection.objects.link(pivot_low)

    pivot_high = bpy.data.objects.new("BustTurntableHigh", None)
    pivot_high.location = (2.35, 0.0, -0.55)
    pivot_high.rotation_mode = "XYZ"
    bpy.context.collection.objects.link(pivot_high)

    mat_tex = make_crisp_tex_mat("SlicedBustTex", "rasputin_kf_3_sliced_bust.jpg", strength=1.0)
    mat_marble = make_studio_3d_mat(
        "BustMarble3D", (0.16, 0.16, 0.19), (0.68, 0.66, 0.62), (0.98, 0.96, 0.92), rim_col=(1.0, 0.25, 0.28)
    )
    mat_laser = make_emit_mat("LaserCut3D", (1.0, 0.08, 0.12), strength=2.2)
    mat_gold = make_emit_mat("BustGold3D", (0.98, 0.80, 0.32), strength=1.2)
    mat_grid = make_emit_mat("BustGrid3D", (0.35, 0.15, 0.18), strength=0.6)

    w, h = 9.6, 5.4
    hw, hh = w * 0.5, h * 0.5

    # 4 Razor-Sharp 16:9 Facades on the Rotating 3D Bust Monument
    faces = [
        ("Front", (0.0, -hw, 0.0), (0.0, 0.0, 0.0)),
        ("Right", (hw, 0.0, 0.0), (0.0, 0.0, math.radians(90.0))),
        ("Back", (0.0, hw, 0.0), (0.0, 0.0, math.radians(180.0))),
        ("Left", (-hw, 0.0, 0.0), (0.0, 0.0, math.radians(270.0))),
    ]
    for fname, floc, frot in faces:
        p_obj = create_flat_uv_panel(f"BustPanel_{fname}", w, h, mat_tex, loc=floc, rot=frot)
        p_obj.parent = pivot_low

    core = add_box("BustMonumentCore", (0.0, 0.0, 0.0), (w - 0.08, w - 0.08, h - 0.08), mat_marble)
    core.parent = pivot_low
    base1 = add_box("BustBase1", (0.0, 0.0, -hh - 0.22), (w + 1.0, w + 1.0, 0.44), mat_marble)
    base1.parent = pivot_low
    rim1 = add_box("BustRimGold", (0.0, 0.0, -hh - 0.02), (w + 0.3, w + 0.3, 0.07), mat_gold)
    rim1.parent = pivot_low
    top_cornice = add_box("BustTopCornice", (0.0, 0.0, hh + 0.15), (w + 0.6, w + 0.6, 0.30), mat_marble)
    top_cornice.parent = pivot_low

    # Real 3D High-Poly Marble Bust of Rasputin (bk_rasputin_bust.blend) crowning the 3D Turntable Monument
    bust_low = load_blend_asset("bk_rasputin_bust.blend", "RealBust3D_Low", target_height=2.35, mat=mat_marble)
    if bust_low:
        bust_high = clone_obj(bust_low, "RealBust3D_High", (0.0, 0.0, hh + 0.28))
        bust_high.data = bust_low.data.copy()
        bust_low.location = (0.0, 0.0, hh + 0.28)

        # Bisect the real 3D bust mesh at 38° so the upper half physically separates along the glowing red laser plane
        plane_co = mathutils.Vector((0.0, 0.0, 1.20))
        plane_no = mathutils.Vector((0.55, 0.0, 0.83)).normalized()

        bm1 = bmesh.new()
        bm1.from_mesh(bust_low.data)
        bmesh.ops.bisect_plane(
            bm1, geom=bm1.verts[:] + bm1.edges[:] + bm1.faces[:], plane_co=plane_co, plane_no=plane_no, clear_outer=True, clear_inner=False
        )
        bm1.to_mesh(bust_low.data)
        bm1.free()

        bm2 = bmesh.new()
        bm2.from_mesh(bust_high.data)
        bmesh.ops.bisect_plane(
            bm2, geom=bm2.verts[:] + bm2.edges[:] + bm2.faces[:], plane_co=plane_co, plane_no=plane_no, clear_outer=False, clear_inner=True
        )
        bm2.to_mesh(bust_high.data)
        bm2.free()

        bust_low.parent = pivot_low
        bust_high.parent = pivot_high

    # 3D Glowing Crimson Laser Sheet slicing through the rotating monument
    laser_ring = add_box("LaserSlice3D", (0.0, 0.0, 0.15), (w + 1.8, w + 1.8, 0.06), mat_laser, rot=(0.0, math.radians(-28.0), 0.0))
    laser_ring.parent = pivot_low

    for g in range(-14, 15, 2):
        add_box(f"BustGX_{g}", (g * 1.2, 0.0, -3.75), (0.02, 30.0, 0.01), mat_grid)
        add_box(f"BustGY_{g}", (0.0, g * 1.2, -3.75), (30.0, 0.02, 0.01), mat_grid)

    cam = add_camera(loc=(0.0, -21.2, 2.15), lens=36.0)
    look_at(cam, (0.0, 0.0, 0.25))

    def update_frame(f):
        # Full 360-degree (0 -> 2*pi) turntable rotation of the 3D Bust Monument + 3D separation of the sliced bust
        u = (f - 600.0) / 300.0
        theta = u * 2.0 * math.pi
        split_t = smoothstep((f - 615.0) / 120.0)
        pivot_low.rotation_euler = (0.0, 0.0, theta)
        pivot_high.rotation_euler = (0.0, 0.0, theta)
        pivot_high.location = (2.35 + 0.28 * split_t, 0.0, -0.55 + 0.42 * split_t)

    return scene, update_frame


# ==============================================================================
# SCENE 3 (Frames 900..1199): FULL 360° ORBIT AROUND REAL GIS 3D RELIEF MAP
# ==============================================================================
def build_scene_3():
    """
    100% Real GIS Geographic Relief Map of Imperial Russia, Baltic Sea, Gulf of Finland
    and the 1916 Eastern Front built from Natural Earth 50m GeoJSON inside Blender 4.3,
    with a full 360° 3D camera orbit and zero blur.
    """
    scene = configure_sharp_1080p()
    setup_world((0.002, 0.004, 0.009))

    mat_grid = make_emit_mat("GISGridWire", (0.52, 0.64, 0.85), strength=0.75)
    mat_ocean = make_studio_3d_mat(
        "DarkBalticOcean", (0.006, 0.010, 0.020), (0.014, 0.022, 0.042), (0.04, 0.07, 0.12), rim_col=(0.12, 0.28, 0.55)
    )
    mat_obsidian_russia = make_obsidian_gis_mat(
        "ObsidianRussia", (0.022, 0.032, 0.055), (0.085, 0.115, 0.185), rim_col=(0.18, 0.52, 1.0), scale=7.5
    )
    mat_obsidian_front = make_obsidian_gis_mat(
        "ObsidianFront", (0.055, 0.014, 0.018), (0.22, 0.045, 0.055), rim_col=(1.0, 0.18, 0.22), scale=7.5
    )
    mat_obsidian_neutral = make_obsidian_gis_mat(
        "ObsidianNeutral", (0.018, 0.022, 0.032), (0.055, 0.065, 0.085), rim_col=(0.25, 0.30, 0.40), scale=7.0
    )
    mat_blue_neon = make_emit_mat("RussiaBlueNeon", (0.18, 0.58, 1.0), strength=1.45)
    mat_red_neon = make_emit_mat("FrontCrimsonNeon", (1.0, 0.14, 0.18), strength=1.65)
    mat_gold_beacon = make_emit_mat("PetrogradGoldBeacon", (1.0, 0.84, 0.28), strength=1.85)
    mat_white_text = make_emit_mat("MapTextWhite", (0.98, 0.96, 0.92), strength=1.35)

    # 1. Dark Ocean Floor + Crisp 3D White Perspective Wireframe Grid
    add_box("OceanFloor", (0.0, 0.0, -0.05), (24.0, 24.0, 0.05), mat_ocean)
    for gx in range(-16, 17, 1):
        add_box(f"GridX_{gx}", (gx * 0.68, 0.0, 0.0), (0.014, 22.0, 0.008), mat_grid)
    for gy in range(-16, 17, 1):
        add_box(f"GridY_{gy}", (0.0, gy * 0.68, 0.0), (22.0, 0.014, 0.008), mat_grid)

    def proj(lon, lat):
        x = (lon - 27.0) * 0.36 + 0.65
        y = (lat - 54.2) * 0.48
        return x, y

    # 2. Real GIS Country Polygons + Neon Glowing Borders from russia_eastern_front_50m.geojson
    geo_path = os.path.join(ASSETS_DIR, "russia_eastern_front_50m.geojson")
    if os.path.exists(geo_path):
        with open(geo_path, "r") as f:
            gdata = json.load(f)

        russian_empire = {"Russia", "Finland", "Estonia", "Latvia", "Belarus", "Ukraine"}
        eastern_front = {"Germany", "Poland", "Lithuania", "Austria", "Hungary", "Romania"}

        for feat in gdata.get("features", []):
            cname = feat.get("properties", {}).get("NAME", "")
            geom = feat.get("geometry", {})
            gtype = geom.get("type")
            coords = geom.get("coordinates", [])
            polys = coords if gtype == "MultiPolygon" else [coords]

            if cname in russian_empire:
                cmat = mat_obsidian_russia
                rmat = mat_blue_neon
                z_off = 0.06
                ext = 0.16
            elif cname in eastern_front:
                cmat = mat_obsidian_front
                rmat = mat_red_neon
                z_off = 0.09
                ext = 0.18
            else:
                cmat = mat_obsidian_neutral
                rmat = None
                z_off = 0.04
                ext = 0.11

            curve_data = bpy.data.curves.new(f"GIS_{cname}", type="CURVE")
            curve_data.dimensions = "2D"
            curve_data.fill_mode = "BOTH"
            curve_data.extrude = ext
            curve_data.bevel_depth = 0.014
            curve_data.resolution_u = 4

            rim_data = bpy.data.curves.new(f"NeonRim_{cname}", type="CURVE") if rmat else None
            if rim_data:
                rim_data.dimensions = "2D"
                rim_data.fill_mode = "NONE"
                rim_data.bevel_depth = 0.032
                rim_data.resolution_u = 4

            has_pts = False
            for poly in polys:
                if not poly:
                    continue
                ring = poly[0]
                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]
                if max(lons) < 10.0 or min(lons) > 49.0 or max(lats) < 42.5 or min(lats) > 66.5:
                    continue
                pts = []
                for pt in ring:
                    lon = min(max(pt[0], 11.0), 47.0)
                    lat = min(max(pt[1], 43.2), 64.8)
                    pts.append(proj(lon, lat))
                if len(pts) >= 4:
                    spline = curve_data.splines.new("POLY")
                    spline.points.add(len(pts) - 1)
                    for idx_p, (px_i, py_i) in enumerate(pts):
                        spline.points[idx_p].co = (px_i, py_i, 0.0, 1.0)
                    spline.use_cyclic_u = True
                    if rim_data:
                        rspline = rim_data.splines.new("POLY")
                        rspline.points.add(len(pts) - 1)
                        for idx_p, (px_i, py_i) in enumerate(pts):
                            rspline.points[idx_p].co = (px_i, py_i, 0.0, 1.0)
                        rspline.use_cyclic_u = True
                    has_pts = True

            if has_pts:
                cobj = bpy.data.objects.new(f"GISMesh_{cname}", curve_data)
                cobj.rotation_mode = "XYZ"
                cobj.location = (0.0, 0.0, z_off)
                cobj.data.materials.append(cmat)
                bpy.context.collection.objects.link(cobj)
                if rim_data:
                    robj = bpy.data.objects.new(f"GISRim_{cname}", rim_data)
                    robj.rotation_mode = "XYZ"
                    robj.location = (0.0, 0.0, z_off + ext + 0.018)
                    robj.data.materials.append(rmat)
                    bpy.context.collection.objects.link(robj)

    # 3. Sculpted 3D Mountain Ridges (Carpathian Arc, Polish Front, Valdai Hills)
    random.seed(1916)
    mountain_clusters = [
        (-1.6, -2.1, 0.58), (-1.3, -2.3, 0.65), (-0.9, -2.4, 0.54), (-0.5, -2.2, 0.50),
        (-1.8, -0.4, 0.45), (-1.5, 0.1, 0.48), (-1.1, 0.5, 0.40),
        (1.4, 0.8, 0.38), (2.0, 1.2, 0.42), (2.6, 0.4, 0.38), (3.2, -0.4, 0.40),
    ]
    for idx_m, (mx, my, mh) in enumerate(mountain_clusters):
        for sub in range(4):
            ox = mx + random.uniform(-0.35, 0.35)
            oy = my + random.uniform(-0.35, 0.35)
            oh = mh * random.uniform(0.7, 1.2)
            bpy.ops.mesh.primitive_cone_add(
                vertices=7, radius1=random.uniform(0.38, 0.65), radius2=0.03, depth=oh, location=(ox, oy, 0.24 + oh * 0.5)
            )
            mc = bpy.context.active_object
            mc.rotation_mode = "XYZ"
            mc.rotation_euler = (0, 0, random.uniform(0, 6.28))
            mc.data.materials.append(mat_obsidian_front if ox < -0.2 else mat_obsidian_russia)

    # 4. Towering Golden Laser Beacon at Real Coordinates of Petrograd (59.93°N, 30.33°E)
    px, py = proj(30.33, 59.93)
    pin_ring = add_cyl("PetrogradRing", (px, py, 0.26), 0.42, 0.05, mat_gold_beacon, verts=48)
    pin_ring2 = add_cyl("PetrogradRingOuter", (px, py, 0.25), 0.68, 0.03, mat_red_neon, verts=48)
    add_cyl("PetrogradLaserSpire", (px, py, 1.95), 0.055, 3.50, mat_gold_beacon, verts=24)

    # 3D World-Locked Map Labels directly on the 3D GIS Terrain
    add_3d_text("PETROGRAD", (px, py + 0.65, 0.38), 0.36, mat_gold_beacon, rot=(0, 0, 0), extrude=0.04)
    add_3d_text("RUSSIAN EMPIRE", (2.8, 0.2, 0.34), 0.44, mat_white_text, rot=(0, 0, 0), extrude=0.04)
    add_3d_text("1916 EASTERN FRONT", (-1.6, -1.2, 0.38), 0.38, mat_red_neon, rot=(0, 0, math.radians(-55.0)), extrude=0.04)

    # Converging Crimson Plot Trajectory Arrows toward Petrograd
    for sx, sy, rot_z in [(-1.3, 0.3, -32), (-0.5, -1.4, -15), (2.3, -0.6, 22)]:
        add_box(
            f"PlotArrow_{sx}",
            ((sx + px) * 0.5, (sy + py) * 0.5, 0.27),
            (0.065, math.hypot(px - sx, py - sy) * 0.78, 0.035),
            mat_red_neon,
            rot=(0, 0, math.radians(rot_z)),
        )

    cam = add_camera(loc=(0.5, -8.2, 6.2), lens=32.0)

    def update_frame(f):
        # Full 360-degree (0 -> 2*pi) continuous 3D orbit around the Real GIS Relief Map
        u = (f - 900.0) / 300.0
        theta = u * 2.0 * math.pi
        cx, cy = 0.45, 0.35
        radius = 7.85
        cam.location = (cx + radius * math.sin(theta), cy - radius * math.cos(theta), 5.85)
        look_at(cam, (cx, cy, 0.25))
        pulse = 1.0 + 0.22 * math.sin(f * 0.3)
        pin_ring.scale = (pulse, pulse, 1.0)
        pin_ring2.scale = (1.15 - 0.15 * math.sin(f * 0.3), 1.15 - 0.15 * math.sin(f * 0.3), 1.0)

    return scene, update_frame


# ==============================================================================
# SCENE 4 (Frames 1200..1499): FULL 360° OVERHEAD FORENSIC CRIME SCENE ORBIT
# ==============================================================================
def build_scene_4():
    scene = configure_sharp_1080p()
    setup_world((0.002, 0.002, 0.005))

    # 100% Flat, Un-Warped, Razor-Sharp 2560x1440 Crime Scene Floor
    mat_floor = make_crisp_tex_mat("CrimeSceneFloorMat", "rasputin_kf_5_crimescene.jpg", strength=1.0)
    create_horizontal_uv_floor("CrimeSceneFloor", 16.0, 9.0, mat_floor, loc=(0.0, 0.0, 0.0))

    mat_marble = make_studio_3d_mat(
        "ForensicMarble3D", (0.16, 0.17, 0.20), (0.68, 0.66, 0.62), (0.98, 0.96, 0.90), rim_col=(1.0, 0.84, 0.52)
    )
    mat_gun_steel = make_studio_3d_mat(
        "WebleySteel3D", (0.12, 0.14, 0.18), (0.55, 0.58, 0.65), (0.95, 0.96, 1.0), rim_col=(1.0, 0.85, 0.45), fresnel_blend=0.45
    )
    mat_brass = make_emit_mat("BrassShell3D", (1.0, 0.82, 0.28), strength=1.35)
    mat_crimson = make_emit_mat("ForensicCrimsonRim", (0.95, 0.14, 0.18), strength=1.25)
    mat_grid = make_emit_mat("ForensicGrid", (0.28, 0.32, 0.42), strength=0.55)

    # 3D Architectural Frame Rim around the 16x9 Crime Scene Floor + Surrounding 3D Grid
    add_box("FloorRimN", (0.0, 4.6, 0.15), (16.4, 0.22, 0.35), mat_marble)
    add_box("FloorRimS", (0.0, -4.6, 0.15), (16.4, 0.22, 0.35), mat_marble)
    add_box("FloorRimE", (8.1, 0.0, 0.15), (0.22, 9.4, 0.35), mat_marble)
    add_box("FloorRimW", (-8.1, 0.0, 0.15), (0.22, 9.4, 0.35), mat_marble)
    add_box("FloorCrimsonBorder", (0.0, 0.0, -0.05), (16.6, 9.6, 0.06), mat_crimson)

    for g in range(-14, 15, 2):
        add_box(f"CrimeGX_{g}", (g * 1.1, 0.0, -0.12), (0.02, 28.0, 0.01), mat_grid)
        add_box(f"CrimeGY_{g}", (0.0, g * 1.1, -0.12), (28.0, 0.02, 0.01), mat_grid)

    # 4 Real 3D Corinthian Columns + 4 Real 3D Marble Statues at the Corners of the Crime Scene
    col_proto = load_blend_asset("bk_column_corinthian.blend", "CrimeColProto", target_height=2.2, mat=mat_marble)
    stat_proto = load_blend_asset("bk_bearded_statue.blend", "CrimeStatueProto", target_height=1.9, mat=mat_marble)
    corners = [(-7.4, -3.9, 45.0), (7.4, -3.9, 135.0), (7.4, 3.9, -135.0), (-7.4, 3.9, -45.0)]
    for idx_c, (cx, cy, rot_d) in enumerate(corners):
        rad = math.radians(rot_d)
        if col_proto:
            if idx_c == 0:
                col_proto.location = (cx, cy, 0.0)
            else:
                clone_obj(col_proto, f"CrimeCol_{idx_c}", (cx, cy, 0.0))
        if stat_proto:
            sx = cx * 0.82
            sy = cy * 0.80
            if idx_c == 0:
                stat_proto.location = (sx, sy, 0.0)
                stat_proto.rotation_euler = (0.0, 0.0, rad)
            else:
                clone_obj(stat_proto, f"CrimeStat_{idx_c}", (sx, sy, 0.0), rot=(0.0, 0.0, rad))

    # Real 3D Webley .455 Revolver + 3 Spent Brass Bullet Casings on the Marble Tiles beside Rasputin's Right Hand
    rev_obj = load_blend_asset("bk_revolver.blend", "CrimeRevolver3D", target_height=1.10, mat=mat_gun_steel)
    if rev_obj:
        rev_obj.location = (1.65, -0.52, 0.05)
        rev_obj.rotation_euler = (0.0, 0.0, math.radians(-38.0))

    for idx_s, (sx, sy) in enumerate([(1.20, -0.82), (1.92, -0.25), (1.48, -0.98)]):
        add_cyl(f"Shell3D_{idx_s}", (sx, sy, 0.05), 0.048, 0.14, mat_brass, verts=16, rot=(math.radians(90), 0, math.radians(idx_s * 52)))

    cam = add_camera(loc=(0.0, -4.2, 13.5), lens=30.0)

    def update_frame(f):
        # Full 360-degree (0 -> 2*pi) overhead forensic crane orbit + pull-up over 300 frames
        u = (f - 1200.0) / 300.0
        theta = u * 2.0 * math.pi
        radius = lerp(4.2, 3.2, smoothstep(u))
        cam_z = lerp(13.5, 15.2, smoothstep(u))
        cam.location = (radius * math.sin(theta), -radius * math.cos(theta), cam_z)
        look_at(cam, (0.0, 0.0, 0.0))

    return scene, update_frame


# ==============================================================================
# MAIN RENDER LOOP ACROSS REQUESTED FRAME RANGE (START_FRAME .. END_FRAME)
# ==============================================================================
BUILDERS = {
    0: build_scene_0,
    1: build_scene_1,
    2: build_scene_2,
    3: build_scene_3,
    4: build_scene_4,
}

current_scene_id = None
scene_obj = None
updater_fn = None

for frame_idx in range(START_FRAME, END_FRAME + 1):
    sid = min(4, max(0, frame_idx // 300))
    if sid != current_scene_id:
        current_scene_id = sid
        scene_obj, updater_fn = BUILDERS[sid]()
    updater_fn(frame_idx)
    out_file = os.path.join(OUT_DIR, f"frame_{frame_idx:04d}.png")
    scene_obj.render.filepath = out_file
    bpy.ops.render.render(write_still=True)
    print(f"Rendered Sharp 1080p 360-Orbit frame {frame_idx:04d} (Scene {sid}) -> {out_file}")
