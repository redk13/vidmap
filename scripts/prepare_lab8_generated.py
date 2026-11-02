from pathlib import Path
import random
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
PW, PH = 720, 920


def key_generated_sheet(filename: str):
    """Only cut out the generated paper; never draw or typeset the paper."""
    img = Image.open(PUBLIC / filename).convert('RGB')
    arr = np.array(img)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    green = (g.astype(np.int16) - np.maximum(r, b).astype(np.int16) > 45) & (g > 105)
    mask = np.where(~green, 255, 0).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(mask)
    cv2.drawContours(mask, [largest], -1, 255, -1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    alpha = cv2.GaussianBlur(mask, (3, 3), 0.65)
    cap = np.clip(np.maximum(r, b).astype(np.int16) + 12, 0, 255).astype(np.uint8)
    arr[..., 1] = np.minimum(g, cap).astype(np.uint8)
    rgba = np.dstack([arr, alpha])
    ys, xs = np.where(alpha > 8)
    left, top, right, bottom = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    return Image.fromarray(rgba[top:bottom, left:right], 'RGBA'), (left, top)


def fit_without_distortion(sheet: Image.Image):
    scale = min(PW / sheet.width, PH / sheet.height)
    size = (round(sheet.width * scale), round(sheet.height * scale))
    resized = sheet.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    offset = ((PW - size[0]) // 2, (PH - size[1]) // 2)
    canvas.alpha_composite(resized, offset)
    return canvas, offset, scale


paper1_raw, _ = key_generated_sheet('lab8-full-paper-a-source.png')
paper1, _, _ = fit_without_distortion(paper1_raw)
paper1.save(PUBLIC / 'lab8-paper1.png')

paper2_raw, crop_origin = key_generated_sheet('lab8-full-paper-b-source.png')
paper2, offset, scale = fit_without_distortion(paper2_raw)

# Measured ink bounds of the generated sentence in the original generated image.
# Mapping them through the cutout transform keeps the effect on the printed ink.
sx0, sy0, sx1, sy1 = 163, 719, 539, 737
target_x = offset[0] + (sx0 - crop_origin[0]) * scale
target_y = offset[1] + (sy0 - crop_origin[1]) * scale
target_w = (sx1 - sx0 + 1) * scale
target_bottom = offset[1] + (sy1 - crop_origin[1]) * scale
print(f'TARGET_X={target_x:.2f};TARGET_Y={target_y:.2f};TARGET_W={target_w:.2f};TARGET_BOTTOM={target_bottom:.2f}')

# Relight the existing generated pixels only. No text, page or chart is drawn.
rgb = np.array(paper2.convert('RGB')).astype(np.float32)
yy, xx = np.mgrid[0:PH, 0:PW]
field = 0.52 + 1.58 * np.exp(-((yy - (target_y + 10)) / 190.0) ** 2 - ((xx - (target_x + target_w / 2)) / 540.0) ** 2)
lit = np.clip(rgb * field[..., None], 0, 255).astype(np.uint8)
lit_img = Image.fromarray(lit, 'RGB').convert('RGBA')
lit_img.putalpha(paper2.getchannel('A'))
paper2.save(PUBLIC / 'lab8-paper2-clean.png')
lit_img.save(PUBLIC / 'lab8-paper2-lit.png')

# A separate irregular yellow marker stroke; the original generated dark ink is
# restored over it rather than retypeset.
stroke = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
sd = ImageDraw.Draw(stroke)
rnd = random.Random(41)
x0, x1 = target_x - 8, target_x + target_w + 12
y0, y1 = target_y - 5, target_bottom + 6
points_top = [(x0 + (x1 - x0) * i / 24, y0 + rnd.uniform(-1.8, 1.8)) for i in range(25)]
points_bottom = [(x0 + (x1 - x0) * i / 24, y1 + rnd.uniform(-2.0, 2.0)) for i in reversed(range(25))]
sd.polygon(points_top + points_bottom, fill=(249, 237, 20, 215))
stroke = stroke.filter(ImageFilter.GaussianBlur(0.4))
stroke.save(PUBLIC / 'lab8-highlight-stroke.png')

highlighted = Image.alpha_composite(lit_img, stroke)
gray = np.array(lit_img.convert('L')).astype(np.float32)
stroke_alpha = np.array(stroke.getchannel('A')).astype(np.float32) / 255.0
ink_alpha = np.clip((155.0 - gray) * 2.4, 0, 255) * stroke_alpha
ink = lit_img.copy()
ink.putalpha(Image.fromarray(ink_alpha.astype(np.uint8), 'L'))
highlighted = Image.alpha_composite(highlighted, ink)
content = highlighted.copy()
content.putalpha(stroke.getchannel('A'))
content.save(PUBLIC / 'lab8-highlight-content.png')
