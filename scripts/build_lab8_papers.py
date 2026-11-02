from pathlib import Path
import random
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
PW, PH = 720, 920
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SANS_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
INK = (24, 26, 25, 255)
MUTED = (70, 72, 68, 255)


def key_sheet(filename: str) -> Image.Image:
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
    # Remove green spill from the thin physical edge.
    cap = np.clip(np.maximum(r, b).astype(np.int16) + 12, 0, 255).astype(np.uint8)
    arr[..., 1] = np.minimum(g, cap).astype(np.uint8)
    rgba = np.dstack([arr, alpha])
    ys, xs = np.where(alpha > 8)
    rgba = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return Image.fromarray(rgba, 'RGBA').resize((PW, PH), Image.Resampling.LANCZOS)


paper1 = key_sheet('lab8-paper-a-source.png')
paper2 = key_sheet('lab8-paper-b-source.png')

f_title = ImageFont.truetype(SERIF_BOLD, 25)
f_small = ImageFont.truetype(SANS, 16)
f_value = ImageFont.truetype(SERIF_BOLD, 19)
f_source = ImageFont.truetype(SERIF, 18)
f_body = ImageFont.truetype(SERIF, 24)
f_body_bold = ImageFont.truetype(SERIF_BOLD, 24)

# FIRST SHEET — original MIC chart.
d = ImageDraw.Draw(paper1)
d.text((60, 62), 'JAPAN / HOUSING DATA · 2023', font=f_small, fill=MUTED)
d.text((60, 105), 'Vacant homes by category', font=f_title, fill=INK)
chart_x, chart_y, chart_w, chart_h = 105, 205, 535, 315
for tick in range(6):
    y = chart_y + chart_h - tick * chart_h / 5
    d.line((chart_x, y, chart_x + chart_w, y), fill=(105, 107, 101, 150), width=1)
    d.text((chart_x - 43, y - 9), f'{tick}M', font=f_small, fill=MUTED)
d.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill=MUTED, width=2)
values = [4.436, 3.856, 0.384, 0.326]
labels = ['RENTAL', 'OTHER /\nABANDONED', 'SECOND\nHOMES', 'FOR SALE']
colors = [(121, 35, 46, 255), (59, 88, 98, 255), (106, 77, 91, 255), (83, 102, 91, 255)]
for i, (value, label, color) in enumerate(zip(values, labels, colors)):
    x = chart_x + 30 + i * 132
    bh = max(2, int(round(value / 5 * chart_h)))
    y = chart_y + chart_h - bh
    bar = Image.new('RGBA', (78, bh), color)
    bd = ImageDraw.Draw(bar)
    for k in range(-bh, 78 + bh, 22):
        bd.line((k, bh, k + bh, 0), fill=(230, 230, 220, 38), width=1)
    bd.rectangle((0, 0, 77, bh - 1), outline=(45, 48, 47, 255), width=2)
    paper1.paste(bar, (int(x), int(y)), bar)
    d = ImageDraw.Draw(paper1)
    txt = f'{value:.3f}M'
    tw = d.textlength(txt, font=f_value)
    d.text((x + (78 - tw) / 2, y - 26), txt, font=f_value, fill=INK)
    for j, line in enumerate(label.split('\n')):
        tw = d.textlength(line, font=f_small)
        d.text((x + (78 - tw) / 2, chart_y + chart_h + 12 + j * 20), line, font=f_small, fill=INK)
d = ImageDraw.Draw(paper1)
d.text((60, 625), '9.002M', font=ImageFont.truetype(SERIF_BOLD, 48), fill=INK)
d.text((60, 685), 'TOTAL VACANT HOMES IN JAPAN', font=f_small, fill=MUTED)
d.text((60, 790), 'Source: MIC Statistics Bureau,', font=f_source, fill=INK)
d.text((60, 818), 'Housing and Land Survey, 2023.', font=f_source, fill=INK)
d.text((60, 856), 'Vacant does not necessarily mean abandoned.', font=f_small, fill=MUTED)
paper1.save(PUBLIC / 'lab8-paper1.png')

# SECOND SHEET — original explanatory text and the selected sentence.
d = ImageDraw.Draw(paper2)
d.text((65, 66), 'TOKYO / DATA NOTE · 2026', font=f_small, fill=MUTED)
d.text((65, 112), 'Vacancy is not abandonment.', font=f_title, fill=INK)
body_lines = [
    'Japan counted 9.002 million vacant homes',
    'in 2023; 4.436 million were rentals.',
    'Another 3.856 million were classified as',
    'other or abandoned.',
    'Tokyo had about 898,000 vacant homes.',
]
for i, line in enumerate(body_lines):
    d.text((65, 230 + i * 58), line, font=f_body, fill=INK)

target = 'Tokyo’s vacancy rate was 10.9% in 2023.'
target_x, target_y = 65, 570
target_w = d.textlength(target, font=f_body)
print(f'PAPER_W={PW};PAPER_H={PH};TARGET_X={target_x};TARGET_Y={target_y};TARGET_W={target_w:.2f}')

# Real relighting is baked into the paper pixels: dark ambient elsewhere and a
# strong Gaussian exposure centered on the target line. There is NO white bar or
# white underline overlay. Black ink remains black because RGB is multiplied.
rgb = np.array(paper2.convert('RGB')).astype(np.float32)
yy, xx = np.mgrid[0:PH, 0:PW]
field = 0.52 + 1.58 * np.exp(-((yy - (target_y + 15)) / 190.0) ** 2 - ((xx - 350) / 540.0) ** 2)
lit = np.clip(rgb * field[..., None], 0, 255).astype(np.uint8)
lit_img = Image.fromarray(lit, 'RGB').convert('RGBA')
lit_img.putalpha(paper2.getchannel('A'))
paper2.save(PUBLIC / 'lab8-paper2-clean.png')
lit_img.save(PUBLIC / 'lab8-paper2-lit.png')

stroke = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
sd = ImageDraw.Draw(stroke)
rnd = random.Random(41)
x0, x1 = target_x - 8, target_x + target_w + 14
y0, y1 = target_y - 5, target_y + 36
points_top = [(x0 + (x1 - x0) * i / 24, y0 + rnd.uniform(-1.8, 1.8)) for i in range(25)]
points_bottom = [(x0 + (x1 - x0) * i / 24, y1 + rnd.uniform(-2.0, 2.0)) for i in reversed(range(25))]
sd.polygon(points_top + points_bottom, fill=(249, 237, 20, 215))
stroke = stroke.filter(ImageFilter.GaussianBlur(0.4))
stroke.save(PUBLIC / 'lab8-highlight-stroke.png')

highlighted = Image.alpha_composite(lit_img, stroke)
hd = ImageDraw.Draw(highlighted)
hd.text((target_x, target_y), target, font=f_body, fill=INK)
content = highlighted.copy()
content.putalpha(stroke.getchannel('A'))
content.save(PUBLIC / 'lab8-highlight-content.png')

# The desk is an original text-to-image asset, never the user's reference.
desk = Image.open(PUBLIC / 'lab8-desk-source.png').convert('RGB').resize((1920, 1080), Image.Resampling.LANCZOS)
desk.save(PUBLIC / 'lab8-desk.webp', quality=95)
