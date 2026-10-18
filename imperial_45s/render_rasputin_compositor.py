#!/usr/bin/env python3
"""
1080p Razor-Sharp Compositor + Audio Mixer + MP4 Encoder for:
"THE MURDER OF GRIGORI RASPUTIN IN THE YUSUPOV PALACE (DECEMBER 30, 1916)"
- ZERO Blur Guarantee:
  * Preserves native 1920x1080 Blender frames 1:1 (no GaussianBlur bloom blend, no downscale).
  * Applies crisp UnsharpMask micro-contrast enhancement.
  * Saves intermediate frames at JPEG quality=98, subsampling=0 (4:4:4 chroma) and encodes H.264 at CRF 15.
"""
import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
VO_DIR = os.path.join(SCRIPT_DIR, "vo")


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def load_fonts():
    font_paths = [
        os.path.join(SCRIPT_DIR, "fonts", "Cinzel-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    fp = next((p for p in font_paths if os.path.exists(p)), None)
    if not fp:
        d = ImageFont.load_default()
        return {"h1": d, "h2": d, "h3": d, "body": d, "sm": d, "xs": d}
    return {
        "h1": ImageFont.truetype(fp, 38),
        "h2": ImageFont.truetype(fp, 28),
        "h3": ImageFont.truetype(fp, 22),
        "body": ImageFont.truetype(fp, 19),
        "sm": ImageFont.truetype(fp, 16),
        "xs": ImageFont.truetype(fp, 14),
    }


FONTS = load_fonts()

# Preload historical portraits once
PORTRAITS = {}
for key, fname, sz in [
    ("rasputin", "portrait_rasputin.jpg", (340, 320)),
    ("yusupov", "portrait_yusupov.jpg", (120, 156)),
    ("dmitri", "portrait_dmitri.jpg", (120, 156)),
    ("purishkevich", "portrait_purishkevich.jpg", (120, 156)),
]:
    p = os.path.join(ASSETS_DIR, fname)
    if os.path.exists(p):
        im_p = Image.open(p).convert("L")
        im_p = ImageEnhance.Contrast(im_p).enhance(1.28)
        PORTRAITS[key] = im_p.convert("RGBA").resize(sz, Image.Resampling.LANCZOS)


def apply_razor_sharp_grade(img_rgb):
    """Preserve 100% native 1920x1080 sharpness + crisp micro-detail UnsharpMask (zero blur/bloom)."""
    if img_rgb.size != (1920, 1080):
        im = img_rgb.resize((1920, 1080), Image.Resampling.LANCZOS)
    else:
        im = img_rgb
    im = im.filter(ImageFilter.UnsharpMask(radius=0.85, percent=115, threshold=2))
    return ImageEnhance.Contrast(im).enhance(1.04)


def draw_tracked_callout(d, target_xy, box_xy, box_wh, kicker, title, color_rgb, progress):
    if progress <= 0.01:
        return
    p_line = smoothstep(progress / 0.45)
    p_box = smoothstep((progress - 0.25) / 0.75)
    tx, ty = target_xy
    bx, by = box_xy
    bw, bh = box_wh
    r = int(5 * p_line)
    if r > 0:
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=(*color_rgb, 255), outline=(255, 255, 255, 230), width=2)
    elbow_x = int(lerp(tx, bx if bx > tx else bx + bw, 0.55))
    elbow_y = by + bh // 2
    cur_x = int(lerp(tx, elbow_x, p_line))
    cur_y = int(lerp(ty, elbow_y, p_line))
    d.line([(tx, ty), (cur_x, cur_y)], fill=(*color_rgb, int(255 * p_line)), width=3)
    if p_line > 0.5:
        anchor_x = bx if bx > tx else bx + bw
        cur_x2 = int(lerp(elbow_x, anchor_x, (p_line - 0.5) * 2.0))
        d.line([(elbow_x, elbow_y), (cur_x2, elbow_y)], fill=(*color_rgb, 255), width=3)
    if p_box > 0.02:
        alpha = int(242 * p_box)
        d.rectangle([bx, by, bx + bw, by + bh], fill=(12, 13, 18, alpha), outline=(*color_rgb, alpha), width=2)
        d.rectangle([bx, by, bx + 7, by + bh], fill=(*color_rgb, alpha))
        d.text((bx + 18, by + 10), kicker, fill=(*color_rgb, alpha), font=FONTS["sm"])
        d.text((bx + 18, by + 34), title, fill=(248, 245, 236, alpha), font=FONTS["h3"])


def composite_frame(frame_idx, raw_img):
    graded = apply_razor_sharp_grade(raw_img).convert("RGBA")
    ov = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    sid = min(4, max(0, frame_idx // 300))
    local_f = frame_idx - sid * 300
    u = local_f / 300.0
    theta = u * 2.0 * math.pi
    deg = int((u * 360.0) % 360)

    # ------------------------------------------------------------------
    # SCENE 0 (0..299): 360° 3D ARCHITECTURAL CUTAWAY OF YUSUPOV PALACE
    # ------------------------------------------------------------------
    if sid == 0:
        p_in = smoothstep(local_f / 28.0)
        alpha = int(242 * p_in)
        d.rectangle([48, 920, 435, 1028], fill=(10, 11, 15, alpha), outline=(215, 42, 46, alpha), width=2)
        d.rectangle([48, 920, 58, 1028], fill=(215, 42, 46, alpha))
        d.text((74, 934), "30TH OF DECEMBER", fill=(248, 244, 234, alpha), font=FONTS["h2"])
        d.text((74, 976), f"1916  //  360° ORBIT ({deg:03d}°)", fill=(225, 65, 68, alpha), font=FONTS["h3"])

        d.rectangle([1390, 42, 1872, 136], fill=(12, 14, 20, alpha), outline=(225, 185, 95, alpha), width=2)
        d.rectangle([1390, 42, 1398, 136], fill=(225, 185, 95, alpha))
        d.text((1414, 54), "YUSUPOV PALACE CUTAWAY", fill=(245, 210, 120, alpha), font=FONTS["h3"])
        d.text((1414, 88), "94 MOIKA EMBANKMENT // SOUNDPROOFED CELLAR", fill=(195, 202, 215, alpha), font=FONTS["sm"])

    # ------------------------------------------------------------------
    # SCENE 1 (300..599): 360° 3D SOUNDPROOFED BASEMENT TABLEAU
    # ------------------------------------------------------------------
    elif sid == 1:
        p_in = smoothstep(local_f / 25.0)
        alpha = int(242 * p_in)
        d.rectangle([48, 920, 435, 1028], fill=(10, 11, 15, alpha), outline=(215, 42, 46, alpha), width=2)
        d.rectangle([48, 920, 58, 1028], fill=(215, 42, 46, alpha))
        d.text((74, 934), "30TH OF DECEMBER", fill=(248, 244, 234, alpha), font=FONTS["h2"])
        d.text((74, 976), f"01:15 AM  //  360° ORBIT ({deg:03d}°)", fill=(225, 65, 68, alpha), font=FONTS["h3"])

        rx = int(680 + 85 * math.sin(theta * 4.0))
        ry = int(430 + 25 * math.cos(theta * 4.0))
        draw_tracked_callout(
            d,
            (rx, ry),
            (60, 140),
            (360, 78),
            "IMPERIAL ADVISOR & MYSTIC",
            "GRIGORI RASPUTIN",
            (235, 58, 62),
            clamp((local_f - 18) / 40.0),
        )

        yx = int(1240 - 85 * math.sin(theta * 4.0))
        yy = int(480 + 25 * math.cos(theta * 4.0))
        draw_tracked_callout(
            d,
            (yx, yy),
            (1460, 140),
            (390, 78),
            "CHIEF CONSPIRATOR // HOST",
            "PRINCE FELIX YUSUPOV",
            (235, 195, 100),
            clamp((local_f - 55) / 40.0),
        )

        draw_tracked_callout(
            d,
            (960, 565),
            (745, 920),
            (430, 76),
            "LETHAL DOSE // POTASSIUM CYANIDE",
            "MADEIRA WINE & ROSE PASTRIES",
            (215, 75, 195),
            clamp((local_f - 110) / 40.0),
        )

    # ------------------------------------------------------------------
    # SCENE 2 (600..899): BENTO NOIR DOSSIER + 360° SLICED 3D BUST
    # ------------------------------------------------------------------
    elif sid == 2:
        p_card = smoothstep(local_f / 32.0)
        cx0 = int(lerp(-420, 46, p_card))
        cy0, cw, ch = 46, 410, 960
        cx1, cy1 = cx0 + cw, cy0 + ch

        d.rectangle([cx0, cy0, cx1, cy1], fill=(18, 18, 22, 246), outline=(215, 205, 185, 245), width=2)
        d.rectangle([cx0 + 12, cy0 + 12, cx1 - 12, cy0 + 58], fill=(175, 26, 30, 255))
        d.text((cx0 + 26, cy0 + 22), "G. Y. RASPUTIN (1869–1916)", fill=(250, 246, 236, 255), font=FONTS["h3"])

        if "rasputin" in PORTRAITS and cx0 > -300:
            ov.paste(PORTRAITS["rasputin"], (cx0 + 35, cy0 + 72))
            d.rectangle([cx0 + 35, cy0 + 72, cx0 + 375, cy0 + 392], outline=(195, 185, 165, 255), width=2)

        p_stamp = smoothstep((local_f - 40) / 14.0)
        if p_stamp > 0.02:
            st_a = int(242 * p_stamp)
            d.rectangle([cx0 + 48, cy0 + 328, cx0 + 362, cy0 + 382], fill=(190, 20, 24, st_a), outline=(255, 235, 225, st_a), width=3)
            d.text((cx0 + 72, cy0 + 342), "STATUS: UNTOUCHABLE", fill=(255, 246, 240, st_a), font=FONTS["h3"])

        d.text((cx0 + 24, cy0 + 418), "IMPERIAL HOLD (1907–1916):", fill=(240, 198, 105, 255), font=FONTS["body"])
        items = [
            ("1907: Royal Healer to Tsarevich Alexei", False, 50),
            ("1915: Tsar Departs for Eastern Front", False, 75),
            ("1916: 4 Prime Ministers Purged", True, 105),
            ("1916: Supreme Wartime & Synod Vetoes", True, 140),
            ("1916: Aristocratic Plot Formed", True, 175),
        ]
        for idx_i, (txt, hi, f_trig) in enumerate(items):
            yy = cy0 + 462 + idx_i * 54
            p_row = smoothstep((local_f - f_trig) / 22.0)
            if hi and p_row > 0.02:
                bw_hi = int((cw - 36) * p_row)
                d.rectangle([cx0 + 18, yy - 4, cx0 + 18 + bw_hi, yy + 32], fill=(195, 28, 32, 235))
            d.text((cx0 + 26, yy + 2), txt, fill=(246, 243, 234, int(255 * clamp((local_f - f_trig + 15) / 20.0))), font=FONTS["sm"])

        d.line([(cx0 + 20, cy1 - 92), (cx1 - 20, cy1 - 92)], fill=(90, 95, 110, 220), width=1)
        d.text((cx0 + 24, cy1 - 76), "SOURCE: STATE ARCHIVE OF RUSSIAN", fill=(175, 180, 192, 255), font=FONTS["xs"])
        d.text((cx0 + 24, cy1 - 52), "FEDERATION (GARF) // CHANCELLERY", fill=(175, 180, 192, 255), font=FONTS["xs"])

        p_q = smoothstep((local_f - 85) / 30.0)
        if p_q > 0.02:
            qa = int(242 * p_q)
            qx0, qy0, qx1, qy1 = 1385, 760, 1876, 1024
            d.rectangle([qx0, qy0, qx1, qy1], fill=(14, 15, 20, qa), outline=(220, 45, 48, qa), width=2)
            d.rectangle([qx0, qy0, qx1, qy0 + 42], fill=(185, 26, 30, qa))
            d.text((qx0 + 16, qy0 + 10), f"DIPLOMATIC DISPATCH // NOV 1916 ({deg:03d}°)", fill=(252, 246, 236, qa), font=FONTS["sm"])
            d.text((qx0 + 18, qy0 + 58), "\"If the Emperor continues to uphold", fill=(242, 238, 228, qa), font=FONTS["body"])
            d.text((qx0 + 18, qy0 + 88), "Rasputin against the entire nation,", fill=(242, 238, 228, qa), font=FONTS["body"])
            d.text((qx0 + 18, qy0 + 118), "a catastrophe is inevitable.\"", fill=(242, 238, 228, qa), font=FONTS["body"])
            d.text((qx0 + 18, qy0 + 166), "— Sir George Buchanan", fill=(235, 195, 100, qa), font=FONTS["body"])
            d.text((qx0 + 18, qy0 + 194), "British Ambassador to Petrograd (1916)", fill=(185, 190, 205, qa), font=FONTS["sm"])

    # ------------------------------------------------------------------
    # SCENE 3 (900..1199): 360° REAL GIS 3D MAP + CONSPIRATOR CARDS
    # ------------------------------------------------------------------
    elif sid == 3:
        cards = [
            ("PRINCE FELIX YUSUPOV", "THE ARISTOCRAT HOST", "yusupov", 42, 46, (235, 192, 95), 10),
            ("GRAND DUKE DMITRI", "COUSIN OF TSAR NICHOLAS II", "dmitri", 42, 256, (230, 62, 65), 45),
            ("V. PURISHKEVICH", "MONARCHIST DUMA DEPUTY", "purishkevich", 42, 466, (85, 170, 245), 80),
        ]
        for title, role, pkey, tx0, ty0, col, f_start in cards:
            pc = smoothstep((local_f - f_start) / 28.0)
            if pc <= 0.01:
                continue
            x0 = int(lerp(-420, tx0, pc))
            y0 = ty0
            d.rectangle([x0, y0, x0 + 395, y0 + 186], fill=(14, 16, 22, 242), outline=(*col, 255), width=2)
            d.rectangle([x0, y0, x0 + 8, y0 + 186], fill=(*col, 255))
            if pkey in PORTRAITS and x0 > -200:
                ov.paste(PORTRAITS[pkey], (x0 + 18, y0 + 15))
                d.rectangle([x0 + 18, y0 + 15, x0 + 138, y0 + 171], outline=(*col, 255), width=2)
            d.text((x0 + 154, y0 + 20), title, fill=(248, 245, 236, 255), font=FONTS["body"])
            d.text((x0 + 154, y0 + 52), role, fill=(*col, 255), font=FONTS["sm"])
            d.text((x0 + 154, y0 + 96), "DESTINATION: MOIKA CANAL", fill=(200, 206, 218, 255), font=FONTS["xs"])
            d.text((x0 + 154, y0 + 124), "PACT: DECEMBER 1916", fill=(235, 80, 82, 255), font=FONTS["sm"])

        px = int(1060 + 165 * math.cos(theta))
        py = int(340 - 95 * math.sin(theta))
        draw_tracked_callout(
            d,
            (px, py),
            (1380, 120),
            (470, 82),
            "IMPERIAL CAPITAL // TARGET",
            "PETROGRAD (YUSUPOV PALACE)",
            (255, 210, 85),
            clamp((local_f - 30) / 35.0),
        )

        fx = int(960 - 150 * math.cos(theta))
        fy = int(610 + 95 * math.sin(theta))
        draw_tracked_callout(
            d,
            (fx, fy),
            (1380, 760),
            (470, 78),
            "WORLD WAR I // 1916 CRISIS",
            "COLLAPSING EASTERN FRONT",
            (235, 55, 58),
            clamp((local_f - 70) / 35.0),
        )

        sy0 = 948
        d.rectangle([42, sy0, 1878, 1034], fill=(10, 12, 18, 244), outline=(205, 44, 48, 255), width=2)
        d.text((68, sy0 + 30), "AUG 1915: TSAR AT FRONT", fill=(195, 202, 215, 255), font=FONTS["body"])
        bar_x0, bar_x1 = 420, 1430
        bar_y = sy0 + 42
        d.line([(bar_x0, bar_y), (bar_x1, bar_y)], fill=(75, 82, 96, 255), width=4)
        cur_bar_x = int(lerp(bar_x0, bar_x1, u))
        d.line([(bar_x0, bar_y), (cur_bar_x, bar_y)], fill=(235, 52, 56, 255), width=6)
        d.ellipse([cur_bar_x - 10, bar_y - 10, cur_bar_x + 10, bar_y + 10], fill=(255, 215, 90, 255), outline=(255, 255, 255, 255), width=2)
        d.text((1455, sy0 + 30), f"DEC 30, 1916 ({deg:03d}°)", fill=(255, 215, 95, 255), font=FONTS["body"])

    # ------------------------------------------------------------------
    # SCENE 4 (1200..1499): 360° OVERHEAD FORENSIC CRIME SCENE
    # ------------------------------------------------------------------
    elif sid == 4:
        p_q = smoothstep(local_f / 28.0)
        qa = int(244 * p_q)
        d.rectangle([46, 42, 790, 224], fill=(12, 13, 18, qa), outline=(215, 45, 48, qa), width=2)
        d.rectangle([46, 42, 790, 84], fill=(185, 26, 30, qa))
        d.text((66, 52), f"FORENSIC AUTOPSY // PROF. KOSOROTOV ({deg:03d}°)", fill=(252, 246, 236, qa), font=FONTS["body"])
        d.text((66, 100), "\"Three close-range revolver shots—one piercing the chest,", fill=(242, 238, 228, qa), font=FONTS["body"])
        d.text((66, 132), "a final point-blank shot through the forehead—before the", fill=(242, 238, 228, qa), font=FONTS["body"])
        d.text((66, 164), "body was dropped beneath the ice of the Malaya Nevka.\"", fill=(235, 195, 100, qa), font=FONTS["body"])

        draw_tracked_callout(
            d,
            (960, 540),
            (60, 860),
            (420, 78),
            "FORENSIC EVIDENCE // 01",
            "FALLEN VICTIM: G. RASPUTIN",
            (235, 55, 58),
            clamp((local_f - 25) / 35.0),
        )

        wx = int(960 + 185 * math.cos(theta - 0.35))
        wy = int(540 + 115 * math.sin(theta - 0.35))
        draw_tracked_callout(
            d,
            (wx, wy),
            (1410, 860),
            (460, 78),
            "FORENSIC EVIDENCE // 02",
            "WEBLEY .455 REVOLVER & SHELLS",
            (240, 198, 95),
            clamp((local_f - 65) / 35.0),
        )

        bx_t = int(960 + 165 * math.cos(theta + 0.85))
        by_t = int(540 - 135 * math.sin(theta + 0.85))
        draw_tracked_callout(
            d,
            (bx_t, by_t),
            (1410, 120),
            (460, 78),
            "FORENSIC EVIDENCE // 03",
            "BLOOD TRAIL TO MOIKA RIVER",
            (215, 75, 78),
            clamp((local_f - 105) / 35.0),
        )

    return Image.alpha_composite(graded, ov).convert("RGB")


def build_master_soundtrack(out_wav_path):
    """Assemble the 5 VO segments (paced cleanly into each 10s scene window) + dark Russian minor drone & SFX."""
    sr = 44100
    dur_s = 50.0
    total_samples = int(sr * dur_s)
    t = np.linspace(0.0, dur_s, total_samples, endpoint=False)

    drone = (
        0.045 * np.sin(2 * np.pi * 73.42 * t)
        + 0.032 * np.sin(2 * np.pi * 110.00 * t)
        + 0.022 * np.sin(2 * np.pi * 146.83 * t)
        + 0.015 * np.sin(2 * np.pi * 220.00 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * t))
    )
    beat_phase = np.mod(t, 1.0)
    heartbeat = 0.055 * np.exp(-28.0 * beat_phase) * np.sin(2 * np.pi * 52.0 * beat_phase)
    bg_mix = drone + heartbeat

    for st in [0.05, 10.0, 20.0, 30.0, 40.0]:
        idx0 = int(st * sr)
        n = min(int(1.8 * sr), total_samples - idx0)
        if n > 0:
            ts = np.linspace(0.0, n / sr, n, endpoint=False)
            bg_mix[idx0 : idx0 + n] += 0.14 * np.exp(-3.2 * ts) * np.sin(2 * np.pi * (65.0 - 22.0 * ts) * ts)

    vo_track = np.zeros(total_samples, dtype=np.float32)
    for i in range(1, 6):
        mp3_path = os.path.join(VO_DIR, f"rasputin_vo_{i}.mp3")
        if not os.path.exists(mp3_path):
            mp3_path = f"/home/user/rasputin_vo_{i}.mp3"
        if not os.path.exists(mp3_path):
            continue
        tmp_wav = f"/tmp/vo_seg_{i}.wav"
        probe = subprocess.check_output(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_path]
        ).decode().strip()
        orig_dur = float(probe)
        target_max = 9.35
        tempo = max(1.0, min(1.65, orig_dur / target_max))
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "quiet", "-i", mp3_path,
                "-af", f"silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,atempo={tempo:.3f}",
                "-ar", str(sr), "-ac", "1", "-f", "s16le", tmp_wav,
            ],
            check=True,
        )
        pcm = np.fromfile(tmp_wav, dtype=np.int16).astype(np.float32) / 32768.0
        peak = np.max(np.abs(pcm)) if len(pcm) > 0 else 1.0
        if peak > 1e-4:
            pcm = pcm / peak * 0.88
        start_idx = int(((i - 1) * 10.0 + 0.25) * sr)
        end_idx = min(total_samples, start_idx + len(pcm))
        vo_track[start_idx:end_idx] = pcm[: end_idx - start_idx]

    master = vo_track + bg_mix * 0.55
    master = np.clip(master, -0.98, 0.98)
    pcm16 = (master * 32767.0).astype(np.int16)
    stereo = np.column_stack([pcm16, pcm16]).ravel()

    import wave
    with wave.open(out_wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())
    print("Built master soundtrack:", out_wav_path)


