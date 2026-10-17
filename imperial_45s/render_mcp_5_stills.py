#!/usr/bin/env python3
"""
Renders the 5 Hero 3D Scenes in Blender 4.3 Cycles using real BlenderKit .blend assets
and Museum Laser Scans, then builds a Side-by-Side Visual Comparison Board against Imperial.
Usage:
  blender -b -P render_mcp_5_stills.py -- <SCENE_ID 0..4> <OUT_PNG>
  python3 render_mcp_5_stills.py --stitch <IN_DIR> <OUT_BOARD_JPG>
"""
import sys, os, math, json

if "--stitch" in sys.argv:
    import cv2, numpy as np
    from PIL import Image, ImageDraw, ImageFont

    idx = sys.argv.index("--stitch")
    in_dir = sys.argv[idx + 1]
    out_jpg = sys.argv[idx + 2]
    here = os.path.dirname(os.path.abspath(__file__))

    def gf(name, sz):
        for d in [here, "/var/tmp/imperial_assets"]:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, sz)
        return ImageFont.load_default()

    board = cv2.imread(os.path.join(here, "imperial_forensic_analysis.jpg"))
    # Extract the 5 exact reference panels from imperial_forensic_analysis.jpg (each panel is 640x360 with 28px header)
    # Row 0: (y=28..388) Col 0=00:15.0 (x=0..640), Col 2=00:42.0 (x=1280..1920)
    # Row 2: (y=776+28..776+388) Col 1=12:30.0 (x=640..1280)
    # Board B starts at y=1164+16=1180:
    # B-Row 1 (y=1180+388+28=1596..1956): Col 1=04:18.0 (x=640..1280), Col 2=05:00.0 (x=1280..1920)
    # B-Row 2 (y=1180+776+28=1984..2344): Col 0=05:15.0 (x=0..640)
    refs = [
        ("SCENE 1: Curia of Pompey Interior (00:15.0)", board[28:388, 0:640]),
        ("SCENE 2: Cutaway Architecture & Portico Gardens (00:42.0)", board[28:388, 1280:1920]),
        ("SCENE 3: 3D Extruded Topographic Relief Map (05:00.0)", board[1596:1956, 1280:1920]),
        ("SCENE 4: Exploded Marble Bust + Medallion + Red Arc (05:15.0)", board[1984:2344, 0:640]),
        ("SCENE 5: Top-Down Crime Scene & Blood Pool (12:30.0)", board[776+28:776+388, 640:1280]),
    ]

    rows_out = []
    for s_id, (title, ref_crop) in enumerate(refs):
        ref_960 = cv2.resize(ref_crop, (960, 540), interpolation=cv2.INTER_AREA)
        our_path = os.path.join(in_dir, f"scene_{s_id}.png")
        our_raw = cv2.imread(our_path)
        if our_raw is None:
            our_raw = np.zeros((540, 960, 3), dtype=np.uint8)
        else:
            our_raw = cv2.resize(our_raw, (960, 540), interpolation=cv2.INTER_AREA)

        # Add clean floating typography matching Imperial (NO black boxes behind callouts!)
        im = Image.fromarray(cv2.cvtColor(our_raw, cv2.COLOR_BGR2RGB)).convert("RGBA")
        ov = Image.new("RGBA", (960, 540), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)

        if s_id == 0:
            dr.text((506, 121), "DICTATOR", font=gf("Inter-Bold.ttf", 12), fill=(0,0,0,180), anchor="lm")
            dr.text((505, 120), "DICTATOR", font=gf("Inter-Bold.ttf", 12), fill=(225,228,235,245), anchor="lm")
            dr.text((506, 141), "JULIUS CAESAR", font=gf("Inter-Bold.ttf", 24), fill=(0,0,0,200), anchor="lm")
            dr.text((505, 140), "JULIUS CAESAR", font=gf("Inter-Bold.ttf", 24), fill=(255,255,255,255), anchor="lm")
            dr.rectangle([38, 392, 185, 456], fill=(18, 19, 22, 235))
            dr.text((50, 404), "15TH OF MARCH", font=gf("Inter-Bold.ttf", 13), fill=(220, 224, 230, 255))
            dr.text((50, 424), "44 BC", font=gf("Inter-Bold.ttf", 24), fill=(255, 255, 255, 255))
        elif s_id == 2:
            # Faction Map white boxes + bottom chronological scrubber
            for bx, by, btxt, bcol in [(260, 205, "CAESAR'S FACTION", (200, 16, 46)), (685, 345, "POMPEY'S FACTION", (35, 95, 225))]:
                dr.rectangle([bx-78, by-13, bx+78, by+13], fill=(248, 248, 250, 245))
                dr.text((bx, by), btxt, font=gf("Inter-Bold.ttf", 12), fill=(*bcol, 255), anchor="mm")
            # Bottom scrubber bar
            dr.rectangle([180, 465, 780, 520], fill=(8, 9, 12, 220), outline=(90, 95, 105, 180), width=1)
            dr.line([(230, 492), (730, 492)], fill=(220, 225, 235, 220), width=2)
            dr.text((230, 506), "JAN, 49 BC", font=gf("Inter-Bold.ttf", 11), fill=(235, 238, 245, 255), anchor="mm")
            dr.text((730, 506), "MARCH, 45 BC", font=gf("Inter-Bold.ttf", 11), fill=(235, 238, 245, 255), anchor="mm")
        elif s_id == 3:
            dr.text((515, 385), "CAESAR", font=gf("Inter-Bold.ttf", 22), fill=(255, 255, 255, 255), anchor="lm")
            dr.text((515, 404), "DICTATOR PERPETUO", font=gf("Inter-Regular.ttf", 10), fill=(210, 215, 222, 235), anchor="lm")
            dr.text((515, 417), "\"TOO POWERFUL\"", font=gf("Inter-Bold.ttf", 11), fill=(235, 45, 55, 255), anchor="lm")

        our_final = cv2.cvtColor(np.array(Image.alpha_composite(im, ov).convert("RGB")), cv2.COLOR_RGB2BGR)
        cv2.putText(ref_960, f"REFERENCE: {title}", (18, 32), cv2.FONT_HERSHEY_DUPLEX, 0.68, (80, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(our_final, f"OUR BLENDER 4.3 + BLENDERKIT MCP: {title}", (18, 32), cv2.FONT_HERSHEY_DUPLEX, 0.68, (100, 255, 120), 2, cv2.LINE_AA)
        rows_out.append(np.hstack([ref_960, our_final]))

    full_board = np.vstack(rows_out)
    cv2.imwrite(out_jpg, full_board, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print("Saved comparison board:", out_jpg)
    sys.exit(0)

# Inside Blender:
import bpy, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SCENE_ID = int(argv[0])
OUT_PNG = argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))

# Import helper functions from mcp_scene1_curia_v2 if available, or define inline
sys.path.insert(0, HERE)
from mcp_scene1_curia import load_mesh_from_blend, make_pbr_stone_or_wood
from mcp_scene1_curia_v2 import make_curia_carpet_and_border_floor, make_senator_clavus_mat, create_seated_male_senator_mesh

def init_cycles():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 18
    scn.cycles.max_bounces = 1
    scn.cycles.diffuse_bounces = 0
    scn.cycles.glossy_bounces = 1
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = 'OPENIMAGEDENOISE'
    scn.cycles.denoising_prefilter = 'FAST'
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - Medium High Contrast'
    scn.view_settings.exposure = -0.05
    world = bpy.data.worlds.new("W")
    scn.world = world
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs[0].default_value = (0.008, 0.009, 0.012, 1.0)
    world.node_tree.nodes.get("Background").inputs[1].default_value = 0.25
    return scn

def load_local_blend(fname):
    bpath = os.path.join(HERE, fname)
    with bpy.data.libraries.load(bpath, link=False) as (df, dt):
        dt.objects = [n for n in df.objects if n]
    meshes = []
    for o in dt.objects:
        if o is not None and o.type == "MESH":
            bpy.context.scene.collection.objects.link(o)
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
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    return obj

if SCENE_ID == 0:
    # Scene 1: Curia of Pompey Interior (00:15.0)
    import mcp_scene1_curia_v2
    mcp_scene1_curia_v2.ASSETS = HERE
    import mcp_scene1_curia
    mcp_scene1_curia.ASSETS = HERE
    scn = init_cycles()
    mat_floor = make_curia_carpet_and_border_floor()
    mat_trav = make_pbr_stone_or_wood("TravWall", (0.42, 0.39, 0.35), rough=0.42, noise_scale=6.0)
    mat_step = make_pbr_stone_or_wood("StepMarble", (0.54, 0.51, 0.46), rough=0.35, noise_scale=8.0)
    mat_wood = make_pbr_stone_or_wood("DarkWalnut", (0.12, 0.06, 0.03), rough=0.32, noise_scale=16.0)

    bpy.ops.mesh.primitive_plane_add(size=22.0, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat_floor)

    for side in (-1, 1):
        for tier in range(3):
            x_c = side * (2.60 + tier * 0.98)
            z_top = 0.16 + tier * 0.28
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c, 0.0, z_top * 0.5))
            st = bpy.context.active_object; st.scale = (0.98, 8.2, z_top); st.data.materials.append(mat_step)
            for y_sec, sec_len in [(-1.85, 3.3), (2.05, 3.3)]:
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.05, y_sec, z_top + 0.42))
                seat = bpy.context.active_object; seat.scale = (0.46, sec_len, 0.06); seat.data.materials.append(mat_wood)
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.26, y_sec, z_top + 0.68))
                back = bpy.context.active_object; back.scale = (0.06, sec_len, 0.52); back.data.materials.append(mat_wood)
                for end_s in (-1, 1):
                    y_end = y_sec + end_s * (sec_len * 0.5)
                    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.06, y_end, z_top + 0.38))
                    arm = bpy.context.active_object; arm.scale = (0.50, 0.08, 0.76); arm.data.materials.append(mat_wood)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.8, 4.0))
    rw = bpy.context.active_object; rw.scale = (14.0, 0.5, 8.0); rw.data.materials.append(mat_trav)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.52, 2.1))
    dr = bpy.context.active_object; dr.scale = (2.3, 0.12, 4.2); dr.data.materials.append(mat_wood)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.55, 2.2))
    df = bpy.context.active_object; df.scale = (2.65, 0.18, 4.5); df.data.materials.append(mat_step)
    for sx in (-3.2, 3.2):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, 5.52, 1.8))
        ml = bpy.context.active_object; ml.scale = (2.8, 0.10, 1.4); ml.data.materials.append(mat_step)

    col_proto = load_local_blend("bk_column_corinthian.blend")
    if col_proto:
        verts = [v.co for v in col_proto.data.vertices]
        mz, xz = min(v.z for v in verts), max(v.z for v in verts)
        cx, cy = 0.5*(min(v.x for v in verts)+max(v.x for v in verts)), 0.5*(min(v.y for v in verts)+max(v.y for v in verts))
        sf = 5.4 / max(xz - mz, 1e-4)
        for v in col_proto.data.vertices:
            v.co = Vector(((v.co.x - cx)*sf, (v.co.y - cy)*sf, (v.co.z - mz)*sf))
        col_proto.data.update()
        col_proto.hide_render = True; col_proto.location = (0, 0, -30)
        for cx_p, cy_p, cz_p in [(-3.2, 4.8, 0.0), (3.2, 4.8, 0.0), (-4.8, 1.8, 0.72), (4.8, 1.8, 0.72), (-4.8, -1.8, 0.72), (4.8, -1.8, 0.72)]:
            inst = col_proto.copy(); inst.hide_render = False; inst.location = (cx_p, cy_p, cz_p)
            scn.collection.objects.link(inst)

    mat_caesar = make_senator_clavus_mat("CaesarMat", is_caesar=True, hair_tone=0.18)
    mat_sen_1 = make_senator_clavus_mat("SenMat1", is_caesar=False, hair_tone=0.55)
    orator_proto = load_local_blend("clean_caesar_orator.blend")
    mod_d = orator_proto.modifiers.new("Dec", "DECIMATE"); mod_d.ratio = 0.35
    bpy.context.view_layer.objects.active = orator_proto; bpy.ops.object.modifier_apply(modifier=mod_d.name)

    seated_male_proto = create_seated_male_senator_mesh(orator_proto)
    seated_male_proto.data.materials.clear(); seated_male_proto.data.materials.append(mat_sen_1)
    seated_male_proto.hide_render = True; seated_male_proto.location = (0, 0, -30)

    stand_male_proto = orator_proto.copy(); stand_male_proto.data = orator_proto.data.copy()
    scn.collection.objects.link(stand_male_proto)
    for v in stand_male_proto.data.vertices:
        if v.co.x < -0.14 and v.co.z > 1.05:
            dx = -0.14 - v.co.x; v.co.z -= dx * 0.75; v.co.x = -0.14 - dx * 0.50
    stand_male_proto.data.update()
    stand_male_proto.data.materials.clear(); stand_male_proto.data.materials.append(mat_sen_1)
    stand_male_proto.hide_render = True; stand_male_proto.location = (0, 0, -30)
    orator_proto.hide_render = True; orator_proto.location = (0, 0, -30)

    caesar_walk = stand_male_proto.copy(); caesar_walk.data = stand_male_proto.data.copy()
    caesar_walk.data.materials.clear(); caesar_walk.data.materials.append(mat_caesar)
    caesar_walk.hide_render = False; caesar_walk.location = (0.05, 1.35, 0.0)
    caesar_walk.rotation_euler = (0, 0, math.radians(-15))
    scn.collection.objects.link(caesar_walk)

    for side in (-1, 1):
        base_rz = 90.0 if side == -1 else -90.0
        for tier in range(3):
            x_pos = side * (2.60 + tier * 0.98)
            z_pos = 0.16 + tier * 0.28
            for y_pos in [-3.1, -2.3, -1.5, -0.7, 0.8, 1.6, 2.4, 3.2]:
                inst = seated_male_proto.copy(); inst.hide_render = False
                inst.location = (x_pos, y_pos, z_pos)
                jitter = ((int(y_pos*10) * 17 + tier * 31) % 16) - 8
                inst.rotation_euler = (0, 0, math.radians(base_rz + jitter))
                scn.collection.objects.link(inst)

    for sx, sy, sz, srz in [(-1.25, 4.3, 0.0, 45), (-0.55, 4.5, 0.0, -35), (-1.45, 0.5, 0.0, 75), (-1.35, -0.3, 0.0, 110), (1.30, -0.1, 0.0, -85), (1.85, 2.8, 0.0, -60), (2.45, 2.9, 0.0, -120)]:
        st_i = stand_male_proto.copy(); st_i.hide_render = False; st_i.location = (sx, sy, sz)
        st_i.rotation_euler = (0, 0, math.radians(srz)); scn.collection.objects.link(st_i)

    ld_key = bpy.data.lights.new("SunShaft", type='AREA'); ld_key.energy = 320.0; ld_key.size = 3.8; ld_key.color = (1.0, 0.95, 0.88)
    lo_key = bpy.data.objects.new("SunShaft", ld_key); scn.collection.objects.link(lo_key); lo_key.location = (-3.5, -2.5, 6.5)
    lo_key.rotation_euler = (Vector((0.0, 1.0, 0.0)) - lo_key.location).to_track_quat('-Z', 'Y').to_euler()
    ld_fill = bpy.data.lights.new("AmbientFill", type='AREA'); ld_fill.energy = 95.0; ld_fill.size = 5.0; ld_fill.color = (0.90, 0.93, 1.0)
    lo_fill = bpy.data.objects.new("AmbientFill", ld_fill); scn.collection.objects.link(lo_fill); lo_fill.location = (3.5, -4.5, 5.0)
    lo_fill.rotation_euler = (Vector((0.0, 0.5, 1.0)) - lo_fill.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 36.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (-0.65, -5.2, 4.1)
    co.rotation_euler = (Vector((-0.05, 1.2, 0.7)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 1:
    # Scene 2: Architectural Cutaway of the Curia & Portico of Pompey (00:42.0)
    scn = init_cycles()
    scn.view_settings.exposure = -0.10
    mat_stone = make_pbr_stone_or_wood("PorticoStone", (0.58, 0.54, 0.48), rough=0.38, noise_scale=8.0)
    mat_wall = make_pbr_stone_or_wood("PorticoWall", (0.48, 0.45, 0.40), rough=0.45, noise_scale=10.0)
    mat_roof_terra = make_pbr_stone_or_wood("TerraRoof", (0.56, 0.36, 0.25), rough=0.42, noise_scale=18.0)
    mat_roof_slate = make_pbr_stone_or_wood("SlateRoof", (0.24, 0.25, 0.27), rough=0.48, noise_scale=15.0)
    mat_grass = make_pbr_stone_or_wood("GardenGrass", (0.22, 0.32, 0.18), rough=0.75, noise_scale=25.0)
    mat_tree = make_pbr_stone_or_wood("CypressFoliage", (0.12, 0.22, 0.10), rough=0.80, noise_scale=30.0)
    mat_txt = bpy.data.materials.new("TxtWhite"); mat_txt.use_nodes = True
    bsdf_t = mat_txt.node_tree.nodes.get("Principled BSDF")
    bsdf_t.inputs["Base Color"].default_value = (0.96, 0.96, 0.98, 1.0)
    if "Emission Color" in bsdf_t.inputs:
        bsdf_t.inputs["Emission Color"].default_value = (0.96, 0.96, 0.98, 1.0)
        bsdf_t.inputs["Emission Strength"].default_value = 0.45

    # Stepped marble base platform in pitch-black void
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.35))
    base = bpy.context.active_object; base.scale = (26.0, 17.5, 0.70); base.data.materials.append(mat_stone)

    # 4 Manicured Green Garden Parterres + rows of 3D Cypress trees along the central avenue!
    for gx in (-5.2, -1.6):
        for gy in (-2.2, 2.2):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gx, gy, 0.04))
            gb = bpy.context.active_object; gb.scale = (2.8, 3.2, 0.08); gb.data.materials.append(mat_grass)
            # Row of cypress trees around each garden bed
            for tx in (gx - 1.1, gx - 0.35, gx + 0.35, gx + 1.1):
                for ty in (gy - 1.25, gy + 1.25):
                    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.22, radius2=0.03, depth=1.15, location=(tx, ty, 0.62))
                    tr = bpy.context.active_object; tr.data.materials.append(mat_tree)

    # Real BlenderKit Columns around the Portico Peristyle!
    col_proto = load_local_blend("bk_column_corinthian.blend")
    if col_proto:
        verts = [v.co for v in col_proto.data.vertices]
        mz, xz = min(v.z for v in verts), max(v.z for v in verts)
        cx, cy = 0.5*(min(v.x for v in verts)+max(v.x for v in verts)), 0.5*(min(v.y for v in verts)+max(v.y for v in verts))
        sf = 1.65 / max(xz - mz, 1e-4)
        for v in col_proto.data.vertices:
            v.co = Vector(((v.co.x - cx)*sf, (v.co.y - cy)*sf, (v.co.z - mz)*sf))
        col_proto.data.update(); col_proto.hide_render = True; col_proto.location = (0, 0, -30)
        for x_p in [i * 0.75 for i in range(-11, 3)]:
            for y_p in (-4.6, 4.6):
                c_i = col_proto.copy(); c_i.hide_render = False; c_i.location = (x_p, y_p, 0.0)
                scn.collection.objects.link(c_i)
        # Front colonnade of the Curia
        for y_p in [-1.8, -1.1, -0.4, 0.4, 1.1, 1.8]:
            c_i = col_proto.copy(); c_i.hide_render = False; c_i.location = (2.6, y_p, 0.35)
            c_i.scale = (1.35, 1.35, 1.45); scn.collection.objects.link(c_i)

    # Covered Portico Colonnade Walkways (North, South, West) + Surrounding Multi-Story Roman Insulae/Arcades
    for gy, sy in [(-5.2, 1.4), (5.2, 1.4)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.2, gy, 1.80))
        rf = bpy.context.active_object; rf.scale = (11.5, sy, 0.25); rf.data.materials.append(mat_roof_terra)
        # Outer multi-story arcade block (matching 00:42.0!)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.5, gy * 1.35, 1.35))
        ab = bpy.context.active_object; ab.scale = (16.0, 2.2, 2.7); ab.data.materials.append(mat_wall)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.5, gy * 1.35, 2.85))
        ar = bpy.context.active_object; ar.scale = (16.2, 2.4, 0.35); ar.data.materials.append(mat_roof_slate)

    # THE CURIA OF POMPEY (Grand Rectangular Senate Hall on the East side X=+5.2 with Classical Pediment & Recessed Roof!)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.2, 0.0, 2.1))
    curia = bpy.context.active_object; curia.scale = (4.8, 4.4, 4.2); curia.data.materials.append(mat_stone)
    # Recessed roof cornice of Curia
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.2, 0.0, 4.35))
    cr = bpy.context.active_object; cr.scale = (5.1, 4.7, 0.35); cr.data.materials.append(mat_roof_terra)
    # Flanking wings next to Curia
    for wy in (-4.4, 4.4):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.6, wy, 1.5))
        wg = bpy.context.active_object; wg.scale = (4.2, 3.2, 3.0); wg.data.materials.append(mat_wall)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.6, wy, 3.15))
        wr = bpy.context.active_object; wr.scale = (4.4, 3.4, 0.30); wr.data.materials.append(mat_roof_slate)

    # 3D Extruded World-Locked Typography: "CURIA" and "PORTICO OF POMPEY"
    font_p = os.path.join(HERE, "Inter-Bold.ttf")
    bpy.ops.object.text_add(location=(5.0, 0.0, 4.58))
    t_cur = bpy.context.active_object; t_cur.data.body = "CURIA"; t_cur.data.align_x = 'CENTER'; t_cur.data.align_y = 'CENTER'
    t_cur.data.size = 1.15; t_cur.data.extrude = 0.12
    if os.path.exists(font_p): t_cur.data.font = bpy.data.fonts.load(font_p)
    t_cur.rotation_euler = (0, 0, math.radians(-90)); t_cur.data.materials.append(mat_txt)

    bpy.ops.object.text_add(location=(-3.2, 0.0, 0.12))
    t_por = bpy.context.active_object; t_por.data.body = "PORTICO OF POMPEY"; t_por.data.align_x = 'CENTER'; t_por.data.align_y = 'CENTER'
    t_por.data.size = 0.72; t_por.data.extrude = 0.08
    if os.path.exists(font_p): t_por.data.font = bpy.data.fonts.load(font_p)
    t_por.data.materials.append(mat_txt)

    # Warm Architectural Sun + Cool Fill
    ld_sun = bpy.data.lights.new("Sun", type='AREA'); ld_sun.energy = 850.0; ld_sun.size = 8.0; ld_sun.color = (1.0, 0.94, 0.85)
    lo_sun = bpy.data.objects.new("Sun", ld_sun); scn.collection.objects.link(lo_sun); lo_sun.location = (-10.0, -12.0, 15.0)
    lo_sun.rotation_euler = (Vector((0, 0, 0)) - lo_sun.location).to_track_quat('-Z', 'Y').to_euler()
    ld_f = bpy.data.lights.new("Fill", type='AREA'); ld_f.energy = 260.0; ld_f.size = 10.0; ld_f.color = (0.85, 0.90, 1.0)
    lo_f = bpy.data.objects.new("Fill", ld_f); scn.collection.objects.link(lo_f); lo_f.location = (12.0, -10.0, 10.0)
    lo_f.rotation_euler = (Vector((0, 0, 0)) - lo_f.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 38.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (-10.5, -11.8, 8.8)
    co.rotation_euler = (Vector((0.8, 0.2, 0.8)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 2:
    # Scene 3: TRUE 3D Extruded Topographic Mountain Relief Map of the Mediterranean (05:00.0)
    scn = init_cycles()
    scn.view_settings.exposure = 0.05
    world_bg = scn.world.node_tree.nodes.get("Background")
    world_bg.inputs[0].default_value = (0.005, 0.005, 0.008, 1.0)

    # 1. 3D Wireframe Perspective Grid Plane in Blender
    mat_grid = bpy.data.materials.new("GridMat"); mat_grid.use_nodes = True
    nt = mat_grid.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.015, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.4
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    wf = nt.nodes.new("ShaderNodeWireframe")
    wf.inputs["Size"].default_value = 0.012
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (0.22, 0.24, 0.28, 1.0)
        nt.links.new(wf.outputs["Fac"], bsdf.inputs["Emission Strength"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=44, y_subdivisions=28, size=18.0, location=(0, 0, -0.02))
    grid_plane = bpy.context.active_object; grid_plane.scale = (1.35, 0.85, 1.0)
    grid_plane.data.materials.append(mat_grid)

    # 2. Build True 3D Topographic Mountain Relief Mesh from med_countries_50m.geojson!
    with open(os.path.join(HERE, "med_countries_50m.geojson"), "r") as f:
        gj = json.load(f)

    caesar_iso = {"ITA", "FRA", "BEL", "CHE", "AUT", "SVN"}
    pompey_iso = {"ESP", "PRT", "GRC", "ALB", "MKD", "BGR", "TUR", "TUN", "DZA", "MAR", "LBY"}

    def make_faction_mat(name, base_rgb, emit_rgb, emit_str):
        m = bpy.data.materials.new(name); m.use_nodes = True
        nt = m.node_tree; bs = nt.nodes.get("Principled BSDF")
        bs.inputs["Base Color"].default_value = (*base_rgb, 1.0)
        bs.inputs["Roughness"].default_value = 0.45
        if "Emission Color" in bs.inputs:
            bs.inputs["Emission Color"].default_value = (*emit_rgb, 1.0)
            bs.inputs["Emission Strength"].default_value = emit_str
        return m

    mat_caesar_land = make_faction_mat("CaesarRed", (0.72, 0.04, 0.08), (0.85, 0.05, 0.10), 0.55)
    mat_pompey_land = make_faction_mat("PompeyBlue", (0.06, 0.18, 0.78), (0.08, 0.25, 0.95), 0.55)
    mat_neutral_land = make_faction_mat("NeutralDark", (0.06, 0.07, 0.09), (0.02, 0.02, 0.03), 0.05)

    for feat in gj["features"]:
        iso = feat["properties"].get("ISO_A3", "")
        geom_d = feat["geometry"]
        polys = geom_d["coordinates"] if geom_d["type"] == "Polygon" else [p[0] for p in geom_d["coordinates"]]
        for ring in polys:
            if len(ring) < 4: continue
            # Map lon (-10..38) -> X (-8.5..+8.5), lat (30..50) -> Y (-4.8..+4.8)
            pts_2d = []
            for lon, lat in ring:
                if -12 <= lon <= 40 and 28 <= lat <= 51:
                    x = (lon - 14.0) * 0.35
                    y = (lat - 41.0) * 0.45
                    pts_2d.append((x, y))
            if len(pts_2d) < 4: continue
            curve_data = bpy.data.curves.new(f"C_{iso}", type='CURVE')
            curve_data.dimensions = '2D'
            curve_data.fill_mode = 'BOTH'
            curve_data.extrude = 0.09 if iso in (caesar_iso | pompey_iso) else 0.04
            curve_data.bevel_depth = 0.015
            spline = curve_data.splines.new('POLY')
            spline.points.add(len(pts_2d) - 1)
            for idx_p, (px, py) in enumerate(pts_2d):
                spline.points[idx_p].co = (px, py, 0.0, 1.0)
            spline.use_cyclic_u = True
            c_obj = bpy.data.objects.new(f"Map_{iso}", curve_data)
            scn.collection.objects.link(c_obj)
            if iso in caesar_iso:
                c_obj.data.materials.append(mat_caesar_land)
            elif iso in pompey_iso:
                c_obj.data.materials.append(mat_pompey_land)
            else:
                c_obj.data.materials.append(mat_neutral_land)

    # Add 3D Sculpted Mountain Ridges (Alps & Apennines & Pyrenees & Greece Pindus) with Displace Noise!
    mountain_chains = [
        # Alps arc
        ((-2.2, 1.9), mat_caesar_land, 2.2, 0.65, 0.42),
        ((-1.2, 2.3), mat_caesar_land, 2.5, 0.70, 0.48),
        # Apennines spine down Italy
        ((-0.8, 1.0), mat_caesar_land, 0.9, 1.8, 0.35),
        ((-0.2, 0.1), mat_caesar_land, 0.8, 1.6, 0.32),
        # Spain Pyrenees & Iberia mountains
        ((-5.8, 0.2), mat_pompey_land, 2.2, 1.4, 0.38),
        # Greece / Macedonia mountains
        ((2.8, -0.4), mat_pompey_land, 1.5, 1.4, 0.38),
    ]
    for (mx, my), m_mat, sx, sy, sz in mountain_chains:
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=24, size=1.0, location=(mx, my, 0.08))
        mt = bpy.context.active_object; mt.scale = (sx, sy, sz)
        # Displace with Voronoi/Clouds texture for sharp 3D mountain peaks!
        tex = bpy.data.textures.new(f"T_{mx}", type='VORONOI')
        tex.noise_scale = 0.65
        mod = mt.modifiers.new("Mtn", "DISPLACE")
        mod.texture = tex; mod.strength = 0.55
        mt.data.materials.append(m_mat)

    # 3D Collector Cards standing on Italy (Rome & Cisalpine Gaul)
    mat_card = make_faction_mat("CardCream", (0.92, 0.89, 0.82), (0.92, 0.89, 0.82), 0.35)
    for cx, cy, crz in [(-0.95, 0.85, 12), (-0.65, 0.35, -8)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, 0.24))
        cd_o = bpy.context.active_object; cd_o.scale = (0.48, 0.68, 0.03)
        cd_o.rotation_euler = (math.radians(25), 0, math.radians(crz))
        cd_o.data.materials.append(mat_card)

    ld = bpy.data.lights.new("MapKey", type='AREA'); ld.energy = 450.0; ld.size = 8.0
    lo = bpy.data.objects.new("MapKey", ld); scn.collection.objects.link(lo); lo.location = (-4.0, -6.0, 9.0)
    lo.rotation_euler = (Vector((0, 0, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 38.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (-0.5, -8.2, 6.4)
    co.rotation_euler = (Vector((-0.3, 0.2, 0.0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 3:
    # Scene 4: Exploded/Sliced Chiaroscuro 3D Marble Bust + Silver Coin Medallion + Sweeping Red Laser Horizon Arc (05:15.0)
    scn = init_cycles()
    scn.view_settings.exposure = -0.25
    scn.world.node_tree.nodes.get("Background").inputs[1].default_value = 0.05

    # Load High-Detail Classical Bust (clean_caesar_bust.blend)
    bust = load_local_blend("clean_caesar_bust.blend")
    # Center and normalize height to 1.45m
    verts = [v.co for v in bust.data.vertices]
    cx = 0.5*(min(v.x for v in verts)+max(v.x for v in verts))
    cy = 0.5*(min(v.y for v in verts)+max(v.y for v in verts))
    mz, xz = min(v.z for v in verts), max(v.z for v in verts)
    sf = 1.45 / max(xz - mz, 1e-4)
    for v in bust.data.vertices:
        v.co = Vector(((v.co.x - cx)*sf, (v.co.y - cy)*sf, (v.co.z - mz)*sf))
    bust.data.update()

    # Dark Chiaroscuro Aged Marble Shader with Pointiness Cavity AO
    mat_marble = bpy.data.materials.new("ChiaroscuroMarble"); mat_marble.use_nodes = True
    nt = mat_marble.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.36
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.44; ramp.color_ramp.elements[0].color = (0.14, 0.14, 0.15, 1.0)
    ramp.color_ramp.elements[1].position = 0.56; ramp.color_ramp.elements[1].color = (0.76, 0.75, 0.73, 1.0)
    nt.links.new(geom.outputs["Pointiness"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Deep Sculpted Crimson Core Material (for the sliced interior & brain core, NOT overexposed pink!)
    mat_core = bpy.data.materials.new("CrimsonCore"); mat_core.use_nodes = True
    nt_c = mat_core.node_tree; bs_c = nt_c.nodes.get("Principled BSDF")
    bs_c.inputs["Base Color"].default_value = (0.48, 0.02, 0.03, 1.0)
    bs_c.inputs["Roughness"].default_value = 0.42
    if "Emission Color" in bs_c.inputs:
        bs_c.inputs["Emission Color"].default_value = (0.55, 0.02, 0.03, 1.0)
        bs_c.inputs["Emission Strength"].default_value = 0.35

    bust.data.materials.clear()
    bust.data.materials.append(mat_marble)
    bust.data.materials.append(mat_core)

    # Duplicate bust into Upper-Right Exploded Slice + Sculpted Crimson Inner Core!
    bust_top = bust.copy(); bust_top.data = bust.data.copy(); scn.collection.objects.link(bust_top)
    bust_core = bust.copy(); bust_core.data = bust.data.copy(); scn.collection.objects.link(bust_core)
    bust_core.scale = (0.82, 0.82, 0.82)
    bust_core.location = (0.02, 0.0, 0.06)
    bust_core.data.materials.clear(); bust_core.data.materials.append(mat_core)

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.42, 0.0, 1.32), rotation=(0.0, math.radians(-26), math.radians(10)))
    cutter = bpy.context.active_object; cutter.data.materials.append(mat_core)

    bpy.context.view_layer.objects.active = bust
    m1 = bust.modifiers.new("Cut1", "BOOLEAN"); m1.operation = 'DIFFERENCE'; m1.solver = 'EXACT'; m1.object = cutter
    bpy.ops.object.modifier_apply(modifier=m1.name)

    bpy.context.view_layer.objects.active = bust_top
    m2 = bust_top.modifiers.new("Cut2", "BOOLEAN"); m2.operation = 'INTERSECT'; m2.solver = 'EXACT'; m2.object = cutter
    bpy.ops.object.modifier_apply(modifier=m2.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

    # Lift the upper-right slice up & right just like 05:15.0!
    bust_top.location = (0.14, 0.02, 0.16)
    bust_top.rotation_euler = (0, math.radians(8), math.radians(-6))

    # Circular Silver Roman Medallion behind the bust (matching 05:15.0!)
    mat_silver = make_pbr_stone_or_wood("SilverCoin", (0.55, 0.56, 0.58), rough=0.28, metal=0.85, noise_scale=22.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.62, depth=0.04, location=(0.0, 0.28, 0.82), rotation=(math.radians(90), 0, 0))
    coin = bpy.context.active_object; coin.data.materials.append(mat_silver)

    # Sweeping Glowing Red Horizon Light Curve across the frame (matching 05:15.0!)
    mat_beam = bpy.data.materials.new("RedArc"); mat_beam.use_nodes = True
    bs_b = mat_beam.node_tree.nodes.get("Principled BSDF")
    bs_b.inputs["Base Color"].default_value = (0.95, 0.05, 0.08, 1.0)
    if "Emission Color" in bs_b.inputs:
        bs_b.inputs["Emission Color"].default_value = (1.0, 0.06, 0.10, 1.0)
        bs_b.inputs["Emission Strength"].default_value = 3.5
    curve_d = bpy.data.curves.new("RedCurve", type='CURVE')
    curve_d.dimensions = '3D'; curve_d.bevel_depth = 0.010
    sp = curve_d.splines.new('NURBS')
    pts_arc = [(-2.4, 0.4, 0.15), (-0.8, 0.35, 0.55), (0.6, 0.35, 0.92), (2.4, 0.4, 1.25)]
    sp.points.add(len(pts_arc) - 1)
    for idx_a, (ax, ay, az) in enumerate(pts_arc):
        sp.points[idx_a].co = (ax, ay, az, 1.0)
    arc_obj = bpy.data.objects.new("RedArcObj", curve_d)
    scn.collection.objects.link(arc_obj); arc_obj.data.materials.append(mat_beam)

    # Dramatic Rim + Side Key Light
    ld_k = bpy.data.lights.new("BustKey", type='AREA'); ld_k.energy = 42.0; ld_k.size = 1.2
    lo_k = bpy.data.objects.new("BustKey", ld_k); scn.collection.objects.link(lo_k); lo_k.location = (-1.5, -1.6, 1.6)
    lo_k.rotation_euler = (Vector((0, 0, 0.85)) - lo_k.location).to_track_quat('-Z', 'Y').to_euler()

    ld_r = bpy.data.lights.new("RedRim", type='AREA'); ld_r.energy = 35.0; ld_r.size = 1.0; ld_r.color = (1.0, 0.12, 0.15)
    lo_r = bpy.data.objects.new("RedRim", ld_r); scn.collection.objects.link(lo_r); lo_r.location = (1.4, -0.8, 1.4)
    lo_r.rotation_euler = (Vector((0, 0, 0.85)) - lo_r.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 55.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (0.0, -3.6, 0.85)
    co.rotation_euler = (Vector((0, 0, 0.82)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 4:
    # Scene 5: Top-Down Crime Scene at the Base of Pompey's Statue (12:30.0)
    import mcp_scene1_curia_v2
    mcp_scene1_curia_v2.ASSETS = HERE
    import mcp_scene1_curia
    mcp_scene1_curia.ASSETS = HERE
    scn = init_cycles()
    scn.view_settings.exposure = -0.15

    # Weathered Cream/Grey Roman Marble Slab Floor with joint lines (matching 12:30.0!)
    mat_slab = make_pbr_stone_or_wood("CrimeMarbleSlab", (0.56, 0.53, 0.49), rough=0.32, noise_scale=4.5)
    bpy.ops.mesh.primitive_plane_add(size=16.0, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat_slab)

    # Organic Multi-Lobed Dark Crimson Glossy Blood Pool (NO black circles, NO pink!)
    mat_blood = bpy.data.materials.new("DarkBlood"); mat_blood.use_nodes = True
    bs_bl = mat_blood.node_tree.nodes.get("Principled BSDF")
    bs_bl.inputs["Base Color"].default_value = (0.18, 0.003, 0.005, 1.0)
    bs_bl.inputs["Roughness"].default_value = 0.06
    if "Coat Weight" in bs_bl.inputs:
        bs_bl.inputs["Coat Weight"].default_value = 1.0
        bs_bl.inputs["Coat Roughness"].default_value = 0.03

    # Build organic multi-lobed puddle from overlapping thin discs at Z=0.004m
    lobes = [
        (0.0, 0.0, 0.85, 0.65, 15),
        (-0.45, -0.35, 0.55, 0.42, -25),
        (0.55, -0.20, 0.48, 0.35, 40),
        (0.15, 0.55, 0.52, 0.38, -10),
        (-0.65, 0.25, 0.38, 0.28, 30),
        (0.85, -0.55, 0.14, 0.11, 0),
        (-0.35, -0.95, 0.16, 0.12, 20),
    ]
    for lx, ly, sx, sy, lrz in lobes:
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=0.006, location=(lx, ly, 0.003))
        lb = bpy.context.active_object; lb.scale = (sx, sy, 1.0); lb.rotation_euler = (0, 0, math.radians(lrz))
        lb.data.materials.append(mat_blood)

    # Bloody footprints leading away to the left (-X)
    for fx, fy, frz in [(-1.05, -0.15, 110), (-1.45, 0.05, 105), (-1.85, -0.10, 115), (-2.25, 0.12, 100)]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.11, depth=0.005, location=(fx, fy, 0.003))
        fp = bpy.context.active_object; fp.scale = (1.3, 0.55, 1.0); fp.rotation_euler = (0, 0, math.radians(frz))
        fp.data.materials.append(mat_blood)

    # Fallen Julius Caesar in Deep Crimson Toga over White Tunic lying in the center of the blood pool!
    mat_caesar = make_senator_clavus_mat("FallenCaesarMat", is_caesar=True, hair_tone=0.18)
    mat_sen = make_senator_clavus_mat("CrimeSenMat", is_caesar=False, hair_tone=0.52)
    caesar_fallen = load_local_blend("clean_caesar_orator.blend")
    caesar_fallen.data.materials.clear(); caesar_fallen.data.materials.append(mat_caesar)
    # Lay Caesar horizontally on the floor at the center of the blood pool
    caesar_fallen.rotation_euler = (math.radians(86), math.radians(15), math.radians(42))
    caesar_fallen.location = (-0.35, 0.25, 0.18)

    # Overturned Golden Throne (top-right of blood pool, matching 12:30.0!)
    mat_gold = make_pbr_stone_or_wood("CrimeGold", (0.78, 0.58, 0.18), rough=0.22, metal=0.92, noise_scale=12.0)
    mat_velvet = make_pbr_stone_or_wood("CrimeVelvet", (0.42, 0.02, 0.03), rough=0.65, noise_scale=20.0)
    mat_wood = make_pbr_stone_or_wood("CrimeWood", (0.14, 0.07, 0.035), rough=0.35, noise_scale=16.0)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.95, 1.15, 0.28))
    gt = bpy.context.active_object; gt.scale = (0.58, 0.58, 0.52)
    gt.rotation_euler = (math.radians(78), math.radians(-20), math.radians(35))
    gt.data.materials.append(mat_gold)

    # Knocked-over Red Velvet Senator Chair (bottom-right of blood pool, matching 12:30.0!)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.35, -1.05, 0.34))
    vc = bpy.context.active_object; vc.scale = (0.62, 0.58, 0.12)
    vc.rotation_euler = (math.radians(15), math.radians(-12), math.radians(-30))
    vc.data.materials.append(mat_velvet)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.55, -1.25, 0.62))
    vb = bpy.context.active_object; vb.scale = (0.10, 0.58, 0.65)
    vb.rotation_euler = (math.radians(15), math.radians(-12), math.radians(-30))
    vb.data.materials.append(mat_velvet)

    # Real BlenderKit Dagger & Roman Sword on the marble floor!
    dag = load_local_blend("bk_dagger.blend")
    if dag:
        verts = [v.co for v in dag.data.vertices]
        sf = 0.42 / max(max(v.z for v in verts) - min(v.z for v in verts), 0.1)
        dag.scale = (sf, sf, sf)
        dag.location = (0.45, -0.65, 0.03)
        dag.rotation_euler = (math.radians(88), 0, math.radians(55))

    # Conspirator Senators standing on the left & top-left perimeter looking down at Caesar (matching 12:30.0!)
    sen_proto = load_local_blend("clean_caesar_orator.blend")
    mod_d = sen_proto.modifiers.new("Dec", "DECIMATE"); mod_d.ratio = 0.35
    bpy.context.view_layer.objects.active = sen_proto; bpy.ops.object.modifier_apply(modifier=mod_d.name)
    for v in sen_proto.data.vertices:
        if v.co.x < -0.14 and v.co.z > 1.05:
            dx = -0.14 - v.co.x; v.co.z -= dx * 0.75; v.co.x = -0.14 - dx * 0.50
    sen_proto.data.update()
    sen_proto.data.materials.clear(); sen_proto.data.materials.append(mat_sen)
    sen_proto.hide_render = True; sen_proto.location = (0, 0, -30)

    for sx, sy, srz in [(-2.3, -1.1, -65), (-1.6, -0.8, -55), (-1.9, 0.4, -85), (-1.2, 1.5, -35), (-0.4, 1.8, -10), (-2.6, 1.2, -70)]:
        st_i = sen_proto.copy(); st_i.hide_render = False
        st_i.location = (sx, sy, 0.0)
        st_i.rotation_euler = (0, 0, math.radians(srz))
        scn.collection.objects.link(st_i)

    # Dramatic Top-Down Chiaroscuro Spotlight
    ld_top = bpy.data.lights.new("CrimeKey", type='AREA'); ld_top.energy = 260.0; ld_top.size = 3.2; ld_top.color = (1.0, 0.94, 0.86)
    lo_top = bpy.data.objects.new("CrimeKey", ld_top); scn.collection.objects.link(lo_top); lo_top.location = (-2.0, -2.5, 5.8)
    lo_top.rotation_euler = (Vector((0, 0, 0)) - lo_top.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 38.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (0.2, -3.2, 4.8)
    co.rotation_euler = (Vector((-0.35, 0.15, 0.0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)
