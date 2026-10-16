"""Render the assembled engine. Run under `blender --background`.

    blender -b build/f110.blend -P engine/render.py -- <mode> [samples]

Modes: hero, cutaway, exploded, front, turntable, all
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "renders")

X_MID = 1.9        # engine centre, metres
SPAN = 4.63


# --------------------------------------------------------------------------

def setup_world(strength=0.35):
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    tex = nt.nodes.new("ShaderNodeTexCoord")
    mapn = nt.nodes.new("ShaderNodeMapping")
    mapn.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    ramp.color_ramp.elements[0].color = (0.012, 0.013, 0.016, 1)
    ramp.color_ramp.elements[1].color = (0.10, 0.11, 0.13, 1)
    nt.links.new(tex.outputs["Generated"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Strength"].default_value = strength


def area_light(name, loc, rot, energy, size):
    d = bpy.data.lights.new(name, type="AREA")
    d.energy = energy
    d.size = size
    d.shape = "RECTANGLE"
    d.size_y = size * 0.55
    o = bpy.data.objects.new(name, d)
    o.location = loc
    o.rotation_euler = rot
    bpy.context.scene.collection.objects.link(o)
    return o


def setup_lights():
    for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o, do_unlink=True)
    # key: high front-left, raking down the length of the engine
    area_light("key", (X_MID - 3.0, -8.5, 6.5),
               (math.radians(50), 0, math.radians(-26)), 2900, 9.0)
    # fill: low right, soft, keeps the underside from going black
    area_light("fill", (X_MID + 2.0, 7.5, -2.4),
               (math.radians(-62), 0, math.radians(152)), 1100, 11.0)
    # rim: behind and above, separates the nozzle from the background
    area_light("rim", (X_MID + 8.0, 4.0, 4.2),
               (math.radians(64), 0, math.radians(116)), 2600, 5.0)
    # nose kicker: picks out the centre-body and fan face
    area_light("nose", (X_MID - 8.0, -2.6, 1.6),
               (math.radians(76), 0, math.radians(-70)), 1400, 4.0)


def setup_camera(loc, look_at, lens=85.0):
    cam = bpy.data.cameras.new("cam")
    cam.lens = lens
    obj = bpy.data.objects.new("cam", cam)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.scene.camera = obj

    aim(obj, look_at)
    return obj


def aim(obj, look_at):
    """Point an object's -Z axis at a world-space target."""
    d = Vector(look_at) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def setup_render(samples=128, res=(1920, 1080)):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = samples
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 8
    s.cycles.caustics_reflective = False
    s.render.resolution_x, s.render.resolution_y = res
    s.render.film_transparent = False
    s.view_settings.view_transform = "AgX"
    s.view_settings.exposure = -0.55
    s.view_settings.look = "AgX - Medium High Contrast"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        s.cycles.device = "GPU"
    except Exception as exc:
        print("  (GPU unavailable, using CPU:", exc, ")")


def engine_objects():
    return [o for o in bpy.data.objects if o.type == "MESH"]