if __name__ == "__main__":
    raw_dir = sys.argv[1]
    out_mp4 = sys.argv[2]
    out_qa = sys.argv[3]
    comp_dir = "/tmp/comp_frames"
    os.makedirs(comp_dir, exist_ok=True)

    last_valid = None
    for f in range(1500):
        fp = os.path.join(raw_dir, f"frame_{f:04d}.png")
        if os.path.exists(fp):
            last_valid = Image.open(fp).convert("RGB")
        elif last_valid is None:
            last_valid = Image.new("RGB", (1920, 1080), (10, 12, 16))
        comp = composite_frame(f, last_valid)
        comp.save(os.path.join(comp_dir, f"frame_{f:04d}.jpg"), quality=98, subsampling=0)
        if f % 150 == 0:
            print(f"Composited razor-sharp frame {f:04d}/1500")

    # Save 10-panel QA sheet showing BOTH 0° Front View AND 45°/135° 360-Orbit View for all 5 scenes!
    qa_pairs = [
        (10, 115),
        (315, 425),
        (645, 735),
        (945, 1065),
        (1245, 1365),
    ]
    qa_board = Image.new("RGB", (1920, 2850), (8, 9, 12))
    qd = ImageDraw.Draw(qa_board)
    qd.rectangle([0, 0, 1920, 78], fill=(16, 18, 24))
    qd.line([(0, 78), (1920, 78)], fill=(215, 42, 46), width=3)
    qd.text((36, 20), "RASPUTIN (1916) — RAZOR-SHARP 1080p + FULL 360° 3D ORBIT QA SHEET (FRONT & ROTATED ANGLES)", fill=(248, 244, 234), font=FONTS["h2"])
    for row_idx, (f_a, f_b) in enumerate(qa_pairs):
        y_top = 92 + row_idx * 550
        for col_idx, qf in enumerate([f_a, f_b]):
            x_left = 20 + col_idx * 945
            cp = os.path.join(comp_dir, f"frame_{qf:04d}.jpg")
            if os.path.exists(cp):
                cim = Image.open(cp).resize((935, 526), Image.Resampling.LANCZOS)
                qa_board.paste(cim, (x_left, y_top))
                qd.rectangle([x_left, y_top, x_left + 935, y_top + 526], outline=(215, 45, 48), width=2)
    qa_board.save(out_qa, quality=96, subsampling=0)

    wav_path = "/tmp/rasputin_master_audio.wav"
    build_master_soundtrack(wav_path)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-framerate", "30",
            "-i", os.path.join(comp_dir, "frame_%04d.jpg"),
            "-i", wav_path,
            "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_mp4,
        ],
        check=True,
    )
    print("Successfully encoded:", out_mp4, "size:", os.path.getsize(out_mp4))
