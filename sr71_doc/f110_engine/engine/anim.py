"""Animated passes for the F110.

Modes:
  ignite     one-shot start-up: spools wind up, flow builds, afterburner lights
  steady     running engine that loops seamlessly
  turntable  not here -- see render.py
  cal <n>    render n low-res frames with a candidate background, for matching
             the background against a plate colour

Rendered frame by frame with transforms set explicitly rather than keyframed, so
a loop closes exactly and the ignition can ramp non-linearly.

The background is deliberately flat rather than the gradient render.py uses:
this footage is composited into a card with a known flat colour, and a gradient
would leave a visible step where the footage meets the plate.

    make ignite
    blender -b build/f110.blend -P engine/anim.py -- calibrate
"""

import bpy
import csv
import math
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import render as R  # noqa: E402  (world, lights, camera, Cycles setup)

OUT = os.path.join(ROOT, "renders", "anim")
RES = (960, 394)
SAMPLES = 20
STREAKS = 90
NOZZLE_X = 4.21

# Linear RGB. AgX plus the -0.55 exposure in render.py does not map these
# straight to the output, so the value is calibrated rather than calculated:
# see calibrate(). (0.013, 0.016, 0.040) lands on #080e1e against the plate's
# #070c1e -- two units out, which is not visible.
WORLD_RGB = (0.013, 0.016, 0.040)

# Core duct radius, from the blade rows and inner casings.
PROFILE = [(-1.5, 0.56), (0.10, 0.59), (0.50, 0.52), (0.86, 0.44),
           (1.60, 0.35), (2.05, 0.31), (2.60, 0.32), (3.60, 0.36), (5.20, 0.34)]

# Outer silhouette, from casing_inlet / casing_fan / casing_bypass /
# casing_augmentor in parts.csv. Flow that runs outside this stays visible
# along the whole engine instead of disappearing behind the casing.
OUTER = [(-1.5, 0.615), (-0.42, 0.614), (0.58, 0.618), (2.52, 0.597),
         (3.64, 0.490), (4.21, 0.440), (5.20, 0.420)]

X_FRONT = -1.5
X_BACK = 5.2

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["ignite"]
MODE = ARGV[0]
IGNITE = MODE != "steady"
N_FRAMES = 60 if IGNITE else 48
# Held to a fraction of the fan's blade pitch per encoded frame; a half turn at
# this frame count strobes.
LP_TURN = 150.0 if IGNITE else 135.0
HP_TURN = -LP_TURN


def interp(table, x):
    if x <= table[0][0]:
        return table[0][1]
    for (x0, r0), (x1, r1) in zip(table, table[1:]):
        if x <= x1:
            return r0 + (r1 - r0) * (x - x0) / (x1 - x0)
    return table[-1][1]


def duct_radius(x):
    return interp(PROFILE, x)


def outer_radius(x):
    return interp(OUTER, x)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# --------------------------------------------------------------------- setup

rows = list(csv.DictReader(open(os.path.join(ROOT, "build", "parts.csv"))))
spinners = []
for r in rows:
    if r["spin"] in ("", "0.0", "0"):
        continue
    ob = bpy.data.objects.get(r["name"])
    if ob:
        spinners.append((ob, float(r["spin"])))
print(f"  spinners: {len(spinners)}")

R.setup_render(SAMPLES, res=RES)
R.setup_world()
R.setup_lights()
R.area_light("inlet", (R.X_MID - 9.5, -3.4, 1.4),
             (math.radians(84), 0, math.radians(-64)), 1700, 3.2)
R.setup_camera((R.X_MID - 10.6, -9.6, 3.5), (R.X_MID - 0.35, 0, -0.05), lens=76)

# flat background, replacing the gradient world
_world = bpy.context.scene.world
_nt = _world.node_tree
_nt.nodes.clear()
_out = _nt.nodes.new("ShaderNodeOutputWorld")
_bg = _nt.nodes.new("ShaderNodeBackground")
_bg.inputs["Color"].default_value = (*WORLD_RGB, 1.0)
_bg.inputs["Strength"].default_value = 1.0
_nt.links.new(_bg.outputs["Background"], _out.inputs["Surface"])

scene = bpy.context.scene
scene.render.fps = 24
scene.render.image_settings.file_format = "PNG"
os.makedirs(OUT, exist_ok=True)


def camera_only(ob):
    """Read to the camera without lighting or occluding the scene."""
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission",
                 "visible_volume_scatter", "visible_shadow"):
        if hasattr(ob, attr):
            setattr(ob, attr, False)


def emission_material(name, colour, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*colour, 1.0)
    emit.inputs["Strength"].default_value = strength
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(emit.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs[0])
    return mat, emit


def plume_material():
    """Emission along the cone's own axis, bright at the nozzle, falling away.

    A cone of flat emission reads as a paper cone glued to the tailpipe; the
    falloff is what makes it read as flame.
    """
    mat = bpy.data.materials.new("plume")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (1.0, 0.62, 0.26, 1.0)
    coords = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Generated"], sep.inputs[0])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    ramp.color_ramp.interpolation = "EASE"
    links.new(sep.outputs["Z"], ramp.inputs[0])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    links.new(ramp.outputs["Color"], mul.inputs[0])
    mul.inputs[1].default_value = 0.0          # animated per frame
    links.new(mul.outputs[0], emit.inputs["Strength"])
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(emit.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs[0])
    return mat, mul


# ------------------------------------------------------------------ streaks

