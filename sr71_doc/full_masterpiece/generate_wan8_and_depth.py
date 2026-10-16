import os, sys, time, json, shutil, subprocess
import cv2
import numpy as np
from gradio_client import Client, handle_file

shot_idx = int(sys.argv[1])
out_dir = os.path.abspath(sys.argv[2])
os.makedirs(out_dir, exist_ok=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
REFS_DIR = os.path.join(DOC_ROOT, "ai3d_refs")

SHOT_CONFIGS = {
    1: {
        "ref": os.path.join(REFS_DIR, "sr71_shot1_strato.png"),
        "pre_depth": os.path.join(REFS_DIR, "depth1.png"),
        "prompt": "Cinematic 3D aerial camera gliding smoothly alongside a Lockheed SR-71 Blackbird flying at Mach 3.2 in the stratosphere at 85,000 feet, glowing orange heated titanium leading edges, violet-amber shock diamonds in twin afterburner exhaust plumes, smooth camera motion, 8k photorealistic.",
        "anchors": {"nose": (0.12, 0.74), "inlet": (0.47, 0.66)},
    },
    2: {
        "ref": os.path.join(REFS_DIR, "sr71_shot2_cutaway.png"),
        "pre_depth": os.path.join(REFS_DIR, "depth2.png"),
        "prompt": "Smooth 3D studio camera dolly push-in around a cutaway engineering model of the Lockheed SR-71 Blackbird, glowing golden amber JP-7 liquid fuel flowing inside the six fuselage tanks and cooling the cutaway J58 engine, photorealistic 3D engineering animation.",
        "anchors": {"tanks": (0.52, 0.44), "engine": (0.49, 0.63)},
    },
    3: {
        "ref": os.path.join(REFS_DIR, "sr71_shot3_hangar_leak.png"),
        "pre_depth": os.path.join(REFS_DIR, "depth3.png"),
        "prompt": "Slow cinematic 3D camera dolly inside a dimly lit Lockheed Skunk Works aircraft hangar, golden JP-7 jet fuel dripping steadily from the unsealed cold titanium fuselage seams of a parked SR-71 Blackbird into a shimmering puddle on the concrete floor, volumetric lighting.",
        "anchors": {"seam": (0.47, 0.43), "puddle": (0.45, 0.83)},
    },
    4: {
        "ref": os.path.join(REFS_DIR, "sr71_shot4_j58_cutaway.png"),
        "pre_depth": os.path.join(REFS_DIR, "depth2.png"),
        "prompt": "Smooth 3D engineering studio camera tracking across a cutaway Pratt and Whitney J58 turbo-ramjet engine, spinning compressor blades, supersonic airflow passing through the six external bypass bleed tubes into a roaring 3200 degree Fahrenheit afterburner flame.",
        "anchors": {"spike": (0.16, 0.52), "tubes": (0.46, 0.35), "ab": (0.74, 0.52)},
    },
    5: {
        "ref": os.path.join(REFS_DIR, "sr71_shot5_urals_cia.png"),
        "pre_depth": os.path.join(REFS_DIR, "depth3.png"),
        "prompt": "Cinematic Cold War harbor scene, a heavy dock crane slowly lowering a wooden crate of Soviet titanium sponge ore onto a flatbed train car through volumetric fog while two CIA agents in trench coats watch from the foreground.",
        "anchors": {"crate": (0.55, 0.64), "agents": (0.21, 0.65)},
    },
    6: {
        "ref": os.path.join(REFS_DIR, "sr71_shot7_cockpit.png"),
        "pre_depth": None,
        "prompt": "Smooth 3D camera push-in inside the cockpit of an SR-71 Blackbird at 85,000 feet, pilot in golden pressure suit gripping the control stick, glowing Mach 3.22 and EGT instrument dials, glowing orange heated nose cone visible through the quartz windshield above moving white clouds.",
        "anchors": {"mach": (0.56, 0.58), "windshield": (0.72, 0.45)},
    },
    7: {
        "ref": os.path.join(REFS_DIR, "sr71_shot8_kc135q_teb.png"),
        "pre_depth": None,
        "prompt": "Cinematic 3D aerial camera tracking a Lockheed SR-71 Blackbird refueling behind a KC-135Q tanker above golden-hour clouds, twin J58 afterburners igniting with a brilliant emerald-green flash of Triethylborane TEB chemical flame.",
        "anchors": {"boom": (0.47, 0.43), "teb": (0.60, 0.74)},
    },
    8: {
        "ref": os.path.join(REFS_DIR, "sr71_shot9_sam_evasion.png"),
        "pre_depth": None,
        "prompt": "Dramatic 3D aerial camera tracking a Lockheed SR-71 Blackbird accelerating at Mach 3.3 at 85,000 feet in the dark blue stratosphere with glowing orange titanium chines and violet shock diamonds while two white SA-2 missile smoke trails curve upward far behind.",
        "anchors": {"chines": (0.68, 0.28), "sams": (0.83, 0.54)},
    },
}

cfg = SHOT_CONFIGS[shot_idx]
ref_img = cfg["ref"]
depth_out = os.path.join(out_dir, f"depth{shot_idx}.png")

if cfg["pre_depth"] and os.path.exists(cfg["pre_depth"]) and os.path.getsize(cfg["pre_depth"]) > 5000:
    shutil.copy(cfg["pre_depth"], depth_out)
else:
    got_depth = False
    for d_space in ["depth-anything/Depth-Anything-V2", "LiheYoung/Depth-Anything"]:
        try:
            c_dep = Client(d_space)
            try:
                res_d = c_dep.predict(image=handle_file(ref_img), api_name="/on_submit")
            except Exception:
                res_d = c_dep.predict(handle_file(ref_img))
            d_file = None
            if isinstance(res_d, (list, tuple)):
                for item in res_d:
                    if isinstance(item, str) and os.path.exists(item):
                        d_file = item
                    elif isinstance(item, (list, tuple)):
                        for sub in item:
                            if isinstance(sub, str) and os.path.exists(sub):
                                d_file = sub
                    elif isinstance(item, dict) and "path" in item:
                        d_file = item["path"]
            elif isinstance(res_d, str) and os.path.exists(res_d):
                d_file = res_d
            if d_file and os.path.exists(d_file):
                shutil.copy(d_file, depth_out)
                got_depth = True
                break
        except Exception as e:
            print(f"[Shot {shot_idx}] Depth {d_space} error: {e}")
    if not got_depth:
        im_g = cv2.imread(ref_img, cv2.IMREAD_GRAYSCALE)
        h, w = im_g.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        grad = np.clip((yy / h) * 150.0 + im_g.astype(np.float32) * 0.42, 0, 255).astype(np.uint8)
        cv2.imwrite(depth_out, cv2.GaussianBlur(grad, (31, 31), 0))

raw_mp4 = os.path.join(out_dir, f"raw_wan_{shot_idx}.mp4")
got_video = False
for sp in ["zerogpu-aoti/wan2-2-fp8da-aoti-faster", "r3gm/wan2-2-fp8da-aoti-preview", "multimodalart/wan2-1-fast", "Lightricks/ltx-video-distilled"]:
    try:
        client = Client(sp)
        if "wan2-2" in sp:
            res = client.predict(
                input_image=handle_file(ref_img), prompt=cfg["prompt"], steps=4,
                negative_prompt="bright tones, overexposed, static, blurred details, subtitles, text, watermark, ugly, deformed",
                duration_seconds=5.0, guidance_scale=1.0, guidance_scale_2=1.0,
                seed=42 + shot_idx * 7, randomize_seed=False, api_name="/generate_video"
            )
        elif "wan2-1" in sp:
            res = client.predict(
                input_image=handle_file(ref_img), prompt=cfg["prompt"],
                negative_prompt="static, blurry, watermark, text",
                height=512, width=896, duration_seconds=4.0, guidance_scale=5.0,
                steps=18, seed=42 + shot_idx, randomize_seed=False, api_name="/generate_video"
            )
        else:
            res = client.predict(
                prompt=cfg["prompt"], negative_prompt="blurry, distorted, text",
                input_image_filepath=handle_file(ref_img), mode="image-to-video",
                height_ui=512, width_ui=768, duration_ui=5.0, ui_frames_to_use=97,
                seed_ui=42 + shot_idx, randomize_seed=False, ui_guidance_scale=3.0,
                improve_texture_flag=True, api_name="/image_to_video"
            )
        vpath = res[0] if isinstance(res, (list, tuple)) else res
        if isinstance(vpath, dict):
            vpath = vpath.get("video") or vpath.get("path")
        if vpath and os.path.exists(vpath) and os.path.getsize(vpath) > 15000:
            shutil.copy(vpath, raw_mp4)
            got_video = True
            print(f"[Shot {shot_idx}] Generated Wan video via {sp}")
            break
    except Exception as e:
        print(f"[Shot {shot_idx}] {sp} error: {e}")

if not got_video:
    img = cv2.imread(ref_img)
    img = cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_LANCZOS4)
    dep = cv2.imread(depth_out, cv2.IMREAD_GRAYSCALE)
    dep = cv2.resize(dep, (1920, 1080), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
    yy, xx = np.mgrid[0:1080, 0:1920].astype(np.float32)
    for f in range(1, 151):
        u = (f - 1) / 149.0
        su = u * u * (3.0 - 2.0 * u)
        scale = 1.0 + 0.065 * su
        shift_x = -24.0 * su * (0.4 + 0.6 * dep)
        shift_y = -8.0 * su * (0.4 + 0.6 * dep)
        map_x = (xx - 960.0) / scale + 960.0 + shift_x
        map_y = (yy - 540.0) / scale + 540.0 + shift_y
        warped = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT_101)
        cv2.imwrite(os.path.join(out_dir, f"wan_frame_{f:04d}.jpg"), warped, [int(cv2.IMWRITE_JPEG_QUALITY), 96])
