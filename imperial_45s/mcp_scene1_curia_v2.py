import sys; sys.path.append("/var/tmp/blender_mcp")
import bpy, os, math
from mathutils import Vector
from mcp_scene1_curia import load_mesh_from_blend, make_pbr_stone_or_wood

ASSETS = "/var/tmp/blender_mcp/assets"
OUT_DIR = "/var/tmp/blender_mcp/renders"

def make_curia_carpet_and_border_floor():
    """
    Matches Imperial 00:15.0 & 07:15.0:
    - Axis-aligned (0 deg) square checkered tiles (gold-ochre & dark slate) in the central aisle
      (|X| < 1.95m and -3.6m < Y < +3.6m)
    - Framed by a thin dark slate border (1.95..2.05m)
    - Surrounded by pale warm-grey Roman marble floor slabs (#8A857C) everywhere else!
    """
    mat = bpy.data.materials.new("CuriaOpusSectileFloor")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.24
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.50

    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(texcoord.outputs["Object"], sep.inputs["Vector"])

    # Axis-aligned Checker texture (Scale = 4.2 -> ~0.42m squares!)
    checker = nt.nodes.new("ShaderNodeTexChecker")
    checker.inputs["Scale"].default_value = 4.2
    checker.inputs["Color1"].default_value = (0.64, 0.55, 0.34, 1.0)  # Warm antique gold-ochre
    checker.inputs["Color2"].default_value = (0.14, 0.17, 0.20, 1.0)  # Dark blue-slate marble
    nt.links.new(texcoord.outputs["Object"], checker.inputs["Vector"])

    # Mask: |X| < 1.95 and |Y| < 3.60 (in Object coords where plane size=1.0 scaled by 16x18 -> wait: Object coords are before object scale if we don't apply scale, so let's use Geometry->Position world coords!)
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep_w = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geom.outputs["Position"], sep_w.inputs["Vector"])
    nt.links.new(geom.outputs["Position"], checker.inputs["Vector"])
    checker.inputs["Scale"].default_value = 2.35  # 2.35 cycles per meter -> 0.425m tiles in world space!

    abs_x = nt.nodes.new("ShaderNodeMath"); abs_x.operation = 'ABSOLUTE'
    nt.links.new(sep_w.outputs["X"], abs_x.inputs[0])
    lt_x = nt.nodes.new("ShaderNodeMath"); lt_x.operation = 'LESS_THAN'; lt_x.inputs[1].default_value = 1.92
    nt.links.new(abs_x.outputs["Value"], lt_x.inputs[0])

    abs_y = nt.nodes.new("ShaderNodeMath"); abs_y.operation = 'ABSOLUTE'
    nt.links.new(sep_w.outputs["Y"], abs_y.inputs[0])
    lt_y = nt.nodes.new("ShaderNodeMath"); lt_y.operation = 'LESS_THAN'; lt_y.inputs[1].default_value = 3.65
    nt.links.new(abs_y.outputs["Value"], lt_y.inputs[0])

    in_carpet = nt.nodes.new("ShaderNodeMath"); in_carpet.operation = 'MULTIPLY'
    nt.links.new(lt_x.outputs["Value"], in_carpet.inputs[0])
    nt.links.new(lt_y.outputs["Value"], in_carpet.inputs[1])

    # Subtle marble noise for the surrounding grey travertine floor slabs
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.8
    noise.inputs["Detail"].default_value = 6.0
    nt.links.new(geom.outputs["Position"], noise.inputs["Vector"])

    ramp_grey = nt.nodes.new("ShaderNodeValToRGB")
    ramp_grey.color_ramp.elements[0].color = (0.38, 0.36, 0.33, 1.0)
    ramp_grey.color_ramp.elements[1].color = (0.52, 0.49, 0.45, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp_grey.inputs["Fac"])

    mix_floor = nt.nodes.new("ShaderNodeMix"); mix_floor.data_type = 'RGBA'
    nt.links.new(in_carpet.outputs["Value"], mix_floor.inputs["Factor"])
    nt.links.new(ramp_grey.outputs["Color"], mix_floor.inputs[6])
    nt.links.new(checker.outputs["Color"], mix_floor.inputs[7])

    # Multiply by subtle marble veining
    mix_vein = nt.nodes.new("ShaderNodeMix"); mix_vein.data_type = 'RGBA'; mix_vein.blend_type = 'MULTIPLY'
    mix_vein.inputs["Factor"].default_value = 0.25
    nt.links.new(mix_floor.outputs[2], mix_vein.inputs[6])
    nt.links.new(ramp_grey.outputs["Color"], mix_vein.inputs[7])

    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.04
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(mix_vein.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_senator_clavus_mat(name, is_caesar=False, hair_tone=0.35):
    """
    Matches Imperial 00:15.0 & 07:15.0:
    - If is_caesar=True: Deep crimson toga over white tunic, warm skin head/arms/calves, golden laurel crown
    - If is_caesar=False: Crisp off-white/cream Roman toga & tunic WITH a distinct purple/burgundy diagonal senatorial sash (latus clavus) over the shoulder!
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.52

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(texcoord.outputs["Object"], sep.inputs["Vector"])

    ramp_ao = nt.nodes.new("ShaderNodeValToRGB")
    ramp_ao.color_ramp.elements[0].position = 0.43
    ramp_ao.color_ramp.elements[0].color = (0.28, 0.22, 0.20, 1.0)
    ramp_ao.color_ramp.elements[1].position = 0.56
    ramp_ao.color_ramp.elements[1].color = (1.08, 1.05, 1.02, 1.0)
    nt.links.new(geom.outputs["Pointiness"], ramp_ao.inputs["Fac"])

    skin = (0.74, 0.54, 0.42, 1.0)
    sandal = (0.16, 0.09, 0.05, 1.0)
    hair = (hair_tone, hair_tone*0.95, hair_tone*0.90, 1.0)
    white_toga = (0.82, 0.79, 0.72, 1.0)
    crimson_toga = (0.55, 0.025, 0.032, 1.0)
    purple_clavus = (0.28, 0.06, 0.22, 1.0)  # Tyrian purple senatorial stripe!

    div_z = nt.nodes.new("ShaderNodeMath"); div_z.operation = 'DIVIDE'; div_z.inputs[1].default_value = 1.82
    nt.links.new(sep.outputs["Z"], div_z.inputs[0])

    main_garment = crimson_toga if is_caesar else white_toga
    hem_garment = white_toga

    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'EASE'
    e0 = ramp.color_ramp.elements[0]; e0.position = 0.07; e0.color = sandal
    e1 = ramp.color_ramp.elements[1]; e1.position = 0.09; e1.color = skin
    for p, c in [(0.16, skin), (0.18, hem_garment), (0.23, hem_garment), (0.25, main_garment), (0.83, main_garment), (0.845, skin), (0.93, skin), (0.95, hair)]:
        el = ramp.color_ramp.elements.new(p); el.color = c
    nt.links.new(div_z.outputs["Value"], ramp.inputs["Fac"])

    base_col = ramp.outputs["Color"]

    # If Senator (not Caesar), add the Tyrian purple diagonal shoulder stripe (latus clavus: 0.06 < X + 0.15*Z < 0.16 and 0.65 < Z < 1.48)
    if not is_caesar:
        mul_z = nt.nodes.new("ShaderNodeMath"); mul_z.operation = 'MULTIPLY'; mul_z.inputs[1].default_value = 0.12
        nt.links.new(sep.outputs["Z"], mul_z.inputs[0])
        add_xz = nt.nodes.new("ShaderNodeMath"); add_xz.operation = 'ADD'
        nt.links.new(sep.outputs["X"], add_xz.inputs[0])
        nt.links.new(mul_z.outputs["Value"], add_xz.inputs[1])

        in_band = nt.nodes.new("ShaderNodeMath"); in_band.operation = 'COMPARE'
        in_band.inputs[1].default_value = 0.14  # center
        in_band.inputs[2].default_value = 0.055 # width
        nt.links.new(add_xz.outputs["Value"], in_band.inputs[0])

        in_z = nt.nodes.new("ShaderNodeMath"); in_z.operation = 'COMPARE'
        in_z.inputs[1].default_value = 1.08
        in_z.inputs[2].default_value = 0.38
        nt.links.new(sep.outputs["Z"], in_z.inputs[0])

        clav_mask = nt.nodes.new("ShaderNodeMath"); clav_mask.operation = 'MULTIPLY'
        nt.links.new(in_band.outputs["Value"], clav_mask.inputs[0])
        nt.links.new(in_z.outputs["Value"], clav_mask.inputs[1])

        mix_clav = nt.nodes.new("ShaderNodeMix"); mix_clav.data_type = 'RGBA'
        nt.links.new(clav_mask.outputs["Value"], mix_clav.inputs["Factor"])
        nt.links.new(base_col, mix_clav.inputs[6])
        mix_clav.inputs[7].default_value = purple_clavus
        base_col = mix_clav.outputs[2]

    # Bare right arm (X < -0.16 and Z > 1.15)
    lt_x = nt.nodes.new("ShaderNodeMath"); lt_x.operation = 'LESS_THAN'; lt_x.inputs[1].default_value = -0.16
    nt.links.new(sep.outputs["X"], lt_x.inputs[0])
    gt_z = nt.nodes.new("ShaderNodeMath"); gt_z.operation = 'GREATER_THAN'; gt_z.inputs[1].default_value = 1.15
    nt.links.new(sep.outputs["Z"], gt_z.inputs[0])
    arm_m = nt.nodes.new("ShaderNodeMath"); arm_m.operation = 'MULTIPLY'
    nt.links.new(lt_x.outputs["Value"], arm_m.inputs[0])
    nt.links.new(gt_z.outputs["Value"], arm_m.inputs[1])

    mix_arm = nt.nodes.new("ShaderNodeMix"); mix_arm.data_type = 'RGBA'
    nt.links.new(arm_m.outputs["Value"], mix_arm.inputs["Factor"])
    nt.links.new(base_col, mix_arm.inputs[6])
    mix_arm.inputs[7].default_value = skin

    mix_ao = nt.nodes.new("ShaderNodeMix")
    mix_ao.data_type = 'RGBA'; mix_ao.blend_type = 'MULTIPLY'
    mix_ao.inputs["Factor"].default_value = 0.90
    nt.links.new(mix_arm.outputs[2], mix_ao.inputs[6])
    nt.links.new(ramp_ao.outputs["Color"], mix_ao.inputs[7])

    nt.links.new(mix_ao.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_seated_male_senator_mesh(orator_proto):
    """
    Creates a realistic SEATED MALE ROMAN SENATOR from clean_caesar_orator.blend
    by bending the hips (+85 deg) and knees (-85 deg) in vertex space so he sits naturally
    on an open bench with his knees forward, lower legs vertical, and male Roman head upright!
    """
    seat_obj = orator_proto.copy()
    seat_obj.data = orator_proto.data.copy()
    bpy.context.scene.collection.objects.link(seat_obj)
    # In clean_caesar_orator: feet at Z=0, knees at Z=0.48, hips at Z=0.92, head at Z=1.82, facing -Y!
    # Also lower his raised right arm (X < -0.15, Z > 1.10) into his lap so seated senators aren't all saluting!
    for v in seat_obj.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        # 1. Relax raised right arm (X < -0.14, Z > 1.05) down toward lap
        if x < -0.14 and z > 1.05:
            dx = -0.14 - x
            z = z - dx * 0.85
            y = y - dx * 0.35
            x = -0.14 - dx * 0.45
        # 2. Bend body into seated posture:
        # Upper body (z >= 0.88): lowers by 0.38m and shifts slightly back (+Y by 0.12m)
        # Thighs (0.46 <= z < 0.88): transitions from hip (y=+0.12, z=0.50) forward to knee (y=-0.32, z=0.46)
        # Lower legs (z < 0.46): hangs vertically down under knee (y shifted by -0.32, z in 0..0.46)
        if z >= 0.88:
            new_z = z - 0.38
            new_y = y + 0.10
        elif z >= 0.46:
            t = (0.88 - z) / (0.88 - 0.46)  # 0 at hip, 1 at knee
            new_z = 0.50 - 0.04 * t + y * 0.15
            new_y = 0.10 - 0.40 * t + y * 0.35
        else:
            new_z = z
            new_y = y - 0.30
        v.co = Vector((x, new_y, new_z))
    seat_obj.data.update()
    bpy.ops.object.select_all(action='DESELECT')
    seat_obj.select_set(True)
    bpy.context.view_layer.objects.active = seat_obj
    bpy.ops.object.shade_smooth()
    return seat_obj

def build_curia_mcp_v2():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 14
    scn.cycles.max_bounces = 1; scn.cycles.diffuse_bounces = 0; scn.cycles.glossy_bounces = 1
    scn.cycles.use_denoising = True; scn.cycles.denoiser = 'OPENIMAGEDENOISE'; scn.cycles.denoising_prefilter = 'FAST'
    scn.render.resolution_x = 1280; scn.render.resolution_y = 720
    scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
    scn.view_settings.exposure = -0.05

    world = bpy.data.worlds.new("W"); scn.world = world; world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs[0].default_value = (0.014, 0.015, 0.018, 1.0)
    world.node_tree.nodes.get("Background").inputs[1].default_value = 0.35

    mat_floor = make_curia_carpet_and_border_floor()
    mat_trav = make_pbr_stone_or_wood("TravWall", (0.42, 0.39, 0.35), rough=0.42, noise_scale=6.0)
    mat_step = make_pbr_stone_or_wood("StepMarble", (0.54, 0.51, 0.46), rough=0.35, noise_scale=8.0)
    mat_wood = make_pbr_stone_or_wood("DarkWalnut", (0.12, 0.06, 0.03), rough=0.32, noise_scale=16.0)
    mat_gold = make_pbr_stone_or_wood("RoyalGold", (0.82, 0.62, 0.20), rough=0.20, metal=0.92, noise_scale=12.0)
    mat_crimson_velvet = make_pbr_stone_or_wood("CrimsonVelvet", (0.48, 0.025, 0.03), rough=0.65, noise_scale=24.0)

    # 1. Floor (Central axis-aligned checkered carpet + surrounding grey marble slabs!)
    bpy.ops.mesh.primitive_plane_add(size=22.0, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.data.materials.append(mat_floor)

    # 2. Stepped Marble Tiers + OPEN-FRONT Dark Walnut Benches (with backrest & carved side armrests, NO pew wall!)
    for side in (-1, 1):
        for tier in range(3):
            x_c = side * (2.60 + tier * 0.98)
            z_top = 0.16 + tier * 0.28
            # Marble step platform
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c, 0.0, z_top * 0.5))
            st = bpy.context.active_object; st.scale = (0.98, 8.2, z_top); st.data.materials.append(mat_step)

            # Open-front dark walnut bench (2 sections along Y: -1.8m and +2.0m with an aisle gap at Y=0.1m just like Imperial 00:15.0!)
            for y_sec, sec_len in [(-1.85, 3.3), (2.05, 3.3)]:
                # Seat plank (at z_top + 0.42m)
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.05, y_sec, z_top + 0.42))
                seat = bpy.context.active_object; seat.scale = (0.46, sec_len, 0.06); seat.data.materials.append(mat_wood)
                # Backrest plank
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.26, y_sec, z_top + 0.68))
                back = bpy.context.active_object; back.scale = (0.06, sec_len, 0.52); back.data.materials.append(mat_wood)
                # Carved wooden end-panels / armrests at both ends of each bench section
                for end_s in (-1, 1):
                    y_end = y_sec + end_s * (sec_len * 0.5)
                    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_c + side*0.06, y_end, z_top + 0.38))
                    arm = bpy.context.active_object; arm.scale = (0.50, 0.08, 0.76); arm.data.materials.append(mat_wood)

    # 3. Rear Wall (Y = +5.6m) with Grand Double Wooden Door + Molded Wall Panels + 2 Massive Columns (matching 00:15.0 top!)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.8, 4.0))
    rw = bpy.context.active_object; rw.scale = (14.0, 0.5, 8.0); rw.data.materials.append(mat_trav)
    # Double wooden door in center (X=0, Y=5.52)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.52, 2.1))
    dr = bpy.context.active_object; dr.scale = (2.3, 0.12, 4.2); dr.data.materials.append(mat_wood)
    # Stone door frame
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 5.55, 2.2))
    df = bpy.context.active_object; df.scale = (2.65, 0.18, 4.5); df.data.materials.append(mat_step)
    # Recessed wainscot wall molding panels on left and right of door
    for sx in (-3.2, 3.2):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, 5.52, 1.8))
        ml = bpy.context.active_object; ml.scale = (2.8, 0.10, 1.4); ml.data.materials.append(mat_step)

    # Load BlenderKit Corinthian Column & place at the 4 corners of the hall (visible in 00:15.0 & 07:15.0!)
    col_proto = load_mesh_from_blend("bk_column_corinthian.blend")
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
            inst = col_proto.copy()
            inst.hide_render = False
            inst.location = (cx_p, cy_p, cz_p)
            scn.collection.objects.link(inst)

    # 4. Raised Marble Tribunal Dais at Front-Left/South (for Shot B 07:15.0 where Caesar sits on his golden throne!)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.4, -4.5, 0.28))
    dais = bpy.context.active_object; dais.scale = (3.4, 2.6, 0.56); dais.data.materials.append(mat_step)
    # Golden Throne on the dais (facing +X/+Y across the Senate floor just like 07:15.0!)
    throne_x, throne_y, throne_z = -1.65, -4.35, 0.56
    # Throne seat, high arched gold back, armrests, and crimson cushion
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(throne_x, throne_y, throne_z + 0.26))
    ts = bpy.context.active_object; ts.scale = (0.62, 0.62, 0.52); ts.rotation_euler = (0,0,math.radians(-55)); ts.data.materials.append(mat_gold)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(throne_x - 0.22, throne_y - 0.16, throne_z + 0.78))
    tb = bpy.context.active_object; tb.scale = (0.10, 0.62, 0.95); tb.rotation_euler = (0,0,math.radians(-55)); tb.data.materials.append(mat_gold)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(throne_x, throne_y, throne_z + 0.54))
    tc = bpy.context.active_object; tc.scale = (0.58, 0.58, 0.08); tc.rotation_euler = (0,0,math.radians(-55)); tc.data.materials.append(mat_crimson_velvet)

    # 5. Characters:
    mat_caesar = make_senator_clavus_mat("CaesarMat", is_caesar=True, hair_tone=0.18)
    mat_sen_1 = make_senator_clavus_mat("SenMat1", is_caesar=False, hair_tone=0.55)
    mat_sen_2 = make_senator_clavus_mat("SenMat2", is_caesar=False, hair_tone=0.28)

    orator_proto = load_mesh_from_blend("clean_caesar_orator.blend")
    mod_d = orator_proto.modifiers.new("Dec", "DECIMATE"); mod_d.ratio = 0.35
    bpy.context.view_layer.objects.active = orator_proto
    bpy.ops.object.modifier_apply(modifier=mod_d.name)

    # Create the Male Seated Senator Prototype from orator_proto!
    seated_male_proto = create_seated_male_senator_mesh(orator_proto)
    seated_male_proto.data.materials.clear(); seated_male_proto.data.materials.append(mat_sen_1)
    seated_male_proto.hide_render = True; seated_male_proto.location = (0, 0, -30)

    # Also create a Standing Senator Prototype with relaxed right arm!
    stand_male_proto = orator_proto.copy()
    stand_male_proto.data = orator_proto.data.copy()
    scn.collection.objects.link(stand_male_proto)
    for v in stand_male_proto.data.vertices:
        if v.co.x < -0.14 and v.co.z > 1.05:
            dx = -0.14 - v.co.x
            v.co.z -= dx * 0.75
            v.co.x = -0.14 - dx * 0.50
    stand_male_proto.data.update()
    stand_male_proto.data.materials.clear(); stand_male_proto.data.materials.append(mat_sen_1)
    stand_male_proto.hide_render = True; stand_male_proto.location = (0, 0, -30)

    # Caesar Standing in Center Aisle (for Shot A 00:15.0)
    caesar_walk = stand_male_proto.copy()
    caesar_walk.data = stand_male_proto.data.copy()
    caesar_walk.data.materials.clear(); caesar_walk.data.materials.append(mat_caesar)
    caesar_walk.hide_render = False
    caesar_walk.location = (0.05, 1.35, 0.0)
    caesar_walk.rotation_euler = (0, 0, math.radians(-15))
    scn.collection.objects.link(caesar_walk)

    # Caesar Seated on Golden Throne (for Shot B 07:15.0)
    caesar_throne = seated_male_proto.copy()
    caesar_throne.data = seated_male_proto.data.copy()
    caesar_throne.data.materials.clear(); caesar_throne.data.materials.append(mat_caesar)
    caesar_throne.hide_render = True
    caesar_throne.location = (throne_x + 0.05, throne_y + 0.05, throne_z + 0.05)
    caesar_throne.rotation_euler = (0, 0, math.radians(-145))
    scn.collection.objects.link(caesar_throne)

    # Populate Seated Male Senators on the Open Benches facing INWARD toward the center aisle!
    # Note: seated_male_proto faces -Y at rotZ=0!
    # So on Left benches (X < 0, looking toward +X), rotZ = +90 deg? Wait:
    # Let's check Blender right-hand rule around +Z:
    # At rotZ = 0, forward is (0, -1, 0) (-Y).
    # Rotating by +90 deg (+pi/2) around Z maps (x, y) -> (-y, x), so (0, -1) -> (+1, 0) (+X, facing right toward center aisle!).
    # Wait: why did Penelopes face the wall in Iter 1? Because in build_clean_statues.py we had rotated Penelope by -90 deg already!
    # Whereas seated_male_proto comes from clean_caesar_orator.blend which we KNOW faces -Y (towards camera at rotZ=0)!
    # Therefore, for seated_male_proto:
    # - Left benches (X < 0, need to face +X): rotZ = +90 deg!
    # - Right benches (X > 0, need to face -X): rotZ = -90 deg!
    for side in (-1, 1):
        base_rz = 90.0 if side == -1 else -90.0
        for tier in range(3):
            x_pos = side * (2.60 + tier * 0.98)
            z_pos = 0.16 + tier * 0.28
            for y_pos in [-3.1, -2.3, -1.5, -0.7, 0.8, 1.6, 2.4, 3.2]:
                inst = seated_male_proto.copy()
                inst.hide_render = False
                inst.location = (x_pos, y_pos, z_pos)
                jitter = ((int(y_pos*10) * 17 + tier * 31) % 16) - 8
                inst.rotation_euler = (0, 0, math.radians(base_rz + jitter))
                scn.collection.objects.link(inst)

    # Standing conversing senators in the aisles & back vestibule (matching 00:15.0 & 07:15.0!)
    standing_coords = [
        # Back vestibule pair
        (-1.25, 4.3, 0.0, 45), (-0.55, 4.5, 0.0, -35),
        # Left & right aisle standing senators (00:15.0)
        (-1.45, 0.5, 0.0, 75), (-1.35, -0.3, 0.0, 110),
        (1.30, -0.1, 0.0, -85),
        (1.85, 2.8, 0.0, -60), (2.45, 2.9, 0.0, -120),
        # Group 1 (Former Allies) & Group 2 (Pompeians) standing near the front-left tribunal for Shot B (07:15.0)
        (-3.1, -3.8, 0.56, -125), (-2.5, -3.5, 0.56, -140), (-2.1, -3.1, 0.56, -115),
        (-1.1, -2.8, 0.0, -145), (-0.4, -2.6, 0.0, 135), (1.35, -2.1, 0.0, -70),
    ]
    for sx, sy, sz, srz in standing_coords:
        st_i = stand_male_proto.copy()
        st_i.hide_render = False
        st_i.location = (sx, sy, sz)
        st_i.rotation_euler = (0, 0, math.radians(srz))
        scn.collection.objects.link(st_i)

    # 6. Warm Roman Chiaroscuro Lighting
    ld_key = bpy.data.lights.new("SunShaft", type='AREA')
    ld_key.energy = 320.0; ld_key.size = 3.8; ld_key.color = (1.0, 0.95, 0.88)
    lo_key = bpy.data.objects.new("SunShaft", ld_key); scn.collection.objects.link(lo_key)
    lo_key.location = (-3.5, -2.5, 6.5)
    lo_key.rotation_euler = (Vector((0.0, 1.0, 0.0)) - lo_key.location).to_track_quat('-Z', 'Y').to_euler()

    ld_fill = bpy.data.lights.new("AmbientFill", type='AREA')
    ld_fill.energy = 95.0; ld_fill.size = 5.0; ld_fill.color = (0.90, 0.93, 1.0)
    lo_fill = bpy.data.objects.new("AmbientFill", ld_fill); scn.collection.objects.link(lo_fill)
    lo_fill.location = (3.5, -4.5, 5.0)
    lo_fill.rotation_euler = (Vector((0.0, 0.5, 1.0)) - lo_fill.location).to_track_quat('-Z', 'Y').to_euler()

    cd = bpy.data.cameras.new("Cam"); cd.lens = 36.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co

    # Shot A (00:15.0: High-angle diagonal crane view looking toward Caesar & the rear entrance doors)
    co.location = (-0.65, -5.2, 4.1)
    co.rotation_euler = (Vector((-0.05, 1.2, 0.7)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = f"{OUT_DIR}/mcp_s1_v2_shotA.png"
    bpy.ops.render.render(write_still=True)

    # Shot B (07:15.0: Over Caesar's shoulder on the Golden Throne looking across at the 3 Faction Groups)
    caesar_walk.hide_render = True
    caesar_throne.hide_render = False
    co.location = (-2.95, -5.85, 2.55)
    co.rotation_euler = (Vector((0.65, -0.4, 0.85)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = f"{OUT_DIR}/mcp_s1_v2_shotB.png"
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    build_curia_mcp_v2()
