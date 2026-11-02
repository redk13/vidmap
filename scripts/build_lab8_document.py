from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
W, H = 1920, 1080
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
SERIF_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
MONT = str(ROOT / 'fonts' / 'Montserrat-SemiBold.ttf')
MONT_BOLD = str(ROOT / 'fonts' / 'Montserrat-ExtraBold.ttf')
SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
SANS_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

source = Image.open(PUBLIC / 'lab8-paper-source.png').convert('RGB')
# Use the generated blank report only as real-looking paper texture. All data and
# typography are original and are added below from the verified MIC figures.
right_texture = source.crop((440, 85, 1135, 690)).resize((1120, 1140), Image.Resampling.LANCZOS)
right_texture = ImageEnhance.Brightness(right_texture).enhance(0.86)
right_texture = ImageEnhance.Contrast(right_texture).enhance(0.92)
left_texture = source.crop((230, 80, 390, 690)).resize((260, 940), Image.Resampling.LANCZOS)
left_texture = ImageEnhance.Brightness(left_texture).enhance(0.27)

canvas = Image.new('RGB', (W, H), '#030405')
# Soft contact shadows keep the document photographic rather than a flat card.
shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rectangle((345, 4, 1490, 1110), fill=(0, 0, 0, 210))
sd.rectangle((145, 100, 420, 1040), fill=(0, 0, 0, 190))
shadow = shadow.filter(ImageFilter.GaussianBlur(28))
canvas = Image.alpha_composite(canvas.convert('RGBA'), shadow)
canvas.paste(left_texture, (150, 95))
canvas.paste(right_texture, (360, -30))

ink = (22, 25, 25, 255)
muted = (66, 68, 66, 255)
grid = (115, 116, 109, 150)
red = (121, 35, 46, 255)
slate = (59, 88, 98, 255)

f_header = ImageFont.truetype(SANS, 16)
f_chart = ImageFont.truetype(SERIF_BOLD, 23)
f_small = ImageFont.truetype(SANS, 16)
f_value = ImageFont.truetype(SERIF_BOLD, 20)
f_serif = ImageFont.truetype(SERIF, 20)
f_body = ImageFont.truetype(SERIF, 28)
f_body_bold = ImageFont.truetype(SERIF_BOLD, 28)

# Header and original data chart.
canvas_draw = ImageDraw.Draw(canvas)
canvas_draw.text((460, 92), 'Figure 1. Japan’s vacant homes by category, 2023', font=f_chart, fill=ink)

chart_x, chart_y, chart_w, chart_h = 510, 150, 830, 225
for tick in range(6):
    y = chart_y + chart_h - tick * chart_h / 5
    canvas_draw.line((chart_x, y, chart_x + chart_w, y), fill=grid, width=1)
    canvas_draw.text((chart_x - 48, y - 10), f'{tick}M', font=f_small, fill=muted)
canvas_draw.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill=muted, width=2)

values = [4.436, 3.856, 0.384, 0.326]
labels = ['RENTAL', 'OTHER /\nABANDONED', 'SECOND\nHOMES', 'FOR SALE']
colors = [red, slate, (106, 77, 91, 255), (83, 102, 91, 255)]
bar_w = 88
for i, (value, label, color) in enumerate(zip(values, labels, colors)):
    x = chart_x + 48 + i * 198
    height = value / 5 * chart_h
    y = chart_y + chart_h - height
    bar_h = max(2, int(round(height)))
    bar = Image.new('RGBA', (bar_w, bar_h), color)
    bd = ImageDraw.Draw(bar)
    # Fine diagonal hatch is clipped to the bar itself, like a printed chart.
    for k in range(-bar_h, bar_w + bar_h, 22):
        bd.line((k, bar_h, k + bar_h, 0), fill=(230, 230, 220, 42), width=1)
    bd.rectangle((0, 0, bar_w - 1, bar_h - 1), outline=(45, 48, 47, 255), width=2)
    canvas.paste(bar, (int(x), int(chart_y + chart_h - bar_h)), bar)
    canvas_draw = ImageDraw.Draw(canvas)
    value_text = f'{value:.3f}M'
    tw = canvas_draw.textlength(value_text, font=f_value)
    canvas_draw.text((x + (bar_w - tw) / 2, y - 28), value_text, font=f_value, fill=ink)
    for j, line in enumerate(label.split('\n')):
        tw = canvas_draw.textlength(line, font=f_small)
        canvas_draw.text((x + (bar_w - tw) / 2, chart_y + chart_h + 12 + j * 21), line, font=f_small, fill=ink)

canvas_draw.text((510, 432), 'Source: MIC Statistics Bureau, Housing and Land Survey, 2023.', font=f_serif, fill=ink)
canvas_draw.text((510, 466), 'Values in millions. Vacant does not necessarily mean abandoned.', font=f_small, fill=muted)

lines = [
    'Japan counted 9.002 million vacant homes in 2023.',
    'Vacant does not mean abandoned: 4.436 million were rentals.',
    'Another 3.856 million were classified as other or abandoned.',
]
text_x = 460
for i, line in enumerate(lines):
    canvas_draw.text((text_x, 555 + i * 58), line, font=f_body, fill=ink)

target = 'Tokyo had 898,000 vacant homes — 10.9% of its housing stock.'
target_y = 735
target_w = canvas_draw.textlength(target, font=f_body)
# Exported for the Remotion sweep; keep these values synchronized with TSX.
print(f'TARGET_X={text_x};TARGET_Y={target_y};TARGET_W={target_w:.2f};TARGET_H=44')


stroke = Image.new('RGBA', (W, H), (0, 0, 0, 0))
od = ImageDraw.Draw(stroke)
rnd = random.Random(23)
x0, x1 = text_x - 9, text_x + target_w + 15
y0, y1 = target_y - 5, target_y + 41
top = [(x0 + (x1 - x0) * i / 28, y0 + rnd.uniform(-2.2, 2.2)) for i in range(29)]
bottom = [(x0 + (x1 - x0) * i / 28, y1 + rnd.uniform(-2.4, 2.4)) for i in reversed(range(29))]
od.polygon(top + bottom, fill=(249, 237, 20, 210))
stroke = stroke.filter(ImageFilter.GaussianBlur(0.45))
stroke.save(PUBLIC / 'lab8-highlight-stroke.png')


def make_image(highlighted: bool) -> Image.Image:
    im = canvas.copy()
    if highlighted:
        im = Image.alpha_composite(im, stroke)
    d = ImageDraw.Draw(im)
    d.text((text_x, target_y), target, font=f_body, fill=ink)
    return im

make_image(False).convert('RGB').save(PUBLIC / 'lab8-document-clean.webp', lossless=True, quality=100)
make_image(True).convert('RGB').save(PUBLIC / 'lab8-document-highlight.webp', lossless=True, quality=100)