else:
    dur_str = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", raw_mp4]).decode().strip()
    dur = float(dur_str) if dur_str else 5.0
    pts_factor = 5.0 / max(0.5, dur)
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_mp4,
        "-vf", f"setpts={pts_factor:.4f}*PTS,fps=30,scale=1920:1080:flags=lanczos",
        "-frames:v", "150", "-qscale:v", "1", "-start_number", "1",
        os.path.join(out_dir, "wan_frame_%04d.jpg")
    ], check=True)
    os.remove(raw_mp4)

existing = sorted([f for f in os.listdir(out_dir) if f.startswith("wan_frame_") and f.endswith(".jpg")])
while len(existing) < 150:
    nxt = len(existing) + 1
    shutil.copy(os.path.join(out_dir, existing[-1]), os.path.join(out_dir, f"wan_frame_{nxt:04d}.jpg"))
    existing.append(f"wan_frame_{nxt:04d}.jpg")

# Track component anchors via Pyramidal Lucas-Kanade (65% LK + 35% rigid)
first_bgr = cv2.imread(os.path.join(out_dir, "wan_frame_0001.jpg"))
H, W = first_bgr.shape[:2]
prev_gray = cv2.cvtColor(first_bgr, cv2.COLOR_BGR2GRAY)

anc_keys = list(cfg["anchors"].keys())
pts_list = [[cfg["anchors"][k][0] * W, cfg["anchors"][k][1] * H] for k in anc_keys]
p0 = np.array(pts_list, dtype=np.float32).reshape(-1, 1, 2)
cur_pts = p0.copy()
lk_params = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))

