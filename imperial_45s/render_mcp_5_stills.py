#!/usr/bin/env python3
"""
Iter 2: Renders the 5 Hero 3D Scenes in Blender 4.3 Cycles using real BlenderKit .blend assets
and Museum Laser Scans (with rotation_mode='XYZ' fix, true 3D topographic relief mesh,
non-overlapping organic blood pool, and exact camera framing), then stitches the Side-by-Side Board.
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
    # Board is 2536x1920:
    # Board A (top): 3 rows of 420px height (header=36px, image=384px -> 3*420 = 1260px), 3 cols of 640px width
    # Divider: 16px red bar (y=1260..1276)
    # Board B (bottom): 3 rows of 420px height starting at y=1276 (1276 + 3*420 = 2536px)
    def crop_cell(is_board_b, row, col):
        y0 = (1276 if is_board_b else 0) + row * 420 + 36
        x0 = col * 640
        return board[y0:y0+384, x0:x0+640]

    refs = [
        ("SCENE 1: Curia of Pompey Interior (00:15.0)", crop_cell(False, 0, 0)),
        ("SCENE 2: Cutaway Architecture & Portico Gardens (00:42.0)", crop_cell(False, 0, 2)),
        ("SCENE 3: 3D Extruded Topographic Relief Map (05:00.0)", crop_cell(True, 1, 2)),
        ("SCENE 4: Exploded Marble Bust + Medallion + Red Arc (05:15.0)", crop_cell(True, 2, 0)),
        ("SCENE 5: Top-Down Crime Scene & Blood Pool (12:30.0)", crop_cell(False, 2, 1)),
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

        im = Image.fromarray(cv2.cvtColor(our_raw, cv2.COLOR_BGR2RGB)).convert("RGBA")
        ov = Image.new("RGBA", (960, 540), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)

        if s_id == 0:
            dr.text((466, 118), "DICTATOR", font=gf("Inter-Bold.ttf", 12), fill=(0,0,0,180), anchor="lm")
            dr.text((465, 117), "DICTATOR", font=gf("Inter-Bold.ttf", 12), fill=(225,228,235,245), anchor="lm")
            dr.text((466, 139), "JULIUS CAESAR", font=gf("Inter-Bold.ttf", 25), fill=(0,0,0,200), anchor="lm")
            dr.text((465, 138), "JULIUS CAESAR", font=gf("Inter-Bold.ttf", 25), fill=(255,255,255,255), anchor="lm")
            dr.rectangle([42, 412, 195, 478], fill=(16, 17, 20, 235))
            dr.text((54, 424), "15TH OF MARCH", font=gf("Inter-Bold.ttf", 13), fill=(220, 224, 230, 255))
            dr.text((54, 444), "44 BC", font=gf("Inter-Bold.ttf", 24), fill=(255, 255, 255, 255))
        elif s_id == 2:
            for bx, by, btxt, bcol in [(325, 185, "CAESAR'S FACTION", (200, 16, 46)), (715, 315, "POMPEY'S FACTION", (35, 95, 225))]:
                dr.rectangle([bx-82, by-14, bx+82, by+14], fill=(248, 248, 250, 248))
                dr.text((bx, by), btxt, font=gf("Inter-Bold.ttf", 12), fill=(*bcol, 255), anchor="mm")
            dr.text((465, 248), "ROME", font=gf("Inter-Bold.ttf", 14), fill=(255, 255, 255, 245), anchor="mm")
            dr.rectangle([140, 448, 820, 512], fill=(8, 9, 12, 225), outline=(110, 115, 125, 190), width=1)
            dr.line([(195, 486), (765, 486)], fill=(235, 238, 245, 235), width=2)
            ticks = [
                (195, "JAN, 49 BC", "RUBICON CROSSING"),
                (310, "MARCH, 49 BC", "CAESAR TAKES ROME"),
                (440, "AUG, 48 BC", "BATTLE OF PHARSALUS"),
                (590, "FEB, 44 BC", "DICTATOR PERPETUO"),
                (765, "MARCH, 45 BC", "BATTLE OF MUNDA"),
            ]
            for tx, t_yr, t_ev in ticks:
                dr.ellipse([tx-3, 483, tx+3, 489], fill=(255,255,255,255))
                dr.text((tx, 468), t_ev, font=gf("Inter-Regular.ttf", 8), fill=(195, 200, 210, 230), anchor="mm")
                dr.text((tx, 499), t_yr, font=gf("Inter-Bold.ttf", 10), fill=(245, 248, 252, 255), anchor="mm")
        elif s_id == 3:
            dr.text((505, 320), "POMPEY", font=gf("Inter-Bold.ttf", 22), fill=(255, 255, 255, 255), anchor="lm")
            dr.text((505, 338), "\"THE GREAT\"", font=gf("Inter-Regular.ttf", 10), fill=(210, 215, 222, 235), anchor="lm")
            dr.text((505, 350), "\"THE DEFEATED\"", font=gf("Inter-Bold.ttf", 10), fill=(235, 55, 65, 255), anchor="lm")

        our_final = cv2.cvtColor(np.array(Image.alpha_composite(im, ov).convert("RGB")), cv2.COLOR_RGB2BGR)
        hdr_ref = np.zeros((38, 960, 3), dtype=np.uint8); hdr_ref[:] = (18, 20, 26)
        hdr_our = np.zeros((38, 960, 3), dtype=np.uint8); hdr_our[:] = (18, 26, 20)
        cv2.putText(hdr_ref, f"ORIGINAL IMPERIAL VIDEO: {title}", (16, 26), cv2.FONT_HERSHEY_DUPLEX, 0.65, (80, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(hdr_our, f"OUR BLENDER 4.3 + BLENDERKIT MCP (Iter 2): {title}", (16, 26), cv2.FONT_HERSHEY_DUPLEX, 0.65, (100, 255, 120), 1, cv2.LINE_AA)
        rows_out.append(np.hstack([np.vstack([hdr_ref, ref_960]), np.vstack([hdr_our, our_final])]))

    full_board = np.vstack(rows_out)
    cv2.imwrite(out_jpg, full_board, [cv2.IMWRITE_JPEG_QUALITY, 94])
    print("Saved comparison board:", out_jpg)
    sys.exit(0)

# Inside Blender:
import bpy, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SCENE_ID = int(argv[0])
OUT_PNG = argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, HERE)
from mcp_scene1_curia import make_pbr_stone_or_wood
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
            o.rotation_mode = 'XYZ'
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
    obj.rotation_mode = 'XYZ'
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    return obj

if SCENE_ID == 0:
    scn = init_cycles()
    mat_floor = make_curia_carpet_and_border_floor()
    mat_trav = make_pbr_stone_or_wood("TravWall", (0.42, 0.39, 0.35), rough=0.42, noise_scale=6.0)
    mat_step = make_pbr_stone_or_wood("StepMarble", (0.54, 0.51, 0.46), rough=0.35, noise_scale=8.0)
    mat_wood = make_pbr_stone_or_wood("DarkWalnut", (0.12, 0.06, 0.03), rough=0.32, noise_scale=16.0)

    bpy.ops.mesh.primitive_plane_add(size=24.0, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat_floor)

    for side in (-1, 1):
        for tier in range(3):
            x_c = side * (2.65 + tier * 0.98)
            z_top = 0.16 + tier * 0.28
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c, -0.4, z_top * 0.5))
            st = bpy.context.active_object; st.scale = (0.98, 7.6, z_top); st.data.materials.append(mat_step)
            for y_sec, sec_len in [(-2.2, 3.0), (1.4, 3.0)]:
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.05, y_sec, z_top + 0.42))
                seat = bpy.context.active_object; seat.scale = (0.46, sec_len, 0.06); seat.data.materials.append(mat_wood)
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.26, y_sec, z_top + 0.68))
                back = bpy.context.active_object; back.scale = (0.06, sec_len, 0.52); back.data.materials.append(mat_wood)
                for end_s in (-1, 1):
                    y_end = y_sec + end_s * (sec_len * 0.5)
                    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.06, y_end, z_top + 0.38))
                    arm = bpy.context.active_object; arm.scale = (0.50, 0.08, 0.76); arm.data.materials.append(mat_wood)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.8, 4.0))
    rw = bpy.context.active_object; rw.scale = (16.0, 0.5, 8.0); rw.data.materials.append(mat_trav)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.52, 2.2))
    dr = bpy.context.active_object; dr.scale = (2.4, 0.12, 4.4); dr.data.materials.append(mat_wood)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.55, 2.3))
    df = bpy.context.active_object; df.scale = (2.75, 0.18, 4.7); df.data.materials.append(mat_step)
    for sx in (-3.4, 3.4):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, 5.52, 1.6))
        ml = bpy.context.active_object; ml.scale = (3.2, 0.10, 1.5); ml.data.materials.append(mat_step)

    col_proto = load_local_blend("bk_column_corinthian.blend")
    if col_proto:
        verts = [v.co for v in col_proto.data.vertices]
        mz, xz = min(v.z for v in verts), max(v.z for v in verts)
        cx, cy = 0.5*(min(v.x for v in verts)+max(v.x for v in verts)), 0.5*(min(v.y for v in verts)+max(v.y for v in verts))
        sf = 5.5 / max(xz - mz, 1e-4)
        for v in col_proto.data.vertices:
            v.co = Vector(((v.co.x - cx)*sf, (v.co.y - cy)*sf, (v.co.z - mz)*sf))
        col_proto.data.update(); col_proto.hide_render = True; col_proto.location = (0, 0, -30)
        for cx_p, cy_p, cz_p in [(-3.4, 4.6, 0.0), (3.4, 4.6, 0.0), (-5.2, 1.5, 0.72), (5.2, 1.5, 0.72)]:
            inst = col_proto.copy(); inst.rotation_mode = 'XYZ'; inst.hide_render = False
            inst.location = (cx_p, cy_p, cz_p); scn.collection.objects.link(inst)

    mat_caesar = make_senator_clavus_mat("CaesarMat", is_caesar=True, hair_tone=0.18)
    mat_sen_1 = make_senator_clavus_mat("SenMat1", is_caesar=False, hair_tone=0.55)
    orator_proto = load_local_blend("clean_caesar_orator.blend")
    mod_d = orator_proto.modifiers.new("Dec", "DECIMATE"); mod_d.ratio = 0.35
    bpy.context.view_layer.objects.active = orator_proto; bpy.ops.object.modifier_apply(modifier=mod_d.name)

    seated_male_proto = create_seated_male_senator_mesh(orator_proto)
    seated_male_proto.rotation_mode = 'XYZ'
    seated_male_proto.data.materials.clear(); seated_male_proto.data.materials.append(mat_sen_1)
    seated_male_proto.hide_render = True; seated_male_proto.location = (0, 0, -30)

    stand_male_proto = orator_proto.copy(); stand_male_proto.data = orator_proto.data.copy()
    stand_male_proto.rotation_mode = 'XYZ'
    scn.collection.objects.link(stand_male_proto)
    for v in stand_male_proto.data.vertices:
        if v.co.x < -0.14 and v.co.z > 1.05:
            dx = -0.14 - v.co.x; v.co.z -= dx * 0.75; v.co.x = -0.14 - dx * 0.50
    stand_male_proto.data.update()
    stand_male_proto.data.materials.clear(); stand_male_proto.data.materials.append(mat_sen_1)
    stand_male_proto.hide_render = True; stand_male_proto.location = (0, 0, -30)
    orator_proto.hide_render = True; orator_proto.location = (0, 0, -30)

    caesar_walk = stand_male_proto.copy(); caesar_walk.data = stand_male_proto.data.copy()
    caesar_walk.rotation_mode = 'XYZ'
    caesar_walk.data.materials.clear(); caesar_walk.data.materials.append(mat_caesar)
    caesar_walk.hide_render = False; caesar_walk.location = (-0.15, 1.55, 0.0)
    caesar_walk.rotation_euler = (0, 0, math.radians(-20))
    scn.collection.objects.link(caesar_walk)

    for side in (-1, 1):
        base_rz = 90.0 if side == -1 else -90.0
        for tier in range(3):
            x_pos = side * (2.65 + tier * 0.98)
            z_pos = 0.16 + tier * 0.28
            for y_pos in [-3.4, -2.5, -1.6, -0.8, 0.3, 1.2, 2.1, 2.9]:
                inst = seated_male_proto.copy()
                inst.rotation_mode = 'XYZ'
                inst.hide_render = False
                inst.location = (x_pos, y_pos, z_pos)
                jitter = ((int(y_pos*10) * 17 + tier * 31) % 16) - 8
                inst.rotation_euler = (0, 0, math.radians(base_rz + jitter))
                scn.collection.objects.link(inst)

    for sx, sy, sz, srz in [
        (-1.35, 4.3, 0.0, 60), (-0.65, 4.5, 0.0, -45),
        (-1.55, 0.6, 0.0, 75), (-1.40, -0.3, 0.0, 115),
        (1.35, -0.2, 0.0, -85),
        (1.85, 2.7, 0.0, -55), (2.45, 2.8, 0.0, -125)
    ]:
        st_i = stand_male_proto.copy(); st_i.rotation_mode = 'XYZ'; st_i.hide_render = False
        st_i.location = (sx, sy, sz); st_i.rotation_euler = (0, 0, math.radians(srz))
        scn.collection.objects.link(st_i)

    ld_key = bpy.data.lights.new("SunShaft", type='AREA'); ld_key.energy = 340.0; ld_key.size = 4.0; ld_key.color = (1.0, 0.95, 0.88)
    lo_key = bpy.data.objects.new("SunShaft", ld_key); scn.collection.objects.link(lo_key); lo_key.location = (-3.8, -2.8, 6.8)
    lo_key.rotation_euler = (Vector((0.0, 1.0, 0.0)) - lo_key.location).to_track_quat('-Z', 'Y').to_euler()
    ld_fill = bpy.data.lights.new("AmbientFill", type='AREA'); ld_fill.energy = 110.0; ld_fill.size = 5.5; ld_fill.color = (0.90, 0.93, 1.0)
    lo_fill = bpy.data.objects.new("AmbientFill", ld_fill); scn.collection.objects.link(lo_fill); lo_fill.location = (3.8, -4.8, 5.2)
    lo_fill.rotation_euler = (Vector((0.0, 0.5, 1.0)) - lo_fill.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 29.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (-0.95, -5.8, 4.85)
    co.rotation_euler = (Vector((-0.05, 1.15, 0.65)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 1:
    scn = init_cycles()
    scn.view_settings.exposure = 0.15
    mat_stone = make_pbr_stone_or_wood("PorticoStone", (0.68, 0.63, 0.55), rough=0.35, noise_scale=8.0)
    mat_wall = make_pbr_stone_or_wood("PorticoWall", (0.54, 0.50, 0.44), rough=0.42, noise_scale=10.0)
    mat_roof_terra = make_pbr_stone_or_wood("TerraRoof", (0.62, 0.42, 0.28), rough=0.40, noise_scale=18.0)
    mat_roof_slate = make_pbr_stone_or_wood("SlateRoof", (0.28, 0.30, 0.34), rough=0.45, noise_scale=15.0)
    mat_city = make_pbr_stone_or_wood("CityBlock", (0.20, 0.22, 0.25), rough=0.55, noise_scale=12.0)
    mat_grass = make_pbr_stone_or_wood("GardenGrass", (0.26, 0.38, 0.20), rough=0.72, noise_scale=25.0)
    mat_tree = make_pbr_stone_or_wood("CypressFoliage", (0.14, 0.26, 0.12), rough=0.78, noise_scale=30.0)
    mat_txt = bpy.data.materials.new("TxtWhite"); mat_txt.use_nodes = True
    bsdf_t = mat_txt.node_tree.nodes.get("Principled BSDF")
    bsdf_t.inputs["Base Color"].default_value = (0.98, 0.98, 1.0, 1.0)
    if "Emission Color" in bsdf_t.inputs:
        bsdf_t.inputs["Emission Color"].default_value = (0.98, 0.98, 1.0, 1.0)
        bsdf_t.inputs["Emission Strength"].default_value = 0.65

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.0, 0, -0.35))
    base = bpy.context.active_object; base.scale = (22.0, 14.5, 0.70); base.data.materials.append(mat_stone)

    for gx in (-5.5, -1.5):
        for gy in (-2.5, 2.5):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gx, gy, 0.04))
            gb = bpy.context.active_object; gb.scale = (3.2, 2.4, 0.08); gb.data.materials.append(mat_grass)
            for tx in (gx - 1.2, gx - 0.4, gx + 0.4, gx + 1.2):
                for ty in (gy - 0.85, gy + 0.85):
                    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.18, radius2=0.02, depth=0.95, location=(tx, ty, 0.52))
                    tr = bpy.context.active_object; tr.data.materials.append(mat_tree)

    col_proto = load_local_blend("bk_column_corinthian.blend")
    if col_proto:
        verts = [v.co for v in col_proto.data.vertices]
        mz, xz = min(v.z for v in verts), max(v.z for v in verts)
        cx, cy = 0.5*(min(v.x for v in verts)+max(v.x for v in verts)), 0.5*(min(v.y for v in verts)+max(v.y for v in verts))
        sf = 1.55 / max(xz - mz, 1e-4)
        for v in col_proto.data.vertices:
            v.co = Vector(((v.co.x - cx)*sf, (v.co.y - cy)*sf, (v.co.z - mz)*sf))
        col_proto.data.update(); col_proto.hide_render = True; col_proto.location = (0, 0, -30)
        for x_p in [i * 0.75 for i in range(-11, 3)]:
            for y_p in (-4.4, 4.4):
                c_i = col_proto.copy(); c_i.hide_render = False; c_i.location = (x_p, y_p, 0.0)
                scn.collection.objects.link(c_i)
        for y_p in [-3.6 + i*0.72 for i in range(11)]:
            c_i = col_proto.copy(); c_i.hide_render = False; c_i.location = (-8.25, y_p, 0.0)
            scn.collection.objects.link(c_i)
        for y_p in [-1.5, -0.9, -0.3, 0.3, 0.9, 1.5]:
            c_i = col_proto.copy(); c_i.hide_render = False; c_i.location = (2.2, y_p, 0.25)
            c_i.scale = (1.25, 1.25, 1.35); scn.collection.objects.link(c_i)

    for gy in (-5.0, 5.0):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.0, gy, 1.68))
        rf = bpy.context.active_object; rf.scale = (11.2, 1.3, 0.22); rf.data.materials.append(mat_roof_terra)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.2, gy * 1.32, 1.25))
        ab = bpy.context.active_object; ab.scale = (15.5, 2.0, 2.5); ab.data.materials.append(mat_wall)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.2, gy * 1.32, 2.65))
        ar = bpy.context.active_object; ar.scale = (15.7, 2.2, 0.30); ar.data.materials.append(mat_roof_slate)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.8, 0.0, 1.68))
    w_rf = bpy.context.active_object; w_rf.scale = (1.3, 11.2, 0.22); w_rf.data.materials.append(mat_roof_terra)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.4, 0.0, 1.85))
    curia = bpy.context.active_object; curia.scale = (4.2, 3.8, 3.7); curia.data.materials.append(mat_stone)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.4, 0.0, 3.85))
    cr = bpy.context.active_object; cr.scale = (4.5, 4.1, 0.30); cr.data.materials.append(mat_roof_terra)
    for wy in (-3.8, 3.8):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.8, wy, 1.35))
        wg = bpy.context.active_object; wg.scale = (3.8, 2.8, 2.7); wg.data.materials.append(mat_wall)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.8, wy, 2.85))
        wr = bpy.context.active_object; wr.scale = (4.0, 3.0, 0.28); wr.data.materials.append(mat_roof_slate)

    for bx, by, sx, sy, sz in [
        (2.5, -9.2, 3.2, 2.4, 1.6), (6.2, -8.8, 3.6, 2.8, 1.9), (4.2, -12.0, 4.0, 2.6, 1.5),
        (-1.5, -9.5, 3.0, 2.2, 1.4), (8.8, -5.5, 2.8, 3.4, 1.8), (9.2, -1.2, 3.2, 3.0, 2.1)
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, sz*0.5 - 0.35))
        cb = bpy.context.active_object; cb.scale = (sx, sy, sz); cb.data.materials.append(mat_city)

    font_p = os.path.join(HERE, "Inter-Bold.ttf")
    bpy.ops.object.text_add(location=(3.8, 0.0, 4.05))
    t_cur = bpy.context.active_object; t_cur.rotation_mode = 'XYZ'
    t_cur.data.body = "CURIA"; t_cur.data.align_x = 'CENTER'; t_cur.data.align_y = 'CENTER'
    t_cur.data.size = 1.05; t_cur.data.extrude = 0.14
    if os.path.exists(font_p): t_cur.data.font = bpy.data.fonts.load(font_p)
    t_cur.rotation_euler = (math.radians(55), 0, math.radians(-35)); t_cur.data.materials.append(mat_txt)

    bpy.ops.object.text_add(location=(-3.4, 0.0, 0.12))
    t_por = bpy.context.active_object; t_por.rotation_mode = 'XYZ'
    t_por.data.body = "PORTICO OF POMPEY"; t_por.data.align_x = 'CENTER'; t_por.data.align_y = 'CENTER'
    t_por.data.size = 0.68; t_por.data.extrude = 0.08
    if os.path.exists(font_p): t_por.data.font = bpy.data.fonts.load(font_p)
    t_por.data.materials.append(mat_txt)

    ld_sun = bpy.data.lights.new("Sun", type='AREA'); ld_sun.energy = 1650.0; ld_sun.size = 10.0; ld_sun.color = (1.0, 0.95, 0.88)
    lo_sun = bpy.data.objects.new("Sun", ld_sun); scn.collection.objects.link(lo_sun); lo_sun.location = (-12.0, -14.0, 18.0)
    lo_sun.rotation_euler = (Vector((0, 0, 0)) - lo_sun.location).to_track_quat('-Z', 'Y').to_euler()
    ld_f = bpy.data.lights.new("Fill", type='AREA'); ld_f.energy = 480.0; ld_f.size = 12.0; ld_f.color = (0.85, 0.90, 1.0)
    lo_f = bpy.data.objects.new("Fill", ld_f); scn.collection.objects.link(lo_f); lo_f.location = (14.0, -12.0, 12.0)
    lo_f.rotation_euler = (Vector((0, 0, 0)) - lo_f.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 34.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (-11.8, -14.8, 11.2)
    co.rotation_euler = (Vector((-0.5, -0.8, 0.5)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 2:
    scn = init_cycles()
    scn.view_settings.exposure = 0.15
    scn.world.node_tree.nodes.get("Background").inputs[0].default_value = (0.004, 0.005, 0.007, 1.0)

    def make_emit_mat(name, base_rgb, emit_rgb, emit_str, rough=0.35):
        m = bpy.data.materials.new(name); m.use_nodes = True
        bs = m.node_tree.nodes.get("Principled BSDF")
        bs.inputs["Base Color"].default_value = (*base_rgb, 1.0)
        bs.inputs["Roughness"].default_value = rough
        if "Emission Color" in bs.inputs:
            bs.inputs["Emission Color"].default_value = (*emit_rgb, 1.0)
            bs.inputs["Emission Strength"].default_value = emit_str
        return m

    mat_grid_line = make_emit_mat("GridLine", (0.25, 0.27, 0.32), (0.25, 0.27, 0.32), 0.45)
    for ix in range(-14, 15):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ix * 0.65, 0.0, 0.0))
        gl = bpy.context.active_object; gl.scale = (0.012, 11.0, 0.004); gl.data.materials.append(mat_grid_line)
    for iy in range(-8, 9):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, iy * 0.65, 0.0))
        gl = bpy.context.active_object; gl.scale = (18.5, 0.012, 0.004); gl.data.materials.append(mat_grid_line)

    with open(os.path.join(HERE, "med_countries_50m.geojson"), "r") as f:
        gj = json.load(f)

    caesar_iso = {"ITA", "FRA", "BEL", "CHE", "AUT", "SVN", "HRV"}
    pompey_iso = {"ESP", "PRT", "GRC", "ALB", "MKD", "BGR", "TUR", "TUN", "DZA", "MAR", "LBY", "SYR", "EGY"}

    mat_caesar_land = make_emit_mat("CaesarRed", (0.85, 0.06, 0.12), (0.95, 0.08, 0.15), 1.35)
    mat_pompey_land = make_emit_mat("PompeyBlue", (0.08, 0.24, 0.92), (0.12, 0.32, 1.0), 1.35)
    mat_neutral_land = make_emit_mat("NeutralDark", (0.08, 0.09, 0.12), (0.05, 0.06, 0.08), 0.25)

    for feat in gj["features"]:
        iso = feat["properties"].get("ISO_A3", "")
        geom_d = feat["geometry"]
        polys = [geom_d["coordinates"][0]] if geom_d["type"] == "Polygon" else [p[0] for p in geom_d["coordinates"]]
        for ring in polys:
            pts_2d = []
            for lon, lat in ring:
                x = (lon - 12.0) * 0.32
                y = (lat - 40.0) * 0.38
                if -10.5 <= x <= 10.5 and -5.5 <= y <= 5.5:
                    pts_2d.append((x, y))
            if len(pts_2d) < 4:
                continue
            curve_data = bpy.data.curves.new(f"C_{iso}", type='CURVE')
            curve_data.dimensions = '2D'
            curve_data.fill_mode = 'BOTH'
            curve_data.extrude = 0.12 if iso in (caesar_iso | pompey_iso) else 0.05
            curve_data.bevel_depth = 0.015
            spline = curve_data.splines.new('POLY')
            spline.points.add(len(pts_2d) - 1)
            for idx_p, (px, py) in enumerate(pts_2d):
                spline.points[idx_p].co = (px, py, 0.0, 1.0)
            spline.use_cyclic_u = True
            c_obj = bpy.data.objects.new(f"Map_{iso}", curve_data)
            c_obj.location = (0, 0, 0.06)
            scn.collection.objects.link(c_obj)
            if iso in caesar_iso:
                c_obj.data.materials.append(mat_caesar_land)
            elif iso in pompey_iso:
                c_obj.data.materials.append(mat_pompey_land)
            else:
                c_obj.data.materials.append(mat_neutral_land)

    mat_caesar_mtn = make_emit_mat("CaesarMtn", (0.95, 0.18, 0.22), (1.0, 0.22, 0.25), 0.95, rough=0.5)
    mat_pompey_mtn = make_emit_mat("PompeyMtn", (0.18, 0.42, 1.0), (0.22, 0.48, 1.0), 0.95, rough=0.5)
    for (mx, my), m_mat, sx, sy, sz in [
        ((-1.2, 2.2), mat_caesar_mtn, 1.8, 0.55, 0.45),
        ((-0.2, 1.2), mat_caesar_mtn, 0.55, 1.4, 0.38),
        ((-4.8, 0.3), mat_pompey_mtn, 1.6, 1.1, 0.38),
        ((3.2, -0.2), mat_pompey_mtn, 1.2, 1.1, 0.38),
    ]:
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=24, size=1.0, location=(mx, my, 0.15))
        mt = bpy.context.active_object; mt.scale = (sx, sy, sz)
        tex = bpy.data.textures.new(f"T_{mx}", type='VORONOI'); tex.noise_scale = 0.55
        mod = mt.modifiers.new("Mtn", "DISPLACE"); mod.texture = tex; mod.strength = 0.55
        mt.data.materials.append(m_mat)

    mat_card = make_emit_mat("CardCream", (0.95, 0.92, 0.86), (0.95, 0.92, 0.86), 1.2)
    for cx, cy, crz in [(-0.45, 1.35, 10), (-0.15, 0.75, -8)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, 0.32))
        cd_o = bpy.context.active_object; cd_o.scale = (0.42, 0.58, 0.03)
        cd_o.rotation_euler = (math.radians(25), 0, math.radians(crz))
        cd_o.data.materials.append(mat_card)

    ld = bpy.data.lights.new("MapKey", type='AREA'); ld.energy = 850.0; ld.size = 10.0
    lo = bpy.data.objects.new("MapKey", ld); scn.collection.objects.link(lo); lo.location = (-3.0, -6.0, 10.0)
    lo.rotation_euler = (Vector((0, 0, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 35.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (-0.4, -7.8, 6.2)
    co.rotation_euler = (Vector((-0.2, 0.3, 0.0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 3:
    scn = init_cycles()
    scn.view_settings.exposure = -0.15
    scn.world.node_tree.nodes.get("Background").inputs[1].default_value = 0.03

    bust = load_local_blend("clean_caesar_bust.blend")
    for v in bust.data.vertices:
        v.co.x = -v.co.x
        v.co.y = -v.co.y
    bust.data.update()

    verts = [v.co for v in bust.data.vertices]
    cx = 0.5*(min(v.x for v in verts)+max(v.x for v in verts))
    cy = 0.5*(min(v.y for v in verts)+max(v.y for v in verts))
    mz, xz = min(v.z for v in verts), max(v.z for v in verts)
    sf = 1.15 / max(xz - mz, 1e-4)
    for v in bust.data.vertices:
        v.co = Vector(((v.co.x - cx)*sf, (v.co.y - cy)*sf, (v.co.z - mz)*sf + 0.25))
    bust.data.update()

    mat_marble = bpy.data.materials.new("ChiaroscuroMarble"); mat_marble.use_nodes = True
    nt = mat_marble.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.34
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.44; ramp.color_ramp.elements[0].color = (0.12, 0.12, 0.13, 1.0)
    ramp.color_ramp.elements[1].position = 0.56; ramp.color_ramp.elements[1].color = (0.82, 0.80, 0.78, 1.0)
    nt.links.new(geom.outputs["Pointiness"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mat_core = bpy.data.materials.new("CrimsonCore"); mat_core.use_nodes = True
    bs_c = mat_core.node_tree.nodes.get("Principled BSDF")
    bs_c.inputs["Base Color"].default_value = (0.52, 0.02, 0.03, 1.0)
    bs_c.inputs["Roughness"].default_value = 0.40
    if "Emission Color" in bs_c.inputs:
        bs_c.inputs["Emission Color"].default_value = (0.65, 0.02, 0.03, 1.0)
        bs_c.inputs["Emission Strength"].default_value = 0.45

    bust.data.materials.clear()
    bust.data.materials.append(mat_marble)
    bust.data.materials.append(mat_core)

    bust_top = bust.copy(); bust_top.data = bust.data.copy(); bust_top.rotation_mode = 'XYZ'; scn.collection.objects.link(bust_top)
    bust_core = bust.copy(); bust_core.data = bust.data.copy(); bust_core.rotation_mode = 'XYZ'; scn.collection.objects.link(bust_core)
    bust_core.scale = (0.78, 0.78, 0.78)
    bust_core.location = (0.04, 0.0, 0.18)
    bust_core.data.materials.clear(); bust_core.data.materials.append(mat_core)

    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.38, 0.0, 1.35), rotation=(0.0, math.radians(-25), math.radians(10)))
    cutter = bpy.context.active_object; cutter.data.materials.append(mat_core)

    bpy.context.view_layer.objects.active = bust
    m1 = bust.modifiers.new("Cut1", "BOOLEAN"); m1.operation = 'DIFFERENCE'; m1.solver = 'EXACT'; m1.object = cutter
    bpy.ops.object.modifier_apply(modifier=m1.name)

    bpy.context.view_layer.objects.active = bust_top
    m2 = bust_top.modifiers.new("Cut2", "BOOLEAN"); m2.operation = 'INTERSECT'; m2.solver = 'EXACT'; m2.object = cutter
    bpy.ops.object.modifier_apply(modifier=m2.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

    bust_top.location = (0.12, 0.02, 0.14)
    bust_top.rotation_euler = (0, math.radians(8), math.radians(-5))

    mat_silver = make_pbr_stone_or_wood("SilverCoin", (0.48, 0.49, 0.52), rough=0.32, metal=0.85, noise_scale=24.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.58, depth=0.04, location=(0.0, 0.25, 0.85), rotation=(math.radians(90), 0, 0))
    coin = bpy.context.active_object; coin.data.materials.append(mat_silver)

    mat_disc = bpy.data.materials.new("RedPodiumDisc"); mat_disc.use_nodes = True
    bs_d = mat_disc.node_tree.nodes.get("Principled BSDF")
    bs_d.inputs["Base Color"].default_value = (0.75, 0.03, 0.05, 1.0)
    if "Emission Color" in bs_d.inputs:
        bs_d.inputs["Emission Color"].default_value = (0.85, 0.04, 0.06, 1.0)
        bs_d.inputs["Emission Strength"].default_value = 1.6
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.52, depth=0.015, location=(0.0, 0.0, 0.02))
    disc = bpy.context.active_object; disc.scale = (1.15, 0.65, 1.0); disc.data.materials.append(mat_disc)

    mat_beam = bpy.data.materials.new("RedArc"); mat_beam.use_nodes = True
    bs_b = mat_beam.node_tree.nodes.get("Principled BSDF")
    bs_b.inputs["Base Color"].default_value = (0.95, 0.05, 0.08, 1.0)
    if "Emission Color" in bs_b.inputs:
        bs_b.inputs["Emission Color"].default_value = (1.0, 0.06, 0.10, 1.0)
        bs_b.inputs["Emission Strength"].default_value = 4.5
    curve_d = bpy.data.curves.new("RedCurve", type='CURVE')
    curve_d.dimensions = '3D'; curve_d.bevel_depth = 0.012
    sp = curve_d.splines.new('NURBS')
    pts_arc = [(-3.2, 0.4, 0.10), (-1.1, 0.35, 0.65), (0.8, 0.35, 1.05), (3.2, 0.4, 1.38)]
    sp.points.add(len(pts_arc) - 1)
    for idx_a, (ax, ay, az) in enumerate(pts_arc):
        sp.points[idx_a].co = (ax, ay, az, 1.0)
    arc_obj = bpy.data.objects.new("RedArcObj", curve_d)
    scn.collection.objects.link(arc_obj); arc_obj.data.materials.append(mat_beam)

    ld_k = bpy.data.lights.new("BustKey", type='AREA'); ld_k.energy = 55.0; ld_k.size = 1.4
    lo_k = bpy.data.objects.new("BustKey", ld_k); scn.collection.objects.link(lo_k); lo_k.location = (-1.6, -1.8, 1.7)
    lo_k.rotation_euler = (Vector((0, 0, 0.85)) - lo_k.location).to_track_quat('-Z', 'Y').to_euler()

    ld_r = bpy.data.lights.new("RedRim", type='AREA'); ld_r.energy = 45.0; ld_r.size = 1.2; ld_r.color = (1.0, 0.12, 0.15)
    lo_r = bpy.data.objects.new("RedRim", ld_r); scn.collection.objects.link(lo_r); lo_r.location = (1.5, -1.0, 1.4)
    lo_r.rotation_euler = (Vector((0, 0, 0.85)) - lo_r.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 50.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (0.0, -5.2, 0.78)
    co.rotation_euler = (Vector((0, 0, 0.72)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

elif SCENE_ID == 4:
    scn = init_cycles()
    scn.view_settings.exposure = 0.05

    mat_slab = make_pbr_stone_or_wood("CrimeMarbleSlab", (0.64, 0.61, 0.57), rough=0.30, noise_scale=3.5)
    bpy.ops.mesh.primitive_plane_add(size=18.0, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat_slab)

    mat_blood = bpy.data.materials.new("WetCrimsonBlood"); mat_blood.use_nodes = True
    bs_bl = mat_blood.node_tree.nodes.get("Principled BSDF")
    bs_bl.inputs["Base Color"].default_value = (0.42, 0.008, 0.012, 1.0)
    bs_bl.inputs["Roughness"].default_value = 0.08
    if "Emission Color" in bs_bl.inputs:
        bs_bl.inputs["Emission Color"].default_value = (0.38, 0.006, 0.010, 1.0)
        bs_bl.inputs["Emission Strength"].default_value = 0.35

    lobes = [
        (0.0, 0.05, 0.78, 0.58, 15),
        (-0.42, -0.28, 0.48, 0.36, -25),
        (0.48, -0.18, 0.44, 0.32, 40),
        (0.12, 0.48, 0.46, 0.34, -10),
        (-0.55, 0.22, 0.35, 0.25, 30),
        (0.78, -0.48, 0.14, 0.10, 0),
        (-0.30, -0.82, 0.15, 0.11, 20),
        (0.42, -0.75, 0.10, 0.08, -15),
    ]
    for i_l, (lx, ly, sx, sy, lrz) in enumerate(lobes):
        h_z = 0.006 + i_l * 0.0015
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=h_z, location=(lx, ly, h_z * 0.5))
        lb = bpy.context.active_object; lb.scale = (sx, sy, 1.0); lb.rotation_euler = (0, 0, math.radians(lrz))
        lb.data.materials.append(mat_blood)

    for i_f, (fx, fy, frz) in enumerate([(-1.05, -0.15, 110), (-1.45, 0.05, 105), (-1.85, -0.10, 115), (1.35, 0.45, -35), (1.65, 0.30, -40)]):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.10, depth=0.005, location=(fx, fy, 0.003 + i_f*0.0005))
        fp = bpy.context.active_object; fp.scale = (1.3, 0.55, 1.0); fp.rotation_euler = (0, 0, math.radians(frz))
        fp.data.materials.append(mat_blood)

    mat_caesar = make_senator_clavus_mat("FallenCaesarMat", is_caesar=True, hair_tone=0.18)
    mat_sen = make_senator_clavus_mat("CrimeSenMat", is_caesar=False, hair_tone=0.52)
    caesar_fallen = load_local_blend("clean_caesar_orator.blend")
    caesar_fallen.rotation_mode = 'XYZ'
    for v in caesar_fallen.data.vertices:
        v.co.z -= 0.90
    caesar_fallen.data.update()
    caesar_fallen.data.materials.clear(); caesar_fallen.data.materials.append(mat_caesar)
    caesar_fallen.rotation_euler = (math.radians(86), math.radians(12), math.radians(38))
    caesar_fallen.location = (-0.08, 0.08, 0.22)

    mat_gold = make_pbr_stone_or_wood("CrimeGold", (0.82, 0.62, 0.20), rough=0.22, metal=0.92, noise_scale=12.0)
    mat_velvet = make_pbr_stone_or_wood("CrimeVelvet", (0.48, 0.02, 0.03), rough=0.60, noise_scale=20.0)
    mat_wood = make_pbr_stone_or_wood("CrimeWood", (0.14, 0.07, 0.035), rough=0.35, noise_scale=16.0)

    throne_grp = bpy.data.objects.new("OverturnedThrone", None); throne_grp.rotation_mode = 'XYZ'
    scn.collection.objects.link(throne_grp)
    for part_loc, part_sc, p_mat in [
        ((0, 0, 0.25), (0.56, 0.52, 0.07), mat_gold),
        ((0, 0.24, 0.58), (0.56, 0.06, 0.65), mat_gold),
        ((-0.24, -0.22, 0.12), (0.06, 0.06, 0.26), mat_gold),
        ((0.24, -0.22, 0.12), (0.06, 0.06, 0.26), mat_gold),
        ((-0.24, 0.22, 0.12), (0.06, 0.06, 0.26), mat_gold),
        ((0.24, 0.22, 0.12), (0.06, 0.06, 0.26), mat_gold),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=part_loc)
        po = bpy.context.active_object; po.scale = part_sc; po.data.materials.append(p_mat); po.parent = throne_grp
    throne_grp.location = (0.75, 1.05, 0.26)
    throne_grp.rotation_euler = (math.radians(78), math.radians(-18), math.radians(32))

    chair_grp = bpy.data.objects.new("VelvetChair", None); chair_grp.rotation_mode = 'XYZ'
    scn.collection.objects.link(chair_grp)
    for part_loc, part_sc, p_mat in [
        ((0, 0, 0.28), (0.62, 0.58, 0.10), mat_velvet),
        ((0, 0.26, 0.62), (0.62, 0.08, 0.65), mat_velvet),
        ((-0.28, 0, 0.42), (0.07, 0.56, 0.25), mat_wood),
        ((0.28, 0, 0.42), (0.07, 0.56, 0.25), mat_wood),
        ((-0.26, -0.24, 0.14), (0.06, 0.06, 0.28), mat_wood),
        ((0.26, -0.24, 0.14), (0.06, 0.06, 0.28), mat_wood),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=part_loc)
        po = bpy.context.active_object; po.scale = part_sc; po.data.materials.append(p_mat); po.parent = chair_grp
    chair_grp.location = (1.25, -0.95, 0.0)
    chair_grp.rotation_euler = (math.radians(8), math.radians(-6), math.radians(-135))

    sen_proto = load_local_blend("clean_caesar_orator.blend")
    mod_d = sen_proto.modifiers.new("Dec", "DECIMATE"); mod_d.ratio = 0.35
    bpy.context.view_layer.objects.active = sen_proto; bpy.ops.object.modifier_apply(modifier=mod_d.name)
    for v in sen_proto.data.vertices:
        if v.co.x < -0.14 and v.co.z > 1.05:
            dx = -0.14 - v.co.x; v.co.z -= dx * 0.75; v.co.x = -0.14 - dx * 0.50
    sen_proto.data.update()
    sen_proto.data.materials.clear(); sen_proto.data.materials.append(mat_sen)
    sen_proto.hide_render = True; sen_proto.location = (0, 0, -30)

    for sx, sy, srz in [
        (-2.2, -0.8, 70), (-1.45, -0.45, 80), (-1.35, -1.55, 55),
        (-0.65, -1.75, 35), (0.05, -1.85, 10), (-1.25, 1.35, 125), (-0.45, 1.65, 155)
    ]:
        st_i = sen_proto.copy(); st_i.rotation_mode = 'XYZ'; st_i.hide_render = False
        st_i.location = (sx, sy, 0.0)
        st_i.rotation_euler = (0, 0, math.radians(srz))
        scn.collection.objects.link(st_i)

    ld_top = bpy.data.lights.new("CrimeKey", type='AREA'); ld_top.energy = 320.0; ld_top.size = 3.8; ld_top.color = (1.0, 0.95, 0.88)
    lo_top = bpy.data.objects.new("CrimeKey", ld_top); scn.collection.objects.link(lo_top); lo_top.location = (-2.2, -2.5, 6.2)
    lo_top.rotation_euler = (Vector((0, 0, 0)) - lo_top.location).to_track_quat('-Z', 'Y').to_euler()
    ld_f = bpy.data.lights.new("CrimeFill", type='AREA'); ld_f.energy = 85.0; ld_f.size = 4.5
    lo_f = bpy.data.objects.new("CrimeFill", ld_f); scn.collection.objects.link(lo_f); lo_f.location = (2.5, 2.0, 5.0)
    lo_f.rotation_euler = (Vector((0, 0, 0)) - lo_f.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 36.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (0.15, -3.1, 4.9)
    co.rotation_euler = (Vector((-0.25, 0.05, 0.0)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)
