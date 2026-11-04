#!/usr/bin/env python3
"""Key a freshly generated chroma-green torn-paper IMAGE for shot 06.

Usage: python scripts/key_tear6_paper.py input-green.png public/tear6-cover-source.webp
This only removes the green screen and its spill; it never constructs a torn mask.
"""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('input', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()

im = Image.open(args.input).convert('RGB').resize((1920, 1080), Image.Resampling.LANCZOS)
a = np.asarray(im).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
maxrb = np.maximum(r, b)
dominance = g - maxrb
alpha = 1 - np.clip((dominance - 10) / 95, 0, 1)
# The upper sheet is known to be opaque well above its generated torn rim.
alpha[:480, :] = 1
# Remove green contamination at the fibrous edge without making a new edge.
g_clean = np.where(dominance > 8, np.minimum(g, maxrb + 6), g)
out = np.dstack([r, g_clean, b, np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
args.output.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(out, 'RGBA').save(args.output, lossless=True, method=6)
print(args.output)
