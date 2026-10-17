import sys; sys.path.append("/var/tmp/blender_mcp")
import bpy, os, math
from mathutils import Vector

ASSETS = "/var/tmp/blender_mcp/assets"
OUT_DIR = "/var/tmp/blender_mcp/renders"
os.makedirs(OUT_DIR, exist_ok=True)

def load_mesh_from_blend(blend_name):
    bpath = os.path.join(ASSETS, blend_name)
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

def make_diagonal_curia_floor_mat():
    mat = bpy.data.materials.new("CuriaDiagonalFloor")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.22
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.55

    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    # Rotate 45 degrees around Z so squares become diagonal diamonds/squares aligned like Imperial 00:15.0!
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(45.0))
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    nt.links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])

    checker = nt.nodes.new("ShaderNodeTexChecker")
    # Scale=3.2 on Object coords of a 16m plane gives ~0.48m tiles exactly like Imperial!
    checker.inputs["Scale"].default_value = 3.2
    # Warm antique Giallo Antico gold-ochre & dark Roman slate
    checker.inputs["Color1"].default_value = (0.58, 0.47, 0.28, 1.0)
    checker.inputs["Color2"].default_value = (0.11, 0.13, 0.15, 1.0)
    nt.links.new(mapping.outputs["Vector"], checker.inputs["Vector"])

    # Subtle marble veining noise mixed into tiles
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 6.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    ramp_n = nt.nodes.new("ShaderNodeValToRGB")
    ramp_n.color_ramp.elements[0].color = (0.85, 0.83, 0.80, 1.0)
    ramp_n.color_ramp.elements[1].color = (1.12, 1.10, 1.06, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp_n.inputs["Fac"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs["Factor"].default_value = 0.65
    nt.links.new(checker.outputs["Color"], mix.inputs[6])
    nt.links.new(ramp_n.outputs["Color"], mix.inputs[7])

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_pbr_stone_or_wood(name, rgb, rough=0.45, metal=0.0, noise_scale=12.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 5.0
    nt.links.new(texcoord.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (rgb[0]*0.82, rgb[1]*0.82, rgb[2]*0.82, 1.0)
    ramp.color_ramp.elements[1].color = (min(1.0, rgb[0]*1.15), min(1.0, rgb[1]*1.15), min(1.0, rgb[2]*1.15), 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.06
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_roman_character_mat(name, mesh_type="ORATOR", toga_rgb=(0.52, 0.025, 0.032), tunic_rgb=(0.82, 0.78, 0.70)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.55

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(texcoord.outputs["Object"], sep.inputs["Vector"])

    ramp_ao = nt.nodes.new("ShaderNodeValToRGB")
    ramp_ao.color_ramp.elements[0].position = 0.43
    ramp_ao.color_ramp.elements[0].color = (0.25, 0.19, 0.17, 1.0)
    ramp_ao.color_ramp.elements[1].position = 0.56
    ramp_ao.color_ramp.elements[1].color = (1.08, 1.05, 1.02, 1.0)
    nt.links.new(geom.outputs["Pointiness"], ramp_ao.inputs["Fac"])

    skin = (0.72, 0.52, 0.40, 1.0)
    sandal = (0.15, 0.08, 0.04, 1.0)
    hair_dark = (0.14, 0.11, 0.09, 1.0)
    hair_grey = (0.50, 0.47, 0.44, 1.0)
    tunic = (*tunic_rgb, 1.0)
    toga = (*toga_rgb, 1.0)
    bench_stone = (0.18, 0.12, 0.08, 1.0)

    if mesh_type == "ORATOR":
        div_z = nt.nodes.new("ShaderNodeMath"); div_z.operation = 'DIVIDE'; div_z.inputs[1].default_value = 1.82
        nt.links.new(sep.outputs["Z"], div_z.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'EASE'
        e0 = ramp.color_ramp.elements[0]; e0.position = 0.08; e0.color = sandal
        e1 = ramp.color_ramp.elements[1]; e1.position = 0.10; e1.color = skin
        # Notice neck starts at 0.835 (1.52m) so shoulders are 100% covered by toga!
        for p, c in [(0.15, skin), (0.165, tunic), (0.21, tunic), (0.23, toga), (0.825, toga), (0.84, skin), (0.93, skin), (0.95, hair_dark)]:
            el = ramp.color_ramp.elements.new(p); el.color = c
        nt.links.new(div_z.outputs["Value"], ramp.inputs["Fac"])

        lt_x = nt.nodes.new("ShaderNodeMath"); lt_x.operation = 'LESS_THAN'; lt_x.inputs[1].default_value = -0.16
        nt.links.new(sep.outputs["X"], lt_x.inputs[0])
        gt_z = nt.nodes.new("ShaderNodeMath"); gt_z.operation = 'GREATER_THAN'; gt_z.inputs[1].default_value = 1.18
        nt.links.new(sep.outputs["Z"], gt_z.inputs[0])
        arm_m = nt.nodes.new("ShaderNodeMath"); arm_m.operation = 'MULTIPLY'
        nt.links.new(lt_x.outputs["Value"], arm_m.inputs[0])
        nt.links.new(gt_z.outputs["Value"], arm_m.inputs[1])

        mix_base = nt.nodes.new("ShaderNodeMix"); mix_base.data_type = 'RGBA'
        nt.links.new(arm_m.outputs["Value"], mix_base.inputs["Factor"])
        nt.links.new(ramp.outputs["Color"], mix_base.inputs[6])
        mix_base.inputs[7].default_value = skin
        base_out = mix_base.outputs[2]

    elif mesh_type == "DRAPED_STANDING":
        div_z = nt.nodes.new("ShaderNodeMath"); div_z.operation = 'DIVIDE'; div_z.inputs[1].default_value = 1.78
        nt.links.new(sep.outputs["Z"], div_z.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'EASE'
        e0 = ramp.color_ramp.elements[0]; e0.position = 0.02; e0.color = sandal
        e1 = ramp.color_ramp.elements[1]; e1.position = 0.04; e1.color = tunic
        for p, c in [(0.22, tunic), (0.25, toga), (0.80, toga), (0.82, skin), (0.91, skin), (0.93, hair_grey)]:
            el = ramp.color_ramp.elements.new(p); el.color = c
        nt.links.new(div_z.outputs["Value"], ramp.inputs["Fac"])
        base_out = ramp.outputs["Color"]

    else:  # SEATED_SENATOR
        div_z = nt.nodes.new("ShaderNodeMath"); div_z.operation = 'DIVIDE'; div_z.inputs[1].default_value = 1.34
        nt.links.new(sep.outputs["Z"], div_z.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = 'EASE'
        e0 = ramp.color_ramp.elements[0]; e0.position = 0.30; e0.color = bench_stone
        e1 = ramp.color_ramp.elements[1]; e1.position = 0.33; e1.color = tunic
        for p, c in [(0.45, tunic), (0.48, toga), (0.83, toga), (0.85, skin), (0.93, skin), (0.95, hair_grey)]:
            el = ramp.color_ramp.elements.new(p); el.color = c
        nt.links.new(div_z.outputs["Value"], ramp.inputs["Fac"])
        base_out = ramp.outputs["Color"]

    mix_ao = nt.nodes.new("ShaderNodeMix")
    mix_ao.data_type = 'RGBA'; mix_ao.blend_type = 'MULTIPLY'
    mix_ao.inputs["Factor"].default_value = 0.90
    nt.links.new(base_out, mix_ao.inputs[6])
    nt.links.new(ramp_ao.outputs["Color"], mix_ao.inputs[7])
    nt.links.new(mix_ao.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def build_curia_mcp_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = 14
    scn.cycles.max_bounces = 1; scn.cycles.diffuse_bounces = 0; scn.cycles.glossy_bounces = 1
    scn.cycles.use_denoising = True; scn.cycles.denoiser = 'OPENIMAGEDENOISE'; scn.cycles.denoising_prefilter = 'FAST'
    scn.render.resolution_x = 1280; scn.render.resolution_y = 720
    scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
    scn.view_settings.exposure = -0.15

    world = bpy.data.worlds.new("W"); scn.world = world; world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs[0].default_value = (0.010, 0.011, 0.014, 1.0)
    world.node_tree.nodes.get("Background").inputs[1].default_value = 0.25

    mat_floor = make_diagonal_curia_floor_mat()
    mat_trav = make_pbr_stone_or_wood("TravertineWall", (0.36, 0.33, 0.28), rough=0.42, noise_scale=8.0)
    mat_step = make_pbr_stone_or_wood("StepStone", (0.44, 0.40, 0.34), rough=0.38, noise_scale=10.0)
    mat_wood = make_pbr_stone_or_wood("WalnutBench", (0.14, 0.07, 0.035), rough=0.34, noise_scale=18.0)
    mat_gold = make_pbr_stone_or_wood("GoldLeaf", (0.76, 0.56, 0.18), rough=0.22, metal=0.92, noise_scale=15.0)
    mat_scroll = make_pbr_stone_or_wood("ScrollPaper", (0.82, 0.77, 0.66), rough=0.65, noise_scale=20.0)

    # 1. Diagonal Checkered Floor (16m x 20m)
    bpy.ops.mesh.primitive_plane_add(size=18.0, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.scale = (0.9, 1.15, 1.0); fl.data.materials.append(mat_floor)

    # 2. Stepped Senate Subsellia (Left & Right, 3 tiers with stone steps + dark walnut seats + front desk balustrade!)
    for side in (-1, 1):
        for tier in range(3):
            x_center = side * (2.65 + tier * 1.05)
            z_step = 0.22 + tier * 0.34
            # Stone tier platform
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_center, 0.5, z_step * 0.5))
            st = bpy.context.active_object; st.scale = (1.02, 12.5, z_step); st.data.materials.append(mat_step)
            # Dark walnut bench top
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x_center + side*0.10, 0.5, z_step + 0.06))
            bn = bpy.context.active_object; bn.scale = (0.55, 12.2, 0.12); bn.data.materials.append(mat_wood)
            # Front wooden desk balustrade facing center aisle
            desk_x = x_center - side * 0.42
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(desk_x, 0.5, z_step + 0.32))
            dk = bpy.context.active_object; dk.scale = (0.14, 12.0, 0.64); dk.data.materials.append(mat_wood)
            # Top ledge of desk
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(desk_x, 0.5, z_step + 0.65))
            lg = bpy.context.active_object; lg.scale = (0.24, 12.1, 0.05); lg.data.materials.append(mat_wood)

    # 3. Side & Rear Travertine Walls + Real BlenderKit Corinthian Columns!
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side * 6.2, 0.0, 4.2))
        wl = bpy.context.active_object; wl.scale = (0.6, 17.0, 8.4); wl.data.materials.append(mat_trav)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 7.8, 4.2))
    rw = bpy.context.active_object; rw.scale = (13.0, 0.6, 8.4); rw.data.materials.append(mat_trav)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -6.8, 4.2))
    fw = bpy.context.active_object; fw.scale = (13.0, 0.6, 8.4); fw.data.materials.append(mat_trav)

    # Load BlenderKit Corinthian Column & instance along walls
    col_proto = load_mesh_from_blend("bk_column_corinthian.blend")
    if col_proto:
        verts = [v.co for v in col_proto.data.vertices]
        mz, xz = min(v.z for v in verts), max(v.z for v in verts)
        cx, cy = 0.5*(min(v.x for v in verts)+max(v.x for v in verts)), 0.5*(min(v.y for v in verts)+max(v.y for v in verts))
        sf = 5.6 / max(xz - mz, 1e-4)
        for v in col_proto.data.vertices:
            v.co = Vector(((v.co.x - cx)*sf, (v.co.y - cy)*sf, (v.co.z - mz)*sf))
        col_proto.data.update()
        col_proto.hide_render = True
        col_proto.location = (0, 0, -30)
        for side in (-1, 1):
            for y_c in (-4.8, -2.0, 0.8, 3.6, 6.2):
                inst = col_proto.copy()
                inst.hide_render = False
                inst.location = (side * 5.55, y_c, 0.90)
                scn.collection.objects.link(inst)

    # 4. Load Characters:
    # - Caesar in crimson Toga Picta walking down center aisle (0, -0.4, 0) AND Caesar on golden curule chair on left tribune!
    mat_caesar = make_roman_character_mat("CaesarCrimson", "ORATOR", (0.54, 0.025, 0.032), (0.84, 0.80, 0.72))
    mat_sen_cream = make_roman_character_mat("SenCream", "SEATED_SENATOR", (0.78, 0.74, 0.65), (0.48, 0.04, 0.05))
    mat_sen_cream_alt = make_roman_character_mat("SenCreamAlt", "SEATED_SENATOR", (0.72, 0.68, 0.59), (0.42, 0.05, 0.06))
    mat_sen_stand1 = make_roman_character_mat("SenStand1", "ORATOR", (0.78, 0.74, 0.65), (0.48, 0.04, 0.05))
    mat_sen_stand2 = make_roman_character_mat("SenStand2", "DRAPED_STANDING", (0.74, 0.70, 0.62), (0.45, 0.04, 0.05))

    caesar_obj = load_mesh_from_blend("clean_caesar_orator.blend")
    caesar_obj.data.materials.clear(); caesar_obj.data.materials.append(mat_caesar)
    caesar_obj.location = (0.0, 0.2, 0.0)
    caesar_obj.rotation_euler = (0, 0, math.radians(10))

    # Seated senator prototype (decimated to 10,000 faces for fast crowd instancing!)
    seat_proto = load_mesh_from_blend("clean_senator_seated.blend")
    mod_d = seat_proto.modifiers.new("FastCrowd", "DECIMATE")
    mod_d.ratio = 0.28
    bpy.context.view_layer.objects.active = seat_proto
    bpy.ops.object.modifier_apply(modifier=mod_d.name)
    seat_proto.data.materials.clear(); seat_proto.data.materials.append(mat_sen_cream)
    seat_proto.hide_render = True; seat_proto.location = (0, 0, -30)

    stand_proto = load_mesh_from_blend("clean_senator_draped.blend")
    mod_d2 = stand_proto.modifiers.new("FastStand", "DECIMATE")
    mod_d2.ratio = 0.30
    bpy.context.view_layer.objects.active = stand_proto
    bpy.ops.object.modifier_apply(modifier=mod_d2.name)
    stand_proto.data.materials.clear(); stand_proto.data.materials.append(mat_sen_stand2)
    stand_proto.hide_render = True; stand_proto.location = (0, 0, -30)

    # Populate 54 seated senators on the 3 tiers (Left & Right) facing the center aisle!
    # Note: clean_senator_seated.blend faces -Y at rotZ=0; so to face +X (from left wall X<0), rotZ = +90 deg!
    # To face -X (from right wall X>0), rotZ = -90 deg!
    for side in (-1, 1):
        base_rz = 90.0 if side == -1 else -90.0
        for tier in range(3):
            x_pos = side * (2.62 + tier * 1.05)
            z_pos = 0.14 + tier * 0.34
            for row_idx in range(9):
                y_pos = -4.6 + row_idx * 1.18 + (tier % 2) * 0.25
                inst = seat_proto.copy()
                inst.hide_render = False
                inst.location = (x_pos, y_pos, z_pos)
                jitter_yaw = ((row_idx * 37 + tier * 13) % 18) - 9
                inst.rotation_euler = (0, 0, math.radians(base_rz + jitter_yaw))
                scn.collection.objects.link(inst)

                # Add parchment scroll on the desk in front of every other senator!
                if (row_idx + tier) % 2 == 0:
                    bpy.ops.mesh.primitive_plane_add(size=0.22, location=(x_pos - side*0.42, y_pos, z_pos + 0.56))
                    sc = bpy.context.active_object; sc.scale = (0.7, 1.1, 1.0)
                    sc.rotation_euler = (0, 0, math.radians(jitter_yaw * 2))
                    sc.data.materials.append(mat_scroll)

    # Add 6 standing conversing senators in the aisles (just like Imperial 00:15.0 & 07:15.0!)
    standing_spots = [
        (-1.65, -1.8, 0.0, 65, caesar_obj),
        (-1.55, -0.9, 0.0, 115, stand_proto),
        (1.65, -2.2, 0.0, -75, stand_proto),
        (1.55, 1.4, 0.0, -110, caesar_obj),
        (-1.70, 2.6, 0.0, 80, stand_proto),
    ]
    for sx, sy, sz, srz, proto in standing_spots:
        st_i = proto.copy()
        st_i.data = proto.data.copy()
        st_i.data.materials.clear()
        st_i.data.materials.append(mat_sen_stand1 if proto == caesar_obj else mat_sen_stand2)
        st_i.hide_render = False
        st_i.location = (sx, sy, sz)
        st_i.rotation_euler = (0, 0, math.radians(srz))
        scn.collection.objects.link(st_i)

    # 5. Chiaroscuro Clerestory Lighting (matching Imperial 00:15.0 & 07:15.0!)
    # Main warm sunlight shaft from upper-left
    ld_key = bpy.data.lights.new("SunShaft", type='AREA')
    ld_key.energy = 280.0; ld_key.size = 3.2; ld_key.color = (1.0, 0.94, 0.84)
    lo_key = bpy.data.objects.new("SunShaft", ld_key); scn.collection.objects.link(lo_key)
    lo_key.location = (-3.8, -3.5, 6.2)
    lo_key.rotation_euler = (Vector((0.0, 0.5, 0.0)) - lo_key.location).to_track_quat('-Z', 'Y').to_euler()

    # Soft cool fill from front-right
    ld_fill = bpy.data.lights.new("Fill", type='AREA')
    ld_fill.energy = 65.0; ld_fill.size = 4.0; ld_fill.color = (0.85, 0.90, 1.0)
    lo_fill = bpy.data.objects.new("Fill", ld_fill); scn.collection.objects.link(lo_fill)
    lo_fill.location = (3.5, -5.0, 4.5)
    lo_fill.rotation_euler = (Vector((0.0, 0.0, 1.0)) - lo_fill.location).to_track_quat('-Z', 'Y').to_euler()

    # Render Shot A (00:15.0 High-Angle Crane View of Caesar in the Curia)
    cd = bpy.data.cameras.new("Cam"); cd.lens = 35.0
    co = bpy.data.objects.new("Cam", cd); scn.collection.objects.link(co); scn.camera = co
    co.location = (-0.4, -6.4, 4.3)
    co.rotation_euler = (Vector((0.0, 0.4, 0.85)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = f"{OUT_DIR}/mcp_s1_shotA.png"
    bpy.ops.render.render(write_still=True)

    # Render Shot B (07:15.0 Diagonal Senate Faction Brackets View)
    co.location = (2.6, -5.8, 3.6)
    co.rotation_euler = (Vector((-1.2, 0.6, 1.1)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = f"{OUT_DIR}/mcp_s1_shotB.png"
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    build_curia_mcp_scene()
