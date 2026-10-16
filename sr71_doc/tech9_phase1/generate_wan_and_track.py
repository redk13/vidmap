import os
import sys
import time
import json
import shutil
import subprocess
import cv2
import numpy as np
from gradio_client import Client, handle_file

shot_idx = int(sys.argv[1])
frames_dir = sys.argv[2]
out_json = sys.argv[3]

os.makedirs(frames_dir, exist_ok=True)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REFS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../ai3d_refs"))

FILES = {
    1: "sr71_shot1_strato.png",
    2: "sr71_shot2_cutaway.png",
    3: "sr71_shot3_hangar_leak.png",
    4: "sr71_shot4_j58_cutaway.png",
    5: "sr71_shot5_urals_cia.png",
}

PROMPTS = {
    1: "Smooth cinematic aerial camera gliding alongside the matte black SR-71 Blackbird jet cruising at Mach 3.2 in the high stratosphere above moving white clouds, glowing orange heat on nose and engine spikes, flickering blue afterburner shock diamonds, photorealistic 3D documentary",
    2: "Smooth cinematic 3D orbital camera slowly orbiting around a photorealistic 3D studio cutaway model of the SR-71 Blackbird on a clean grey studio floor, golden JP-7 fuel shimmering inside the internal fuselage tanks and cutaway J58 turbo-ramjet engine, 3D engineering documentary",
    3: "Smooth cinematic 3D dolly camera moving slowly across the Lockheed Skunk Works hangar floor as golden JP-7 jet fuel drips steadily from the SR-71 Blackbird underbelly titanium seams into a reflective puddle on the concrete floor, volumetric hangar light rays, photorealistic 3D documentary",
    4: "Smooth cinematic 3D camera gliding along a photorealistic 3D cutaway Pratt & Whitney J58 turbo-ramjet engine on a studio stand, spinning axial compressor blades and roaring orange-blue flame inside the afterburner nozzle, 3D engineering documentary",
    5: "Smooth cinematic 3D camera drifting slowly across a misty Cold War harbor dock at dusk as a harbor crane lowers a heavy wooden crate stenciled CCCP from a steel cargo ship onto a railway flatcar while two intelligence agents watch, photorealistic 3D documentary"
}

SHOT_RANGES = {
    1: (1,   150, 0.0,  5.0),
    2: (151, 300, 5.0,  10.0),
    3: (301, 450, 10.0, 15.0),
    4: (451, 600, 15.0, 20.0),
    5: (601, 750, 20.0, 25.0),
}

img_p = os.path.join(REFS_DIR, FILES[shot_idx])
dep_p = os.path.join(frames_dir, f"depth{shot_idx}.png")
cached_dep = os.path.join(REFS_DIR, f"depth{shot_idx}.png")

# 1. Obtain Depth-Anything-V2 depth map
if os.path.exists(cached_dep) and os.path.getsize(cached_dep) > 10000:
    print(f"[Shot {shot_idx}] Using pre-computed Depth-Anything-V2 map: {cached_dep}")
    shutil.copy(cached_dep, dep_p)
else:
    try:
        print(f"[Shot {shot_idx}] Calling depth-anything/Depth-Anything-V2...")
        dc = Client("depth-anything/Depth-Anything-V2")
        dres = dc.predict(handle_file(img_p), api_name="/on_submit")
        dpath = dres[1]["path"] if isinstance(dres[1], dict) else dres[1]
        shutil.copy(dpath, dep_p)
        print(f"[Shot {shot_idx}] Depth-Anything-V2 succeeded -> {dep_p}")
    except Exception as e:
        print(f"[Shot {shot_idx}] Depth-Anything-V2 fallback smooth luminance depth: {e}")
        im_bgr = cv2.imread(img_p)
        g = cv2.cvtColor(im_bgr, cv2.COLOR_BGR2GRAY)
        g_blur = cv2.GaussianBlur(g, (31, 31), 0)
        cv2.imwrite(dep_p, g_blur)

