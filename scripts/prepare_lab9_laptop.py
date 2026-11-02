from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
W, H = 1920, 1080

img = Image.open(PUBLIC / 'lab9-laptop-source.png').convert('RGB').resize((W, H), Image.Resampling.LANCZOS)
arr = np.array(img)
r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
green = (g > 110) & (g.astype(np.int16) - r.astype(np.int16) > 45) & (g.astype(np.int16) - b.astype(np.int16) > 45)
mask = np.where(green, 255, 0).astype(np.uint8)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
largest = max(contours, key=cv2.contourArea)
x, y, w, h = cv2.boundingRect(largest)
screen = np.zeros_like(mask)
cv2.drawContours(screen, [largest], -1, 255, -1)
screen = cv2.morphologyEx(screen, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
alpha = cv2.GaussianBlur(255 - screen, (3, 3), 0.55)
cap = np.clip(np.maximum(r, b).astype(np.int16) + 12, 0, 255).astype(np.uint8)
arr[..., 1] = np.minimum(g, cap).astype(np.uint8)
rgba = np.dstack([arr, alpha])
Image.fromarray(rgba, 'RGBA').save(PUBLIC / 'lab9-laptop.png')
print(f'SCREEN_X={x};SCREEN_Y={y};SCREEN_W={w};SCREEN_H={h}')
