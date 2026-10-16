"""Check the built model against spec.py by measurement.

Reads build/parts.csv (written by assemble.py) and asserts that what actually
got built matches what was specified. Exits non-zero on any failure, so this
is the command that settles whether the model is right.
"""

import csv
import re
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import spec  # noqa: E402

TOL = 2.0   # mm


class Check:
    def __init__(self):
        self.fails, self.n = [], 0

    def close(self, label, got, want, tol=TOL):
        self.n += 1
        if abs(got - want) > tol:
            self.fails.append(f"{label}: got {got:.1f}, want {want:.1f} (+-{tol})")
            return False
        print(f"  ok  {label:46s} {got:9.1f}  (spec {want:.1f})")
        return True

    def true(self, label, cond, detail=""):
        self.n += 1
        if not cond:
            self.fails.append(f"{label}: {detail}")
            return False
        print(f"  ok  {label:46s} {detail}")
        return True


def main():
    path = os.path.join(ROOT, "build", "parts.csv")
    if not os.path.exists(path):
        print("build/parts.csv missing -- run assemble.py first")
        return 1
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    by = {r["name"]: r for r in rows}

    def f(r, k):
        return float(r[k])

    c = Check()
    print("\nENVELOPE")
    x_min = min(f(r, "x_min_mm") for r in rows)
    x_max = max(f(r, "x_max_mm") for r in rows)
    c.close("overall length", x_max - x_min, spec.LENGTH, 3.0)
    c.close("front face station", x_min, spec.STATION["inlet_lip"], 3.0)
    c.close("rear face station", x_max, spec.STATION["nozzle_exit"], 3.0)

    # fan tip diameter, measured off the stage-1 fan blades themselves
    r_fan = max(abs(f(by["blades_fan_r1"], k)) for k in
                ("y_min_mm", "y_max_mm", "z_min_mm", "z_max_mm"))
    c.close("fan tip diameter", r_fan * 2, spec.FAN_TIP_DIAMETER, 4.0)

    print("\nBLADE ROWS")
    for row in spec.all_blade_rows():
        key = f"blades_{row.name}" if f"blades_{row.name}" in by else f"vanes_{row.name}"
        if key not in by:
            c.true(f"row {row.name} present", False, "missing from build")
            continue
        r = by[key]
        got_tip = max(abs(f(r, k)) for k in
                      ("y_min_mm", "y_max_mm", "z_min_mm", "z_max_mm"))
        want_tip = max(row.r_tip_le, row.r_tip_te)
        # A row reaches its annulus, and stops at the casing bore.
        #
        # This used to be an allowance -- 12 mm for anything carrying a band
        # or a shroud -- which is not a statement about the engine, and it
        # passed three shrouded turbine rows that were up to 16 mm THROUGH
        # the turbine case. What a row may not do is stand outside the bore
        # of the casing it runs in, so that is what is measured.
        # Over the whole span the row's platforms cover, not just midspan:
        # a band follows the bore, and through the compressor the bore at the
        # front of a row is several millimetres above the bore at its middle.
        cas = spec.enclosing_casing(row.x + row.chord * 0.5, want_tip)
        xa, xb = row.x - row.chord * 0.14, row.x + row.chord * 1.14
        bore = (max(spec.casing_inner(cas, xa + (xb - xa) * i / 8.0)
                    for i in range(9)) if cas else want_tip + 12.0)
        c.true(f"{row.name} tip radius",
               got_tip <= bore + 0.5 and got_tip >= want_tip - 3.0,
               f"{got_tip:.1f} mm (annulus {want_tip:.1f}, bore {bore:.1f})")

    print("\nCOMPLETENESS")
    c.true("object count", len(rows) >= 95, f"{len(rows)} objects")
    # Every rotor turns with a spool.
    #
    # The viewer used to decide this with a regex in its HTML, so a rotor that
    # was added or renamed silently stopped turning and no test could see it.
    # The build assigns it now, and this is the test: anything whose name says
    # it is a rotating blade row, disc, drum or shaft must have been given a
    # spool, and nothing static may have been given one.
    spun = [r for r in rows if (r.get("spool") or "")]
    turning = re.compile(r"^(blades_(fan|hpc|hpt|lpt)_r\d+|shaft_(lp|hp)"
                         r"|hpc_drum|hpt_disc|fan_disc_assembly"
                         r"|lpt_disc_assembly)$")
    missed = [r["name"] for r in rows
              if turning.match(r["name"]) and not (r.get("spool") or "")]
    stray = [r["name"] for r in spun if not turning.match(r["name"])
             and "cone" not in r["name"] and "seals" not in r["name"]]
    c.true("every rotor is assigned to a spool", not missed and not stray,
           f"{len(spun)} rotating parts")
    for mm in missed:
        c.fails.append(f"rotor with no spool: {mm}")
    for mm in stray:
        c.fails.append(f"static part assigned a spool: {mm}")

    c.true("every object has a material",
           all(r["material"] for r in rows), "all assigned")
    # A name in MATERIAL_MAP that is not in PALETTE silently falls back to the
    # default, so a part ends up the wrong material and nothing says so. Caught
    # exactly that: "steel_polished" was assigned to six new parts and does not
    # exist -- the palette calls it "steel".
    unknown = sorted({v for v in spec.MATERIAL_MAP.values()
                      if v not in spec.PALETTE})
    # Installed envelope.
    #
    # `attached` cannot catch a unit that floats: the oil tank, heat exchanger,
    # control and exciters were each built as a revolve running along x and
    # then rotated so their length pointed outward, which put them 1,070 to
    # 1,247 mm from an axis whose casings stop at 606. They passed the
    # attachment test because their mounting straps still wrapped the casing.
    # An engine has to go inside a nacelle, so the radius every part actually
    # reaches is a real constraint and a real test. Ratchet: lower it when the
    # installation gets tighter, never raise it to make a build pass.
    ENVELOPE_R = 860.0
    over = [(r["name"], float(r["r_max_mm"])) for r in rows
            if r.get("r_max_mm") and float(r["r_max_mm"]) > ENVELOPE_R]
    c.true("every part inside the installed envelope", not over,
           f"widest {max((float(r['r_max_mm']) for r in rows if r.get('r_max_mm')), default=0):.0f} mm"
           f" of {ENVELOPE_R:.0f}"
           + ("" if not over else ": " + ", ".join(f"{n} {v:.0f}" for n, v in over[:4])))

    c.true("every material name is real", not unknown,
           f"{len(spec.PALETTE)} in palette"
           + (f", unknown: {', '.join(unknown)}" if unknown else ""))
    used = sorted({r["material"] for r in rows if r["material"]})
    c.true("every material used is in the palette",
           all(m in spec.PALETTE for m in used), f"{len(used)} used")
    c.true("no empty meshes",
           all(int(r["verts"]) > 0 for r in rows), "all non-empty")

    expect = ["centre_body", "combustor_dome", "fuel_nozzles", "igniters",
              "hpt_disc", "lpt_disc_assembly", "shaft_lp", "shaft_hp",
              "mixer", "flameholder", "spraybars", "augmentor_liner",
              "nozzle_flaps_convergent", "nozzle_flaps_divergent",
              "nozzle_seals", "nozzle_actuators", "gearbox", "towershaft",
              "bypass_struts", "splitter", "variable_vane_actuation"]
    missing = [n for n in expect if n not in by]
    c.true("key components present", not missing, f"{len(expect)} checked")
    for n in missing:
        c.fails.append(f"missing component: {n}")

    for name, count in (("brg_1_lp_thrust", 1), ("brg_5_lp_roller", 1)):
        c.true(f"{name} present", name in by, "yes" if name in by else "no")

    print("\nAIRFOIL COUNT")
    c.true("total airfoils", spec.total_airfoil_count() == 2044,
           f"{spec.total_airfoil_count():,} across {len(spec.all_blade_rows())} rows")

    print("\nCONSISTENCY")
    cb = spec.CENTRE_BODY
    igv = spec.FAN_ROWS[0]
    c.true("centre-body carries the guide vanes' hub",
           igv.r_hub_le - 12.0 <= cb["hub_radius"] <= igv.r_hub_le,
           f"r {cb['hub_radius']:.0f} under an IGV hub at {igv.r_hub_le:.0f}")
    c.true("centre-body stands clear of the fan",
           cb["x_aft"] < spec.FAN_ROWS[1].x - 20.0,
           f"ends at {cb['x_aft']:.0f}, fan rotor 1 at {spec.FAN_ROWS[1].x:.0f}")
    c.true("centre-body inside inlet",
           cb["x_nose"] >= spec.STATION["inlet_lip"],
           f"nose {cb['x_nose']:.0f} >= lip {spec.STATION['inlet_lip']:.0f}")
    c.true("stations monotonic",
           all(spec.STATION[a] <= spec.STATION[b] for a, b in [
               ("fan_face", "fan_exit"), ("fan_exit", "hpc_inlet"),
               ("hpc_inlet", "hpc_exit"), ("hpc_exit", "combustor_exit"),
               ("combustor_exit", "lpt_exit"), ("lpt_exit", "augmentor_exit"),
               ("augmentor_exit", "nozzle_throat"),
               ("nozzle_throat", "nozzle_exit")]),
           "flowpath ordered front to back")

    # bypass ratio implied by the splitter radius must match the published value
    ogv = spec.FAN_ROWS[6]          # last fan row before the splitter
    r_h = ogv.r_hub_te
    r_t = ogv.r_tip_te
    r_s = spec.BYPASS["splitter_radius"]
    a_core = math.pi * (r_s ** 2 - r_h ** 2)
    a_byp = math.pi * (r_t ** 2 - r_s ** 2)
    c.close("bypass ratio from splitter radius",
            a_byp / a_core, spec.BYPASS_RATIO, 0.02)

    print("\n" + "=" * 60)
    if c.fails:
        print(f"FAIL  {len(c.fails)} of {c.n} checks")
        for x in c.fails:
            print("   x " + x)
        return 1
    print(f"PASS  all {c.n} checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
