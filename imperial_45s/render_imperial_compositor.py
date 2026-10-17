import os, sys, json, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
FPS = 30.0

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(ROOT, "fonts")
ASSET_DIR = os.path.join(ROOT, "assets")

def get_font(name, size):
    p = os.path.join(FONT_DIR, name)
    if os.path.exists(p):
        return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def ease_out_cubic(t):
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) ** 3

def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, float(t)))
    return 4 * t * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2

def draw_perspective_grid_bg(t_sec, tilt_strength=1.0):
    """Dark Noir #050507 background with subtle 3D perspective wireframe floor grid & radial spotlight."""
    img = np.full((H, W, 3), (8, 6, 5), dtype=np.uint8) # BGR for #050608
    # Radial spotlight in center
    yy, xx = np.mgrid[0:H, 0:W]
    dist2 = ((xx - W * 0.5) / (W * 0.52)) ** 2 + ((yy - H * 0.52) / (H * 0.52)) ** 2
    glow = np.exp(-dist2 * 1.65)
    img[:, :, 0] = np.clip(img[:, :, 0] + glow * 22, 0, 255).astype(np.uint8)
    img[:, :, 1] = np.clip(img[:, :, 1] + glow * 19, 0, 255).astype(np.uint8)
    img[:, :, 2] = np.clip(img[:, :, 2] + glow * 18, 0, 255).astype(np.uint8)

    overlay = img.copy()
    # 3D perspective grid lines across full canvas with subtle drift
    drift = (t_sec * 18.0) % 64.0
    for x in range(-400, W + 400, 64):
        x_top = int(W * 0.5 + (x - W * 0.5) * (0.72 if tilt_strength > 0.5 else 0.95))
        x_bot = int(W * 0.5 + (x - W * 0.5) * (1.28 if tilt_strength > 0.5 else 1.05))
        cv2.line(overlay, (x_top, 0), (x_bot, H), (42, 40, 38), 1, cv2.LINE_AA)
    for y_idx in range(20):
        y = int(((y_idx * 64 + drift) % (H + 64)))
        cv2.line(overlay, (0, y), (W, y), (42, 40, 38), 1, cv2.LINE_AA)

    # Blend grid more strongly near center, fading at edges
    alpha = (glow * 0.42)[:, :, None]
    out = (img.astype(np.float32) * (1.0 - alpha) + overlay.astype(np.float32) * alpha).astype(np.uint8)
    return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))

_GEO_CACHE = None
def get_geojson():
    global _GEO_CACHE
    if _GEO_CACHE is None:
        p = os.path.join(ASSET_DIR, "med_countries_50m.geojson")
        with open(p, "r") as f:
            _GEO_CACHE = json.load(f)["features"]
    return _GEO_CACHE

