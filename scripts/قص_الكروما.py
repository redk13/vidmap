#!/usr/bin/env python3
"""قصّ الكروما الخضراء وإزالة الهالة من قصاصة ورق مولّدة.

المتطلبات:
    python3 -m pip install pillow numpy scipy
الاستخدام:
    python3 قص_الكروما.py input-green.png output-cutout.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def cutout(src: str | Path, dst: str | Path) -> Path:
    """يفرّغ أكبر مكوّن غير أخضر ويحفظ PNG بقناة ألفا."""
    src, dst = Path(src), Path(dst)
    im = Image.open(src).convert('RGB')
    a = np.asarray(im).astype(int)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    green = (G > 120) & (G > R + 40) & (G > B + 40)
    obj = ~green
    lab, n = ndimage.label(obj)
    if n > 1:
        sizes = ndimage.sum(obj, lab, range(1, n + 1))
        obj = lab == (int(np.argmax(sizes)) + 1)
    obj = ndimage.binary_fill_holes(obj)
    alpha = Image.fromarray((obj * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.0))
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError('لم يُعثر على جسم غير أخضر في الصورة.')
    out = im.convert('RGBA')
    out.putalpha(alpha)
    out = out.crop(bbox)

    # إزالة الهالة الخضراء من الألياف مع الإبقاء على قناة ألفا.
    d = np.asarray(out).copy()
    rgb = d[:, :, :3].astype(int)
    g_ex = rgb[:, :, 1] - ((rgb[:, :, 0] + rgb[:, :, 2]) // 2)
    rgb[:, :, 1] = np.where(g_ex > 12, (rgb[:, :, 0] + rgb[:, :, 2]) // 2, rgb[:, :, 1])
    d[:, :, :3] = rgb.astype('uint8')
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(d, 'RGBA').save(dst)
    return dst


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='صورة PNG على خلفية خضراء')
    parser.add_argument('output', help='مسار PNG المفرّغ الناتج')
    args = parser.parse_args()
    result = cutout(args.input, args.output)
    print(result)


if __name__ == '__main__':
    main()