streak_objs = []
random.seed(7)
for i in range(STREAKS):
    kind = ("outer", "outer", "inlet")[i % 3]
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = f"streak_{i:03d}"
    if kind == "outer":
        frac = random.uniform(1.06, 1.50)
        length, thick = random.uniform(0.34, 0.70), 0.013
        colour, strength = (0.60, 0.84, 1.0), 3.4
        speed, swirl = random.uniform(0.85, 1.15), 0.10
    else:
        frac = random.uniform(0.12, 0.94)
        length, thick = random.uniform(0.26, 0.55), 0.013
        colour, strength = (0.52, 0.80, 1.0), 4.2
        speed, swirl = random.uniform(1.05, 1.45), 0.55
    ob.scale = (length, thick, thick)
    mat, emit = emission_material(f"streak_mat_{i:03d}", colour, strength)
    ob.data.materials.append(mat)
    camera_only(ob)
    streak_objs.append({
        "ob": ob, "emit": emit, "frac": frac, "kind": kind,
        "strength": strength, "phase": random.random(),
        "speed": speed, "swirl": swirl, "angle0": random.uniform(0, 2 * math.pi),
    })

# Exhaust: hot streaks leaving the nozzle, diverging as pressure drops.
for i in range(26):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = f"exhaust_{i:02d}"
    length, thick = random.uniform(0.22, 0.46), 0.012
    ob.scale = (length, thick, thick)
    mat, emit = emission_material(f"exhaust_mat_{i:02d}", (1.00, 0.78, 0.46), 6.0)
    ob.data.materials.append(mat)
    camera_only(ob)
    streak_objs.append({
        "ob": ob, "emit": emit, "frac": random.uniform(0.10, 0.80),
        "kind": "exhaust", "strength": 6.0, "phase": random.random(),
        "speed": random.uniform(1.5, 2.1), "swirl": 0.35,
        "angle0": random.uniform(0, 2 * math.pi),
    })

plume, plume_mul = None, None
if IGNITE:
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.36, radius2=0.05,
                                    depth=2.6, location=(NOZZLE_X, 0, 0),
                                    rotation=(0, math.pi / 2, 0))
    plume = bpy.context.active_object
    plume.name = "plume"
    mat, plume_mul = plume_material()
    plume.data.materials.append(mat)
    camera_only(plume)


def timeline(f):
    t = f / N_FRAMES
    if not IGNITE:
        return {"spool": t * 2 * math.pi, "progress": t, "flow": 1.0,
                "exhaust": 1.0, "plume": 0.0, "plume_scale": 0.0,
                "pulse": math.sin(t * 2 * math.pi)}
    spool = 0.15 * t + 0.85 * t * t      # rate ramps, so the wind-up reads
    return {"spool": spool * 2 * math.pi,
            "progress": spool * 1.7,
            "flow": smooth((t - 0.06) / 0.34),
            "exhaust": smooth((t - 0.46) / 0.16),
            "plume": smooth((t - 0.58) / 0.22),
            "plume_scale": 0.25 + 0.75 * smooth((t - 0.56) / 0.30),
            "pulse": 0.0}


def set_frame(f):
    s = timeline(f)
    for ob, spin in spinners:
        ob.rotation_mode = "XYZ"
        ob.rotation_euler.x = (math.radians(LP_TURN if spin > 0 else HP_TURN)
                               * s["spool"] / (2 * math.pi))

    for k in streak_objs:
        u = (s["progress"] * k["speed"] + k["phase"]) % 1.0
        if k["kind"] == "exhaust":
            x = NOZZLE_X + 2.0 * u
            r = outer_radius(NOZZLE_X) * k["frac"] * (1.0 + 0.9 * u)
            edge = min(smooth(u / 0.10), smooth((1.0 - u) / 0.45))
            gain = s["exhaust"] * (0.85 + 0.15 * s["pulse"])
        else:
            x = X_FRONT + (X_BACK - X_FRONT) * u
            rad = outer_radius(x) if k["kind"] == "outer" else duct_radius(x)
            r = rad * k["frac"]
            edge = min(smooth(u / 0.12), smooth((1.0 - u) / 0.12))
            gain = s["flow"]
        a = k["angle0"] + s["spool"] * 1.7 * k["swirl"]
        k["ob"].location = (x, r * math.cos(a), r * math.sin(a))
        k["emit"].inputs["Strength"].default_value = edge * k["strength"] * gain

    if plume is not None:
        sc = max(s["plume_scale"], 1e-3)
        plume.scale = (1.0, 1.0, sc)
        plume.location.x = NOZZLE_X + 1.30 * sc
        plume_mul.inputs[1].default_value = 13.0 * s["plume"]


# --------------------------------------------------------------------- run

if MODE == "calibrate":
    # Renders one frame at each end of the sequence so the flat background can
    # be sampled against the plate colour it has to sit on.
    scene.render.resolution_x, scene.render.resolution_y = 320, 131
    for name, f in (("cal_cold", 0), ("cal_lit", N_FRAMES - 1)):
        set_frame(f)
        scene.render.filepath = os.path.join(OUT, name + ".png")
        bpy.ops.render.render(write_still=True)
        print(f"  -> {name}.png")
    print(f"  world linear RGB {WORLD_RGB}")
elif MODE == "test":
    set_frame(int(N_FRAMES * 0.92))
    scene.render.filepath = os.path.join(OUT, "test.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"  single frame ({MODE}): {time.time() - t0:.1f}s")
else:
    t0 = time.time()
    for f in range(N_FRAMES):
        set_frame(f)
        scene.render.filepath = os.path.join(OUT, f"f_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 10 == 0:
            print(f"  frame {f}/{N_FRAMES}  {time.time() - t0:.0f}s")
    print(f"  {N_FRAMES} frames in {time.time() - t0:.0f}s")