tracked_data = {}
for idx in range(1, 151):
    if idx > 1:
        bgr = cv2.imread(os.path.join(out_dir, f"wan_frame_{idx:04d}.jpg"))
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, cur_pts, None, **lk_params)
        deltas = p1 - cur_pts
        good_d = deltas[st.flatten() == 1]
        med_dx = float(np.median(good_d[:, 0, 0])) if len(good_d) > 0 else 0.0
        med_dy = float(np.median(good_d[:, 0, 1])) if len(good_d) > 0 else 0.0
        new_pts = np.zeros_like(cur_pts)
        for i in range(len(cur_pts)):
            if st[i][0] == 1:
                dx = 0.65 * deltas[i, 0, 0] + 0.35 * med_dx
                dy = 0.65 * deltas[i, 0, 1] + 0.35 * med_dy
            else:
                dx, dy = med_dx, med_dy
            new_pts[i, 0, 0] = np.clip(cur_pts[i, 0, 0] + dx, 60, W - 60)
            new_pts[i, 0, 1] = np.clip(cur_pts[i, 0, 1] + dy, 60, H - 60)
        cur_pts = new_pts
        prev_gray = gray
    anc_uv = {}
    for ki, k in enumerate(anc_keys):
        anc_uv[k] = [round(float(cur_pts[ki, 0, 0] / W), 5), round(float(cur_pts[ki, 0, 1] / H), 5)]
    tracked_data[str(idx)] = {"anchors": anc_uv}

with open(os.path.join(out_dir, f"tracked_uvs_{shot_idx}.json"), "w") as fp:
    json.dump(tracked_data, fp)
print(f"[Shot {shot_idx}] Completed 150 frames + depth + tracking!")
