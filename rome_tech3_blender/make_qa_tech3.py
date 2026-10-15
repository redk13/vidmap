from PIL import Image, ImageDraw
import sys

frames_dir = sys.argv[1]
out_path = sys.argv[2]

cols, rows = 2, 5
tw, th = 640, 360
grid = Image.new("RGB", (cols * tw, rows * th), (10, 12, 16))
draw = ImageDraw.Draw(grid)
frames = [25, 85, 145, 211, 265, 331, 385, 451, 505, 577]
labels = [
    "Blender 4.3 Shot 1A (f0025): 3D Displaced Mesh + Scan", "Blender 4.3 Shot 1B (f0085): 3D NURBS Specus Tube",
    "Blender 4.3 Shot 2A (f0145): 3D Map + Extruded 3D Text", "Blender 4.3 Shot 2B (f0211): Aqua Marcia 90km 3D Curve",
    "Blender 4.3 Shot 3A (f0265): 3D Cutaway + 3D Font Badges", "Blender 4.3 Shot 3B (f0331): 3D Cyan Tube + Ray Light",
    "Blender 4.3 Shot 4A (f0385): 3D Studio + 3D Extruded Text", "Blender 4.3 Shot 4B (f0451): 0.09-0.17 deg 3D Laser",
    "Blender 4.3 Shot 5A (f0505): 3D Valley + Header Tank 3D", "Blender 4.3 Shot 5B (f0577): 3D U-Siphon NURBS Tube"
]
for i, fn in enumerate(frames):
    im = Image.open(f"{frames_dir}/frame_{fn:04d}.jpg").resize((tw, th), Image.Resampling.LANCZOS)
    x, y = (i % cols) * tw, (i // cols) * th
    grid.paste(im, (x, y))
    draw.rectangle([x + 8, y + 8, x + 490, y + 34], fill=(0, 0, 0))
    draw.text((x + 14, y + 12), labels[i], fill=(255, 200, 50))
grid.save(out_path, quality=94)
print("Saved QA grid:", out_path)
