#!/usr/bin/env python3
"""
Blender MCP + BlenderKit 5-Scene Production Renderer for Brand-New Script:
"THE MURDER OF GRIGORI RASPUTIN IN THE YUSUPOV PALACE (DECEMBER 30, 1916)"
Replicating the exact visual DNA of Imperial ("The Most Famous Killing in History")
on a 100% new historical subject and script:
  - Scene 0: 3D Architectural Cutaway of Yusupov Palace & Moika Canal in Void
  - Scene 1: 3D Interior Tableau of the Soundproofed Basement (Rasputin vs. Prince Yusupov)
  - Scene 2: 3D Exploded Marble Bust of Rasputin + 3-Column Bento Noir Dossier ("UNTOUCHABLE")
  - Scene 3: 3D Tilted Topographic Relief Map of Russia & Eastern Front + Conspirator Collector Cards
  - Scene 4: 90° Top-Down Forensic Crime Scene (Fallen Rasputin, Blood Pool, Revolver, Footprints)
"""
import os
import sys
import math
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")


def run_stitch(stills_dir, out_board_path):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    W, H = 1920, 3000
    board = Image.new("RGB", (W, H), (10, 11, 14))
    draw = ImageDraw.Draw(board)

    font_paths = [
        os.path.join(SCRIPT_DIR, "fonts", "Cinzel-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_path = next((p for p in font_paths if os.path.exists(p)), None)
    f_title = ImageFont.truetype(font_path, 26) if font_path else ImageFont.load_default()
    f_sub = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
    f_lbl = ImageFont.truetype(font_path, 15) if font_path else ImageFont.load_default()
    f_small = ImageFont.truetype(font_path, 13) if font_path else ImageFont.load_default()
    f_giant = ImageFont.truetype(font_path, 40) if font_path else ImageFont.load_default()

    # Header
    draw.rectangle([0, 0, W, 88], fill=(16, 18, 23))
    draw.line([(0, 88), (W, 88)], fill=(195, 38, 42), width=3)
    draw.text(
        (32, 18),
        "IMPERIAL VISUAL DNA  x  NEW 45s SCRIPT: THE MURDER OF RASPUTIN (DEC 30, 1916)",
        fill=(242, 238, 228),
        font=f_title,
    )
    draw.text(
        (32, 54),
        "LEFT: Original 'Imperial' Style Reference   |   RIGHT: New Script Rendered in Blender 4.3 Cycles + BlenderKit (Yusupov Palace, Petrograd)",
        fill=(185, 190, 202),
        font=f_sub,
    )

    ref_path = os.path.join(SCRIPT_DIR, "imperial_forensic_analysis.jpg")
    ref_img = Image.open(ref_path).convert("RGB") if os.path.exists(ref_path) else None

    def crop_cell(is_board_b, row, col):
        if ref_img is None:
            return Image.new("RGB", (640, 328), (24, 24, 28))
        y_base = 1096 if is_board_b else 0
        x0 = col * 640
        y0 = y_base + row * 360 + 32
        return ref_img.crop((x0, y0, x0 + 640, y0 + 328))

    ref_crops = [
        crop_cell(False, 0, 2),  # Scene 0 ref: 3D Cutaway Architecture in Void (02:25.0)
        crop_cell(False, 0, 0),  # Scene 1 ref: 3D Interior Hall Tableau + Callouts (00:18.0)
        crop_cell(True, 2, 0),   # Scene 2 ref: Sliced 3D Marble Bust + Red Streak (05:15.0)
        crop_cell(True, 1, 2),   # Scene 3 ref: 3D Tilted Topographic Map + Scrubber (05:00.0)
        crop_cell(False, 2, 1),  # Scene 4 ref: 3D Top-Down Crime Scene Blood Pool (12:30.0)
    ]

    scene_meta = [
        (
            "SCENE 1 (00:00-00:09) — 3D ARCHITECTURAL CUTAWAY: YUSUPOV PALACE & MOIKA CANAL",
            "VO: \"Just after midnight on Dec 30th, 1916, inside the Yusupov Palace in Petrograd, four aristocrats lured Rasputin into a soundproofed basement.\"",
        ),
        (
            "SCENE 2 (00:09-00:18) — 3D BASEMENT TABLEAU: CYANIDE WINE & PASTRIES",
            "VO: \"Grigori Rasputin sat across from Prince Felix Yusupov beneath vaulted stone arches—unaware the Madeira wine held potassium cyanide.\"",
        ),
        (
            "SCENE 3 (00:18-00:27) — BENTO NOIR DOSSIER + SLICED 3D BUST: 'UNTOUCHABLE'",
            "VO: \"To the nobility, the Siberian mystic had become untouchable—appointing ministers and dictating Tsarina Alexandra's wartime rule.\"",
        ),
        (
            "SCENE 4 (00:27-00:36) — 3D TOPOGRAPHIC MAP OF RUSSIA + CONSPIRATOR COLLECTOR CARDS",
            "VO: \"As collapsing frontlines pushed Petrograd toward revolution, three conspirators converged on the Moika Canal to save the monarchy by murder.\"",
        ),
        (
            "SCENE 5 (00:36-00:45) — 90° TOP-DOWN FORENSIC CRIME SCENE: THREE REVOLVER SHOTS",
            "VO: \"When poison failed, three close-range revolver shots brought Rasputin down—leaving a trail of blood to the Moika River.\"",
        ),
    ]

    def decorate_rasputin_still(idx, img):
        """Apply authentic Imperial 2.5D Noir HUD / Bento Dossier / Callouts onto the rendered 3D frame."""
        im = img.copy().convert("RGBA")
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        w, h = im.size

        if idx == 0:
            # Bottom-left black date stamp ("30TH OF DECEMBER / 1916")
            d.rectangle([28, h - 92, 265, h - 26], fill=(12, 13, 16, 235), outline=(210, 45, 48, 255), width=2)
            d.rectangle([28, h - 92, 35, h - 26], fill=(210, 45, 48, 255))
            d.text((46, h - 82), "30TH OF DECEMBER", fill=(245, 242, 232, 255), font=f_sub)
            d.text((46, h - 56), "1916  //  PETROGRAD", fill=(215, 65, 68, 255), font=f_lbl)
            # Top-right architectural legend badge
            d.rectangle([w - 310, 22, w - 24, 78], fill=(14, 15, 20, 220), outline=(180, 155, 95, 220), width=1)
            d.text((w - 296, 30), "YUSUPOV PALACE CUTAWAY", fill=(240, 215, 145, 255), font=f_lbl)
            d.text((w - 296, 52), "94 MOIKA EMBANKMENT", fill=(185, 190, 200, 255), font=f_small)

        elif idx == 1:
            # Bottom-left date stamp
            d.rectangle([28, h - 92, 265, h - 26], fill=(12, 13, 16, 235), outline=(210, 45, 48, 255), width=2)
            d.rectangle([28, h - 92, 35, h - 26], fill=(210, 45, 48, 255))
            d.text((46, h - 82), "30TH OF DECEMBER", fill=(245, 242, 232, 255), font=f_sub)
            d.text((46, h - 56), "1916  //  01:15 AM", fill=(215, 65, 68, 255), font=f_lbl)

            # Tracked 3D Callout for Rasputin (Left-Center)
            rx, ry = int(w * 0.43), int(h * 0.34)
            bx, by = int(w * 0.14), int(h * 0.16)
            d.line([(rx, ry), (rx - 35, by + 24), (bx + 230, by + 24)], fill=(235, 60, 62, 255), width=2)
            d.ellipse([rx - 5, ry - 5, rx + 5, ry + 5], fill=(235, 60, 62, 255))
            d.rectangle([bx, by, bx + 230, by + 54], fill=(14, 15, 20, 238), outline=(235, 60, 62, 255), width=2)
            d.text((bx + 12, by + 8), "IMPERIAL ADVISOR", fill=(235, 75, 75, 255), font=f_small)
            d.text((bx + 12, by + 26), "GRIGORI RASPUTIN", fill=(248, 245, 236, 255), font=f_lbl)

            # Tracked 3D Callout for Prince Felix Yusupov (Right-Center)
            yx, yy = int(w * 0.61), int(h * 0.48)
            bx2, by2 = int(w * 0.66), int(h * 0.22)
            d.line([(yx, yy), (yx + 28, by2 + 24), (bx2, by2 + 24)], fill=(230, 195, 110, 255), width=2)
            d.ellipse([yx - 5, yy - 5, yx + 5, yy + 5], fill=(230, 195, 110, 255))
            d.rectangle([bx2, by2, bx2 + 240, by2 + 54], fill=(14, 15, 20, 238), outline=(230, 195, 110, 255), width=2)
            d.text((bx2 + 12, by2 + 8), "CHIEF CONSPIRATOR", fill=(230, 195, 110, 255), font=f_small)
            d.text((bx2 + 12, by2 + 26), "PRINCE FELIX YUSUPOV", fill=(248, 245, 236, 255), font=f_lbl)

        elif idx == 2:
            # Left Column: Tactile Bento Noir Collector Card ("G. Y. RASPUTIN" + "UNTOUCHABLE" Stamp)
            cx0, cy0, cx1, cy1 = 26, 28, 286, h - 28
            d.rectangle([cx0, cy0, cx1, cy1], fill=(22, 21, 20, 245), outline=(215, 205, 185, 240), width=2)
            d.rectangle([cx0 + 8, cy0 + 8, cx1 - 8, cy0 + 38], fill=(165, 28, 32, 255))
            d.text((cx0 + 18, cy0 + 14), "G. Y. RASPUTIN (1869–1916)", fill=(248, 244, 232, 255), font=f_lbl)

            p_ras = os.path.join(ASSETS_DIR, "portrait_rasputin.jpg")
            if os.path.exists(p_ras):
                pr = Image.open(p_ras).convert("L").convert("RGBA").resize((236, 230))
                ov.paste(pr, (cx0 + 12, cy0 + 46))
            d.rectangle([cx0 + 12, cy0 + 46, cx0 + 248, cy0 + 276], outline=(185, 175, 155, 255), width=2)

            # Red rubber stamp "UNTOUCHABLE"
            d.rectangle([cx0 + 24, cy0 + 225, cx0 + 236, cy0 + 266], fill=(185, 22, 26, 235), outline=(255, 230, 220, 255), width=2)
            d.text((cx0 + 42, cy0 + 235), "STAMP: UNTOUCHABLE", fill=(255, 245, 240, 255), font=f_lbl)

            # Bottom Bento Career List inside Left/Center Card
            d.text((cx0 + 14, cy0 + 290), "IMPERIAL HOLD (1907–1916):", fill=(235, 195, 110, 255), font=f_small)
            items = [
                ("1907: Royal Healer to Alexei", False),
                ("1915: Tsar Departs for Front", False),
                ("1916: 4 PMs Purged in 12 Months", True),
                ("1916: Military & Synod Vetoes", True),
            ]
            for ii, (txt, hi) in enumerate(items):
                yy = cy0 + 316 + ii * 32
                if hi:
                    d.rectangle([cx0 + 12, yy - 2, cx1 - 12, yy + 22], fill=(195, 32, 36, 225))
                d.text((cx0 + 18, yy + 2), txt, fill=(248, 245, 236, 255), font=f_small)

            # Right Primary-Source Quote Box (Sir George Buchanan, 1916)
            qx0, qy0, qx1, qy1 = w - 320, h - 165, w - 22, h - 26
            d.rectangle([qx0, qy0, qx1, qy1], fill=(18, 18, 22, 238), outline=(215, 48, 52, 255), width=2)
            d.rectangle([qx0, qy0, qx1, qy0 + 28], fill=(185, 30, 34, 255))
            d.text((qx0 + 10, qy0 + 6), "PRIMARY SOURCE // NOV 1916", fill=(250, 245, 235, 255), font=f_small)
            d.text((qx0 + 12, qy0 + 38), "\"If the Emperor upholds", fill=(240, 238, 230, 255), font=f_small)
            d.text((qx0 + 12, qy0 + 58), "Rasputin against Russia,", fill=(240, 238, 230, 255), font=f_small)
            d.text((qx0 + 12, qy0 + 78), "catastrophe is inevitable.\"", fill=(240, 238, 230, 255), font=f_small)
            d.text((qx0 + 12, qy0 + 106), "— Sir G. Buchanan, Brit. Amb.", fill=(220, 185, 105, 255), font=f_small)

        elif idx == 3:
            # 3 Conspirator Collector Cards Sliding Toward Petrograd + Bottom Timeline Scrubber
            cards = [
                ("PRINCE F. YUSUPOV", "THE ARISTOCRAT HOST", "portrait_yusupov.jpg", 26, 26, (215, 180, 95, 255)),
                ("GRAND DUKE DMITRI", "THE TSAR'S COUSIN", "portrait_dmitri.jpg", 26, 178, (215, 60, 62, 255)),
                ("V. PURISHKEVICH", "MONARCHIST DEPUTY", "portrait_purishkevich.jpg", 26, 330, (90, 165, 235, 255)),
            ]
            for title, role, pfile, x0, y0, col in cards:
                d.rectangle([x0, y0, x0 + 255, y0 + 136], fill=(16, 18, 24, 238), outline=col, width=2)
                pp = os.path.join(ASSETS_DIR, pfile)
                if os.path.exists(pp):
                    pi = Image.open(pp).convert("L").convert("RGBA").resize((84, 112))
                    ov.paste(pi, (x0 + 10, y0 + 12))
                d.rectangle([x0 + 10, y0 + 12, x0 + 94, y0 + 124], outline=col, width=1)
                d.text((x0 + 104, y0 + 18), title, fill=(248, 245, 235, 255), font=f_small)
                d.text((x0 + 104, y0 + 42), role, fill=col, font=f_small)
                d.text((x0 + 104, y0 + 72), "TARGET: MOIKA", fill=(200, 205, 215, 255), font=f_small)
                d.text((x0 + 104, y0 + 94), "DEC 30, 1916", fill=(235, 75, 75, 255), font=f_small)

            # Map Callout Labels
            px, py = int(w * 0.63), int(h * 0.28)
            d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=(255, 210, 80, 255), outline=(255, 255, 255, 255), width=2)
            d.rectangle([px + 14, py - 20, px + 245, py + 24], fill=(14, 16, 22, 235), outline=(255, 210, 80, 255), width=2)
            d.text((px + 22, py - 12), "PETROGRAD (YUSUPOV PALACE)", fill=(255, 215, 95, 255), font=f_small)
            d.text((px + 22, py + 5), "IMPERIAL CAPITAL // 1916", fill=(220, 225, 235, 255), font=f_small)

            fx, fy = int(w * 0.45), int(h * 0.62)
            d.rectangle([fx - 110, fy - 18, fx + 155, fy + 22], fill=(165, 24, 28, 230), outline=(255, 180, 180, 255), width=1)
            d.text((fx - 98, fy - 8), "COLLAPSING EASTERN FRONT (1916)", fill=(255, 245, 240, 255), font=f_small)

            # Bottom Chronological Scrubber
            d.rectangle([295, h - 64, w - 24, h - 18], fill=(12, 14, 18, 240), outline=(195, 42, 46, 255), width=2)
            d.text((312, h - 48), "AUG 1915: TSAR TAKES COMMAND", fill=(185, 190, 202, 255), font=f_small)
            d.line([(565, h - 40), (w - 255, h - 40)], fill=(225, 55, 58, 255), width=3)
            d.ellipse([w - 262, h - 47, w - 248, h - 33], fill=(235, 65, 68, 255))
            d.text((w - 240, h - 48), "DEC 30, 1916: MOIKA PLOT", fill=(255, 215, 100, 255), font=f_small)

        elif idx == 4:
            # Top-Left Forensic Autopsy / Source Spotlight Box
            d.rectangle([24, 22, 435, 128], fill=(14, 15, 20, 238), outline=(215, 48, 52, 255), width=2)
            d.rectangle([24, 22, 435, 50], fill=(185, 28, 32, 255))
            d.text((36, 28), "FORENSIC AUTOPSY // PROF. D. KOSOROTOV (DEC 1916)", fill=(250, 245, 235, 255), font=f_small)
            d.text((36, 58), "\"Three close-range revolver shots—one piercing the", fill=(238, 235, 226, 255), font=f_small)
            d.text((36, 78), "chest, a final shot through the forehead at point-blank", fill=(238, 235, 226, 255), font=f_small)
            d.text((36, 98), "range—before the body was cast into the Malaya Nevka.\"", fill=(225, 190, 110, 255), font=f_small)

            # Weapon Callout ("WEBLEY .455 REVOLVER")
            wx, wy = int(w * 0.60), int(h * 0.56)
            d.line([(wx, wy), (wx + 55, wy - 45), (wx + 195, wy - 45)], fill=(235, 200, 110, 255), width=2)
            d.ellipse([wx - 5, wy - 5, wx + 5, wy + 5], fill=(235, 200, 110, 255))
            d.rectangle([wx + 55, wy - 76, wx + 285, wy - 38], fill=(14, 15, 20, 235), outline=(235, 200, 110, 255), width=1)
            d.text((wx + 65, wy - 64), "MURDER WEAPON: REVOLVER", fill=(245, 215, 125, 255), font=f_small)

            # Victim Callout ("FALLEN MYSTIC: G. RASPUTIN")
            vx, vy = int(w * 0.48), int(h * 0.50)
            d.line([(vx, vy), (vx - 65, vy + 68), (vx - 265, vy + 68)], fill=(235, 58, 62, 255), width=2)
            d.ellipse([vx - 5, vy - 5, vx + 5, vy + 5], fill=(235, 58, 62, 255))
            d.rectangle([vx - 285, vy + 38, vx - 55, vy + 76], fill=(14, 15, 20, 235), outline=(235, 58, 62, 255), width=1)
            d.text((vx - 275, vy + 50), "FALLEN VICTIM: G. RASPUTIN", fill=(245, 95, 95, 255), font=f_small)

        return Image.alpha_composite(im, ov).convert("RGB")

    row_h = 575
    y_start = 104
    for idx in range(5):
        y0 = y_start + idx * row_h
        draw.rectangle([20, y0, W - 20, y0 + row_h - 14], fill=(18, 20, 26), outline=(52, 56, 68), width=2)
        draw.rectangle([20, y0, W - 20, y0 + 58], fill=(25, 28, 36))
        draw.text((36, y0 + 8), scene_meta[idx][0], fill=(245, 212, 128), font=f_sub)
        draw.text((36, y0 + 33), scene_meta[idx][1], fill=(205, 212, 225), font=f_small)

        # Left Panel: Original Imperial Visual DNA Reference
        ref_panel = ref_crops[idx].resize((896, 488), Image.Resampling.LANCZOS)
        board.paste(ref_panel, (36, y0 + 66))
        draw.rectangle([36, y0 + 66, 36 + 896, y0 + 66 + 488], outline=(110, 115, 130), width=2)
        draw.rectangle([46, y0 + 76, 430, y0 + 106], fill=(12, 12, 16))
        draw.text((56, y0 + 82), "STYLE DNA REFERENCE (IMPERIAL)", fill=(215, 220, 230), font=f_lbl)

        # Right Panel: Brand-New Rasputin Script Rendered in Blender 4.3 + BlenderKit
        still_path = os.path.join(stills_dir, f"scene_{idx}.png")
        if os.path.exists(still_path):
            mcp_raw = Image.open(still_path).convert("RGB").resize((896, 488), Image.Resampling.LANCZOS)
            mcp_panel = decorate_rasputin_still(idx, mcp_raw)
        else:
            mcp_panel = Image.new("RGB", (896, 488), (40, 15, 15))
        board.paste(mcp_panel, (988, y0 + 66))
        draw.rectangle([988, y0 + 66, 988 + 896, y0 + 66 + 488], outline=(205, 48, 52), width=2)

    board.save(out_board_path, quality=94)
    print("Saved 5-scene Rasputin comparison board to", out_board_path)


if "--stitch" in sys.argv:
    idx = sys.argv.index("--stitch")
    run_stitch(sys.argv[idx + 1], sys.argv[idx + 2])
    sys.exit(0)

# ==============================================================================
# BLENDER 4.3 CYCLES + BLENDERKIT 3D SCENE BUILDER FOR RASPUTIN (DEC 30, 1916)
# ==============================================================================
import bpy
import bmesh
import mathutils

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else ["0", "/tmp/scene_0.png"]
SCENE_ID = int(argv[0])
OUT_PATH = argv[1]
FAST_TEST = "--fast" in argv

sys.path.insert(0, SCRIPT_DIR)
from mcp_scene1_curia_v2 import make_curia_carpet_and_border_floor

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 4 if FAST_TEST else 28
scene.cycles.use_denoising = not FAST_TEST
if not FAST_TEST:
    scene.cycles.denoiser = "OPENIMAGEDENOISER"
    scene.cycles.denoising_prefilter = "FAST"
scene.cycles.max_bounces = 2
scene.cycles.diffuse_bounces = 1
scene.cycles.glossy_bounces = 1
scene.cycles.transmission_bounces = 1
scene.cycles.transparent_max_bounces = 2
scene.render.resolution_x = 480 if FAST_TEST else 1280
scene.render.resolution_y = 270 if FAST_TEST else 720
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"


def make_mat(name, color, rough=0.45, metal=0.0, emit_col=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if emit_col and emit_str > 0.0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (*emit_col, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emit_str
    return m


def make_stone_mat(name, c1, c2, rough=0.42, scale=4.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (*c1, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (*c2, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
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


def setup_world(col=(0.014, 0.015, 0.020), strength=1.0):
    w = bpy.data.worlds.new("World")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*col, 1.0)
    bg.inputs[1].default_value = strength


def add_area_light(name, loc, rot_deg, energy, size, col=(1.0, 0.92, 0.80)):
    ld = bpy.data.lights.new(name, type="AREA")
    ld.energy = energy
    ld.size = size
    ld.color = col
    lo = bpy.data.objects.new(name, ld)
    lo.rotation_mode = "XYZ"
    lo.location = loc
    lo.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.collection.objects.link(lo)
    return lo


def add_camera(loc, rot_deg, lens=32.0):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    co = bpy.data.objects.new("Cam", cd)
    co.rotation_mode = "XYZ"
    co.location = loc
    co.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.collection.objects.link(co)
    scene.camera = co
    return co


# ==============================================================================
# SCENE 0: 3D ARCHITECTURAL CUTAWAY OF YUSUPOV PALACE & MOIKA CANAL (DEC 1916)
# ==============================================================================
if SCENE_ID == 0:
    setup_world((0.012, 0.014, 0.020), 1.0)

    mat_stucco_gold = make_stone_mat("YusupovStucco", (0.76, 0.64, 0.38), (0.64, 0.52, 0.28), rough=0.45, scale=5.0)
    mat_granite = make_stone_mat("MoikaGranite", (0.28, 0.29, 0.32), (0.18, 0.19, 0.22), rough=0.5, scale=8.0)
    mat_vault_stone = make_stone_mat("VaultStone", (0.52, 0.48, 0.42), (0.36, 0.33, 0.28), rough=0.55, scale=6.0)
    mat_white_trim = make_mat("WhiteCol", (0.90, 0.88, 0.84), rough=0.35)
    mat_snow = make_stone_mat("Snow", (0.86, 0.89, 0.94), (0.74, 0.78, 0.86), rough=0.65, scale=4.0)
    mat_ice = make_mat("CanalIce", (0.08, 0.14, 0.22), rough=0.12, metal=0.2)
    mat_cut_red = make_mat("CutEdgeRed", (0.68, 0.16, 0.16), rough=0.4, emit_col=(0.68, 0.16, 0.16), emit_str=0.4)
    mat_wood_dark = make_mat("DarkWood", (0.22, 0.13, 0.08), rough=0.35)
    mat_carpet_red = make_mat("CarpetRed", (0.58, 0.08, 0.10), rough=0.7)
    mat_text_white = make_mat("TextWhite", (0.96, 0.95, 0.92), rough=0.2, emit_col=(0.96, 0.95, 0.92), emit_str=1.6)
    mat_text_gold = make_mat("TextGold", (0.95, 0.78, 0.35), rough=0.2, emit_col=(0.95, 0.78, 0.35), emit_str=1.8)
    mat_footstep = make_mat("FootstepRed", (0.92, 0.14, 0.16), rough=0.2, emit_col=(0.95, 0.15, 0.18), emit_str=3.2)

    # Dark architectural plinth base in void
    add_box("BasePlinth", (0.0, 0.0, -0.8), (22.0, 14.0, 0.6), mat_granite)

    # 1. Left Wing: Frozen Moika Canal + Granite Embankment (-10.5 .. -5.2)
    add_box("MoikaCanalWater", (-8.0, 0.0, -0.38), (5.0, 13.6, 0.12), mat_ice)
    add_box("MoikaEmbankmentWall", (-5.3, 0.0, 0.05), (0.6, 13.8, 0.95), mat_granite)
    add_box("MoikaSnowBank", (-4.4, 0.0, 0.42), (1.4, 13.6, 0.14), mat_snow)

    # 2. Center Block: Yusupov Palace Neoclassical Facade & Courtyard (-3.8 .. +2.8)
    add_box("CourtyardFloor", (-0.5, 0.0, 0.42), (6.6, 13.6, 0.16), mat_snow)
    # Rear Palace Grand Wing with Corinthian Columns
    add_box("PalaceRearWall", (-0.5, 4.8, 2.5), (6.8, 0.45, 4.2), mat_stucco_gold)
    add_box("PalaceRearCutTop", (-0.5, 4.8, 4.65), (6.9, 0.50, 0.12), mat_cut_red)
    # West Wing Wall (facing Moika Canal)
    add_box("PalaceWestWall", (-3.7, 0.2, 2.2), (0.45, 9.6, 3.6), mat_stucco_gold)
    add_box("PalaceWestCutTop", (-3.7, 0.2, 4.05), (0.50, 9.7, 0.12), mat_cut_red)

    col_proto = load_blend_asset("bk_column_corinthian.blend", "ColProto", target_height=3.6, mat=mat_white_trim)
    if col_proto:
        col_proto.hide_render = True
        for cx in [-3.0, -1.8, -0.6, 0.6, 1.8]:
            instance_obj(col_proto, f"FacadeCol_{cx}", (cx, 4.35, 0.50))

    # Upper Cutaway Drawing Room (where conspirators wait above the basement)
    add_box("DrawingRoomFloor", (4.8, 2.2, 2.35), (5.8, 5.2, 0.18), mat_wood_dark)
    add_box("DrawingRoomRug", (4.8, 2.2, 2.46), (3.8, 3.4, 0.04), mat_carpet_red)
    add_box("DrawingRoomBackWall", (4.8, 4.7, 3.5), (5.8, 0.35, 2.4), mat_stucco_gold)
    add_box("DrawingRoomCutTop", (4.8, 4.7, 4.72), (5.9, 0.40, 0.10), mat_cut_red)

    # 3. Right Wing Cutaway: Soundproofed Basement & Spiral Staircase (X = +2.2 .. +9.2, Z = 0.0)
    add_box("BasementFloor", (5.6, -1.2, 0.05), (6.8, 8.2, 0.18), mat_vault_stone)
    add_box("BasementRug", (5.8, -1.2, 0.16), (4.2, 4.6, 0.03), mat_carpet_red)
    add_box("BasementBackWall", (5.6, 2.8, 1.25), (6.8, 0.38, 2.3), mat_vault_stone)
    add_box("BasementRightWall", (8.9, -1.2, 1.25), (0.38, 8.2, 2.3), mat_vault_stone)
    add_box("BasementRightCut", (8.9, -1.2, 2.42), (0.42, 8.3, 0.10), mat_cut_red)

    # Vaulted Stone Arches inside the Basement
    for ay in [-3.4, 0.8]:
        add_box(f"VaultPillarL_{ay}", (2.6, ay, 1.2), (0.45, 0.45, 2.2), mat_vault_stone)
        add_box(f"VaultPillarR_{ay}", (8.5, ay, 1.2), (0.45, 0.45, 2.2), mat_vault_stone)
        add_box(f"VaultBeam_{ay}", (5.55, ay, 2.25), (6.3, 0.42, 0.28), mat_vault_stone)

    # Spiral / Stepped Staircase descending from Courtyard/Drawing Room into Basement
    for s in range(9):
        sx = 2.2 + s * 0.22
        sy = 1.8 - s * 0.42
        sz = 2.25 - s * 0.24
        add_box(f"Stair_{s}", (sx, sy, sz), (0.85, 0.40, 0.12), mat_white_trim)

    # Populate Basement & Drawing Room with BlenderKit Furniture & Characters
    tbl_proto = load_blend_asset("bk_table_round.blend", "TblProto", target_height=0.78, mat=mat_wood_dark)
    if tbl_proto:
        tbl_proto.hide_render = True
        instance_obj(tbl_proto, "BasementTable", (5.8, -1.2, 0.18), scale=(1.35, 1.35, 1.1))
        instance_obj(tbl_proto, "DrawingRoomTable", (4.8, 2.2, 2.48), scale=(1.2, 1.2, 1.0))

    ras_proto = load_blend_asset("bk_bearded_statue.blend", "RasProto", target_height=1.82, mat=mat_white_trim)
    if ras_proto:
        ras_proto.hide_render = True
        instance_obj(ras_proto, "RasputinBasement", (4.9, -1.2, 0.18), rot=(0, 0, math.radians(90)))

    yus_proto = load_blend_asset("bk_male_sitting.blend", "YusProto", target_height=1.35, mat=mat_text_gold)
    if yus_proto:
        yus_proto.hide_render = True
        instance_obj(yus_proto, "YusupovBasement", (6.7, -1.2, 0.18), rot=(0, 0, math.radians(-90)))

    con_proto = load_blend_asset("bk_decor_man.blend", "ConProto", target_height=1.75, mat=mat_white_trim)
    if con_proto:
        con_proto.hide_render = True
        instance_obj(con_proto, "Conspirator1", (3.8, 2.4, 2.48), rot=(0, 0, math.radians(-35)))
        instance_obj(con_proto, "Conspirator2", (5.7, 2.5, 2.48), rot=(0, 0, math.radians(25)))
        instance_obj(con_proto, "Conspirator3", (4.8, 3.3, 2.48), rot=(0, 0, math.radians(0)))

    # Animated Red Dotted Footstep Trail (from Courtyard -> Stairs -> Basement Table)
    trail_pts = [
        (-2.2, -2.5, 0.52), (-1.2, -1.6, 0.52), (-0.2, -0.6, 0.52),
        (0.8, 0.4, 0.52), (1.6, 1.2, 1.25), (2.4, 1.4, 2.05),
        (2.9, 0.5, 1.45), (3.4, -0.4, 0.85), (4.0, -1.0, 0.24), (4.6, -1.2, 0.22),
    ]
    for idx_p, pt in enumerate(trail_pts):
        add_cyl(f"StepDot_{idx_p}", pt, 0.18, 0.06, mat_footstep, verts=20)

    # 3D World-Locked Extruded Architectural Labels (Imperial Style)
    add_3d_text("MOIKA CANAL", (-8.2, -3.2, 0.15), 0.58, mat_text_white, rot=(math.radians(52), 0, math.radians(-20)), extrude=0.05)
    add_3d_text("COURTYARD", (-0.6, -3.6, 0.72), 0.58, mat_text_white, rot=(math.radians(52), 0, math.radians(-20)), extrude=0.05)
    add_3d_text("DRAWING ROOM", (4.5, 3.8, 5.05), 0.56, mat_text_gold, rot=(math.radians(54), 0, math.radians(-20)), extrude=0.05)
    add_3d_text("BASEMENT", (5.6, -4.6, 0.65), 0.58, mat_text_gold, rot=(math.radians(52), 0, math.radians(-20)), extrude=0.05)

    # Lighting & Isometric-Perspective Cutaway Camera
    add_area_light("KeyMoon", (-10.0, -12.0, 14.0), (45, -20, -25), 1400.0, 8.0, (0.78, 0.86, 1.0))
    add_area_light("BasementWarm", (5.8, -1.2, 2.1), (0, 0, 0), 420.0, 2.5, (1.0, 0.76, 0.42))
    add_area_light("DrawingWarm", (4.8, 2.2, 4.3), (0, 0, 0), 320.0, 2.5, (1.0, 0.82, 0.52))
    add_camera(loc=(-8.0, -16.8, 11.8), rot_deg=(54.5, 0.0, -21.0), lens=30.0)


# ==============================================================================
# SCENE 1: 3D BASEMENT TABLEAU (RASPUTIN VS. PRINCE YUSUPOV, CYANIDE WINE)
# ==============================================================================
elif SCENE_ID == 1:
    setup_world((0.015, 0.013, 0.018), 1.0)

    # Checkered marble floor + crimson-and-gold Russian carpet in center
    make_curia_carpet_and_border_floor()

    mat_vault = make_stone_mat("VaultStone", (0.46, 0.42, 0.37), (0.30, 0.27, 0.23), rough=0.52, scale=6.0)
    mat_col = make_stone_mat("ColMarble", (0.84, 0.80, 0.73), (0.70, 0.65, 0.58), rough=0.32, scale=4.0)
    mat_walnut = make_stone_mat("Walnut", (0.24, 0.14, 0.08), (0.15, 0.08, 0.04), rough=0.32, scale=8.0)
    mat_gold = make_mat("GoldBrass", (0.90, 0.72, 0.28), rough=0.22, metal=0.88)
    mat_crystal = make_mat("RubyWine", (0.65, 0.06, 0.10), rough=0.12, metal=0.1, emit_col=(0.55, 0.04, 0.08), emit_str=0.35)
    mat_rasputin = make_stone_mat("RasputinSculpt", (0.88, 0.84, 0.76), (0.74, 0.69, 0.61), rough=0.34, scale=5.0)
    mat_sash_red = make_mat("CrimsonSash", (0.72, 0.09, 0.11), rough=0.45, emit_col=(0.55, 0.05, 0.07), emit_str=0.25)
    mat_yusupov = make_stone_mat("YusupovSculpt", (0.82, 0.80, 0.76), (0.68, 0.66, 0.62), rough=0.36, scale=5.0)

    # Basement Walls & Vaulted Arches
    add_box("RearWall", (0.0, 5.8, 3.2), (14.0, 0.5, 6.6), mat_vault)
    add_box("LeftWall", (-6.2, 0.0, 3.2), (0.5, 12.0, 6.6), mat_vault)
    add_box("RightWall", (6.2, 0.0, 3.2), (0.5, 12.0, 6.6), mat_vault)

    # Vaulted Stone Ribs across the ceiling
    for vy in [-2.2, 1.2, 4.6]:
        add_box(f"VaultRibL_{vy}", (-4.8, vy, 2.8), (0.65, 0.65, 5.6), mat_vault)
        add_box(f"VaultRibR_{vy}", (4.8, vy, 2.8), (0.65, 0.65, 5.6), mat_vault)
        add_box(f"VaultArchTop_{vy}", (0.0, vy, 5.4), (10.2, 0.60, 0.55), mat_vault)

    # Rear Heavy Cellar Doors & Corinthian Pilasters
    door_proto = load_blend_asset("bk_classic_door.blend", "DoorProto", target_height=3.8, mat=mat_walnut)
    if door_proto:
        door_proto.location = (0.0, 5.45, 0.0)

    col_proto = load_blend_asset("bk_column_corinthian.blend", "ColProto", target_height=5.2, mat=mat_col)
    if col_proto:
        col_proto.hide_render = True
        for cx in [-3.8, -1.9, 1.9, 3.8]:
            instance_obj(col_proto, f"BgCol_{cx}", (cx, 5.2, 0.0))

    # Upper Balcony / Staircase Landing at Rear where 3 Co-Conspirators Watch
    add_box("UpperBalcony", (0.0, 4.6, 2.65), (7.6, 1.6, 0.22), mat_vault)
    con_proto = load_blend_asset("bk_decor_man.blend", "ConProto", target_height=1.78, mat=mat_yusupov)
    if con_proto:
        con_proto.hide_render = True
        for idx_c, cx in enumerate([-2.4, 0.0, 2.4]):
            instance_obj(con_proto, f"UpperConspirator_{idx_c}", (cx, 4.5, 2.76), rot=(0, 0, math.radians(180)))

    # Centerpiece Poisoned Banquet Table + Chairs + Wine Bottle + Goblets + Candelabra
    tbl_proto = load_blend_asset("bk_table_round.blend", "TableCenter", target_height=0.84, mat=mat_walnut)
    if tbl_proto:
        tbl_proto.location = (0.2, 0.4, 0.0)
        tbl_proto.scale = (1.55, 1.55, 1.08)

    # Silver platter of cyanide pastries
    add_cyl("SilverPlatter", (0.05, 0.35, 0.92), 0.24, 0.03, mat_gold, verts=32)
    for px, py in [(-0.04, 0.32), (0.08, 0.30), (0.02, 0.42)]:
        add_cyl(f"Pastry_{px}", (px, py, 0.96), 0.055, 0.06, mat_sash_red, verts=20)

    bot_proto = load_blend_asset("bk_wine_bottle.blend", "WineBot", target_height=0.38, mat=mat_crystal)
    if bot_proto:
        bot_proto.location = (0.38, 0.52, 0.90)

    gob_proto = load_blend_asset("bk_goblet.blend", "GobletProto", target_height=0.24, mat=mat_gold)
    if gob_proto:
        gob_proto.hide_render = True
        instance_obj(gob_proto, "GobletRasputin", (-0.28, 0.32, 0.90))
        instance_obj(gob_proto, "GobletYusupov", (0.52, 0.28, 0.90))

    cand_proto = load_blend_asset("bk_candelabra.blend", "Candelabra", target_height=0.48, mat=mat_gold)
    if cand_proto:
        cand_proto.location = (0.20, 0.65, 0.90)

    # Grigori Rasputin (Left of Table, Bearded Statue with Crimson Sash Accent)
    ras_proto = load_blend_asset("bk_bearded_statue.blend", "RasputinMain", target_height=1.92, mat=mat_rasputin)
    if ras_proto:
        ras_proto.location = (-0.95, 0.45, 0.0)
        ras_proto.rotation_euler = (0.0, 0.0, math.radians(52))

    # Prince Felix Yusupov (Right of Table, Seated on Ornate Antique Chair facing Rasputin)
    chair_proto = load_blend_asset("bk_antique_chair.blend", "ChairProto", target_height=0.92, mat=mat_walnut)
    if chair_proto:
        chair_proto.hide_render = True
        instance_obj(chair_proto, "YusupovChair", (1.35, 0.40, 0.0), rot=(0, 0, math.radians(-65)))
        instance_obj(chair_proto, "SideChairL", (-2.6, 1.4, 0.0), rot=(0, 0, math.radians(35)))
        instance_obj(chair_proto, "SideChairR", (2.8, 1.5, 0.0), rot=(0, 0, math.radians(-35)))

    yus_proto = load_blend_asset("bk_male_sitting.blend", "YusupovMain", target_height=1.42, mat=mat_yusupov)
    if yus_proto:
        yus_proto.location = (1.25, 0.38, 0.04)
        yus_proto.rotation_euler = (0.0, 0.0, math.radians(-58))

    # Dramatic Warm Candelabra Key + Cold Moonlight Rim Lighting
    add_area_light("TableWarmKey", (-0.4, -1.8, 2.8), (48, 0, -10), 420.0, 2.5, (1.0, 0.80, 0.52))
    add_area_light("MoonRimLeft", (-4.8, 2.5, 4.2), (55, 0, -55), 380.0, 3.0, (0.65, 0.78, 1.0))
    add_area_light("BackVaultFill", (0.0, 4.2, 4.5), (-35, 0, 0), 260.0, 4.0, (0.95, 0.72, 0.45))
    add_camera(loc=(-0.35, -4.65, 2.15), rot_deg=(74.5, 0.0, -4.0), lens=29.0)


# ==============================================================================
# SCENE 2: SLICED 3D MARBLE BUST OF RASPUTIN + BENTO NOIR DOSSIER
# ==============================================================================
elif SCENE_ID == 2:
    setup_world((0.022, 0.012, 0.015), 1.0)

    mat_marble = make_stone_mat("BustMarble", (0.90, 0.87, 0.81), (0.74, 0.70, 0.64), rough=0.26, scale=5.0)
    mat_crimson_core = make_mat("CrimsonCore", (0.95, 0.10, 0.14), rough=0.15, emit_col=(0.98, 0.12, 0.16), emit_str=4.8)
    mat_plinth = make_stone_mat("DarkPlinth", (0.14, 0.14, 0.17), (0.08, 0.08, 0.10), rough=0.35, scale=6.0)
    mat_silver_halo = make_mat("SilverHalo", (0.72, 0.74, 0.78), rough=0.28, metal=0.82)

    # Glowing Crimson Podium Disc + Dark Pedestal (shifted slightly right so Left Bento Card has clean room)
    bx_center = 0.35
    add_cyl("PodiumBase", (bx_center, 0.0, -0.06), 1.35, 0.12, mat_plinth, verts=64)
    add_cyl("PodiumGlowRing", (bx_center, 0.0, 0.01), 1.12, 0.03, mat_crimson_core, verts=64)

    # Imperial Medallion / Halo Disc behind the bust
    add_cyl("ImperialMedallion", (bx_center, 0.65, 0.72), 0.78, 0.05, mat_silver_halo, verts=64, rot=(math.radians(90), 0, 0))

    # Load Bearded Rasputin Bust and Bisect at 38° Diagonal Angle
    bust_orig = load_blend_asset("bk_rasputin_bust.blend", "RasputinBustOrig", target_height=1.18, mat=mat_marble)
    if bust_orig:
        bust_orig.hide_render = True
        plane_co = mathutils.Vector((0.0, 0.0, 0.58))
        plane_no = mathutils.Vector((0.62, 0.0, 0.78)).normalized()

        # Lower-Left Half
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
        b_low.location = (bx_center - 0.06, 0.0, 0.02)
        b_low.rotation_euler = (0.0, 0.0, math.radians(-22.0))

        # Upper-Right Exploded Half
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
        b_high.location = (bx_center + 0.14, 0.0, 0.18)
        b_high.rotation_euler = (0.0, math.radians(6.0), math.radians(-22.0))

        # Glowing Crimson Laser Slice Plane + Interior Core
        add_box(
            "CrimsonLaserStreak",
            (bx_center + 0.04, -0.05, 0.66),
            (1.65, 0.018, 0.022),
            mat_crimson_core,
            rot=(0.0, math.radians(-38.0), 0.0),
        )
        add_cyl(
            "CrimsonCoreDisc",
            (bx_center + 0.04, 0.0, 0.66),
            0.26,
            0.05,
            mat_crimson_core,
            verts=40,
            rot=(0.0, math.radians(38.0), 0.0),
        )

    add_area_light("BustKey", (-2.4, -2.8, 2.2), (55, 0, -35), 260.0, 2.2, (1.0, 0.95, 0.90))
    add_area_light("BustRimRed", (2.5, 1.5, 1.8), (60, 0, 130), 340.0, 2.0, (1.0, 0.18, 0.22))
    add_camera(loc=(0.0, -3.55, 0.68), rot_deg=(87.5, 0.0, 0.0), lens=36.0)


# ==============================================================================
# SCENE 3: 3D TILTED TOPOGRAPHIC RELIEF MAP OF RUSSIA & EASTERN FRONT (1916)
# ==============================================================================
elif SCENE_ID == 3:
    setup_world((0.010, 0.012, 0.018), 1.0)

    mat_grid = make_mat("GridWire", (0.75, 0.80, 0.88), rough=0.2, emit_col=(0.75, 0.80, 0.88), emit_str=0.85)
    mat_russia_blue = make_mat("RussiaBlue", (0.14, 0.34, 0.62), rough=0.35, emit_col=(0.16, 0.42, 0.78), emit_str=0.95)
    mat_front_red = make_mat("FrontCrimson", (0.78, 0.12, 0.15), rough=0.32, emit_col=(0.88, 0.14, 0.18), emit_str=1.25)
    mat_neutral_dark = make_mat("NeutralDark", (0.16, 0.18, 0.22), rough=0.45, emit_col=(0.18, 0.20, 0.25), emit_str=0.45)
    mat_gold_pin = make_mat("GoldPin", (1.0, 0.82, 0.28), rough=0.15, emit_col=(1.0, 0.82, 0.28), emit_str=3.5)
    mat_arrow_red = make_mat("ArrowRed", (0.95, 0.18, 0.20), rough=0.2, emit_col=(0.95, 0.18, 0.20), emit_str=2.6)

    # 1. Explicit 3D Perspective Grid Lines in Dark Void (Z = 0.0)
    for gx in range(-12, 13, 1):
        add_box(f"GridX_{gx}", (gx * 0.75, 0.0, 0.0), (0.016, 15.0, 0.008), mat_grid)
    for gy in range(-10, 11, 1):
        add_box(f"GridY_{gy}", (0.0, gy * 0.75, 0.0), (18.0, 0.016, 0.008), mat_grid)

    # 2. Load Real Geographic Borders of Russia & Eastern Europe (russia_eastern_front_50m.geojson)
    geo_path = os.path.join(ASSETS_DIR, "russia_eastern_front_50m.geojson")
    if os.path.exists(geo_path):
        with open(geo_path, "r") as f:
            gdata = json.load(f)

        # Map projection: lon 14..46 -> X -5.5..+6.5, lat 45..63 -> Y -4.5..+4.5
        def proj(lon, lat):
            x = (lon - 28.0) * 0.36 + 0.8
            y = (lat - 54.5) * 0.48
            return x, y

        russian_heartland = {"Russia", "Finland", "Estonia", "Latvia", "Belarus", "Ukraine"}
        eastern_front = {"Germany", "Poland", "Lithuania", "Austria", "Hungary", "Romania"}

        for feat in gdata.get("features", []):
            cname = feat.get("properties", {}).get("NAME", "")
            geom = feat.get("geometry", {})
            gtype = geom.get("type")
            coords = geom.get("coordinates", [])
            polys = coords if gtype == "MultiPolygon" else [coords]

            if cname in russian_heartland:
                cmat = mat_russia_blue
                z_off = 0.08
                ext = 0.14
            elif cname in eastern_front:
                cmat = mat_front_red
                z_off = 0.11
                ext = 0.16
            else:
                cmat = mat_neutral_dark
                z_off = 0.05
                ext = 0.09

            curve_data = bpy.data.curves.new(f"Map_{cname}", type="CURVE")
            curve_data.dimensions = "2D"
            curve_data.fill_mode = "BOTH"
            curve_data.extrude = ext
            curve_data.bevel_depth = 0.015

            has_pts = False
            for poly in polys:
                if not poly:
                    continue
                ring = poly[0]
                pts = []
                # Skip tiny far-east islands outside European Russia
                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]
                if max(lons) < 11.0 or min(lons) > 48.0 or max(lats) < 43.0 or min(lats) > 66.0:
                    continue
                for pt in ring:
                    lon = min(max(pt[0], 11.0), 46.5)
                    lat = min(max(pt[1], 43.5), 64.5)
                    pts.append(proj(lon, lat))
                if len(pts) >= 4:
                    spline = curve_data.splines.new("POLY")
                    spline.points.add(len(pts) - 1)
                    for idx_p, (px, py) in enumerate(pts):
                        spline.points[idx_p].co = (px, py, 0.0, 1.0)
                    spline.use_cyclic_u = True
                    has_pts = True

            if has_pts:
                cobj = bpy.data.objects.new(f"Country_{cname}", curve_data)
                cobj.rotation_mode = "XYZ"
                cobj.location = (0.0, 0.0, z_off)
                cobj.data.materials.append(cmat)
                bpy.context.collection.objects.link(cobj)

        # Glowing Beacon at Petrograd (59.93°N, 30.33°E)
        px, py = proj(30.33, 59.93)
        add_cyl("PetrogradPinBase", (px, py, 0.26), 0.28, 0.08, mat_gold_pin, verts=32)
        add_cyl("PetrogradBeacon", (px, py, 0.65), 0.06, 0.80, mat_gold_pin, verts=20)

        # Glowing Frontline Converging Arrows toward Petrograd
        for sx, sy, rot_z in [(-1.2, 0.2, -32), (-0.4, -1.6, -15), (2.4, -0.8, 22)]:
            add_box(
                f"PlotArrow_{sx}",
                ((sx + px) * 0.5, (sy + py) * 0.5, 0.28),
                (0.08, math.hypot(px - sx, py - sy) * 0.75, 0.04),
                mat_arrow_red,
                rot=(0, 0, math.radians(rot_z)),
            )

    add_area_light("MapKey", (0.0, -6.0, 8.0), (35, 0, 0), 650.0, 6.0, (0.85, 0.90, 1.0))
    add_camera(loc=(0.2, -7.8, 6.8), rot_deg=(46.0, 0.0, 0.0), lens=32.0)


# ==============================================================================
# SCENE 4: 90° TOP-DOWN FORENSIC CRIME SCENE (FALLEN RASPUTIN + REVOLVER)
# ==============================================================================
elif SCENE_ID == 4:
    setup_world((0.012, 0.013, 0.018), 1.0)

    # Checkered marble courtyard/basement floor + crimson carpet runner
    make_curia_carpet_and_border_floor()

    mat_blood = make_mat("ForensicBlood", (0.52, 0.02, 0.03), rough=0.08, metal=0.05, emit_col=(0.42, 0.01, 0.02), emit_str=0.25)
    mat_rasputin_fallen = make_stone_mat("FallenRasputin", (0.88, 0.84, 0.78), (0.72, 0.68, 0.62), rough=0.32, scale=5.0)
    mat_gun_steel = make_mat("Gunmetal", (0.72, 0.74, 0.78), rough=0.22, metal=0.88, emit_col=(0.72, 0.74, 0.78), emit_str=0.25)
    mat_gold_brass = make_mat("BrassShell", (0.95, 0.78, 0.30), rough=0.18, metal=0.90, emit_col=(0.95, 0.78, 0.30), emit_str=0.45)
    mat_walnut = make_stone_mat("ChairWalnut", (0.28, 0.16, 0.09), (0.18, 0.10, 0.05), rough=0.32, scale=6.0)
    mat_conspirator = make_stone_mat("ConspiratorStone", (0.78, 0.76, 0.72), (0.62, 0.60, 0.56), rough=0.38, scale=5.0)

    # 1. Stepped-Z Glossy Crimson Blood Pool (Zero Coplanar Z-Fighting!)
    lobes = [
        (0.0, 0.0, 0.95, 0.75, 0.006),
        (-0.42, 0.18, 0.62, 0.48, 0.008),
        (0.38, -0.22, 0.58, 0.44, 0.010),
        (0.15, 0.42, 0.45, 0.36, 0.012),
    ]
    for idx_l, (lx, ly, rx, ry, lz) in enumerate(lobes):
        c = add_cyl(f"BloodLobe_{idx_l}", (lx, ly, lz), 1.0, 0.003, mat_blood, verts=48)
        c.scale = (rx, ry, 1.0)

    # 2. Fallen Grigori Rasputin Lying Horizontally in Center of Blood Pool
    ras_fallen = load_blend_asset("bk_bearded_statue.blend", "FallenRasputinMesh", target_height=1.88, mat=mat_rasputin_fallen)
    if ras_fallen:
        # Shift Z by -0.94m so rotation is around his waist/torso center
        for v in ras_fallen.data.vertices:
            v.co.z -= 0.94
        ras_fallen.data.update()
        ras_fallen.rotation_mode = "XYZ"
        ras_fallen.location = (-0.08, 0.06, 0.24)
        ras_fallen.rotation_euler = (math.radians(88.0), math.radians(12.0), math.radians(52.0))

    # 3. Dropped Webley .455 Revolver + 3 Spent Brass Shell Casings beside the Blood Pool
    rev_obj = load_blend_asset("bk_revolver.blend", "CrimeRevolver", target_height=0.52, mat=mat_gun_steel)
    if rev_obj:
        rev_obj.location = (0.72, -0.28, 0.02)
        rev_obj.rotation_euler = (0.0, 0.0, math.radians(-34.0))

    for idx_s, (sx, sy) in enumerate([(0.55, -0.45), (0.88, -0.18), (0.64, -0.62)]):
        add_cyl(f"ShellCasing_{idx_s}", (sx, sy, 0.018), 0.022, 0.065, mat_gold_brass, verts=16, rot=(math.radians(90), 0, math.radians(idx_s * 47)))

    # 4. Overturned Antique Chair & Spilled Wine Goblet
    chair_ov = load_blend_asset("bk_antique_chair.blend", "OverturnedChair", target_height=0.95, mat=mat_walnut)
    if chair_ov:
        for v in chair_ov.data.vertices:
            v.co.z -= 0.45
        chair_ov.data.update()
        chair_ov.location = (-1.28, 0.62, 0.32)
        chair_ov.rotation_euler = (math.radians(82.0), math.radians(-18.0), math.radians(38.0))

    gob_spilled = load_blend_asset("bk_goblet.blend", "SpilledGoblet", target_height=0.26, mat=mat_gold_brass)
    if gob_spilled:
        gob_spilled.location = (-0.75, -0.48, 0.05)
        gob_spilled.rotation_euler = (math.radians(86.0), 0.0, math.radians(115.0))

    # 5. Neoclassical Pedestal Base + Ring of 4 Conspirators Casting Long Shadows
    add_cyl("CourtyardPillarBase", (0.0, 1.85, 0.35), 0.68, 0.70, mat_conspirator, verts=48)
    add_3d_text("YUSUPOV PALACE", (0.0, 1.85, 0.72), 0.18, mat_gold_brass, rot=(0, 0, 0), extrude=0.02)

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

    add_area_light("CrimeTopSpot", (0.4, -0.5, 5.2), (12, 8, 0), 580.0, 2.8, (1.0, 0.90, 0.76))
    add_area_light("CrimeRimCold", (-3.5, 2.5, 3.8), (45, 0, -40), 320.0, 3.5, (0.68, 0.80, 1.0))
    add_camera(loc=(0.0, -0.25, 5.35), rot_deg=(3.0, 0.0, 0.0), lens=34.0)

scene.render.filepath = OUT_PATH
bpy.ops.render.render(write_still=True)
print(f"Rendered Rasputin Scene {SCENE_ID} to {OUT_PATH}")