def shoot(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("  ->", path)


# --------------------------------------------------------------------------

def mode_hero(samples):
    setup_render(samples)
    setup_world()
    setup_lights()
    # three-quarter front: reads the fan face and the full length at once,
    # which a pure side view does not -- from the side this engine is a tube.
    area_light("inlet", (X_MID - 9.5, -3.4, 1.4),
               (math.radians(84), 0, math.radians(-64)), 1700, 3.2)
    setup_camera((X_MID - 10.6, -9.6, 3.5), (X_MID - 0.35, 0, -0.05), lens=76)
    shoot("01_hero")


def mode_front(samples):
    setup_render(samples)
    setup_world(0.45)
    setup_lights()
    setup_camera((X_MID - 11.5, -4.6, 2.2), (X_MID - 0.9, 0, 0), lens=105)
    shoot("02_front_quarter")


# Only the static outer shell is sectioned. Cutting everything leaves the far
# half of the casings occluding the core, which is why a plain half-section of a
# turbine engine reads as a blank wall -- real cutaway displays peel the casing
# away and leave the rotor whole.
CUT_PATTERNS = ("casing_", "flange_", "inlet_case", "inlet_lip",
                "bypass_inner_wall", "bypass_struts", "augmentor_liner",
                "combustor_liner_outer", "nozzle_ext_flaps", "nozzle_seals",
                "nozzle_flaps_convergent", "nozzle_flaps_divergent",
                "turbine_blade_outer_air_seals", "splitter", "mixer")


def should_cut(name):
    return any(p in name for p in CUT_PATTERNS)


def _add_section_cutter():
    """A box occupying y < 0, referenced by a boolean modifier on the shell
    objects only. Modifiers are left unapplied -- the cut exists at render time."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    cutter = bpy.context.active_object
    cutter.name = "__section_cutter"
    # half-extent 0.8 m, so this must sit at y = +0.8 to remove exactly y > 0
    cutter.scale = (SPAN * 1.8, 1.6, 2.0)
    cutter.location = (X_MID, -0.8, 0.0)
    cutter.hide_render = True
    n = 0
    for o in engine_objects():
        if o is cutter or not should_cut(o.name):
            continue
        n += 1
        m = o.modifiers.new("section", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.solver = "FAST"
        m.object = cutter
    print(f"  sectioned {n} shell objects")
    return cutter


def mode_cutaway(samples):
    setup_render(samples)
    setup_world(0.26)
    setup_lights()
    _add_section_cutter()
    # extra light down the open bore, or the core reads as a black slot
    # the cut plane faces the camera and is otherwise entirely self-shadowed
    area_light("bore", (X_MID - 0.4, -4.2, 1.2),
               (math.radians(74), 0, 0), 1500, 8.0)
    area_light("bore2", (X_MID + 1.2, -2.6, 3.4),
               (math.radians(38), 0, 0), 700, 6.0)
    setup_camera((X_MID - 3.4, -11.4, 4.2), (X_MID - 0.15, 0, 0.0), lens=80)
    shoot("03_cutaway")


def mode_exploded(samples):
    setup_render(samples)
    setup_world()
    setup_lights()
    order = ["01 Inlet and Fan", "02 HP Compressor", "03 Combustor",
             "04 Turbines", "05 Augmentor", "06 Nozzle",
             "07 Casings and Frames", "08 Shafts and Bearings",
             "09 Accessories"]
    for i, cname in enumerate(order):
        col = bpy.data.collections.get(cname)
        if not col:
            continue
        if cname == "07 Casings and Frames":
            dx, dz = 0.0, 2.05           # lift the casings clear
        elif cname == "08 Shafts and Bearings":
            dx, dz = 0.0, -1.55          # drop the spools below
        elif cname == "09 Accessories":
            dx, dz = 0.0, -2.45
        else:
            dx, dz = (i - 2) * 0.92, 0.0
        for o in col.objects:
            o.location.x += dx
            o.location.z += dz
    setup_camera((X_MID - 6.2, -20.5, 5.6), (X_MID + 0.45, 0, 0.22), lens=56)
    shoot("04_exploded")


def mode_turntable(samples, frames=36):
    setup_render(samples, res=(1280, 720))
    setup_world()
    setup_lights()
    cam = setup_camera((X_MID - 5.2, -12.4, 4.1), (X_MID - 0.1, 0, 0.0), lens=80)
    os.makedirs(os.path.join(OUT, "turntable"), exist_ok=True)
    r = math.hypot(5.2, 12.4)
    for i in range(frames):
        a = 2 * math.pi * i / frames
        cam.location = (X_MID - r * math.cos(a) * 0.49,
                        -r * math.sin(a + 1.2), 4.1)
        aim(cam, (X_MID - 0.1, 0.0, 0.05))
        bpy.context.scene.render.filepath = os.path.join(
            OUT, "turntable", f"tt_{i:03d}.png")
        bpy.ops.render.render(write_still=True)
    print("  ->", os.path.join(OUT, "turntable"))


MODES = {"hero": mode_hero, "front": mode_front, "cutaway": mode_cutaway,
         "exploded": mode_exploded, "turntable": mode_turntable}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["hero"]
    mode = argv[0] if argv else "hero"
    samples = int(argv[1]) if len(argv) > 1 else 128
    if mode == "all":
        for m in ("hero", "front", "cutaway", "exploded"):
            MODES[m](samples)
    else:
        MODES[mode](samples)