# 2. Generate moving 3D video via Wan 2.2 / Wan 2.1 / LTX-Video
out_mp4 = f"/tmp/wan_shot_{shot_idx}.mp4"
prompt = PROMPTS[shot_idx]

SPACES = [
    ("zerogpu-aoti/wan2-2-fp8da-aoti-faster", "wan22"),
    ("r3gm/wan2-2-fp8da-aoti-preview", "wan22"),
    ("r3gm/wan2-2-fp8da-aoti-preview2", "wan22"),
    ("multimodalart/wan2-1-fast", "wan21"),
    ("Lightricks/ltx-video-distilled", "ltx"),
]

gen_ok = False
for attempt in range(3):
    if gen_ok:
        break
    for sp, mode in SPACES:
        try:
            print(f"[Shot {shot_idx} | Attempt {attempt+1}] Trying {sp} ({mode})...")
            c = Client(sp)
            if mode == "wan22":
                res = c.predict(
                    input_image=handle_file(img_p),
                    prompt=prompt,
                    steps=6,
                    duration_seconds=4.0,
                    guidance_scale=1.0,
                    guidance_scale_2=1.0,
                    seed=100 + shot_idx,
                    randomize_seed=False,
                    api_name="/generate_video"
                )
            elif mode == "wan21":
                res = c.predict(
                    input_image=handle_file(img_p),
                    prompt=prompt,
                    height=512,
                    width=896,
                    duration_seconds=4.0,
                    guidance_scale=1.0,
                    steps=4,
                    seed=100 + shot_idx,
                    randomize_seed=False,
                    api_name="/generate_video"
                )
            else:
                res = c.predict(
                    prompt=prompt,
                    negative_prompt="worst quality, inconsistent motion, blurry, jittery, distorted",
                    input_image_filepath=handle_file(img_p),
                    input_video_filepath=None,
                    height_ui=512,
                    width_ui=896,
                    mode="image-to-video",
                    duration_ui=4.0,
                    ui_frames_to_use=9,
                    seed_ui=100 + shot_idx,
                    randomize_seed=False,
                    ui_guidance_scale=1.0,
                    improve_texture_flag=True,
                    api_name="/image_to_video"
                )
            vid_path = res[0]["video"] if isinstance(res[0], dict) else res[0]
            if isinstance(vid_path, dict):
                vid_path = vid_path.get("path") or vid_path.get("value")
            shutil.copy(vid_path, out_mp4)
            if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 50000:
                print(f"SUCCESS generating Shot {shot_idx} via {sp} -> {out_mp4} ({os.path.getsize(out_mp4)} bytes)")
                gen_ok = True
                break
        except Exception as e:
            print(f"  Warning on {sp}: {e}")
            time.sleep(2)

if not gen_ok:
    raise RuntimeError(f"All AI video spaces failed for Shot {shot_idx}")

# 3. Extract 150 30fps 1920x1080 frames & Track 3D Spline + Anchors via Pyramidal LK (65% local + 35% median rigid)
f_start, f_end, t0, t1 = SHOT_RANGES[shot_idx]
num_frames = f_end - f_start + 1
dur = t1 - t0

probe = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", out_mp4
]).decode().strip()
in_dur = float(probe)
time_scale = in_dur / dur

tmp_pattern = os.path.join(frames_dir, "raw_%04d.jpg")
subprocess.run([
    "ffmpeg", "-y", "-i", out_mp4,
    "-vf", f"setpts=PTS/{time_scale:.6f},fps=30,scale=1920:1080:flags=lanczos",
    "-frames:v", str(num_frames),
    "-q:v", "2", tmp_pattern
], check=True)

raw_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("raw_") and f.endswith(".jpg")])
while len(raw_files) < num_frames:
    shutil.copy(os.path.join(frames_dir, raw_files[-1]), os.path.join(frames_dir, f"raw_{len(raw_files)+1:04d}.jpg"))
    raw_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("raw_") and f.endswith(".jpg")])

frame_paths = []
for i in range(num_frames):
    gf = f_start + i
    src = os.path.join(frames_dir, raw_files[i])
    dst = os.path.join(frames_dir, f"wan_frame_{gf:04d}.jpg")
    os.rename(src, dst)
    frame_paths.append(dst)

