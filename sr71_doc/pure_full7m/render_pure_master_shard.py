import os, sys, math, cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

f_start = int(sys.argv[1])
f_end   = int(sys.argv[2])
cad_dir = os.path.abspath(sys.argv[3])
out_dir = os.path.abspath(sys.argv[4])
os.makedirs(out_dir, exist_ok=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_ROOT   = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PHOTOS_HD  = os.path.join(DOC_ROOT, "real_hd_photos")
ARCH_PH    = os.path.join(DOC_ROOT, "archival_photos")
REAL_VIDS  = os.path.join(DOC_ROOT, "real_videos")
FONT_BEBAS = os.path.join(DOC_ROOT, "fonts", "BebasNeue-Regular.ttf")
FONT_OSWALD= os.path.join(DOC_ROOT, "fonts", "Oswald-Bold.ttf")

def f_bebas(sz):  return ImageFont.truetype(FONT_BEBAS, sz)
def f_oswald(sz): return ImageFont.truetype(FONT_OSWALD, sz)

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / max(1e-6, b - a)))
    return t * t * (3.0 - 2.0 * t)

def draw_tracked_text(draw, pos, text, font, fill, tracking=5):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((x, y), ch, font=font)
        x += (bbox[2] - bbox[0]) + tracking

def draw_cable_0012_label(img_bgr, center_xy, lines_list, u, t_in=0.10, t_out=0.88, max_alpha=0.60):
    """Exact Primal Space '1. Cable 00:12' ('JEAN-ANTOINE / NOLLET'):
    Zero pointer lines, zero dots, zero boxes, single muted-white Bebas Neue font in negative space."""
    if not lines_list:
        return img_bgr
    if u < t_in or u > t_out:
        return img_bgr
    alpha = max_alpha
    if u < t_in + 0.10:
        alpha = max_alpha * ((u - t_in) / 0.10)
    elif u > t_out - 0.10:
        alpha = max_alpha * ((t_out - u) / 0.10)
    if alpha <= 0.02:
        return img_bgr

    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    font = f_bebas(46)
    cx = max(140, min(1780, int(center_xy[0])))
    cy = max(70,  min(980,  int(center_xy[1])))
    line_h = 44
    total_h = len(lines_list) * line_h
    y0 = cy - total_h // 2
    for idx, line in enumerate(lines_list):
        tb = draw.textbbox((0, 0), line, font=font)
        w = tb[2] - tb[0]
        draw.text((cx - w // 2, y0 + idx * line_h), line, font=font, fill=(230, 235, 242))
    res = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return cv2.addWeighted(res, alpha, img_bgr, 1.0 - alpha, 0)

def render_pure_3d_scene(seq_id, u, labels_cfg=None, reverse=False):
    eff_u = (1.0 - u) if reverse else u
    f_idx = min(149, max(0, int(round(eff_u * 149))))
    img_path = os.path.join(cad_dir, f"s{seq_id}_{f_idx:04d}.png")
    if not os.path.exists(img_path):
        img_path = os.path.join(cad_dir, f"s{seq_id}_{f_idx:04d}.jpg")
    if os.path.exists(img_path):
        img_bgr = cv2.imread(img_path)
    else:
        img_bgr = cv2.imread(os.path.join(PHOTOS_HD, "nasa_sr71_headon_ramp.jpg"))
    if labels_cfg:
        for (cx, cy, lines_list, t0, t1) in labels_cfg:
            img_bgr = draw_cable_0012_label(img_bgr, (cx, cy), lines_list, u, t0, t1, max_alpha=0.60)
    return img_bgr

NASA_CACHE = {}
def render_pure_nasa_16x9(fn, u, labels_cfg=None):
    """100% Unfiltered Official NASA Dryden/Glenn 1080p Photograph (CIA 00:46 / Ford 00:22 style):
    Zero Sobel filters, zero darkening spotlights, zero pointer lines — pure gentle cinematic camera push."""
    if fn not in NASA_CACHE:
        p = os.path.join(PHOTOS_HD, fn)
        NASA_CACHE[fn] = cv2.imread(p)
    src = NASA_CACHE[fn]
    su = 0.5 - 0.5 * math.cos(u * math.pi)
    scale = 1.0 + 0.045 * su
    h, w = src.shape[:2]
    cw, ch = int(w / scale), int(h / scale)
    x0 = (w - cw) // 2
    y0 = (h - ch) // 2
    crop = src[y0:y0+ch, x0:x0+cw]
    img_bgr = cv2.resize(crop, (1920, 1080), interpolation=cv2.INTER_LANCZOS4)
    if labels_cfg:
        for (cx, cy, lines_list, t0, t1) in labels_cfg:
            img_bgr = draw_cable_0012_label(img_bgr, (cx, cy), lines_list, u, t0, t1, max_alpha=0.60)
    return img_bgr

VID_CAPS = {}
def render_pure_archival_video_16x9(v_fn, u):
    """100% Pure Full-Bleed 16:9 Archival Video (CIA 00:46 / Ford 00:22): Zero pointer lines or overlays."""
    v_path = os.path.join(REAL_VIDS, v_fn)
    if v_fn not in VID_CAPS:
        cap = cv2.VideoCapture(v_path)
        n_frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        VID_CAPS[v_fn] = (cap, n_frames)
    cap, n_frames = VID_CAPS[v_fn]
    target_f = int((u * 0.85 + 0.05) * (n_frames - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_f)
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = cap.read()
    h, w = frame.shape[:2]
    target_ar = 16.0 / 9.0
    if (w / float(h)) > target_ar:
        nw = int(h * target_ar); x0 = (w - nw) // 2; crop = frame[:, x0:x0+nw]
    else:
        nh = int(w / target_ar); y0 = (h - nh) // 2; crop = frame[y0:y0+nh, :]
    return cv2.resize(crop, (1920, 1080), interpolation=cv2.INTER_LANCZOS4)

ARCH_CACHE = {}
def render_pure_archival_4x3_filmgate(p_fn, u):
    """Exact Primal Space Cable 00:58 / Gyro 00:58 4:3 Vintage Film-Gate on Pitch-Black #000000, Zero lines."""
    if p_fn not in ARCH_CACHE:
        p = os.path.join(ARCH_PH, p_fn)
        ARCH_CACHE[p_fn] = Image.open(p).convert("RGB")
    src = ARCH_CACHE[p_fn]
    canvas = Image.new("RGB", (1920, 1080), (0, 0, 0))
    gw, gh = 1280, 920
    gx, gy = (1920 - gw) // 2, (1080 - gh) // 2
    su = 0.5 - 0.5 * math.cos(u * math.pi)
    scale = 1.0 + 0.042 * su
    sw, sh = int(gw * scale), int(gh * scale)
    resized = src.resize((sw, sh), Image.Resampling.LANCZOS)
    x0 = (sw - gw) // 2
    y0 = (sh - gh) // 2
    cropped = resized.crop((x0, y0, x0 + gw, y0 + gh))

    mask = Image.new("L", (gw, gh), 0)
    mdr = ImageDraw.Draw(mask)
    mdr.rounded_rectangle([0, 0, gw - 1, gh - 1], radius=28, fill=255)
    canvas.paste(cropped, (gx, gy), mask)
    return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)

yy_grid, xx_grid = np.mgrid[0:1080, 0:1920].astype(np.float32)
xx_n = xx_grid / 1920.0
yy_n = yy_grid / 1080.0

def render_ford_chart(u, mode="j58_thrust"):
    """Exact Primal Space Ford 00:46 Warm Cream Radial Vignette Canvas (#EAE6DF -> #CFC9BE)."""
    h, w = 1080, 1920
    dist = np.sqrt(((xx_n - 0.5)*1.2)**2 + ((yy_n - 0.5)*1.2)**2)
    vig = np.clip(1.0 - 0.14 * dist, 0.82, 1.0)
    base = np.zeros((h, w, 3), dtype=np.uint8)
    base[:,:,0] = (236 * vig).astype(np.uint8)
    base[:,:,1] = (232 * vig).astype(np.uint8)
    base[:,:,2] = (224 * vig).astype(np.uint8)
    im = Image.fromarray(base).convert("RGBA")
    dr = ImageDraw.Draw(im)

    f_title = f_bebas(64)
    f_lbl   = f_bebas(46)

    if mode == "j58_thrust":
        draw_tracked_text(dr, (180, 95), "J58 THRUST SHARE AT MACH 3.2", f_title, (28, 30, 34, 255), tracking=6)
        bars = [
            ("INLET CONE COMPRESSION", 58, "58%", (35, 115, 185)),
            ("AFTERBURNER RAMJET",     25, "25%", (215, 95, 35)),
            ("TURBOJET CORE",          17, "17%", (65, 72, 82)),
        ]
        for i, (name, val, v_txt, col) in enumerate(bars):
            by = 290 + i * 210
            p = smoothstep(0.05 + i * 0.14, 0.55 + i * 0.14, u)
            bw = int((val / 65.0) * 1120 * p)
            dr.rounded_rectangle([180, by, 180 + max(12, bw), by + 108], radius=10, fill=(*col, 255))
            draw_tracked_text(dr, (180, by - 52), name, f_lbl, (32, 35, 40, 255), tracking=4)
            draw_tracked_text(dr, (180 + bw + 28, by + 22), v_txt, f_title, (*col, 255), tracking=4)
    else:
        draw_tracked_text(dr, (180, 95), "SKIN TEMPERATURE BY AIRFRAME ZONE", f_title, (28, 30, 34, 255), tracking=6)
        bars = [
            ("J58 AFTERBURNER PLUME", 3200, "3,200°F", (215, 75, 30)),
            ("TITANIUM NOSE & CHINES", 950, "950°F",   (225, 135, 35)),
            ("QUARTZ CANOPY EXTERIOR", 620, "620°F",   (35, 115, 185)),
        ]
        for i, (name, val, v_txt, col) in enumerate(bars):
            by = 290 + i * 210
            p = smoothstep(0.05 + i * 0.14, 0.55 + i * 0.14, u)
            bw = int((val / 3400.0) * 1120 * p)
            dr.rounded_rectangle([180, by, 180 + max(12, bw), by + 108], radius=10, fill=(*col, 255))
            draw_tracked_text(dr, (180, by - 52), name, f_lbl, (32, 35, 40, 255), tracking=4)
            draw_tracked_text(dr, (180 + bw + 28, by + 22), v_txt, f_title, (*col, 255), tracking=4)

    return cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)

# Complete 54-Segment Timeline across 0.0s .. 426.99s (12,810 frames @ 30fps)
# 27 Pure Blender 4.3.2 1080p 3D Studio Scenes (s0..s8) + 27 Pure Unfiltered Archival Videos, NASA Photos, Film-Gate & Ford Charts!
TIMELINE = [
    # CHAPTER 1 (0.0 .. 53.25s): The Mach 3.2 Anomaly & Leaking Fuel Tank Paradox
    (0.0,   7.5,  "3d",   (1, None, False)),
    (7.5,   15.0, "vid",  ("v_takeoff.webm",)),
    (15.0,  22.5, "3d",   (3, [(420, 120, ["TITANIUM", "DOUBLE-DELTA"], 0.12, 0.88)], False)),
    (22.5,  30.0, "nasa", ("nasa_sr71_topdown_planform.jpg", None)),
    (30.0,  38.0, "3d",   (5, [(380, 130, ["KNIFE-EDGE", "CHINE PROFILE"], 0.12, 0.88)], False)),
    (38.0,  45.5, "3d",   (0, None, False)), # s0 already has Cable 00:12 labels baked in
    (45.5,  53.25,"vid",  ("v_flight.webm",)),

    # CHAPTER 2 (53.25 .. 103.87s): May 1960 U-2 Shootdown & CIA Oxcart Mandate
    (53.25, 61.5, "arch", ("u2_flight.jpg",)),
    (61.5,  69.5, "arch", ("kelly.jpg",)),
    (69.5,  78.0, "3d",   (8, [(420, 125, ["LOCKHEED", "SKUNK WORKS"], 0.12, 0.88)], False)),
    (78.0,  86.5, "nasa", ("real_skunkworks_hangar.jpg", None)),
    (86.5,  95.0, "3d",   (5, [(1480, 130, ["LOW RADAR", "CROSS-SECTION"], 0.12, 0.88)], True)),
    (95.0,  103.87,"chart",("temp_zones",)),

    # CHAPTER 3 (103.87 .. 163.84s): The 950°F Thermal Wall & Soviet Titanium Espionage
    (103.87,112.5,"3d",   (1, [(420, 125, ["85% TITANIUM", "B-120VCA ALLOY"], 0.12, 0.88)], True)),
    (112.5, 121.0,"arch", ("crate.jpg",)),
    (121.0, 129.5,"3d",   (3, [(1460, 125, ["CHORDWISE", "EXPANSION SEAMS"], 0.12, 0.88)], True)),
    (129.5, 138.0,"nasa", ("nasa_sr71_rear_inlet.jpg", None)),
    (138.0, 146.5,"arch", ("a12_hangar.jpg",)),
    (146.5, 155.0,"3d",   (7, [(440, 125, ["TWIN J58", "EXHAUST NOZZLES"], 0.12, 0.88)], False)),
    (155.0, 163.84,"nasa",("nasa_sr71_takeoff_ab.jpg", None)),

    # CHAPTER 4 (163.84 .. 216.39s): JP-7 Fuel Chemistry, Cesium & TEB Pyrophoric Ignition
    (163.84,172.5,"3d",   (3, [(420, 125, ["80,000 POUNDS", "JP-7 FUEL SINK"], 0.12, 0.88)], False)),
    (172.5, 181.0,"nasa", ("nasa_sr71_ground_test.jpg", None)),
    (181.0, 190.0,"3d",   (4, [(520, 120, ["TRIETHYLBORANE", "CATALYTIC IGNITION"], 0.12, 0.88)], False)),
    (190.0, 199.0,"vid",  ("v_refuel.webm",)),
    (199.0, 208.0,"nasa", ("nasa_sr71_kc135_refuel.jpg", None)),
    (208.0, 216.39,"3d",  (2, None, False)),

    # CHAPTER 5 (216.39 .. 269.43s): The Pratt & Whitney J58 Turbo-Ramjet Hybrid Miracle
    (216.39,225.0,"3d",   (6, [(460, 120, ["PRATT & WHITNEY", "J58 ARCHITECTURE"], 0.12, 0.88)], False)),
    (225.0, 234.0,"3d",   (0, None, False)),
    (234.0, 243.0,"nasa", ("nasa_yf12_windtunnel.jpg", None)),
    (243.0, 252.0,"3d",   (4, [(1380, 120, ["3,200°F", "AFTERBURNER CORE"], 0.12, 0.88)], True)),
    (252.0, 261.0,"nasa", ("nasa_j58_full_afterburner.jpg", None)),
    (261.0, 269.43,"chart",("j58_thrust",)),

    # CHAPTER 6 (269.43 .. 324.20s): The Brutal Reality of an Inlet Unstart at Mach 3.2
    (269.43,278.5,"3d",   (0, None, True)),
    (278.5, 287.5,"3d",   (2, None, False)),
    (287.5, 296.5,"vid",  ("v_trainer.webm",)),
    (296.5, 305.5,"3d",   (6, [(460, 120, ["DAFICS DIGITAL", "INLET CONTROL"], 0.12, 0.88)], True)),
    (305.5, 315.0,"nasa", ("nasa_sr71_headon_ramp.jpg", None)),
    (315.0, 324.20,"arch",("cockpit.jpg",)),

    # CHAPTER 7 (324.20 .. 375.57s): Flying at the Edge of Space (85,000 Feet) & Astro-Inertial Navigation
    (324.20,333.0,"nasa", ("nasa_sr71_pressure_suits.jpg", None)),
    (333.0, 342.0,"3d",   (2, None, True)),
    (342.0, 350.5,"arch", ("crew.jpg",)),
    (350.5, 359.0,"3d",   (8, [(420, 125, ["85,000 FEET", "MACH 3.2 CRUISE"], 0.12, 0.88)], False)),
    (359.0, 367.5,"vid",  ("v_flight.webm",)),
    (367.5, 375.57,"nasa",("nasa_sr71_sierra_flight.jpg", None)),

    # CHAPTER 8 (375.57 .. 426.99s): 3,551 Combat Sorties, Zero Shootdowns & Immortality
    (375.57,384.5,"3d",   (7, [(440, 125, ["3,551 COMBAT", "SORTIES FLOWN"], 0.12, 0.88)], True)),
    (384.5, 393.5,"nasa", ("nasa_sr71_inflight_side.jpg", None)),
    (393.5, 402.5,"vid",  ("v_takeoff.webm",)),
    (402.5, 411.0,"arch", ("sunset.jpg",)),
    (411.0, 419.0,"3d",   (8, [(440, 125, ["2,193.2 MPH", "ABSOLUTE RECORD"], 0.12, 0.88)], True)),
    (419.0, 427.5,"3d",   (1, None, False)),
]

for f in range(f_start, f_end + 1):
    t = (f - 1) / 30.0
    seg = TIMELINE[-1]
    for s in TIMELINE:
        if s[0] <= t < s[1]:
            seg = s
            break
    t0, t1, stype, payload = seg
    u = max(0.0, min(1.0, (t - t0) / max(1e-6, t1 - t0)))

    if stype == "3d":
        seq_id, l_cfg, rev = payload
        img = render_pure_3d_scene(seq_id, u, l_cfg, rev)
    elif stype == "nasa":
        fn, l_cfg = payload
        img = render_pure_nasa_16x9(fn, u, l_cfg)
    elif stype == "vid":
        img = render_pure_archival_video_16x9(payload[0], u)
    elif stype == "arch":
        img = render_pure_archival_4x3_filmgate(payload[0], u)
    elif stype == "chart":
        img = render_ford_chart(u, payload[0])

    cv2.imwrite(os.path.join(out_dir, f"frame_{f:05d}.jpg"), img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

print(f"Rendered pure master shard frames {f_start}..{f_end}")
