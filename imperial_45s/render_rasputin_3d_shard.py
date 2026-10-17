#!/usr/bin/env python3
"""
Blender 4.3 Cycles + BlenderKit Full Animated 3D Shard Renderer (30.00 fps)
NEW 50s SCRIPT: "THE MURDER OF GRIGORI RASPUTIN IN THE YUSUPOV PALACE (DEC 30, 1916)"
Total frames: 1500 (50.0s @ 30fps), split across 20 shards (75 frames/shard):
  - Frames 0..299    (Scene 0): 3D Architectural Cutaway of Yusupov Palace, Moika Canal & Petrograd Blocks
  - Frames 300..599  (Scene 1): 3D Soundproofed Basement Tableau (Rasputin vs. Prince Yusupov, Cyanide Table)
  - Frames 600..899  (Scene 2): 3D Sliced Marble Bust of Rasputin (Animated Laser Split) + Bento Noir Dossier
  - Frames 900..1199 (Scene 3): 3D Obsidian Topographic Relief Map of Russia & 1916 Eastern Front + Collector Cards
  - Frames 1200..1499(Scene 4): 90° Top-Down Forensic Crime Scene Crane Pull-Up (Fallen Rasputin, Revolver, Blood)
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


def configure_cycles():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12 if PREVIEW_MODE else 20
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.denoising_prefilter = "FAST"
    scene.cycles.use_persistent_data = True
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 1
    scene.cycles.transmission_bounces = 1
    scene.cycles.transparent_max_bounces = 2
    scene.render.resolution_x = 960 if PREVIEW_MODE else 1280
    scene.render.resolution_y = 540 if PREVIEW_MODE else 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - High Contrast"
    scene.view_settings.exposure = -0.25
    scene.view_settings.gamma = 0.95
    return scene


def make_pbr_mat(name, color, rough=0.32, metal=0.0, coat=0.0, sss=0.0, emit_col=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if "Coat Weight" in bsdf.inputs and coat > 0:
            bsdf.inputs["Coat Weight"].default_value = coat
            bsdf.inputs["Coat Roughness"].default_value = 0.08
        if "Subsurface Weight" in bsdf.inputs and sss > 0:
            bsdf.inputs["Subsurface Weight"].default_value = sss
            bsdf.inputs["Subsurface Scale"].default_value = 0.025
        if emit_col and emit_str > 0.0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (*emit_col, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emit_str
    return m


def make_rich_stone_mat(name, c1, c2, rough=0.28, metal=0.0, coat=0.25, scale=5.5, bump_str=0.14, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Coat Weight" in bsdf.inputs and coat > 0:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.10
    if "Subsurface Weight" in bsdf.inputs and sss > 0:
        bsdf.inputs["Subsurface Weight"].default_value = sss
        bsdf.inputs["Subsurface Scale"].default_value = 0.02
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.62
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (*c1, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (*c2, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_str
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def make_checker_marble_floor_mat(name="NoirCheckerMarble", scale=10.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.14
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.65
        bsdf.inputs["Coat Roughness"].default_value = 0.06
    tc = nt.nodes.new("ShaderNodeTexCoord")
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = scale
    # Rich dark obsidian-green vs warm antique gold-veined marble (NOT washed-out white!)
    chk.inputs["Color1"].default_value = (0.045, 0.048, 0.055, 1.0)
    chk.inputs["Color2"].default_value = (0.48, 0.39, 0.25, 1.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.05
    nt.links.new(tc.outputs["Object"], chk.inputs["Vector"])
    nt.links.new(chk.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


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


def instance_obj(proto, name, loc, rot=(0, 0, 0), scale=(1, 1, 1), mat=None):
    inst = proto.copy()
    inst.data = proto.data.copy() if mat else proto.data
    inst.name = name
    inst.rotation_mode = "XYZ"
    inst.location = loc
    inst.rotation_euler = rot
    inst.scale = scale
    inst.hide_render = False
    if mat:
        inst.data.materials.clear()
        inst.data.materials.append(mat)
    bpy.context.collection.objects.link(inst)
    return inst


def add_box(name, loc, scale, mat, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "XYZ"
    o.scale = scale
    o.data.materials.clear()
    o.data.materials.append(mat)
    if bevel > 0:
        mod = o.modifiers.new("Bev", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return o


def add_cyl(name, loc, r, depth, mat, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "XYZ"
    o.data.materials.clear()
    o.data.materials.append(mat)
    return o


def add_3d_text(text, loc, size, mat, rot=(0, 0, 0), extrude=0.05):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.active_object
    t.rotation_mode = "XYZ"
    t.data.body = text
    t.data.size = size
    t.data.extrude = extrude
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    font_path = os.path.join(SCRIPT_DIR, "fonts", "Cinzel-Bold.ttf")
    if os.path.exists(font_path):
        t.data.font = bpy.data.fonts.load(font_path)
    t.data.materials.clear()
    t.data.materials.append(mat)
    return t


def setup_world(col=(0.004, 0.005, 0.009), strength=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*col, 1.0)
    bg.inputs[1].default_value = strength


def add_spot_light(name, loc, rot_deg, energy, size=1.2, spot_deg=55.0, blend=0.55, col=(1.0, 0.78, 0.48)):
    ld = bpy.data.lights.new(name, type="SPOT")
    ld.energy = energy
    ld.shadow_soft_size = size
    ld.spot_size = math.radians(spot_deg)
    ld.spot_blend = blend
    ld.color = col
    lo = bpy.data.objects.new(name, ld)
    lo.rotation_mode = "XYZ"
    lo.location = loc
    lo.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.collection.objects.link(lo)
    return lo


def add_point_light(name, loc, energy, radius=0.25, col=(1.0, 0.72, 0.35)):
    ld = bpy.data.lights.new(name, type="POINT")
    ld.energy = energy
    ld.shadow_soft_size = radius
    ld.color = col
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    bpy.context.collection.objects.link(lo)
    return lo


def add_camera(loc, rot_deg, lens=32.0, dof_dist=0.0, fstop=2.8):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    if dof_dist > 0:
        cd.dof.use_dof = True
        cd.dof.focus_distance = dof_dist
        cd.dof.aperture_fstop = fstop
    co = bpy.data.objects.new("Cam", cd)
    co.rotation_mode = "XYZ"
    co.location = loc
    co.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.collection.objects.link(co)
    bpy.context.scene.camera = co
    return co


# ==============================================================================
# SCENE BUILDERS + FRAME ANIMATORS
# ==============================================================================
def build_scene_0():
    """Scene 0 (Frames 0..299): 3D Cutaway of Yusupov Palace, Moika Canal & Petrograd City Blocks."""
    scene = configure_cycles()
    setup_world((0.004, 0.006, 0.012), 1.0)

    mat_stucco_gold = make_rich_stone_mat("PalaceOchre", (0.58, 0.44, 0.20), (0.38, 0.27, 0.11), rough=0.34, scale=6.0)
    mat_granite = make_rich_stone_mat("MoikaGranite", (0.14, 0.15, 0.18), (0.07, 0.08, 0.10), rough=0.38, scale=9.0)
    mat_city_block = make_rich_stone_mat("PetrogradCity", (0.06, 0.07, 0.09), (0.03, 0.04, 0.05), rough=0.45, scale=8.0)
    mat_vault_stone = make_rich_stone_mat("VaultStone", (0.34, 0.29, 0.24), (0.18, 0.15, 0.12), rough=0.42, scale=7.0)
    mat_white_col = make_rich_stone_mat("WhiteCol", (0.86, 0.83, 0.77), (0.68, 0.64, 0.58), rough=0.25, sss=0.25)
    mat_snow = make_rich_stone_mat("WinterSnow", (0.72, 0.78, 0.88), (0.52, 0.58, 0.70), rough=0.45, coat=0.3, scale=5.0)
    mat_ice = make_pbr_mat("CanalIce", (0.02, 0.05, 0.09), rough=0.06, metal=0.15, coat=0.9)
    mat_cut_red = make_pbr_mat("CutEdgeRed", (0.85, 0.10, 0.12), rough=0.25, emit_col=(0.90, 0.12, 0.14), emit_str=1.4)
    mat_wood_dark = make_rich_stone_mat("Mahogany", (0.18, 0.09, 0.04), (0.09, 0.04, 0.02), rough=0.22, coat=0.5, scale=10.0)
    mat_carpet_red = make_rich_stone_mat("RussianCarpet", (0.48, 0.04, 0.06), (0.28, 0.02, 0.03), rough=0.65, scale=12.0)
    mat_win_glow = make_pbr_mat("WindowWarm", (1.0, 0.76, 0.36), rough=0.1, emit_col=(1.0, 0.74, 0.32), emit_str=4.5)
    mat_iron = make_pbr_mat("WroughtIron", (0.05, 0.05, 0.06), rough=0.25, metal=0.85)
    mat_text_white = make_pbr_mat("TextWhite", (0.98, 0.96, 0.92), rough=0.15, emit_col=(0.98, 0.96, 0.92), emit_str=2.2)
    mat_text_gold = make_pbr_mat("TextGold", (1.0, 0.80, 0.32), rough=0.15, emit_col=(1.0, 0.80, 0.32), emit_str=2.5)
    mat_step_on = make_pbr_mat("FootstepOn", (1.0, 0.12, 0.15), rough=0.15, emit_col=(1.0, 0.14, 0.18), emit_str=5.5)
    mat_step_off = make_pbr_mat("FootstepOff", (0.25, 0.04, 0.05), rough=0.5, emit_col=(0.25, 0.04, 0.05), emit_str=0.2)

    # Dark diorama plinth + surrounding Petrograd urban blocks (like Imperial's surrounding city context)
    add_box("DioramaPlinth", (0.0, 0.0, -0.85), (26.0, 18.0, 0.7), mat_granite, bevel=0.04)
    city_blocks = [
        (-13.5, 5.5, 4.2, 5.5, 2.8), (-13.5, -1.5, 4.2, 6.2, 2.4), (-13.5, -7.5, 4.2, 4.2, 2.1),
        (-2.0, 9.2, 7.5, 3.2, 3.0), (6.5, 9.2, 7.2, 3.2, 2.7), (12.8, 3.5, 3.8, 6.5, 2.6),
        (12.8, -3.8, 3.8, 6.2, 2.2), (4.5, -8.8, 8.5, 2.6, 1.8), (-4.5, -8.8, 7.2, 2.6, 1.9),
    ]
    for idx_b, (bx, by, sx, sy, sz) in enumerate(city_blocks):
        add_box(f"CityBlock_{idx_b}", (bx, by, -0.5 + sz * 0.5), (sx, sy, sz), mat_city_block, bevel=0.03)
        add_box(f"CityRoof_{idx_b}", (bx, by, -0.5 + sz + 0.06), (sx + 0.15, sy + 0.15, 0.10), mat_snow)

    # 1. Frozen Moika Canal + Arched Stone Bridge + Embankment Streetlamps
    add_box("MoikaIce", (-8.0, 0.0, -0.42), (4.8, 16.5, 0.10), mat_ice)
    add_box("EmbankmentL", (-10.5, 0.0, 0.0), (0.65, 16.5, 0.95), mat_granite)
    add_box("EmbankmentR", (-5.3, 0.0, 0.0), (0.65, 16.5, 0.95), mat_granite)
    # Stone Bridge across Moika Canal
    add_box("MoikaBridgeDeck", (-7.9, -5.8, 0.55), (5.4, 2.2, 0.28), mat_granite, bevel=0.03)
    add_box("MoikaBridgeSnow", (-7.9, -5.8, 0.71), (5.2, 1.9, 0.05), mat_snow)
    # Wrought-iron railings & glowing streetlamps along Moika Embankment
    for ly in [-6.5, -3.5, -0.5, 2.5, 5.5]:
        add_cyl(f"LampPost_{ly}", (-5.1, ly, 0.95), 0.05, 1.1, mat_iron, verts=12)
        add_cyl(f"LampGlobe_{ly}", (-5.1, ly, 1.55), 0.14, 0.22, mat_win_glow, verts=16)
        add_point_light(f"LampLight_{ly}", (-5.1, ly, 1.65), 18.0, radius=0.2, col=(1.0, 0.72, 0.32))
    add_box("IronRailBar", (-5.1, 0.0, 0.78), (0.05, 15.6, 0.06), mat_iron)

    # 2. Yusupov Palace Courtyard & Neoclassical Wings (-4.8 .. +2.6)
    add_box("CourtyardFloor", (-1.0, 0.0, 0.42), (7.8, 13.8, 0.16), make_checker_marble_floor_mat("CourtFloor", 12.0))
    # Snow parterres + courtyard stone fountain
    for px, py in [(-2.6, -1.8), (0.6, -1.8), (-2.6, 1.6), (0.6, 1.6)]:
        add_box(f"SnowBed_{px}_{py}", (px, py, 0.52), (2.2, 2.2, 0.08), mat_snow, bevel=0.02)
        add_cyl(f"Cypress_{px}_{py}", (px, py, 1.05), 0.32, 1.1, mat_city_block, verts=16)
        add_cyl(f"CypressSnow_{px}_{py}", (px, py, 1.45), 0.22, 0.4, mat_snow, verts=16)
    add_cyl("CourtFountainRim", (-1.0, -0.1, 0.58), 0.85, 0.22, mat_white_col, verts=32)
    add_cyl("CourtFountainSpire", (-1.0, -0.1, 0.95), 0.22, 0.75, mat_white_col, verts=24)

    # Palace Main North Facade + Glowing Windows + Cutaway Red Rim
    add_box("PalaceNorthWall", (-0.8, 5.2, 2.6), (8.2, 0.55, 4.4), mat_stucco_gold)
    add_box("PalaceNorthCut", (-0.8, 5.2, 4.85), (8.3, 0.60, 0.12), mat_cut_red)
    for wx in [-3.8, -2.6, -1.4, -0.2, 1.0, 2.2]:
        for wz in [1.6, 3.3]:
            add_box(f"WinN_{wx}_{wz}", (wx, 4.90, wz), (0.62, 0.08, 0.95), mat_win_glow)
            add_box(f"WinFrameN_{wx}_{wz}", (wx, 4.88, wz + 0.52), (0.74, 0.14, 0.10), mat_white_col)

    # Palace West Wing (facing Moika Canal) + Glowing Windows
    add_box("PalaceWestWall", (-4.6, 0.2, 2.3), (0.55, 10.4, 3.8), mat_stucco_gold)
    add_box("PalaceWestCut", (-4.6, 0.2, 4.25), (0.60, 10.5, 0.12), mat_cut_red)
    for wy in [-3.6, -1.8, 0.0, 1.8, 3.6]:
        add_box(f"WinW_{wy}", (-4.30, wy, 2.2), (0.08, 0.65, 1.05), mat_win_glow)

    col_proto = load_blend_asset("bk_column_corinthian.blend", "ColProto", target_height=3.8, mat=mat_white_col)
    if col_proto:
        col_proto.hide_render = True
        for cx in [-3.6, -2.4, -1.2, 0.0, 1.2, 2.4]:
            instance_obj(col_proto, f"ColN_{cx}", (cx, 4.65, 0.50))

    # 3. Upper Cutaway: Grand Drawing Room (X = 2.6..8.8, Y = 1.2..5.4, Z = 2.4)
    add_box("DrawingFloor", (5.6, 3.2, 2.40), (6.2, 4.4, 0.18), mat_wood_dark)
    add_box("DrawingRug", (5.6, 3.2, 2.51), (4.2, 2.8, 0.03), mat_carpet_red)
    add_box("DrawingBackWall", (5.6, 5.3, 3.65), (6.2, 0.42, 2.5), mat_stucco_gold)
    add_box("DrawingBackCut", (5.6, 5.3, 4.94), (6.3, 0.48, 0.12), mat_cut_red)

    # 4. Lower Cutaway: Soundproofed Basement + Vaulted Stone Arches (X = 2.6..9.2, Y = -4.8..1.2, Z = 0.0)
    add_box("BasementFloor", (5.8, -1.8, 0.05), (6.6, 6.2, 0.18), make_checker_marble_floor_mat("BaseFloor", 8.0))
    add_box("BasementRug", (5.8, -1.8, 0.16), (4.2, 3.8, 0.03), mat_carpet_red)
    add_box("BasementRightWall", (9.0, -0.8, 1.35), (0.45, 8.4, 2.6), mat_vault_stone)
    add_box("BasementRightCut", (9.0, -0.8, 2.70), (0.50, 8.5, 0.12), mat_cut_red)
    for ay in [-3.8, -1.8, 0.2]:
        add_box(f"VaultRibL_{ay}", (2.8, ay, 1.25), (0.42, 0.42, 2.3), mat_vault_stone)
        add_box(f"VaultRibR_{ay}", (8.6, ay, 1.25), (0.42, 0.42, 2.3), mat_vault_stone)
        add_box(f"VaultArch_{ay}", (5.7, ay, 2.35), (6.2, 0.38, 0.26), mat_vault_stone)

    # Spiral Staircase connecting Drawing Room & Courtyard down to Basement
    for s in range(10):
        sx = 2.2 + s * 0.22
        sy = 1.6 - s * 0.36
        sz = 2.35 - s * 0.22
        add_box(f"Stair_{s}", (sx, sy, sz), (0.85, 0.38, 0.12), mat_white_col)

    # Populate Basement & Drawing Room with BlenderKit Models
    tbl_proto = load_blend_asset("bk_table_round.blend", "TblProto", target_height=0.80, mat=mat_wood_dark)
    if tbl_proto:
        tbl_proto.hide_render = True
        instance_obj(tbl_proto, "BasementTable", (5.8, -1.8, 0.18), scale=(1.4, 1.4, 1.1))
        instance_obj(tbl_proto, "DrawingTable", (5.6, 3.2, 2.52), scale=(1.2, 1.2, 1.0))

    ras_proto = load_blend_asset("bk_bearded_statue.blend", "RasProto", target_height=1.85, mat=mat_white_col)
    if ras_proto:
        ras_proto.hide_render = True
        instance_obj(ras_proto, "RasputinBase", (4.8, -1.8, 0.18), rot=(0, 0, math.radians(80)))

    yus_proto = load_blend_asset("bk_male_sitting.blend", "YusProto", target_height=1.38, mat=mat_text_gold)
    if yus_proto:
        yus_proto.hide_render = True
        instance_obj(yus_proto, "YusupovBase", (6.8, -1.8, 0.18), rot=(0, 0, math.radians(-85)))

    con_proto = load_blend_asset("bk_decor_man.blend", "ConProto", target_height=1.76, mat=mat_white_col)
    if con_proto:
        con_proto.hide_render = True
        instance_obj(con_proto, "Con1", (4.5, 3.3, 2.52), rot=(0, 0, math.radians(-30)))
        instance_obj(con_proto, "Con2", (6.6, 3.4, 2.52), rot=(0, 0, math.radians(25)))
        instance_obj(con_proto, "Con3", (5.6, 4.1, 2.52), rot=(0, 0, math.radians(0)))

    # Animated Footstep Dots (12 steps lighting up sequentially as frame progresses)
    trail_pts = [
        (-3.2, -3.2, 0.54), (-2.2, -2.2, 0.54), (-1.2, -1.2, 0.54), (-0.2, -0.2, 0.54),
        (0.8, 0.6, 0.54), (1.6, 1.2, 1.25), (2.3, 1.5, 2.25), (2.7, 0.8, 1.75),
        (3.1, 0.0, 1.20), (3.5, -0.8, 0.65), (4.0, -1.4, 0.24), (4.5, -1.8, 0.22),
    ]
    step_objs = []
    for idx_p, pt in enumerate(trail_pts):
        so = add_cyl(f"StepDot_{idx_p}", pt, 0.20, 0.07, mat_step_on, verts=24)
        step_objs.append(so)

    # 3D World-Locked Extruded Architectural Typography
    add_3d_text("MOIKA CANAL", (-8.0, -2.5, 0.18), 0.62, mat_text_white, rot=(math.radians(52), 0, math.radians(-18)), extrude=0.06)
    add_3d_text("YUSUPOV COURTYARD", (-1.0, -3.6, 0.72), 0.58, mat_text_white, rot=(math.radians(52), 0, math.radians(-18)), extrude=0.06)
    add_3d_text("GRAND DRAWING ROOM", (5.6, 4.2, 5.25), 0.55, mat_text_gold, rot=(math.radians(54), 0, math.radians(-18)), extrude=0.06)
    add_3d_text("SOUNDPROOFED BASEMENT", (4.5, -4.6, 0.72), 0.44, mat_text_gold, rot=(math.radians(52), 0, math.radians(-18)), extrude=0.06)

    # Chiaroscuro Dramatic Lighting (No flat wash-out!)
    add_spot_light("MoonKey", (-12.0, -14.0, 16.0), (46, -15, -28), 2200.0, size=3.5, spot_deg=68.0, col=(0.55, 0.74, 1.0))
    add_point_light("BasementCandleGlow", (5.8, -1.8, 1.85), 260.0, radius=0.6, col=(1.0, 0.68, 0.28))
    add_point_light("DrawingRoomGlow", (5.6, 3.2, 4.15), 220.0, radius=0.8, col=(1.0, 0.76, 0.38))
    add_point_light("CourtyardWarmFill", (-0.8, 3.5, 2.8), 160.0, radius=1.2, col=(1.0, 0.78, 0.45))

    cam = add_camera(loc=(-8.4, -16.8, 11.8), rot_deg=(54.5, 0.0, -21.0), lens=31.0, dof_dist=18.5, fstop=4.0)

    def update_frame(f):
        u = smoothstep((f - 0.0) / 299.0)
        # Smooth orbital crane push-in toward the cutaway basement
        cam.location = (
            lerp(-9.2, -6.2, u),
            lerp(-17.4, -14.2, u),
            lerp(12.4, 9.8, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(54.0, 56.5, u)),
            0.0,
            math.radians(lerp(-23.5, -16.5, u)),
        )
        # Sequentially illuminate footsteps leading into the basement
        active_steps = int(lerp(2, len(step_objs) + 1, clamp((f - 10) / 220.0)))
        for idx_s, so in enumerate(step_objs):
            so.data.materials[0] = mat_step_on if idx_s <= active_steps else mat_step_off

    return scene, update_frame


def build_scene_1():
    """Scene 1 (Frames 300..599): 3D Soundproofed Basement Banquet Tableau (Rasputin vs. Yusupov)."""
    scene = configure_cycles()
    setup_world((0.005, 0.004, 0.008), 1.0)

    # Rich dark obsidian & antique gold checkerboard marble floor + multi-bordered Russian crimson rug
    mat_floor = make_checker_marble_floor_mat("BasementMarbleFloor", scale=12.0)
    add_box("BasementMainFloor", (0.0, 0.5, -0.05), (14.0, 13.0, 0.10), mat_floor)

    mat_rug_crimson = make_rich_stone_mat("RugCrimson", (0.46, 0.03, 0.05), (0.26, 0.015, 0.025), rough=0.68, scale=14.0)
    mat_rug_gold = make_pbr_mat("RugGoldTrim", (0.82, 0.62, 0.22), rough=0.35, metal=0.65)
    add_box("RugOuterGold", (0.1, 0.4, 0.004), (4.6, 3.6, 0.008), mat_rug_gold)
    add_box("RugInnerCrimson", (0.1, 0.4, 0.009), (4.3, 3.3, 0.010), mat_rug_crimson)
    add_box("RugCenterMedallion", (0.1, 0.4, 0.015), (2.2, 1.6, 0.008), mat_rug_gold)

    mat_vault = make_rich_stone_mat("CellarStone", (0.22, 0.19, 0.16), (0.10, 0.08, 0.07), rough=0.44, coat=0.15, scale=7.0, bump_str=0.22)
    mat_wainscot = make_rich_stone_mat("DarkWalnutPanel", (0.14, 0.07, 0.03), (0.07, 0.03, 0.015), rough=0.24, coat=0.55, scale=9.0)
    mat_col = make_rich_stone_mat("PilasterMarble", (0.72, 0.66, 0.56), (0.50, 0.44, 0.36), rough=0.24, coat=0.35, sss=0.2)
    mat_gold = make_pbr_mat("AntiqueBrass", (0.92, 0.72, 0.26), rough=0.18, metal=0.90)
    mat_ruby_wine = make_pbr_mat("RubyWine", (0.65, 0.03, 0.06), rough=0.08, coat=0.9, emit_col=(0.55, 0.02, 0.05), emit_str=0.45)
    mat_flame = make_pbr_mat("CandleFlame", (1.0, 0.82, 0.38), rough=0.1, emit_col=(1.0, 0.78, 0.32), emit_str=8.0)

    # Distinct sculpted materials for Rasputin (dark bronze-cloaked mystic with warm ivory face/hands) & Yusupov (alabaster aristocrat)
    mat_rasputin = make_rich_stone_mat("RasputinMarble", (0.86, 0.80, 0.70), (0.62, 0.54, 0.44), rough=0.22, coat=0.35, sss=0.38, scale=5.0)
    mat_yusupov = make_rich_stone_mat("YusupovMarble", (0.90, 0.87, 0.82), (0.72, 0.68, 0.62), rough=0.20, coat=0.40, sss=0.40, scale=5.0)
    mat_conspirator = make_rich_stone_mat("ShadowConspirator", (0.52, 0.50, 0.48), (0.34, 0.32, 0.30), rough=0.32, scale=5.0)

    # Basement Walls + Lower Walnut Wainscoting Panels
    add_box("RearWall", (0.0, 5.6, 3.2), (13.6, 0.5, 6.6), mat_vault)
    add_box("RearWainscot", (0.0, 5.32, 0.85), (13.4, 0.12, 1.7), mat_wainscot)
    add_box("LeftWall", (-6.0, 0.0, 3.2), (0.5, 11.6, 6.6), mat_vault)
    add_box("LeftWainscot", (-5.72, 0.0, 0.85), (0.12, 11.4, 1.7), mat_wainscot)
    add_box("RightWall", (6.0, 0.0, 3.2), (0.5, 11.6, 6.6), mat_vault)
    add_box("RightWainscot", (5.72, 0.0, 0.85), (0.12, 11.4, 1.7), mat_wainscot)

    # Vaulted Stone Ceiling Arches & Ribs
    for vy in [-2.0, 0.6, 3.2, 5.2]:
        add_box(f"VaultPillarL_{vy}", (-4.8, vy, 2.7), (0.62, 0.62, 5.4), mat_vault, bevel=0.03)
        add_box(f"VaultPillarR_{vy}", (4.8, vy, 2.7), (0.62, 0.62, 5.4), mat_vault, bevel=0.03)
        add_box(f"VaultBeam_{vy}", (0.0, vy, 5.2), (10.2, 0.55, 0.50), mat_vault, bevel=0.03)

    # Wall Sconces with Warm Flickering Point Lights
    for sx, sy in [(-4.4, 2.0), (4.4, 2.0), (-2.6, 5.1), (2.6, 5.1)]:
        add_cyl(f"SconcePlate_{sx}_{sy}", (sx, sy, 2.35), 0.14, 0.06, mat_gold, verts=20)
        add_cyl(f"SconceCandle_{sx}_{sy}", (sx, sy - 0.12, 2.50), 0.04, 0.24, mat_Flame := mat_flame, verts=12)
        add_point_light(f"SconceLight_{sx}_{sy}", (sx, sy - 0.18, 2.65), 45.0, radius=0.25, col=(1.0, 0.70, 0.32))

    # Rear Heavy Cellar Doors & Corinthian Columns
    door_proto = load_blend_asset("bk_classic_door.blend", "DoorProto", target_height=3.6, mat=mat_wainscot)
    if door_proto:
        door_proto.location = (0.0, 5.25, 0.0)

    col_proto = load_blend_asset("bk_column_corinthian.blend", "ColProto", target_height=5.0, mat=mat_col)
    if col_proto:
        col_proto.hide_render = True
        for cx in [-3.8, -1.8, 1.8, 3.8]:
            instance_obj(col_proto, f"BgCol_{cx}", (cx, 4.95, 0.0))

    # Upper Staircase Balcony Landing with 3 Waiting Co-Conspirators
    add_box("BalconySlab", (0.0, 4.4, 2.55), (7.4, 1.5, 0.20), mat_vault, bevel=0.02)
    add_box("BalconyRail", (0.0, 3.72, 3.05), (7.2, 0.08, 0.08), mat_gold)
    for bx in range(-32, 34, 4):
        add_cyl(f"Baluster_{bx}", (bx * 0.1, 3.72, 2.80), 0.025, 0.48, mat_gold, verts=12)

    con_proto = load_blend_asset("bk_decor_man.blend", "ConProto", target_height=1.74, mat=mat_conspirator)
    if con_proto:
        con_proto.hide_render = True
        for idx_c, cx in enumerate([-2.2, 0.0, 2.2]):
            instance_obj(con_proto, f"UpperCon_{idx_c}", (cx, 4.3, 2.65), rot=(0, 0, math.radians(180)))

    # Centerpiece Poisoned Banquet Table + Candelabra + Madeira Wine + Cyanide Pastries
    tbl_proto = load_blend_asset("bk_table_round.blend", "BanquetTable", target_height=0.84, mat=mat_wainscot)
    if tbl_proto:
        tbl_proto.location = (0.15, 0.40, 0.0)
        tbl_proto.scale = (1.60, 1.60, 1.08)

    # Golden tray + rose-cream cyanide pastries
    add_cyl("SilverPlatter", (0.0, 0.34, 0.91), 0.25, 0.025, mat_gold, verts=36)
    for px, py in [(-0.08, 0.30), (0.08, 0.28), (0.0, 0.42), (-0.06, 0.40), (0.07, 0.39)]:
        add_cyl(f"PastryBase_{px}_{py}", (px, py, 0.94), 0.048, 0.045, mat_col, verts=20)
        add_cyl(f"PastryTop_{px}_{py}", (px, py, 0.97), 0.038, 0.025, mat_ruby_wine, verts=20)

    bot_proto = load_blend_asset("bk_wine_bottle.blend", "WineBot", target_height=0.38, mat=mat_ruby_wine)
    if bot_proto:
        bot_proto.location = (0.38, 0.50, 0.89)

    gob_proto = load_blend_asset("bk_goblet.blend", "GobletProto", target_height=0.23, mat=mat_gold)
    if gob_proto:
        gob_proto.hide_render = True
        instance_obj(gob_proto, "GobletRas", (-0.30, 0.30, 0.89))
        instance_obj(gob_proto, "GobletYus", (0.50, 0.26, 0.89))
        instance_obj(gob_proto, "GobletMid", (0.16, 0.18, 0.89))

    cand_proto = load_blend_asset("bk_candelabra.blend", "Candelabra", target_height=0.48, mat=mat_gold)
    if cand_proto:
        cand_proto.location = (0.16, 0.62, 0.89)
    # Warm glowing candle flame light right above the table candelabra!
    table_candle_light = add_point_light("TableCandleLight", (0.16, 0.40, 1.55), 165.0, radius=0.35, col=(1.0, 0.72, 0.32))

    # Grigori Rasputin (Left of Table, turned 3/4 toward camera & table so his bearded face is clearly visible!)
    ras_obj = load_blend_asset("bk_bearded_statue.blend", "RasputinMain", target_height=1.92, mat=mat_rasputin)
    if ras_obj:
        ras_obj.location = (-0.98, 0.42, 0.02)
        ras_obj.rotation_euler = (0.0, 0.0, math.radians(28.0))

    # Prince Felix Yusupov (Right of Table, Seated on Ornate Chair facing Rasputin)
    chair_proto = load_blend_asset("bk_antique_chair.blend", "ChairProto", target_height=0.92, mat=mat_wainscot)
    if chair_proto:
        chair_proto.hide_render = True
        instance_obj(chair_proto, "YusChair", (1.32, 0.38, 0.02), rot=(0, 0, math.radians(-62)))
        instance_obj(chair_proto, "RasChair", (-1.45, 0.68, 0.02), rot=(0, 0, math.radians(48)))

    yus_obj = load_blend_asset("bk_male_sitting.blend", "YusupovMain", target_height=1.42, mat=mat_yusupov)
    if yus_obj:
        yus_obj.location = (1.22, 0.36, 0.04)
        yus_obj.rotation_euler = (0.0, 0.0, math.radians(-52.0))

    # Dramatic Chiaroscuro Spotlights (Warm Overhead Spot on Table/Characters + Cold Moonlight Rim from Upper Window)
    add_spot_light("MainTableSpot", (-0.3, -2.2, 3.6), (42, 0, -8), 680.0, size=1.4, spot_deg=52.0, col=(1.0, 0.82, 0.56))
    add_spot_light("ColdCellarRim", (-4.8, 1.8, 4.0), (58, 0, -58), 520.0, size=1.8, spot_deg=58.0, col=(0.42, 0.68, 1.0))
    add_spot_light("BalconyRim", (0.0, 2.2, 4.8), (-32, 0, 0), 340.0, size=2.2, spot_deg=65.0, col=(0.95, 0.68, 0.36))

    cam = add_camera(loc=(-0.45, -4.60, 2.05), rot_deg=(75.5, 0.0, -5.0), lens=31.0, dof_dist=5.0, fstop=2.8)

    def update_frame(f):
        u = smoothstep((f - 300.0) / 299.0)
        # Slow, tense cinematic dolly-in toward Rasputin and the poisoned wine table
        cam.location = (
            lerp(-0.55, -0.15, u),
            lerp(-4.85, -3.55, u),
            lerp(2.18, 1.68, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(74.5, 78.5, u)),
            0.0,
            math.radians(lerp(-6.0, -1.8, u)),
        )
        # Subtle candle flicker & subtle turn of Rasputin toward the poisoned goblet
        table_candle_light.data.energy = 165.0 + 18.0 * math.sin(f * 0.35)
        if ras_obj:
            ras_obj.rotation_euler = (0.0, 0.0, math.radians(lerp(24.0, 36.0, u)))

    return scene, update_frame


def build_scene_2():
    """Scene 2 (Frames 600..899): Animated 3D Sliced Marble Bust of Rasputin + Red Laser Core."""
    scene = configure_cycles()
    setup_world((0.012, 0.004, 0.006), 1.0)

    # Polished Carrara marble exterior + deep bloody crimson sculpted interior (matching Imperial's Pompey bust!)
    mat_marble_ext = make_rich_stone_mat("CarraraMarble", (0.88, 0.85, 0.80), (0.66, 0.62, 0.56), rough=0.18, coat=0.45, sss=0.38, scale=5.0)
    mat_crimson_flesh = make_rich_stone_mat("CrimsonCoreFlesh", (0.72, 0.04, 0.06), (0.38, 0.01, 0.02), rough=0.22, coat=0.4, scale=7.0)
    mat_laser_red = make_pbr_mat("LaserBeamRed", (1.0, 0.08, 0.12), rough=0.1, emit_col=(1.0, 0.10, 0.14), emit_str=9.5)
    mat_podium_disc = make_pbr_mat("PodiumDiscRed", (0.85, 0.06, 0.09), rough=0.15, emit_col=(0.92, 0.08, 0.12), emit_str=3.2)
    mat_plinth = make_rich_stone_mat("ObsidianPlinth", (0.06, 0.06, 0.08), (0.02, 0.02, 0.03), rough=0.16, coat=0.6, scale=8.0)
    mat_silver_medallion = make_rich_stone_mat("ImperialSilver", (0.76, 0.78, 0.82), (0.42, 0.44, 0.48), rough=0.24, metal=0.88, scale=10.0)
    mat_gold_rim = make_pbr_mat("ImperialGoldRim", (0.95, 0.76, 0.28), rough=0.20, metal=0.92)

    bx_center = 0.42
    add_cyl("PodiumBase", (bx_center, 0.0, -0.08), 1.45, 0.12, mat_plinth, verts=64)
    add_cyl("PodiumGlowRing", (bx_center, 0.0, 0.005), 0.92, 0.018, mat_podium_disc, verts=64)

    # Ornate Multi-Ring Imperial Medallion Halo behind the Bust
    add_cyl("MedallionDisc", (bx_center, 0.55, 0.68), 0.72, 0.04, mat_silver_medallion, verts=64, rot=(math.radians(90), 0, 0))
    add_cyl("MedallionGoldRim", (bx_center, 0.53, 0.68), 0.52, 0.05, mat_gold_rim, verts=48, rot=(math.radians(90), 0, 0))

    bust_orig = load_blend_asset("bk_rasputin_bust.blend", "RasBustOrig", target_height=1.18, mat=mat_marble_ext)
    b_low = None
    b_high = None
    b_core = None
    laser_beam = None

    if bust_orig:
        bust_orig.hide_render = True
        plane_co = mathutils.Vector((0.0, 0.0, 0.58))
        plane_no = mathutils.Vector((0.62, 0.0, 0.78)).normalized()

        # 1. Lower-Left White Marble Half
        b_low = bust_orig.copy()
        b_low.data = bust_orig.data.copy()
        b_low.hide_render = False
        b_low.rotation_mode = "XYZ"
        bpy.context.collection.objects.link(b_low)
        bm1 = bmesh.new()
        bm1.from_mesh(b_low.data)
        bmesh.ops.bisect_plane(
            bm1,
            geom=bm1.verts[:] + bm1.edges[:] + bm1.faces[:],
            plane_co=plane_co,
            plane_no=plane_no,
            clear_outer=True,
            clear_inner=False,
        )
        bm1.to_mesh(b_low.data)
        bm1.free()

        # 2. Inner Crimson Core Bust (slightly scaled down inside the split so the interior head is deep crimson!)
        b_core = bust_orig.copy()
        b_core.data = bust_orig.data.copy()
        b_core.hide_render = False
        b_core.rotation_mode = "XYZ"
        b_core.data.materials.clear()
        b_core.data.materials.append(mat_crimson_flesh)
        bpy.context.collection.objects.link(b_core)
        b_core.scale = (0.94, 0.94, 0.94)

        # 3. Upper-Right Exploded Marble Half
        b_high = bust_orig.copy()
        b_high.data = bust_orig.data.copy()
        b_high.hide_render = False
        b_high.rotation_mode = "XYZ"
        bpy.context.collection.objects.link(b_high)
        bm2 = bmesh.new()
        bm2.from_mesh(b_high.data)
        bmesh.ops.bisect_plane(
            bm2,
            geom=bm2.verts[:] + bm2.edges[:] + bm2.faces[:],
            plane_co=plane_co,
            plane_no=plane_no,
            clear_outer=False,
            clear_inner=True,
        )
        bm2.to_mesh(b_high.data)
        bm2.free()

        # Diagonal Glowing Red Laser Streak across the slice plane
        laser_beam = add_box(
            "CrimsonLaserStreak",
            (bx_center + 0.04, -0.18, 0.64),
            (2.40, 0.014, 0.018),
            mat_laser_red,
            rot=(0.0, math.radians(-38.0), 0.0),
        )

    add_spot_light("BustKey", (-2.6, -2.8, 2.4), (55, 0, -38), 420.0, size=1.2, spot_deg=50.0, col=(1.0, 0.96, 0.90))
    add_spot_light("BustRimCrimson", (2.6, 1.4, 1.8), (62, 0, 128), 580.0, size=1.4, spot_deg=55.0, col=(1.0, 0.12, 0.16))
    add_point_light("CoreGlowLight", (bx_center + 0.05, -0.25, 0.65), 85.0, radius=0.25, col=(1.0, 0.10, 0.14))

    cam = add_camera(loc=(0.0, -3.55, 0.66), rot_deg=(87.5, 0.0, 0.0), lens=36.0, dof_dist=3.55, fstop=2.8)

    def update_frame(f):
        u = smoothstep((f - 600.0) / 299.0)
        split_t = smoothstep((f - 625.0) / 140.0)
        rot_z = math.radians(lerp(-32.0, -14.0, u))
        if b_low:
            b_low.location = (bx_center - lerp(0.0, 0.06, split_t), 0.0, 0.02)
            b_low.rotation_euler = (0.0, 0.0, rot_z)
        if b_core:
            b_core.location = (bx_center + lerp(0.0, 0.04, split_t), 0.02, 0.05)
            b_core.rotation_euler = (0.0, 0.0, rot_z)
        if b_high:
            b_high.location = (
                bx_center + lerp(0.0, 0.18, split_t),
                0.0,
                0.02 + lerp(0.0, 0.18, split_t),
            )
            b_high.rotation_euler = (0.0, math.radians(lerp(0.0, 7.5, split_t)), rot_z)
        if laser_beam:
            laser_beam.scale = (lerp(0.1, 2.45, smoothstep((f - 610.0) / 60.0)), 0.014, 0.018)
        cam.location = (lerp(-0.12, 0.08, u), lerp(-3.68, -3.38, u), lerp(0.64, 0.70, u))

    return scene, update_frame


def build_scene_3():
    """Scene 3 (Frames 900..1199): 3D Tilted Obsidian Topographic Relief Map of Russia & 1916 Eastern Front."""
    scene = configure_cycles()
    setup_world((0.004, 0.006, 0.012), 1.0)

    # Crisp perspective wireframe grid in pitch-black void + dark obsidian relief terrain with neon-lit borders
    mat_grid = make_pbr_mat("GridWire", (0.55, 0.64, 0.78), rough=0.2, emit_col=(0.55, 0.64, 0.78), emit_str=0.55)
    mat_obsidian_russia = make_rich_stone_mat("ObsidianRussia", (0.04, 0.08, 0.18), (0.02, 0.04, 0.09), rough=0.22, coat=0.6, scale=6.0, bump_str=0.25)
    mat_blue_rim = make_pbr_mat("RussiaCobaltGlow", (0.14, 0.42, 0.95), rough=0.2, emit_col=(0.16, 0.48, 1.0), emit_str=2.2)
    mat_front_crimson = make_rich_stone_mat("FrontCrimson", (0.55, 0.04, 0.06), (0.28, 0.02, 0.03), rough=0.25, coat=0.5, scale=6.0, bump_str=0.28)
    mat_front_glow = make_pbr_mat("FrontGlowRim", (1.0, 0.12, 0.16), rough=0.15, emit_col=(1.0, 0.14, 0.18), emit_str=3.2)
    mat_neutral_dark = make_rich_stone_mat("NeutralDark", (0.05, 0.06, 0.08), (0.02, 0.03, 0.04), rough=0.38, scale=6.0)
    mat_gold_pin = make_pbr_mat("GoldPin", (1.0, 0.82, 0.25), rough=0.12, emit_col=(1.0, 0.82, 0.25), emit_str=4.5)
    mat_arrow_red = make_pbr_mat("ArrowRed", (1.0, 0.16, 0.18), rough=0.15, emit_col=(1.0, 0.16, 0.18), emit_str=3.5)

    # 1. Explicit 3D Perspective Grid Lines (Z = 0.0)
    for gx in range(-14, 15, 1):
        add_box(f"GridX_{gx}", (gx * 0.68, 0.0, 0.0), (0.012, 14.0, 0.006), mat_grid)
    for gy in range(-10, 11, 1):
        add_box(f"GridY_{gy}", (0.0, gy * 0.68, 0.0), (19.0, 0.012, 0.006), mat_grid)

    def proj(lon, lat):
        x = (lon - 27.5) * 0.36 + 0.85
        y = (lat - 54.5) * 0.48
        return x, y

    geo_path = os.path.join(ASSETS_DIR, "russia_eastern_front_50m.geojson")
    if os.path.exists(geo_path):
        with open(geo_path, "r") as f:
            gdata = json.load(f)

        russian_heartland = {"Russia", "Finland", "Estonia", "Latvia", "Belarus", "Ukraine"}
        eastern_front = {"Germany", "Poland", "Lithuania", "Austria", "Hungary", "Romania"}

        for feat in gdata.get("features", []):
            cname = feat.get("properties", {}).get("NAME", "")
            geom = feat.get("geometry", {})
            gtype = geom.get("type")
            coords = geom.get("coordinates", [])
            polys = coords if gtype == "MultiPolygon" else [coords]

            if cname in russian_heartland:
                cmat = mat_obsidian_russia
                rmat = mat_blue_rim
                z_off = 0.06
                ext = 0.12
            elif cname in eastern_front:
                cmat = mat_front_crimson
                rmat = mat_front_glow
                z_off = 0.09
                ext = 0.15
            else:
                cmat = mat_neutral_dark
                rmat = None
                z_off = 0.04
                ext = 0.08

            curve_data = bpy.data.curves.new(f"Map_{cname}", type="CURVE")
            curve_data.dimensions = "2D"
            curve_data.fill_mode = "BOTH"
            curve_data.extrude = ext
            curve_data.bevel_depth = 0.012

            # Glowing outline curve on top of the dark obsidian slab (authentic Imperial neon-border look!)
            rim_data = bpy.data.curves.new(f"Rim_{cname}", type="CURVE") if rmat else None
            if rim_data:
                rim_data.dimensions = "2D"
                rim_data.fill_mode = "NONE"
                rim_data.bevel_depth = 0.028

            has_pts = False
            for poly in polys:
                if not poly:
                    continue
                ring = poly[0]
                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]
                if max(lons) < 11.0 or min(lons) > 48.0 or max(lats) < 43.0 or min(lats) > 66.0:
                    continue
                pts = []
                for pt in ring:
                    lon = min(max(pt[0], 11.0), 46.5)
                    lat = min(max(pt[1], 43.5), 64.5)
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
                cobj = bpy.data.objects.new(f"Country_{cname}", curve_data)
                cobj.rotation_mode = "XYZ"
                cobj.location = (0.0, 0.0, z_off)
                cobj.data.materials.append(cmat)
                bpy.context.collection.objects.link(cobj)
                if rim_data:
                    robj = bpy.data.objects.new(f"RimObj_{cname}", rim_data)
                    robj.rotation_mode = "XYZ"
                    robj.location = (0.0, 0.0, z_off + ext + 0.015)
                    robj.data.materials.append(rmat)
                    bpy.context.collection.objects.link(robj)

    # 3D Displaced Mountain Ridges (Carpathians & Western Front Relief)
    random.seed(1916)
    for mx, my, mh in [
        (-0.8, -1.8, 0.42), (-0.4, -2.1, 0.48), (0.1, -2.3, 0.38),
        (1.8, 0.4, 0.32), (2.4, 1.2, 0.35), (3.1, -0.5, 0.30),
    ]:
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=0.55, radius2=0.04, depth=mh, location=(mx, my, 0.22 + mh * 0.5))
        m_cone = bpy.context.active_object
        m_cone.rotation_euler = (0, 0, random.uniform(0, 3.14))
        m_cone.data.materials.append(mat_front_crimson if mx < 0.8 else mat_obsidian_russia)

    # Glowing Target Pin & Concentric Rings at Petrograd (59.93°N, 30.33°E)
    px, py = proj(30.33, 59.93)
    pin_base = add_cyl("PetrogradPinBase", (px, py, 0.24), 0.30, 0.05, mat_gold_pin, verts=40)
    pin_spire = add_cyl("PetrogradBeacon", (px, py, 0.68), 0.055, 0.88, mat_gold_pin, verts=20)

    arrow_objs = []
    for sx, sy, rot_z in [(-1.3, 0.3, -32), (-0.5, -1.5, -15), (2.3, -0.7, 22)]:
        ao = add_box(
            f"PlotArrow_{sx}",
            ((sx + px) * 0.5, (sy + py) * 0.5, 0.26),
            (0.07, math.hypot(px - sx, py - sy) * 0.78, 0.035),
            mat_arrow_red,
            rot=(0, 0, math.radians(rot_z)),
        )
        arrow_objs.append(ao)

    add_spot_light("MapTopSpot", (0.5, -5.5, 8.5), (34, 0, 0), 950.0, size=3.0, spot_deg=70.0, col=(0.75, 0.86, 1.0))
    add_point_light("PetrogradBeaconLight", (px, py, 1.2), 140.0, radius=0.4, col=(1.0, 0.78, 0.28))

    cam = add_camera(loc=(0.2, -7.8, 6.6), rot_deg=(46.5, 0.0, 0.0), lens=32.0)

    def update_frame(f):
        u = smoothstep((f - 900.0) / 299.0)
        cam.location = (
            lerp(-0.25, 0.65, u),
            lerp(-8.2, -6.6, u),
            lerp(7.1, 5.6, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(45.0, 48.5, u)),
            0.0,
            math.radians(lerp(-3.5, 2.5, u)),
        )
        pulse = 1.0 + 0.18 * math.sin(f * 0.25)
        pin_base.scale = (pulse, pulse, 1.0)

    return scene, update_frame


def build_scene_4():
    """Scene 4 (Frames 1200..1499): 90° Top-Down Forensic Crime Scene Crane Pull-Up."""
    scene = configure_cycles()
    setup_world((0.004, 0.005, 0.009), 1.0)

    # Wet-polished dark checkerboard marble floor + crimson carpet border
    mat_floor = make_checker_marble_floor_mat("CrimeFloorMarble", scale=12.0)
    add_box("CrimeMainFloor", (0.0, 0.0, -0.05), (12.0, 12.0, 0.10), mat_floor)

    mat_blood = make_pbr_mat("ForensicBlood", (0.45, 0.01, 0.015), rough=0.03, coat=1.0, emit_col=(0.35, 0.008, 0.01), emit_str=0.22)
    mat_rasputin_fallen = make_rich_stone_mat("FallenRasputin", (0.86, 0.81, 0.73), (0.62, 0.56, 0.48), rough=0.24, coat=0.35, sss=0.35, scale=5.0)
    mat_gun_steel = make_pbr_mat("WebleySteel", (0.76, 0.78, 0.82), rough=0.16, metal=0.92, emit_col=(0.76, 0.78, 0.82), emit_str=0.20)
    mat_gold_brass = make_pbr_mat("BrassShell", (0.96, 0.78, 0.28), rough=0.14, metal=0.94, emit_col=(0.96, 0.78, 0.28), emit_str=0.35)
    mat_walnut = make_rich_stone_mat("ChairWalnut", (0.20, 0.10, 0.04), (0.10, 0.04, 0.02), rough=0.22, coat=0.5, scale=7.0)
    mat_conspirator = make_rich_stone_mat("ConspiratorStone", (0.76, 0.73, 0.68), (0.52, 0.49, 0.44), rough=0.28, sss=0.25, scale=5.0)

    # 1. Stepped-Z Glossy Crimson Blood Pool (Zero Coplanar Z-Fighting)
    lobes = [
        (0.0, 0.0, 0.96, 0.76, 0.006),
        (-0.44, 0.18, 0.64, 0.48, 0.008),
        (0.38, -0.22, 0.58, 0.44, 0.010),
        (0.16, 0.44, 0.46, 0.36, 0.012),
    ]
    blood_objs = []
    for idx_l, (lx, ly, rx, ry, lz) in enumerate(lobes):
        c = add_cyl(f"BloodLobe_{idx_l}", (lx, ly, lz), 1.0, 0.003, mat_blood, verts=48)
        c.scale = (rx, ry, 1.0)
        blood_objs.append((c, rx, ry))

    # 2. Fallen Grigori Rasputin Lying Horizontally in Center of Blood Pool
    ras_fallen = load_blend_asset("bk_bearded_statue.blend", "FallenRasputinMesh", target_height=1.88, mat=mat_rasputin_fallen)
    if ras_fallen:
        for v in ras_fallen.data.vertices:
            v.co.z -= 0.94
        ras_fallen.data.update()
        ras_fallen.rotation_mode = "XYZ"
        ras_fallen.location = (-0.08, 0.06, 0.24)
        ras_fallen.rotation_euler = (math.radians(88.0), math.radians(12.0), math.radians(52.0))

    # 3. Dropped Webley .455 Revolver + 3 Spent Brass Shell Casings
    rev_obj = load_blend_asset("bk_revolver.blend", "CrimeRevolver", target_height=0.58, mat=mat_gun_steel)
    if rev_obj:
        rev_obj.location = (0.76, -0.26, 0.025)
        rev_obj.rotation_euler = (0.0, 0.0, math.radians(-34.0))

    for idx_s, (sx, sy) in enumerate([(0.56, -0.46), (0.90, -0.16), (0.65, -0.62)]):
        add_cyl(f"ShellCasing_{idx_s}", (sx, sy, 0.018), 0.024, 0.070, mat_gold_brass, verts=16, rot=(math.radians(90), 0, math.radians(idx_s * 47)))

    # 4. Overturned Antique Chair & Spilled Wine Goblet
    chair_ov = load_blend_asset("bk_antique_chair.blend", "OverturnedChair", target_height=0.95, mat=mat_walnut)
    if chair_ov:
        for v in chair_ov.data.vertices:
            v.co.z -= 0.45
        chair_ov.data.update()
        chair_ov.location = (-1.32, 0.64, 0.32)
        chair_ov.rotation_euler = (math.radians(82.0), math.radians(-18.0), math.radians(38.0))

    gob_spilled = load_blend_asset("bk_goblet.blend", "SpilledGoblet", target_height=0.26, mat=mat_gold_brass)
    if gob_spilled:
        gob_spilled.location = (-0.76, -0.48, 0.05)
        gob_spilled.rotation_euler = (math.radians(86.0), 0.0, math.radians(115.0))

    # 5. Neoclassical Pedestal Base + Ring of 4 Conspirators Casting Long Dramatic Shadows
    add_cyl("CourtyardPillarBase", (0.0, 1.88, 0.35), 0.68, 0.70, mat_conspirator, verts=48)
    add_3d_text("YUSUPOV PALACE", (0.0, 1.88, 0.72), 0.18, mat_gold_brass, rot=(0, 0, 0), extrude=0.02)

    con_proto = load_blend_asset("bk_decor_man.blend", "ConspiratorRingProto", target_height=1.78, mat=mat_conspirator)
    if con_proto:
        con_proto.hide_render = True
        ring_positions = [
            (-2.15, 0.95, -28),
            (-1.85, -1.05, -125),
            (1.95, 0.85, 32),
            (1.85, -1.10, 130),
        ]
        for idx_r, (rx, ry, rz) in enumerate(ring_positions):
            instance_obj(con_proto, f"RingConspirator_{idx_r}", (rx, ry, 0.0), rot=(0, 0, math.radians(rz)))

    # 6. Trail of Bloody Footprints Leading Toward the Moika River Gate
    footprints = [
        (0.35, -0.55), (0.62, -0.82), (0.92, -1.05),
        (1.22, -1.28), (1.55, -1.48), (1.88, -1.68),
    ]
    for idx_f, (fx, fy) in enumerate(footprints):
        fp = add_cyl(f"BloodFoot_{idx_f}", (fx, fy, 0.007), 0.09, 0.002, mat_blood, verts=20)
        fp.scale = (1.4, 0.65, 1.0)
        fp.rotation_euler = (0.0, 0.0, math.radians(-32.0))

    # Low-angle raking spotlight to cast long dramatic shadows across the marble tiles + top forensic spot
    add_spot_light("CrimeRakingShadowLight", (-3.8, -2.6, 2.8), (58, 0, -35), 950.0, size=0.6, spot_deg=65.0, col=(1.0, 0.78, 0.45))
    add_spot_light("CrimeTopSpot", (0.2, -0.2, 5.8), (8, 5, 0), 480.0, size=1.8, spot_deg=55.0, col=(0.75, 0.85, 1.0))

    cam = add_camera(loc=(0.0, -0.15, 4.2), rot_deg=(2.5, 0.0, 0.0), lens=34.0)

    def update_frame(f):
        u = smoothstep((f - 1200.0) / 299.0)
        # Slow overhead forensic crane pull-up + subtle counter-clockwise spiral
        cam.location = (
            lerp(-0.05, 0.05, u),
            lerp(-0.15, -0.25, u),
            lerp(3.85, 6.15, u),
        )
        cam.rotation_euler = (
            math.radians(lerp(2.0, 3.5, u)),
            0.0,
            math.radians(lerp(-8.0, 6.0, u)),
        )
        # Subtle spreading of blood pool over the shot
        spread = lerp(0.86, 1.05, u)
        for c, rx, ry in blood_objs:
            c.scale = (rx * spread, ry * spread, 1.0)

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
    print(f"Rendered frame {frame_idx:04d} (Scene {sid}) -> {out_file}")
