import os, sys, json, cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

F_START = int(sys.argv[1])
F_END   = int(sys.argv[2])
OUT_DIR = sys.argv[3]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BEBAS  = os.path.join(ROOT, "fonts", "BebasNeue-Regular.ttf")
FONT_OSWALD = os.path.join(ROOT, "fonts", "Oswald-Bold.ttf")
f_main = ImageFont.truetype(FONT_BEBAS, 62)
f_sub  = ImageFont.truetype(FONT_OSWALD, 28)

with open(os.path.join(OUT_DIR, f"coords_{F_START}_{F_END}.json")) as fp:
    coords = json.load(fp)

def add_label(img_bgr, target_xy, offset_xy, title, sub, alpha=1.0):
    if alpha <= 0.02: return img_bgr
    base = img_bgr.copy()
    tx, ty = int(target_xy[0]), int(target_xy[1])
    lx, ly = int(tx + offset_xy[0]), int(ty + offset_xy[1])
    lx = max(45, min(1520, lx))
    ly = max(75, min(980, ly))

    cv2.line(base, (tx, ty), (lx, ly), (15, 18, 24), 5, cv2.LINE_AA)
    cv2.line(base, (tx, ty), (lx, ly), (240, 244, 248), 3, cv2.LINE_AA)
    cv2.circle(base, (tx, ty), 8, (15, 18, 24), -1, cv2.LINE_AA)
    cv2.circle(base, (tx, ty), 5, (255, 255, 255), -1, cv2.LINE_AA)

    pil = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    draw.text((lx + 14, ly - 36), title, font=f_main, fill=(10, 12, 16))
    draw.text((lx + 12, ly - 38), title, font=f_main, fill=(248, 250, 252))
    if sub:
        draw.text((lx + 14, ly + 26), sub, font=f_sub, fill=(10, 12, 16))
        draw.text((lx + 12, ly + 24), sub, font=f_sub, fill=(255, 190, 90))
    labeled = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return cv2.addWeighted(labeled, alpha, img_bgr, 1.0 - alpha, 0)

def env_alpha(f, f0, f1):
    if f < f0 or f > f1: return 0.0
    if f < f0 + 12: return (f - f0) / 12.0
    if f > f1 - 12: return (f1 - f) / 12.0
    return 1.0

for f in range(F_START, F_END):
    raw_p = os.path.join(OUT_DIR, f"raw_{f:04d}.png")
    img = cv2.imread(raw_p)
    c = coords.get(str(f), {})
    if f < 150:
        img = add_label(img, c.get("spike", [260, 620]), (65, -195), "INLET SPIKE", "26-INCH TRANSLATION", env_alpha(f, 10, 140))
        img = add_label(img, c.get("bypass", [820, 330]), (60, -140), "6 BYPASS DUCTS", "COMPRESSOR BLEED AIR", env_alpha(f, 25, 142))
        img = add_label(img, c.get("combustor", [1140, 615]), (65, 210), "COMBUSTOR & TURBINE", "PRATT & WHITNEY J58", env_alpha(f, 40, 144))
    elif f < 300:
        lf = f - 150
        img = add_label(img, c.get("chine", [810, 690]), (80, 170), "TITANIUM CHINE", "85% Ti-13V-11Cr-3Al", env_alpha(lf, 10, 140))
        img = add_label(img, c.get("nacelle", [1290, 510]), (65, -185), "J58 NACELLE", "INWARD-CANTED RUDDERS", env_alpha(lf, 25, 140))
    else:
        lf = f - 300
        img = add_label(img, c.get("mach", [665, 435]), (-380, -125), "MACH METER", "CRUISE MACH 3.2", env_alpha(lf, 10, 140))
        img = add_label(img, c.get("egt", [1430, 785]), (65, -165), "DUAL EGT GAUGES", "950°C LIMIT", env_alpha(lf, 25, 140))
    cv2.imwrite(os.path.join(OUT_DIR, f"final_{f:04d}.png"), img)
    os.remove(raw_p)