SPLINE_UVS = {
    1: [(0.135, 0.755), (0.34, 0.70), (0.55, 0.57), (0.64, 0.65), (0.78, 0.52), (0.93, 0.37)],
    2: [(0.46, 0.40), (0.56, 0.45), (0.66, 0.50), (0.76, 0.55), (0.60, 0.56), (0.48, 0.60), (0.60, 0.66), (0.72, 0.73)],
    3: [(0.36, 0.42), (0.45, 0.44), (0.45, 0.58), (0.45, 0.72), (0.44, 0.82), (0.34, 0.84)],
    4: [(0.06, 0.45), (0.21, 0.43), (0.30, 0.35), (0.33, 0.23), (0.46, 0.23), (0.59, 0.26), (0.67, 0.42), (0.83, 0.44), (0.96, 0.44)],
    5: [(0.68, 0.34), (0.62, 0.14), (0.62, 0.43), (0.62, 0.65), (0.46, 0.78)],
}

ANCHOR_UVS = {
    1: {"nose": (0.19, 0.72), "inlet": (0.65, 0.64)},
    2: {"tanks": (0.55, 0.43), "engine": (0.52, 0.62)},
    3: {"seam": (0.45, 0.45), "puddle": (0.38, 0.83)},
    4: {"spike": (0.14, 0.45), "tubes": (0.44, 0.22), "ab": (0.74, 0.42)},
    5: {"crate": (0.62, 0.43), "agents": (0.21, 0.56)},
}

W_LK, H_LK = 960, 540
lk_params = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))

init_spline = SPLINE_UVS[shot_idx]
init_anchors = ANCHOR_UVS[shot_idx]
anchor_keys = list(init_anchors.keys())

all_uvs = list(init_spline) + [init_anchors[k] for k in anchor_keys]
pts_cur = np.array([[[u * W_LK, v * H_LK]] for u, v in all_uvs], dtype=np.float32)

prev_gray = cv2.cvtColor(cv2.resize(cv2.imread(frame_paths[0]), (W_LK, H_LK)), cv2.COLOR_BGR2GRAY)

tracked_frames = {}
for i, fp in enumerate(frame_paths):
    gf = f_start + i
    if i > 0:
        cur_gray = cv2.cvtColor(cv2.resize(cv2.imread(fp), (W_LK, H_LK)), cv2.COLOR_BGR2GRAY)
        pts_next, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, cur_gray, pts_cur, None, **lk_params)
        deltas = pts_next - pts_cur
        valid = (st.flatten() == 1)
        if np.any(valid):
            med_dx = float(np.median(deltas[valid, 0, 0]))
            med_dy = float(np.median(deltas[valid, 0, 1]))
        else:
            med_dx, med_dy = 0.0, 0.0
        for idx_p in range(len(all_uvs)):
            if valid[idx_p] and abs(deltas[idx_p, 0, 0] - med_dx) < 8.0 and abs(deltas[idx_p, 0, 1] - med_dy) < 8.0:
                dx = 0.65 * float(deltas[idx_p, 0, 0]) + 0.35 * med_dx
                dy = 0.65 * float(deltas[idx_p, 0, 1]) + 0.35 * med_dy
            else:
                dx, dy = med_dx, med_dy
            pts_cur[idx_p, 0, 0] += dx
            pts_cur[idx_p, 0, 1] += dy
        prev_gray = cur_gray

    cur_uv_list = [(float(pts_cur[j, 0, 0] / W_LK), float(pts_cur[j, 0, 1] / H_LK)) for j in range(len(all_uvs))]
    sp_uvs = cur_uv_list[:len(init_spline)]
    an_uvs = {anchor_keys[k]: cur_uv_list[len(init_spline) + k] for k in range(len(anchor_keys))}
    tracked_frames[str(gf)] = {"spline": sp_uvs, "anchors": an_uvs}

with open(out_json, "w") as f:
    json.dump(tracked_frames, f)
print(f"Tracked {num_frames} frames for Shot {shot_idx} -> {out_json}")
