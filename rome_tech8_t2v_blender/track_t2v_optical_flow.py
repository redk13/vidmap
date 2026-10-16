import os
import sys
import json
import shutil
import subprocess
import cv2
import numpy as np

shot_idx = int(sys.argv[1])
in_mp4 = sys.argv[2]
frames_dir = sys.argv[3]
out_json = sys.argv[4]

os.makedirs(frames_dir, exist_ok=True)

SHOT_RANGES = {
    1: (1, 130, 0.0, 4.35),
    2: (131, 248, 4.35, 8.25),
    3: (249, 353, 8.25, 11.75),
    4: (354, 474, 11.75, 15.80),
    5: (475, 600, 15.80, 20.00),
}

f_start, f_end, t0, t1 = SHOT_RANGES[shot_idx]
num_frames = f_end - f_start + 1
dur = t1 - t0

probe = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", in_mp4
]).decode().strip()
in_dur = float(probe)
time_scale = in_dur / dur

tmp_pattern = os.path.join(frames_dir, "raw_%04d.jpg")
subprocess.run([
    "ffmpeg", "-y", "-i", in_mp4,
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

# Auto-detect dominant architectural crest / feature ridge in Frame 0 of the newly generated T2V video
f0_bgr = cv2.resize(cv2.imread(frame_paths[0]), (960, 540))
f0_gray = cv2.cvtColor(f0_bgr, cv2.COLOR_BGR2GRAY)

# Save a smoothed depth proxy from Frame 0 luminance + vertical gradient for 3D Z-mapping
grad_y = np.linspace(0.2, 0.85, 540).reshape(540, 1) * np.ones((1, 960))
luma_norm = f0_gray.astype(np.float32) / 255.0
dep_proxy = np.clip((0.55 * grad_y + 0.45 * luma_norm) * 255.0, 0, 255).astype(np.uint8)
dep_proxy = cv2.GaussianBlur(dep_proxy, (31, 31), 0)
cv2.imwrite(os.path.join(frames_dir, f"depth_t2v_{shot_idx}.png"), dep_proxy)

SPLINE_UVS = {
    1: [(0.05, 0.56), (0.22, 0.52), (0.39, 0.48), (0.56, 0.44), (0.73, 0.40), (0.90, 0.36)],
    2: [(0.26, 0.62), (0.35, 0.63), (0.45, 0.62), (0.55, 0.58), (0.65, 0.51), (0.75, 0.42)],
    3: [(0.82, 0.52), (0.68, 0.50), (0.52, 0.48), (0.36, 0.46), (0.20, 0.44)],
    4: [(0.06, 0.48), (0.28, 0.44), (0.50, 0.40), (0.72, 0.36), (0.92, 0.32)],
    5: [(0.14, 0.46), (0.24, 0.66), (0.36, 0.84), (0.50, 0.88), (0.64, 0.82), (0.76, 0.64), (0.84, 0.48)],
}

ANCHOR_UVS = {
    1: {},
    2: {"marcia": (0.54, 0.42), "rome": (0.26, 0.62)},
    3: {"source": (0.80, 0.32), "rome": (0.18, 0.24)},
    4: {"pL": (0.10, 0.36), "pR": (0.86, 0.22), "mid": (0.46, 0.22)},
    5: {"ht_lbl": (0.16, 0.30), "ht_tank": (0.14, 0.45), "top50": (0.50, 0.48), "bot50": (0.50, 0.86)},
}

W, H = 960, 540
lk_params = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))

init_spline = SPLINE_UVS[shot_idx]
init_anchors = ANCHOR_UVS[shot_idx]
anchor_keys = list(init_anchors.keys())

all_uvs = list(init_spline) + [init_anchors[k] for k in anchor_keys]
pts_cur = np.array([[[u * W, v * H]] for u, v in all_uvs], dtype=np.float32)

prev_gray = f0_gray
tracked_frames = {}

for i, fp in enumerate(frame_paths):
    gf = f_start + i
    if i > 0:
        cur_gray = cv2.cvtColor(cv2.resize(cv2.imread(fp), (W, H)), cv2.COLOR_BGR2GRAY)
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
                dx = 0.60 * float(deltas[idx_p, 0, 0]) + 0.40 * med_dx
                dy = 0.60 * float(deltas[idx_p, 0, 1]) + 0.40 * med_dy
            else:
                dx, dy = med_dx, med_dy
            pts_cur[idx_p, 0, 0] = np.clip(pts_cur[idx_p, 0, 0] + dx, 30, W - 30)
            pts_cur[idx_p, 0, 1] = np.clip(pts_cur[idx_p, 0, 1] + dy, 30, H - 30)
        prev_gray = cur_gray

    cur_uv_list = [(float(pts_cur[j, 0, 0] / W), float(pts_cur[j, 0, 1] / H)) for j in range(len(all_uvs))]
    sp_uvs = cur_uv_list[:len(init_spline)]
    an_uvs = {anchor_keys[k]: cur_uv_list[len(init_spline) + k] for k in range(len(anchor_keys))}
    tracked_frames[str(gf)] = {"spline": sp_uvs, "anchors": an_uvs}

with open(out_json, "w") as f:
    json.dump(tracked_frames, f)
print(f"Tracked {num_frames} T2V frames for Shot {shot_idx} -> {out_json}")