def make_collector_card(card_img_name, top_banner, bottom_title, bottom_sub, stamp_text=None, stamp_prog=0.0, w=320, h=430):
    """Creates a tactile cream archival collector card like Imperial's C. IVLIVS CAESAR & Legionary cards."""
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    # Cream archival paper card body with subtle inner border
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=8, fill=(238, 234, 226, 255), outline=(195, 188, 176, 255), width=2)
    draw.rectangle([12, 12, w - 13, h - 13], outline=(160, 152, 140, 180), width=1)

    # Top crimson banner
    if top_banner:
        draw.rectangle([22, 20, w - 22, 46], fill=(196, 24, 36, 255))
        f_ban = get_font("Cinzel-Bold.ttf", 17)
        bb = draw.textbbox((0, 0), top_banner, font=f_ban)
        draw.text(((w - (bb[2] - bb[0])) // 2, 24), top_banner, font=f_ban, fill=(248, 245, 240, 255))

    # Central engraving image
    img_p = os.path.join(ASSET_DIR, card_img_name)
    if os.path.exists(img_p):
        art = Image.open(img_p).convert("RGBA")
        target_w, target_h = w - 48, h - 155
        art = art.resize((target_w, target_h), Image.Resampling.LANCZOS)
        card.paste(art, (24, 56), art)
        draw.rectangle([24, 56, 24 + target_w, 56 + target_h], outline=(90, 85, 78, 200), width=1)

    # Bottom cursive/serif signature or title (scaled to card width w)
    scale_f = w / 320.0
    if not (stamp_text and stamp_prog > 0.1):
        f_bot = get_font("Cinzel-Bold.ttf", max(10, int(19 * scale_f)))
        bb = draw.textbbox((0, 0), bottom_title, font=f_bot)
        draw.text(((w - (bb[2] - bb[0])) // 2, h - int(82 * scale_f)), bottom_title, font=f_bot, fill=(35, 32, 28, 255))

        if bottom_sub:
            f_sub = get_font("Montserrat-SemiBold.ttf", max(8, int(13 * scale_f)))
            bb2 = draw.textbbox((0, 0), bottom_sub, font=f_sub)
            draw.text(((w - (bb2[2] - bb2[0])) // 2, h - int(54 * scale_f)), bottom_sub, font=f_sub, fill=(185, 24, 34, 255))

    # Optional crimson rubber stamp [ TOO POWERFUL ]
    if stamp_text and stamp_prog > 0.01:
        sp = ease_out_cubic(stamp_prog)
        st_img = Image.new("RGBA", (260, 56), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st_img)
        alpha = int(245 * sp)
        sd.rectangle([4, 4, 255, 51], fill=(238, 234, 226, int(245 * sp)), outline=(198, 22, 32, alpha), width=3)
        sd.rectangle([9, 9, 250, 46], outline=(198, 22, 32, int(alpha * 0.7)), width=1)
        f_st = get_font("Montserrat-Bold.ttf", 21)
        bb_s = sd.textbbox((0, 0), stamp_text, font=f_st)
        sd.text(((260 - (bb_s[2] - bb_s[0])) // 2, 14), stamp_text, font=f_st, fill=(198, 22, 32, alpha))
        st_rot = st_img.rotate(4.5, expand=True, resample=Image.Resampling.BICUBIC)
        card.alpha_composite(st_rot, ((w - st_rot.width) // 2, h - 84))

    return card

def render_scene2_bento_dossier(local_t):
    """
    Scene 2 (12.0s - 18.0s, local_t = 0.0..6.0s):
    Dynamic Unfolding 3-Column Bento Dossier:
      - Col 1: Tactile C. IVLIVS CAESAR collector card + [TOO POWERFUL] red stamp
      - Col 2: POLITICAL CAREER vertical timeline + red brush highlight on Consul & Dictator
      - Col 3 (unfolds at local_t = 2.0s): MILITARY CAREER + glowing crimson GAUL map
    """
    canvas = draw_perspective_grid_bg(local_t, tilt_strength=0.4).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Unfold progress for 3rd column (starts at local_t = 1.8s, completes at 3.0s)
    unfold = ease_in_out_cubic((local_t - 1.8) / 1.2)
    entry = ease_out_cubic(local_t / 0.7)

    col1_w = 380
    col2_w = 470
    col3_w = int(490 * unfold)
    box_h = 540
    total_w = col1_w + col2_w + col3_w
    x0 = (W - total_w) // 2
    y0 = (H - box_h) // 2 + int((1.0 - entry) * 40)

    f_hdr = get_font("Oswald-Bold.ttf", 34)
    f_title = get_font("Montserrat-Bold.ttf", 24)
    f_sub = get_font("Montserrat-Medium.ttf", 17)
    f_small = get_font("Montserrat-SemiBold.ttf", 14)

    # Column 1 & 2 dark translucent interior
    draw.rectangle([x0, y0, x0 + col1_w + col2_w, y0 + box_h], fill=(14, 15, 18, 235), outline=(235, 235, 240, 255), width=2)
    draw.line([(x0 + col1_w, y0), (x0 + col1_w, y0 + box_h)], fill=(235, 235, 240, 255), width=2)

    # Header above Column 2: POLITICAL CAREER
    draw.text((x0 + col1_w + 24, y0 - 48), "POLITICAL CAREER", font=f_hdr, fill=(245, 245, 248, 255))

    # Column 1: Collector Card of Julius Caesar with subtle 3D hover & drop shadow
    stamp_p = max(0.0, min(1.0, (local_t - 1.1) / 0.45))
    card = make_collector_card("card_caesar_coin.png", "C. IVLIVS CAESAR", "Gaius Julius Caesar", "100 BC – 44 BC", stamp_text="TOO POWERFUL", stamp_prog=stamp_p, w=316, h=460)
    # Shadow
    shadow = Image.new("RGBA", (336, 480), (0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    cx = x0 + (col1_w - 316) // 2
    cy = y0 + (box_h - 460) // 2
    canvas.alpha_composite(shadow, (cx + 4, cy + 8))
    canvas.alpha_composite(card, (cx, cy))

    # Column 2: Vertical Political Career Timeline
    tl_x = x0 + col1_w + 46
    items = [
        ("Consul", "59, 48, 46, 45, 44 BC", 0.35, True),
        ("Dictator in Perpetuity", "49 – 44 BC (Supreme Power)", 0.75, True),
        ("Governor / Proconsul", "58 – 49 BC (Cisalpine & Transalpine)", 1.15, False),
        ("Praetor & Pontifex Maximus", "63 – 62 BC (Chief Priest of Rome)", 1.50, False),
    ]
    # Vertical line
    draw.line([(tl_x, y0 + 75), (tl_x, y0 + box_h - 75)], fill=(180, 182, 190, 220), width=2)
    # Horizontal connector arrow from Col 1 card to Col 2 timeline
    draw.line([(x0 + col1_w - 18, y0 + box_h // 2), (tl_x, y0 + box_h // 2)], fill=(210, 210, 218, 220), width=2)

    for idx, (role, dates, t_appear, is_red_hi) in enumerate(items):
        p_item = ease_out_cubic((local_t - t_appear) / 0.45)
        if p_item <= 0.01:
            continue
        iy = y0 + 75 + idx * 122
        alpha = int(255 * p_item)

        # Red marker highlighter brush behind Consul & Dictator
        if is_red_hi and local_t > t_appear + 0.35:
            hp = ease_out_cubic((local_t - (t_appear + 0.35)) / 0.45)
            bb_r = draw.textbbox((0, 0), role, font=f_title)
            rw = int(((bb_r[2] - bb_r[0]) + 24) * hp)
            draw.rounded_rectangle([tl_x + 22, iy - 14, tl_x + 22 + rw, iy + 20], radius=4, fill=(198, 22, 34, 215))

        # Node circle
        draw.ellipse([tl_x - 8, iy - 8, tl_x + 8, iy + 8], fill=(18, 19, 24, alpha), outline=(245, 245, 250, alpha), width=3)
        draw.text((tl_x + 28, iy - 14), role, font=f_title, fill=(248, 248, 252, alpha))
        draw.text((tl_x + 28, iy + 20), dates, font=f_sub, fill=(175, 178, 188, alpha))

    # Column 3: Unfolding Military Career & Map of Gaul
    if unfold > 0.02:
        col3_x0 = x0 + col1_w + col2_w
        # Render Column 3 on a fixed 490x540 sub-canvas and crop horizontally by col3_w
        c3 = Image.new("RGBA", (490, box_h), (14, 15, 18, 235))
        d3 = ImageDraw.Draw(c3)

        # Render vector map of Western Europe & Gaul inside c3
        feats = get_geojson()
        def lonlat_to_c3(lon, lat):
            # Lon: -9..18 -> x: 15..475, Lat: 36..54 -> y: 500..40
            mx = (lon - (-8.5)) / (17.5 - (-8.5)) * 460.0 + 15.0
            my = (53.5 - lat) / (53.5 - 36.5) * 460.0 + 40.0
            return (mx, my)

        for feat in feats:
            name = feat["properties"].get("NAME") or feat["properties"].get("ADMIN") or ""
            geom = feat["geometry"]
            polys = geom["coordinates"] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
            is_gaul = name in ("France", "Belgium", "Switzerland")
            is_roman = name in ("Italy", "Spain")
            for ring in polys:
                pts = [lonlat_to_c3(pt[0], pt[1]) for pt in ring]
                if len(pts) < 3:
                    continue
                if is_gaul:
                    d3.polygon(pts, fill=(198, 22, 34, int(230 * unfold)), outline=(255, 110, 115, 255))
                elif is_roman:
                    d3.polygon(pts, fill=(45, 18, 22, 200), outline=(175, 45, 55, 220))
                else:
                    d3.polygon(pts, fill=(24, 26, 30, 180), outline=(95, 98, 106, 170))

        # Bold GAUL label over France
        gx, gy = lonlat_to_c3(2.2, 46.8)
        f_gaul = get_font("Montserrat-Bold.ttf", 30)
        d3.text((gx - 42, gy - 16), "GAUL", font=f_gaul, fill=(252, 250, 248, 255))
        d3.text((gx - 55, gy + 18), "58 – 50 BC", font=f_small, fill=(255, 210, 210, 240))

        # Legend box top-right inside Column 3
        d3.rounded_rectangle([235, 18, 472, 82], radius=4, fill=(10, 11, 14, 220), outline=(120, 122, 130, 180), width=1)
        d3.rectangle([248, 30, 268, 42], fill=(198, 22, 34, 255))
        d3.text((278, 27), "CAESAR'S CONQUESTS", font=f_small, fill=(240, 240, 245, 255))
        d3.rectangle([248, 54, 268, 66], fill=(45, 18, 22, 255), outline=(198, 22, 34, 255), width=2)
        d3.text((278, 51), "EXISTING PROVINCES", font=f_small, fill=(200, 202, 210, 255))

        d3.rectangle([0, 0, col3_w - 1, box_h - 1], outline=(235, 235, 240, 255), width=2)
        c3_crop = c3.crop((0, 0, col3_w, box_h))
        canvas.alpha_composite(c3_crop, (col3_x0, y0))

        # Header above Column 3
        if col3_w > 180:
            draw.text((col3_x0 + 24, y0 - 48), "MILITARY CAREER", font=f_hdr, fill=(245, 245, 248, int(255 * unfold)))
        # Connector arrow from Col 2 to Col 3
        draw.line([(col3_x0 - 24, y0 + 200), (col3_x0 + 24, y0 + 200)], fill=(235, 235, 240, 255), width=2)

    # Academic source citation bottom-right
    f_cit = get_font("Montserrat-Medium.ttf", 14)
    draw.text((x0, y0 + box_h + 18), "Source: T.R.S. Broughton, The Magistrates of the Roman Republic (1952) • Caesar, Commentarii de Bello Gallico (50 BC)", font=f_cit, fill=(140, 144, 154, 220))
    return canvas.convert("RGB")


def render_scene3b_crimson_poster(local_t):
    """
    Scene 3 Part B (21.0s - 24.0s, local_t = 0.0..3.0s):
    Full-screen Crimson Red Editorial Poster: MAN OF THE PEOPLE*
    with B&W classical marble bust & dark speech-bubble quote cards.
    """
    # Deep crimson red background (#B61A24) with subtle radial vignette
    img = np.zeros((H, W, 3), dtype=np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    dist2 = ((xx - W * 0.5) / (W * 0.6)) ** 2 + ((yy - H * 0.48) / (H * 0.6)) ** 2
    vig = np.clip(1.08 - dist2 * 0.42, 0.58, 1.05)
    img[:, :, 0] = np.clip(192 * vig, 0, 255).astype(np.uint8) # R
    img[:, :, 1] = np.clip(24 * vig, 0, 255).astype(np.uint8)  # G
    img[:, :, 2] = np.clip(32 * vig, 0, 255).astype(np.uint8)  # B

    canvas = Image.fromarray(img).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Central B&W Marble Bust cutout (from bust_decimus_brutus.png or ref_caesar_standing head/bust)
    bust_p = os.path.join(ASSET_DIR, "bust_decimus_brutus.png")
    if os.path.exists(bust_p):
        b_cv = cv2.imread(bust_p)
        gray = cv2.cvtColor(b_cv, cv2.COLOR_BGR2GRAY)
        # Clean alpha mask from black background
        alpha = np.clip((gray.astype(np.float32) - 12.0) * 6.0, 0, 255).astype(np.uint8)
        alpha = cv2.GaussianBlur(alpha, (5, 5), 0)
        # Enhance contrast of marble
        hi_gray = np.clip((gray.astype(np.float32) - 20.0) * 1.25 + 20.0, 0, 255).astype(np.uint8)
        bust_rgba = Image.fromarray(np.dstack([hi_gray, hi_gray, hi_gray, alpha]))
        scale_p = 0.96 + 0.04 * ease_out_cubic(local_t / 3.0)
        bw, bh = int(520 * scale_p), int(520 * scale_p)
        bust_rgba = bust_rgba.resize((bw, bh), Image.Resampling.LANCZOS)
        canvas.alpha_composite(bust_rgba, ((W - bw) // 2, 165))

    # Giant stacked typography: MAN / OF THE / PEOPLE*
    f_giant = get_font("Montserrat-Bold.ttf", 112)
    f_thin = get_font("Montserrat-Medium.ttf", 58)

    p1 = ease_out_cubic(local_t / 0.4)
    p2 = ease_out_cubic((local_t - 0.18) / 0.45)

    if p1 > 0.01:
        draw.text((510, 520 + int((1 - p1) * 25)), "MAN", font=f_giant, fill=(248, 248, 250, int(255 * p1)))
    if p2 > 0.01:
        draw.text((615, 628 + int((1 - p2) * 25)), "OF THE", font=f_thin, fill=(235, 232, 232, int(255 * p2)))
        draw.text((835, 602 + int((1 - p2) * 25)), "PEOPLE*", font=f_giant, fill=(248, 248, 250, int(255 * p2)))

    # Two dark charcoal speech-bubble callout cards on Left and Right
    f_q = get_font("Montserrat-SemiBold.ttf", 22)
    f_c = get_font("DejaVuSerif.ttf", 16)

    q1_p = ease_out_cubic((local_t - 0.45) / 0.45)
    if q1_p > 0.01:
        qx, qy = 330, 310 + int((1 - q1_p) * 20)
        al = int(245 * q1_p)
        draw.rounded_rectangle([qx, qy, qx + 410, qy + 118], radius=24, fill=(14, 14, 16, al))
        # Speech pointer triangle toward bust
        draw.polygon([(qx + 410, qy + 55), (qx + 445, qy + 72), (qx + 395, qy + 88)], fill=(14, 14, 16, al))
        draw.text((qx + 28, qy + 26), "BREAD & GRAIN FOR", font=f_q, fill=(215, 38, 46, al))
        draw.text((qx + 28, qy + 58), "320,000 CITIZENS!!", font=f_q, fill=(215, 38, 46, al))
        draw.text((qx + 245, qy + 128), "— Suetonius, §41", font=f_c, fill=(245, 240, 240, al))

    q2_p = ease_out_cubic((local_t - 0.85) / 0.45)
    if q2_p > 0.01:
        qx, qy = 1165, 335 + int((1 - q2_p) * 20)
        al = int(245 * q2_p)
        draw.rounded_rectangle([qx, qy, qx + 435, qy + 118], radius=24, fill=(14, 14, 16, al))
        draw.polygon([(qx, qy + 58), (qx - 35, qy + 72), (qx + 15, qy + 88)], fill=(14, 14, 16, al))
        draw.text((qx + 28, qy + 26), "LAND REFORM FOR", font=f_q, fill=(215, 38, 46, al))
        draw.text((qx + 28, qy + 58), "VETERANS & PLEBEIANS", font=f_q, fill=(215, 38, 46, al))
        draw.text((qx + 250, qy + 128), "— Appian, BC 2.10", font=f_c, fill=(245, 240, 240, al))

    # Footnote at bottom
    f_foot = get_font("Montserrat-Medium.ttf", 15)
    fn = "*Passed agrarian & grain laws through the Popular Assembly, bypassing the Optimate Senate faction (59–44 BC)."
    bb = draw.textbbox((0, 0), fn, font=f_foot)
    draw.text(((W - (bb[2] - bb[0])) // 2, H - 52), fn, font=f_foot, fill=(245, 235, 235, 225))
    return canvas.convert("RGB")


def render_scene4_tilted_relief_map(local_t):
    """
    Scene 4 (24.0s - 30.0s, local_t = 0.0..6.0s):
    3D Tilted Topographic Relief Map of Italy, Cisalpine Gaul & the Mediterranean
    over a White 3D Perspective Wireframe Grid, with 3D Collector Cards sliding
    across the Rubicon toward Rome + Bottom Chronological Timeline Scrubber.
    """
    # Create flat high-res map canvas (2200 x 1400) then warp in 3D perspective with OpenCV!
    mw, mh = 2200, 1400
    flat = Image.new("RGBA", (mw, mh), (7, 8, 11, 255))
    fd = ImageDraw.Draw(flat)

    # Draw latitude/longitude wireframe grid on flat canvas before 3D perspective warp
    for gx in range(0, mw, 90):
        fd.line([(gx, 0), (gx, mh)], fill=(65, 68, 76, 175), width=2)
    for gy in range(0, mh, 90):
        fd.line([(0, gy), (mw, gy)], fill=(65, 68, 76, 175), width=2)

    feats = get_geojson()
    def lonlat_to_map(lon, lat):
        # Lon: -6..26 -> 100..2100, Lat: 34..50 -> 1300..100
        x = (lon - (-5.0)) / (25.0 - (-5.0)) * 1950.0 + 120.0
        y = (49.5 - lat) / (49.5 - 34.5) * 1200.0 + 100.0
        return (x, y)

    for feat in feats:
        name = feat["properties"].get("NAME") or feat["properties"].get("ADMIN") or ""
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
        is_caesar = name in ("Italy", "France")
        is_pompey = name in ("Spain", "Greece", "Albania", "Turkey")
        for ring in polys:
            pts = [lonlat_to_map(pt[0], pt[1]) for pt in ring]
            if len(pts) < 3:
                continue
            if is_caesar:
                # Extruded 3D shadow offset
                pts_sh = [(px + 8, py + 12) for px, py in pts]
                fd.polygon(pts_sh, fill=(85, 8, 14, 220))
                fd.polygon(pts, fill=(205, 22, 34, 245), outline=(255, 130, 135, 255))
            elif is_pompey:
                pts_sh = [(px + 8, py + 12) for px, py in pts]
                fd.polygon(pts_sh, fill=(10, 28, 95, 220))
                fd.polygon(pts, fill=(28, 74, 215, 230), outline=(120, 165, 255, 255))
            else:
                fd.polygon(pts, fill=(22, 24, 30, 235), outline=(92, 96, 108, 210))

    # Overlay subtle wireframe grid ON TOP of the red/blue territories too (exact Imperial look!)
    for gx in range(0, mw, 90):
        fd.line([(gx, 0), (gx, mh)], fill=(255, 255, 255, 38), width=1)
    for gy in range(0, mh, 90):
        fd.line([(0, gy), (mw, gy)], fill=(255, 255, 255, 38), width=1)

    # Map labels on the 3D surface: CISALPINE GAUL, RUBICON, ROME
    f_map_lg = get_font("Oswald-Bold.ttf", 46)
    f_map_sm = get_font("Montserrat-Bold.ttf", 28)
    cg_x, cg_y = lonlat_to_map(9.2, 45.6)
    rm_x, rm_y = lonlat_to_map(12.5, 41.9)
    rb_x, rb_y = lonlat_to_map(12.4, 44.1)

    fd.text((cg_x - 140, cg_y - 55), "CISALPINE GAUL", font=f_map_lg, fill=(250, 250, 252, 255))
    # Rubicon river glowing white/cyan line across northern Italy
    fd.line([(rb_x - 75, rb_y + 10), (rb_x + 55, rb_y - 12)], fill=(255, 255, 255, 255), width=5)
    fd.text((rb_x + 68, rb_y - 24), "RUBICON (49 BC)", font=f_map_sm, fill=(255, 235, 190, 255))
    fd.ellipse([rm_x - 10, rm_y - 10, rm_x + 10, rm_y + 10], fill=(255, 255, 255, 255))
    fd.text((rm_x - 135, rm_y + 12), "ROME", font=f_map_lg, fill=(250, 250, 252, 255))

    # 3D Perspective Homography Transform (camera tilting and slowly pushing in over Italy)
    cam_push = ease_in_out_cubic(local_t / 6.0) * 55.0
    src_pts = np.float32([
        [180 + cam_push, 110 + cam_push * 0.5],
        [2020 - cam_push, 110 + cam_push * 0.5],
        [2180, 1320],
        [20, 1320]
    ])
    dst_pts = np.float32([
        [240, 40],
        [W - 240, 40],
        [W + 180, H - 110],
        [-180, H - 110]
    ])
    H_mat = cv2.getPerspectiveTransform(src_pts, dst_pts)
    flat_bgr = cv2.cvtColor(np.array(flat), cv2.COLOR_RGBA2BGR)
    warped_bgr = cv2.warpPerspective(flat_bgr, H_mat, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(8, 6, 5))

    canvas = Image.fromarray(cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Helper to project (lon, lat) through H_mat to screen (sx, sy)
    def project_pt(lon, lat):
        mx, my = lonlat_to_map(lon, lat)
        v = np.array([mx, my, 1.0], dtype=np.float64)
        p = H_mat @ v
        return (float(p[0] / p[2]), float(p[1] / p[2]))

    # Animate 2 miniature 3D Collector Cards sliding from Cisalpine Gaul (9.5, 45.2) across Rubicon down to Rome (12.5, 41.9)
    slide_p = ease_in_out_cubic(max(0.0, min(1.0, (local_t - 0.5) / 3.8)))
    cur_lon = 9.5 + (12.5 - 9.5) * slide_p
    cur_lat = 45.2 + (41.9 - 45.2) * slide_p
    sx_c, sy_c = project_pt(cur_lon, cur_lat)
    sx_start, sy_start = project_pt(9.5, 45.2)

    # Glowing trajectory line behind the sliding cards
    draw.line([(sx_start, sy_start), (sx_c, sy_c)], fill=(255, 240, 200, 240), width=4)

    card_c = make_collector_card("card_caesar_coin.png", "CAESAR", "Julius Caesar", "PROCONSUL", w=130, h=176).rotate(-8, expand=True, resample=Image.Resampling.BICUBIC)
    card_l = make_collector_card("card_legionary.png", "LEGIO XIII", "13th Legion", "LOYALISTS", w=130, h=176).rotate(7, expand=True, resample=Image.Resampling.BICUBIC)

    canvas.alpha_composite(card_l, (int(sx_c - 15), int(sy_c - 110)))
    canvas.alpha_composite(card_c, (int(sx_c - 115), int(sy_c - 125)))

    # Faction Callout Pill Boxes (CAESAR'S FACTION vs POMPEY'S FACTION)
    f_fac = get_font("Montserrat-Bold.ttf", 20)
    f_sm = get_font("Montserrat-SemiBold.ttf", 14)
    f_tiny = get_font("Montserrat-Medium.ttf", 12)

    draw.rounded_rectangle([140, 220, 410, 266], radius=4, fill=(245, 245, 248, 250), outline=(198, 22, 34, 255), width=3)
    draw.text((162, 231), "CAESAR'S FACTION", font=f_fac, fill=(198, 22, 34, 255))

    draw.rounded_rectangle([1430, 520, 1710, 566], radius=4, fill=(245, 245, 248, 250), outline=(28, 74, 215, 255), width=3)
    draw.text((1452, 531), "POMPEY'S FACTION", font=f_fac, fill=(28, 74, 215, 255))

    # Bottom Chronological Timeline Scrubber (exact Imperial style at 05:00!)
    bar_y = H - 115
    draw.rounded_rectangle([160, bar_y - 42, W - 160, H - 22], radius=6, fill=(10, 11, 15, 230), outline=(90, 94, 106, 180), width=1)
    tl_x0, tl_x1 = 230, W - 230
    draw.line([(tl_x0, bar_y), (tl_x1, bar_y)], fill=(235, 235, 242, 255), width=3)

    milestones = [
        (0.00, "RUBICON CROSSING", "JAN. 49 BC", True),
        (0.28, "CAESAR TAKES ROME", "MARCH 49 BC", False),
        (0.55, "BATTLE OF PHARSALUS", "AUG. 48 BC", True),
        (0.80, "DICTATOR FOR LIFE", "FEB. 44 BC", False),
        (1.00, "IDES OF MARCH", "MARCH 15, 44 BC", True),
    ]
    for frac, title, dt_str, is_top in milestones:
        mx = int(tl_x0 + frac * (tl_x1 - tl_x0))
        draw.line([(mx, bar_y - 12), (mx, bar_y + 12)], fill=(245, 245, 250, 255), width=2)
        ty = bar_y - 34 if is_top else bar_y + 16
        bb = draw.textbbox((0, 0), title, font=f_tiny)
        draw.text((mx - (bb[2] - bb[0]) // 2, ty), title, font=f_tiny, fill=(210, 212, 220, 245))
        bb2 = draw.textbbox((0, 0), dt_str, font=f_sm)
        draw.text((mx - (bb2[2] - bb2[0]) // 2, ty + 15 if not is_top else ty - 16), dt_str, font=f_sm, fill=(255, 255, 255, 255))

    # Moving Crimson Playhead on the Timeline
    ph_x = int(tl_x0 + slide_p * (tl_x1 - tl_x0))
    draw.line([(ph_x, bar_y - 26), (ph_x, bar_y + 26)], fill=(225, 32, 42, 255), width=4)
    draw.ellipse([ph_x - 7, bar_y - 7, ph_x + 7, bar_y + 7], fill=(225, 32, 42, 255), outline=(255, 255, 255, 255), width=2)

    return canvas.convert("RGB")


def render_decimus_brutus_dossier_overlay(base_rgb_pil, local_t):
    """
    Overlays the Character Profile Dossier Card of DECIMUS BRUTUS (15:07 in Board B)
    over the darkened 3D Curia background.
    """
    canvas = base_rgb_pil.convert("RGBA")
    # Dark Noir vignette dim
    dim_p = ease_out_cubic(local_t / 0.45)
    dim_layer = Image.new("RGBA", (W, H), (6, 7, 10, int(205 * dim_p)))
    canvas = Image.alpha_composite(canvas, dim_layer)
    draw = ImageDraw.Draw(canvas)

    bw, bh = 1040, 520
    x0 = (W - bw) // 2
    y0 = (H - bh) // 2 + int((1.0 - dim_p) * 30)
    left_w = 390

    # Left portrait box with white border
    draw.rectangle([x0, y0, x0 + left_w, y0 + bh], fill=(10, 11, 14, 245), outline=(240, 240, 245, 255), width=2)
    # Top & Bottom horizontal extension bars for the right intelligence list (exact 15:07 layout!)
    draw.line([(x0 + left_w, y0), (x0 + bw, y0)], fill=(240, 240, 245, 255), width=2)
    draw.line([(x0 + left_w, y0 + bh), (x0 + bw, y0 + bh)], fill=(240, 240, 245, 255), width=2)

    # Paste Decimus Brutus chiaroscuro marble bust inside left box
    bust_p = os.path.join(ASSET_DIR, "bust_decimus_brutus.png")
    if os.path.exists(bust_p):
        b_img = Image.open(bust_p).convert("RGBA").resize((left_w - 24, bh - 90), Image.Resampling.LANCZOS)
        canvas.alpha_composite(b_img, (x0 + 12, y0 + 16))

    f_name = get_font("Montserrat-SemiBold.ttf", 22)
    f_sub = get_font("Montserrat-Medium.ttf", 14)
    bb = draw.textbbox((0, 0), "DECIMUS BRUTUS", font=f_name)
    draw.text((x0 + (left_w - (bb[2] - bb[0])) // 2, y0 + bh - 64), "DECIMUS BRUTUS", font=f_name, fill=(245, 245, 250, 255))
    bb2 = draw.textbbox((0, 0), "LEGATE & CONSPIRATOR (85–43 BC)", font=f_sub)
    draw.text((x0 + (left_w - (bb2[2] - bb2[0])) // 2, y0 + bh - 34), "LEGATE & CONSPIRATOR (85–43 BC)", font=f_sub, fill=(175, 178, 188, 235))

    # 4 Intelligence bullets on the right with ⊕ icons
    f_item = get_font("Montserrat-Medium.ttf", 26)
    bullets = [
        (0.20, "Trusted military lieutenant in Gaul", False),
        (0.55, "Named second heir in Caesar's will", False),
        (0.90, "Owns gladiator company in the Portico", False),
        (1.25, "Conspirator who lured Caesar to the Senate", True),
    ]
    for idx, (t_b, text, is_alert) in enumerate(bullets):
        bp = ease_out_cubic((local_t - t_b) / 0.4)
        if bp <= 0.01:
            continue
        al = int(255 * bp)
        ix = x0 + left_w + 54
        iy = y0 + 82 + idx * 104
        # Circle-plus icon ⊕
        col_icon = (225, 36, 46, al) if is_alert else (235, 235, 242, al)
        draw.ellipse([ix - 13, iy + 3, ix + 13, iy + 29], outline=col_icon, width=2)
        draw.line([(ix - 7, iy + 16), (ix + 7, iy + 16)], fill=col_icon, width=2)
        draw.line([(ix, iy + 9), (ix, iy + 23)], fill=col_icon, width=2)

        t_col = (255, 95, 102, al) if is_alert else (238, 238, 244, al)
        draw.text((ix + 30, iy), text, font=f_item, fill=t_col)

    return canvas.convert("RGB")


def render_scene6a_plutarch_spotlight(local_t):
    """
    Scene 6 Part A (36.0s - 38.8s, local_t = 0.0..2.8s):
    Primary Source Academic Quote Spotlight (exact match to 12:12 & 17:27 in Board B):
    Plutarch — Parallel Lives: Life of Caesar, §66 (~100 AD).
    """
    img = np.full((H, W, 3), (8, 8, 10), dtype=np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    # Moving soft overhead reading spotlight
    spot_x = W * (0.46 + 0.08 * math.sin(local_t * 0.8))
    spot_y = H * 0.50
    dist2 = ((xx - spot_x) / (W * 0.42)) ** 2 + ((yy - spot_y) / (H * 0.38)) ** 2
    glow = np.exp(-dist2 * 1.45)
    for c in range(3):
        img[:, :, c] = np.clip(img[:, :, c] + glow * 26, 0, 255).astype(np.uint8)

    canvas = Image.fromarray(img).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    x_left, x_right = 340, W - 340
    y_top = 185

    f_author = get_font("Montserrat-Medium.ttf", 22)
    f_work = get_font("Montserrat-Bold.ttf", 32)
    f_date = get_font("Montserrat-Medium.ttf", 22)
    f_serif = get_font("DejaVuSerif.ttf", 29)
    f_serif_b = get_font("DejaVuSerif-Bold.ttf", 29)

    # Top Citation Header Bar
    draw.text((x_left, y_top), "Plutarch", font=f_author, fill=(145, 148, 158, 240))
    draw.text((x_left, y_top + 32), "Parallel Lives: Life of Caesar, §66", font=f_work, fill=(242, 242, 248, 255))
    dt_txt = "~100 AD (Primary Source)"
    bb_d = draw.textbbox((0, 0), dt_txt, font=f_date)
    draw.text((x_right - (bb_d[2] - bb_d[0]), y_top + 38), dt_txt, font=f_date, fill=(165, 168, 178, 240))
    draw.line([(x_left, y_top + 82), (x_right, y_top + 82)], fill=(215, 215, 225, 220), width=2)

    # Lines of the passage: dim context lines + bright spotlighted lines
    lines = [
        ("...At the very beginning of the attack, Casca gave him the first blow", False, 0.0),
        ("with his dagger, in the neck, a wound not mortal nor deep, as coming", False, 0.0),
        ("from one who at the outset of so bold a deed was much disturbed;", False, 0.0),
        ("and Caesar, hemmed in on all sides, whichever way he turned", True, 0.15),
        ("confronting blows of weapons aimed at his face and eyes, driven", True, 0.45),
        ("hither and thither like a wild beast, was entangled in the hands of all;", True, 0.75),
        ("for all had to take part in the sacrifice and taste of the slaughter—", True, 1.05),
        ("receiving twenty-three dagger wounds at the base of Pompey's statue.", "CRIMSON", 1.35),
    ]

    for idx, (line_str, mode, t_on) in enumerate(lines):
        ly = y_top + 125 + idx * 58
        if mode is False:
            draw.text((x_left, ly), line_str, font=f_serif, fill=(92, 95, 104, 155))
        elif mode is True:
            lp = ease_out_cubic((local_t - t_on) / 0.45)
            c_val = int(92 + (246 - 92) * lp)
            draw.text((x_left, ly), line_str, font=f_serif, fill=(c_val, c_val, min(255, c_val + 4), 255))
        elif mode == "CRIMSON":
            lp = ease_out_cubic((local_t - t_on) / 0.45)
            if lp > 0.05:
                bb_l = draw.textbbox((0, 0), line_str, font=f_serif_b)
                bw_box = int(((bb_l[2] - bb_l[0]) + 28) * lp)
                draw.rounded_rectangle([x_left - 12, ly - 8, x_left - 12 + bw_box, ly + 42], radius=4, fill=(198, 22, 34, int(235 * lp)))
            c_val = int(95 + (255 - 95) * lp)
            draw.text((x_left, ly), line_str, font=f_serif_b, fill=(c_val, c_val, c_val, 255))

    draw.line([(x_left, y_top + 635), (x_right, y_top + 635)], fill=(140, 142, 152, 180), width=1)
    return canvas.convert("RGB")


def overlay_scene0_curia(base_rgb_pil, local_t):
    """
    Overlays Imperial's tracked 3D Character Callout (DICTATOR / JULIUS CAESAR)
    and Bottom-Left Black Date Stamp Card (15TH OF MARCH / 44 BC) onto Scene 0.
    """
    canvas = base_rgb_pil.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Caesar's head screen position as camera slowly cranes up & dollies back over 6.0s
    u_prog = local_t / 6.0
    cx = int(W * 0.50)
    cy = int(H * (0.31 - 0.05 * u_prog))

    p_call = ease_out_cubic((local_t - 0.35) / 0.55)
    if p_call > 0.01:
        al = int(255 * p_call)
        f_role = get_font("Montserrat-SemiBold.ttf", 15)
        f_name = get_font("Montserrat-Bold.ttf", 30)
        # Pointer line from Caesar's head up to label
        draw.line([(cx, cy - 10), (cx, cy - 52)], fill=(255, 255, 255, al), width=2)
        draw.ellipse([cx - 4, cy - 14, cx + 4, cy - 6], fill=(255, 255, 255, al))

        role_s = "DICTATOR IN PERPETUITY"
        name_s = "JULIUS CAESAR"
        b1 = draw.textbbox((0, 0), role_s, font=f_role)
        b2 = draw.textbbox((0, 0), name_s, font=f_name)
        # Subtle dark backdrop pill for legibility
        mw = max(b1[2] - b1[0], b2[2] - b2[0]) + 36
        draw.rounded_rectangle([cx - mw // 2, cy - 122, cx + mw // 2, cy - 52], radius=4, fill=(8, 9, 12, int(175 * p_call)))
        draw.text((cx - (b1[2] - b1[0]) // 2, cy - 114), role_s, font=f_role, fill=(210, 214, 224, al))
        draw.text((cx - (b2[2] - b2[0]) // 2, cy - 92), name_s, font=f_name, fill=(255, 255, 255, al))

    # Bottom-Left Black Date Stamp Card (15TH OF MARCH / 44 BC)
    p_date = ease_out_cubic((local_t - 0.15) / 0.5)
    if p_date > 0.01:
        al = int(250 * p_date)
        bx, by = 56, H - 158
        draw.rectangle([bx, by, bx + 285, by + 104], fill=(8, 8, 10, al), outline=(255, 255, 255, int(60 * p_date)), width=1)
        draw.rectangle([bx, by, bx + 6, by + 104], fill=(198, 22, 34, al))
        f_d1 = get_font("Montserrat-Medium.ttf", 21)
        f_d2 = get_font("Montserrat-Bold.ttf", 40)
        draw.text((bx + 24, by + 16), "15TH OF MARCH", font=f_d1, fill=(225, 228, 235, al))
        draw.text((bx + 24, by + 46), "44 BC", font=f_d2, fill=(255, 255, 255, al))

    return canvas.convert("RGB")


def overlay_scene5a_grouping_brackets(base_rgb_pil, local_t):
    """
    Overlays Imperial's 3D Senate Faction Grouping Brackets (07:15 in Board A):
    GROUP 1: FORMER ALLIES, GROUP 2: PARDONED POMPEIANS, GROUP 3: THE LIBERATORS (60 SENATORS)
    """
    canvas = base_rgb_pil.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    f_grp = get_font("Montserrat-SemiBold.ttf", 15)
    f_title = get_font("Montserrat-Bold.ttf", 25)

    groups = [
        (0.20, 270, 340, 320, "GROUP 1", "FORMER ALLIES", (245, 245, 250)),
        (0.65, 860, 275, 340, "GROUP 2", "PARDONED POMPEIANS", (245, 245, 250)),
        (1.10, 1460, 330, 370, "GROUP 3", "THE LIBERATORS (60)", (255, 95, 102)),
    ]
    for t_on, cx, cy, span_w, g_top, g_bot, col_rgb in groups:
        p = ease_out_cubic((local_t - t_on) / 0.45)
        if p <= 0.01:
            continue
        al = int(255 * p)
        hw = int((span_w // 2) * p)
        # Draw horizontal grouping bracket ┌───────┴───────┐
        draw.line([(cx - hw, cy), (cx + hw, cy)], fill=(255, 255, 255, al), width=2)
        draw.line([(cx - hw, cy), (cx - hw, cy + 18)], fill=(255, 255, 255, al), width=2)
        draw.line([(cx + hw, cy), (cx + hw, cy + 18)], fill=(255, 255, 255, al), width=2)
        draw.line([(cx, cy - 14), (cx, cy)], fill=(255, 255, 255, al), width=2)

        b1 = draw.textbbox((0, 0), g_top, font=f_grp)
        b2 = draw.textbbox((0, 0), g_bot, font=f_title)
        mw = max(b1[2] - b1[0], b2[2] - b2[0]) + 28
        draw.rounded_rectangle([cx - mw // 2, cy - 78, cx + mw // 2, cy - 16], radius=4, fill=(8, 9, 12, int(185 * p)))
        draw.text((cx - (b1[2] - b1[0]) // 2, cy - 72), g_top, font=f_grp, fill=(195, 200, 210, al))
        draw.text((cx - (b2[2] - b2[0]) // 2, cy - 50), g_bot, font=f_title, fill=(col_rgb[0], col_rgb[1], col_rgb[2], al))

    return canvas.convert("RGB")


def overlay_scene7_crime_scene(base_rgb_pil, local_t):
    """Overlays tracked callouts on Scene 7 Overhead Crime Scene at the base of Pompey's statue."""
    canvas = base_rgb_pil.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    p = ease_out_cubic((local_t - 0.35) / 0.55)
    if p > 0.01:
        al = int(255 * p)
        f_sm = get_font("Montserrat-SemiBold.ttf", 15)
        f_lg = get_font("Montserrat-Bold.ttf", 26)

        # Callout on Pompey's Statue at top center
        px, py = W // 2, 165
        draw.rounded_rectangle([px - 165, py - 62, px + 165, py - 4], radius=4, fill=(8, 9, 12, int(190 * p)))
        draw.text((px - 145, py - 56), "MARBLE STATUE OF", font=f_sm, fill=(200, 204, 214, al))
        draw.text((px - 145, py - 34), "POMPEY THE GREAT", font=f_lg, fill=(255, 255, 255, al))

        # Bottom source citation
        f_cit = get_font("Montserrat-Medium.ttf", 15)
        cit = "Primary Sources: Suetonius, Divus Julius §82 • Plutarch, Life of Caesar §66 • Appian, Civil Wars 2.117"
        bb = draw.textbbox((0, 0), cit, font=f_cit)
        draw.rounded_rectangle([(W - (bb[2] - bb[0])) // 2 - 18, H - 58, (W + (bb[2] - bb[0])) // 2 + 18, H - 22], radius=4, fill=(8, 9, 12, int(200 * p)))
        draw.text(((W - (bb[2] - bb[0])) // 2, H - 49), cit, font=f_cit, fill=(215, 218, 226, al))

    # Smooth fade to black in final 0.8s (local_t = 5.2..6.0s)
    if local_t > 5.2:
        fp = ease_in_out_cubic((local_t - 5.2) / 0.8)
        fade = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * fp)))
        canvas = Image.alpha_composite(canvas, fade)

    return canvas.convert("RGB")


def overlay_scene1_complex_badge(base_rgb_pil, local_t):
    """Overlays top-right date stamp and bottom-left architectural caption on Scene 1."""
    canvas = base_rgb_pil.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    p = ease_out_cubic((local_t - 0.25) / 0.5)
    if p > 0.01:
        al = int(245 * p)
        f_sm = get_font("Montserrat-SemiBold.ttf", 15)
        f_lg = get_font("Montserrat-Bold.ttf", 24)
        bx, by = 56, H - 128
        draw.rounded_rectangle([bx, by, bx + 530, by + 76], radius=4, fill=(8, 9, 12, int(210 * p)), outline=(255, 255, 255, int(70 * p)), width=1)
        draw.rectangle([bx, by, bx + 5, by + 76], fill=(198, 22, 34, al))
        draw.text((bx + 22, by + 13), "ARCHITECTURAL CUTAWAY • CAMPUS MARTIUS, ROME", font=f_sm, fill=(195, 200, 212, al))
        draw.text((bx + 22, by + 36), "THEATRE & CURIA OF POMPEY (55 BC)", font=f_lg, fill=(255, 255, 255, al))
    return canvas.convert("RGB")


def overlay_scene3a_bust_caption(base_rgb_pil, local_t):
    """Overlays Imperial-style center-right label on the 3D Sliced Classical Marble Bust (Scene 3A)."""
    canvas = base_rgb_pil.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    p = ease_out_cubic((local_t - 0.35) / 0.5)
    if p > 0.01:
        al = int(250 * p)
        f_lg = get_font("Montserrat-Bold.ttf", 32)
        f_sm = get_font("Montserrat-SemiBold.ttf", 15)
        tx, ty = int(W * 0.57), int(H * 0.64)
        draw.text((tx, ty), "CAESAR", font=f_lg, fill=(255, 255, 255, al))
        draw.text((tx, ty + 38), "\"DICTATOR PERPETUO\"", font=f_sm, fill=(225, 42, 50, al))
        draw.text((tx, ty + 58), "\"THE POPULIST REFORMER\"", font=f_sm, fill=(200, 204, 214, al))
    return canvas.convert("RGB")


def overlay_scene6b_stab_caption(base_rgb_pil, local_t):
    """Overlays subtle bottom-left identification on Scene 6B 3D Assassination Tableau."""
    canvas = base_rgb_pil.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    p = ease_out_cubic((local_t - 0.25) / 0.45)
    if p > 0.01:
        al = int(245 * p)
        f_sm = get_font("Montserrat-SemiBold.ttf", 15)
        f_lg = get_font("Montserrat-Bold.ttf", 26)
        bx, by = 56, H - 128
        draw.rounded_rectangle([bx, by, bx + 485, by + 76], radius=4, fill=(8, 9, 12, int(210 * p)), outline=(198, 22, 34, int(180 * p)), width=1)
        draw.rectangle([bx, by, bx + 5, by + 76], fill=(198, 22, 34, al))
        draw.text((bx + 22, by + 13), "FIRST DAGGER BLOW • CURIA OF POMPEY", font=f_sm, fill=(225, 85, 92, al))
        draw.text((bx + 22, by + 36), "PUBLIUS SERVILIUS CASCA (44 BC)", font=f_lg, fill=(255, 255, 255, al))
    return canvas.convert("RGB")


if __name__ == "__main__":
    import subprocess
    if sys.argv[1] == "--render-25d-all":
        out_root = sys.argv[2]
        os.makedirs(out_root, exist_ok=True)
        ranges_25d = [
            (360,  540),  # Scene 2: Bento Dossier (180 frames)
            (630,  720),  # Scene 3B: Crimson Poster (90 frames)
            (720,  900),  # Scene 4: 3D Tilted Relief Map + Cards (180 frames)
            (1080, 1170), # Scene 6A: Plutarch Spotlight (90 frames)
        ]
        for s_f, e_f in ranges_25d:
            cdir = f"/tmp/comp_25d_{s_f:04d}"
            os.makedirs(cdir, exist_ok=True)
            for idx, f in enumerate(range(s_f, e_f)):
                scene_id = f // 180
                local_t = (f % 180) / FPS
                if scene_id == 2:
                    out_pil = render_scene2_bento_dossier(local_t)
                elif scene_id == 3:
                    out_pil = render_scene3b_crimson_poster(local_t - 3.0)
                elif scene_id == 4:
                    out_pil = render_scene4_tilted_relief_map(local_t)
                elif scene_id == 6:
                    out_pil = render_scene6a_plutarch_spotlight(local_t)
                out_pil.save(os.path.join(cdir, f"frame_{idx:04d}.png"))
            out_mp4 = os.path.join(out_root, f"part_{s_f:04d}.mp4")
            subprocess.run([
                "ffmpeg", "-y", "-framerate", "30",
                "-i", os.path.join(cdir, "frame_%04d.png"),
                "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                "-pix_fmt", "yuv420p", out_mp4
            ], check=True)
            print("Encoded 2.5D part:", out_mp4)
        sys.exit(0)

    shard_id = int(sys.argv[1])
    SHARD_3D_RANGES = [
        (0,   45),   (45,  90),   (90,  135),  (135, 180),
        (180, 225),  (225, 270),  (270, 315),  (315, 360),
        (540, 585),  (585, 630),
        (900, 945),  (945, 990),  (990, 1035), (1035, 1080),
        (1170, 1215),(1215, 1260),
        (1260, 1305),(1305, 1350),(1350, 1395),(1395, 1440),
    ]
    start_f, end_f = SHARD_3D_RANGES[shard_id]
    raw_dir = f"/tmp/imperial_shard_{shard_id:02d}"
    comp_dir = f"/tmp/imperial_comp_{shard_id:02d}"
    os.makedirs(comp_dir, exist_ok=True)

    for idx, f in enumerate(range(start_f, end_f)):
        scene_id = f // 180
        local_t = (f % 180) / FPS
        raw_p = os.path.join(raw_dir, f"raw_{f:04d}.png")
        base = Image.open(raw_p).convert("RGB")

        if scene_id == 0:
            out_pil = overlay_scene0_curia(base, local_t)
        elif scene_id == 1:
            out_pil = overlay_scene1_complex_badge(base, local_t)
        elif scene_id == 3:
            out_pil = overlay_scene3a_bust_caption(base, local_t)
        elif scene_id == 5:
            if local_t < 3.4:
                out_pil = overlay_scene5a_grouping_brackets(base, local_t)
            else:
                out_pil = render_decimus_brutus_dossier_overlay(base, local_t - 3.4)
        elif scene_id == 6:
            out_pil = overlay_scene6b_stab_caption(base, local_t - 3.0)
        elif scene_id == 7:
            out_pil = overlay_scene7_crime_scene(base, local_t)

        out_pil.save(os.path.join(comp_dir, f"frame_{idx:04d}.png"))

    out_mp4 = f"/tmp/part_{start_f:04d}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", "30",
        "-i", os.path.join(comp_dir, "frame_%04d.png"),
        "-c:v", "libx264", "-preset", "slow", "-crf", "15",
        "-pix_fmt", "yuv420p", out_mp4
    ], check=True)
    print(f"Encoded {out_mp4} ({os.path.getsize(out_mp4)} bytes)")

