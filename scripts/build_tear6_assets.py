#!/usr/bin/env python3
"""Build shot-06 raster clippings: generated paper -> licensed typesetting -> two WebP halves."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / 'public'
FONT_B = ROOT / 'fonts' / 'Montserrat-ExtraBold.ttf'
FONT_S = ROOT / 'fonts' / 'Montserrat-SemiBold.ttf'
W, H = 1500, 760

CARDS = [
    {
        'src': 'tear6-paper1-green.webp', 'out': 'tear6-1',
        'source': 'Wikinews', 'date': 'DECEMBER 27, 2005',
        'credit': 'Wikinews · CC BY 2.5',
        'lines': [[("Japan's ", False), ('population declines', True)]],
        'fs': 78,
        'body1': "Japan's population declined by 19,000 in 2005, according to the government census.",
        'body2': 'It was the first recorded decline since 1899. The birth rate stood at 1.29 children per woman.',
        'seed': 106,
    },
    {
        'src': 'tear6-paper2-green.webp', 'out': 'tear6-2',
        'source': 'Wikinews', 'date': 'OCTOBER 27, 2008',
        'credit': 'Wikinews · CC BY 2.5',
        'lines': [
            [('Asian stock markets slide;', False)],
            [("Nikkei at lowest level since '82", True)],
        ],
        'fs': 61,
        'body1': "Japan's Nikkei stock index fell to lows not seen since October 1982.",
        'body2': 'The Nikkei closed down 6.4 percent, or 486.18 points, at 7,162.90.',
        'seed': 208,
    },
    {
        'src': 'tear6-paper3-green.webp', 'out': 'tear6-3',
        'source': 'Global Voices', 'date': 'MAY 31, 2009',
        'credit': 'Tomomi Sasaki · Global Voices · CC BY 3.0',
        'lines': [
            [('Go Farm, Young Man! –', False)],
            [('How Farming in Japan is Changing', True)],
        ],
        'fs': 60,
        'body1': "Japan's agricultural workforce is rapidly aging, with too few successors.",
        'body2': 'The government is looking at agricultural employment as one answer to rising unemployment.',
        'seed': 312,
    },
]


def font(path: Path, size: int):
    return ImageFont.truetype(str(path), size)


def chroma_cutout(path: Path) -> Image.Image:
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g > 95) & (g > r * 1.22) & (g > b * 1.22) & ((g - np.maximum(r, b)) > 32)
    paper = ~green
    labels, n = ndimage.label(paper)
    if n > 1:
        sizes = ndimage.sum(paper, labels, range(1, n + 1))
        paper = labels == (int(np.argmax(sizes)) + 1)
    paper = ndimage.binary_fill_holes(paper)
    ys, xs = np.where(paper)
    y0, y1 = max(0, ys.min() - 3), min(im.height, ys.max() + 4)
    x0, x1 = max(0, xs.min() - 3), min(im.width, xs.max() + 4)
    a = a[y0:y1, x0:x1]
    mask = paper[y0:y1, x0:x1]
    # Remove green spill without touching the paper's neutral gray texture.
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    spill = (g > np.maximum(r, b) + 8)
    g[spill] = np.maximum(r[spill], b[spill])
    alpha = ndimage.gaussian_filter(mask.astype(np.float32), 0.65)
    rgba = np.dstack([np.clip(a, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA').resize((W, H), Image.Resampling.LANCZOS)


def draw_segments(draw: ImageDraw.ImageDraw, xy, segments, fnt, fill):
    x, y = xy
    for text, marked in segments:
        width = draw.textlength(text, font=fnt)
        if marked:
            draw.rectangle((x - 4, y + 5, x + width + 5, y + fnt.size + 12), fill='#e5ed2f')
        draw.text((x, y), text, font=fnt, fill=fill)
        x += width


def wrap_text(draw, text, fnt, width):
    lines, line = [], ''
    for word in text.split():
        test = word if not line else line + ' ' + word
        if draw.textlength(test, font=fnt) <= width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def compose(card):
    im = chroma_cutout(PUB / card['src'])
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ink = (22, 22, 22, 255)
    d.text((90, 55), card['source'], font=font(FONT_B, 55), fill=ink)
    y = 165
    hf = font(FONT_B, card['fs'])
    for segments in card['lines']:
        draw_segments(d, (90, y), segments, hf, ink)
        y += int(card['fs'] * 1.22)
    d.text((90, y + 15), card['date'], font=font(FONT_S, 28), fill=(52, 52, 52, 255))
    d.text((90, H - 105), card['credit'], font=font(FONT_S, 17), fill=(68, 68, 68, 235))
    bf = font(FONT_S, 14)
    for i, key in enumerate(('body1', 'body2')):
        x = W - 570 + i * 250
        yy = H - 190
        for line in wrap_text(d, card[key], bf, 225)[:7]:
            d.text((x, yy), line, font=bf, fill=(65, 65, 65, 190))
            yy += 20
    im = Image.alpha_composite(im, layer)
    return im


def split_halves(im: Image.Image, seed: int):
    rng = np.random.default_rng(seed)
    xs = np.arange(W)
    coarse = ndimage.gaussian_filter1d(rng.normal(0, 1, W), 24)
    coarse = coarse / max(np.max(np.abs(coarse)), 1e-6)
    fine = ndimage.gaussian_filter1d(rng.normal(0, 1, W), 2.2)
    fine = fine / max(np.max(np.abs(fine)), 1e-6)
    seam = H * 0.48 + coarse * 13 + fine * 3.2
    yy = np.arange(H)[:, None]
    top_mask = yy < seam[None, :]
    alpha = np.asarray(im)[..., 3]
    top_a = np.where(top_mask, alpha, 0).astype(np.uint8)
    bottom_a = np.where(~top_mask, alpha, 0).astype(np.uint8)
    rgb = np.asarray(im)[..., :3]
    top = Image.fromarray(np.dstack([rgb, top_a]), 'RGBA')
    bottom = Image.fromarray(np.dstack([rgb, bottom_a]), 'RGBA')
    return top, bottom


def main():
    meta = []
    for card in CARDS:
        im = compose(card)
        im.save(PUB / f"{card['out']}-full.webp", quality=95, method=6)
        top, bottom = split_halves(im, card['seed'])
        top.save(PUB / f"{card['out']}-top.webp", quality=95, method=6)
        bottom.save(PUB / f"{card['out']}-bottom.webp", quality=95, method=6)
        meta.append({'top': f"{card['out']}-top.webp", 'bottom': f"{card['out']}-bottom.webp", 'w': W, 'h': H})
        print('built', card['out'], flush=True)
    (PUB / 'tear6-meta.json').write_text(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
