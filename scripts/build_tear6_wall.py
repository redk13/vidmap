#!/usr/bin/env python3
"""Shot 06 corrected layer model: text on the WALL, gray paper cover tears away."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / 'public'
FONT_B = ROOT / 'fonts' / 'Montserrat-ExtraBold.ttf'
FONT_S = ROOT / 'fonts' / 'Montserrat-SemiBold.ttf'
W, H = 1920, 1080

CARDS = [
    {
        'out': 'tear6-wall-1.webp', 'source': 'Wikinews', 'date': 'DECEMBER 27, 2005',
        'credit': 'Wikinews · CC BY 2.5',
        'lines': [[("Japan's ", False), ('population declines', True)]], 'fs': 78,
        'body1': "Japan's population declined by 19,000 in 2005, according to the government census.",
        'body2': 'It was the first recorded decline since 1899. The birth rate stood at 1.29 children per woman.',
    },
    {
        'out': 'tear6-wall-2.webp', 'source': 'Wikinews', 'date': 'OCTOBER 27, 2008',
        'credit': 'Wikinews · CC BY 2.5',
        'lines': [[('Asian stock markets slide;', False)], [("Nikkei at lowest level since '82", True)]], 'fs': 64,
        'body1': "Japan's Nikkei stock index fell to lows not seen since October 1982.",
        'body2': 'The Nikkei closed down 6.4 percent, or 486.18 points, at 7,162.90.',
    },
    {
        'out': 'tear6-wall-3.webp', 'source': 'Global Voices', 'date': 'MAY 31, 2009',
        'credit': 'Tomomi Sasaki · Global Voices · CC BY 3.0',
        'lines': [[('Go Farm, Young Man! –', False)], [('How Farming in Japan is Changing', True)]], 'fs': 63,
        'body1': "Japan's agricultural workforce is rapidly aging, with too few successors.",
        'body2': 'The government is looking at agricultural employment as one answer to rising unemployment.',
    },
]


def font(path, size):
    return ImageFont.truetype(str(path), size)


def segments(draw, xy, parts, fnt):
    x, y = xy
    for text, marked in parts:
        width = draw.textlength(text, font=fnt)
        if marked:
            draw.rectangle((x - 4, y + 5, x + width + 5, y + fnt.size + 12), fill='#e5ed2f')
        draw.text((x, y), text, font=fnt, fill=(22, 22, 22, 255))
        x += width


def wrap(draw, text, fnt, width):
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


def build_walls():
    blank = Image.open(PUB / 'tear6-wall-blank.webp').convert('RGB').resize((W, H), Image.Resampling.LANCZOS)
    for card in CARDS:
        im = blank.copy()
        d = ImageDraw.Draw(im)
        d.text((250, 190), card['source'], font=font(FONT_B, 59), fill=(22, 22, 22, 255))
        y = 315
        hf = font(FONT_B, card['fs'])
        for parts in card['lines']:
            segments(d, (250, y), parts, hf)
            y += int(card['fs'] * 1.23)
        d.text((250, y + 18), card['date'], font=font(FONT_S, 30), fill=(52, 52, 52, 255))
        d.text((250, 950), card['credit'], font=font(FONT_S, 18), fill=(68, 68, 68, 255))
        bf = font(FONT_S, 15)
        for i, key in enumerate(('body1', 'body2')):
            x = 1110 + i * 285
            yy = 790
            for line in wrap(d, card[key], bf, 255)[:7]:
                d.text((x, yy), line, font=bf, fill=(65, 65, 65, 220))
                yy += 22
        im.save(PUB / card['out'], quality=95, method=6)
        print('wall', card['out'], flush=True)


def build_cover():
    # The generated gray fibrous image is the PAPER that hides the wall.
    cover = Image.open(PUB / 'tear6-background.webp').convert('RGB').resize((W, H), Image.Resampling.LANCZOS)
    cover = ImageEnhance.Brightness(cover).enhance(1.04)
    cover = ImageEnhance.Contrast(cover).enhance(0.9).filter(ImageFilter.GaussianBlur(0.45))
    cover.save(PUB / 'tear6-cover-full.webp', quality=95, method=6)
    rng = np.random.default_rng(601)
    coarse = ndimage.gaussian_filter1d(rng.normal(0, 1, W), 28)
    coarse /= max(np.max(np.abs(coarse)), 1e-6)
    fine = ndimage.gaussian_filter1d(rng.normal(0, 1, W), 2.4)
    fine /= max(np.max(np.abs(fine)), 1e-6)
    seam = H / 2 + coarse * 18 + fine * 4
    yy = np.arange(H)[:, None]
    top_mask = yy < seam[None, :]
    rgb = np.asarray(cover)
    alpha = np.full((H, W), 255, dtype=np.uint8)
    top = Image.fromarray(np.dstack([rgb, np.where(top_mask, alpha, 0).astype(np.uint8)]), 'RGBA')
    bottom = Image.fromarray(np.dstack([rgb, np.where(~top_mask, alpha, 0).astype(np.uint8)]), 'RGBA')
    top.save(PUB / 'tear6-cover-top.webp', quality=95, method=6)
    bottom.save(PUB / 'tear6-cover-bottom.webp', quality=95, method=6)
    print('cover split', flush=True)


if __name__ == '__main__':
    build_walls()
    build_cover()
