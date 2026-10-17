import os, sys, json, cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

F_START = int(sys.argv[1])
F_END   = int(sys.argv[2])
OUT_DIR = sys.argv[3]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BEBAS = os.path.join(ROOT, "fonts", "BebasNeue-Regular.ttf")
f_main = ImageFont.truetype(FONT_BEBAS, 44)

with open(os.path.join(OUT_DIR, f"coords_{F_START}_{F_END}.json")) as fp:
    coords = json.load(fp)

def draw_cable_0012_label(img_bgr, center_xy, lines_list, alpha=0.60):
    if alpha <= 0.02: return img_bgr
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    cx = max(110, min(1810, int(center_xy[0])))
    cy = max(65,  min(260,  int(center_xy[1])))
    line_h = 42
    total_h = len(lines_list) * line_h
    y0 = cy - total_h // 2
    for idx, line in enumerate(lines_list):
        tb = draw.textbbox((0, 0), line, font=f_main)
        w = tb[2] - tb[0]
        draw.text((cx - w // 2, y0 + idx * line_h), line, font=f_main, fill=(228, 234, 242))
    res = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return cv2.addWeighted(res, alpha, img_bgr, 1.0 - alpha, 0)

def env_alpha(f, f0, f1, max_a=0.60):
    if f < f0 or f > f1: return 0.0
    if f < f0 + 15: return max_a * ((f - f0) / 15.0)
    if f > f1 - 15: return max_a * ((f1 - f) / 15.0)
    return max_a

for f in range(F_START, F_END):
    raw_p = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
    img = cv2.imread(raw_p)
    c = coords.get(str(f), {})
    if f < 150:
        sp_xy = c.get("spike", [220, 480])
        by_xy = c.get("bypass", [820, 240])
        cb_xy = c.get("combustor", [1320, 480])
        img = draw_cable_0012_label(img, (sp_xy[0], 195), ["INLET", "SPIKE"], env_alpha(f, 8, 140))
        img = draw_cable_0012_label(img, (by_xy[0], 115), ["BLEED BYPASS", "DUCTS"], env_alpha(f, 24, 142))
        img = draw_cable_0012_label(img, (cb_xy[0] + 120, 125), ["COMBUSTOR", "& TURBINE"], env_alpha(f, 42, 144))
    cv2.imwrite(os.path.join(OUT_DIR, f"final_{f:04d}.png"), img)
    os.remove(raw_p)
