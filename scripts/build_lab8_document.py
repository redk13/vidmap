from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
W, H = 1920, 1080
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

# AI reference-guided open book: dark printed page behind + a real-looking loose
# sheet on top. Crop to 16:9 while preserving the reference's close framing.
book = Image.open(PUBLIC / 'lab8-book-layers.png').convert('RGB')
book = book.crop((150, 0, 1373, 688)).resize((W, H), Image.Resampling.LANCZOS)
canvas = book.convert('RGBA')

ink = (25, 27, 26, 255)
muted = (68, 70, 67, 255)
grid = (112, 113, 107, 145)
red = (121, 35, 46, 255)
slate = (59, 88, 98, 255)

f_chart = ImageFont.truetype(SERIF_BOLD, 25)
f_small = ImageFont.truetype(SANS, 17)
f_value = ImageFont.truetype(SERIF_BOLD, 21)
f_source = ImageFont.truetype(SERIF, 21)
f_body = ImageFont.truetype(SERIF, 30)

d = ImageDraw.Draw(canvas)
d.text((565, 110), 'Figure 1. Japan’s vacant homes by category, 2023', font=f_chart, fill=ink)

chart_x, chart_y, chart_w, chart_h = 620, 165, 1010, 235
for tick in range(6):
    y = chart_y + chart_h - tick * chart_h / 5
    d.line((chart_x, y, chart_x + chart_w, y), fill=grid, width=1)
    d.text((chart_x - 52, y - 10), f'{tick}M', font=f_small, fill=muted)
d.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill=muted, width=2)

values = [4.436, 3.856, 0.384, 0.326]
labels = ['RENTAL', 'OTHER /\nABANDONED', 'SECOND\nHOMES', 'FOR SALE']
colors = [red, slate, (106, 77, 91, 255), (83, 102, 91, 255)]
bar_w = 105
for i, (value, label, color) in enumerate(zip(values, labels, colors)):
    x = chart_x + 62 + i * 238
    height = value / 5 * chart_h
    bar_h = max(2, int(round(height)))
    y = int(chart_y + chart_h - bar_h)
    bar = Image.new('RGBA', (bar_w, bar_h), color)
    bd = ImageDraw.Draw(bar)
    for k in range(-bar_h, bar_w + bar_h, 24):
        bd.line((k, bar_h, k + bar_h, 0), fill=(230, 230, 220, 38), width=1)
    bd.rectangle((0, 0, bar_w - 1, bar_h - 1), outline=(45, 48, 47, 255), width=2)
    canvas.paste(bar, (int(x), y), bar)
    d = ImageDraw.Draw(canvas)
    value_text = f'{value:.3f}M'
    tw = d.textlength(value_text, font=f_value)
    d.text((x + (bar_w - tw) / 2, y - 29), value_text, font=f_value, fill=ink)
    for j, line in enumerate(label.split('\n')):
        tw = d.textlength(line, font=f_small)
        d.text((x + (bar_w - tw) / 2, chart_y + chart_h + 12 + j * 21), line, font=f_small, fill=ink)

d = ImageDraw.Draw(canvas)
d.text((620, 468), 'Source: MIC Statistics Bureau, Housing and Land Survey, 2023.', font=f_source, fill=ink)
d.text((620, 502), 'Values in millions. Vacant does not necessarily mean abandoned.', font=f_small, fill=muted)

lines = [
    'Japan counted 9.002 million vacant homes in 2023.',
    'Vacant does not mean abandoned: 4.436 million were rentals.',
    'Another 3.856 million were classified as other or abandoned.',
]
text_x = 565
for i, line in enumerate(lines):
    d.text((text_x, 580 + i * 64), line, font=f_body, fill=ink)

target = 'Tokyo had 898,000 vacant homes — 10.9% of its housing stock.'
target_y = 780
target_w = d.textlength(target, font=f_body)
print(f'TARGET_X={text_x};TARGET_Y={target_y};TARGET_W={target_w:.2f};TARGET_H=48')

stroke = Image.new('RGBA', (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(stroke)
rnd = random.Random(23)
x0, x1 = text_x - 10, text_x + target_w + 16
y0, y1 = target_y - 6, target_y + 44
top = [(x0 + (x1 - x0) * i / 30, y0 + rnd.uniform(-2.1, 2.1)) for i in range(31)]
bottom = [(x0 + (x1 - x0) * i / 30, y1 + rnd.uniform(-2.3, 2.3)) for i in reversed(range(31))]
od.polygon(top + bottom, fill=(249, 237, 20, 210))
stroke = stroke.filter(ImageFilter.GaussianBlur(0.45))
# Keep a clean but slightly irregular highlighter edge, matching a printed page.
stroke.save(PUBLIC / 'lab8-highlight-stroke.png')


def make_image(highlighted: bool) -> Image.Image:
    im = canvas.copy()
    if highlighted:
        im = Image.alpha_composite(im, stroke)
    dd = ImageDraw.Draw(im)
    dd.text((text_x, target_y), target, font=f_body, fill=ink)
    return im

clean = make_image(False)
highlighted = make_image(True)
clean.convert('RGB').save(PUBLIC / 'lab8-document-clean.webp', lossless=True, quality=100)
highlighted.convert('RGB').save(PUBLIC / 'lab8-document-highlight.webp', lossless=True, quality=100)
content = highlighted.convert('RGBA')
content.putalpha(stroke.getchannel('A'))
content.save(PUBLIC / 'lab8-highlight-content.png')
