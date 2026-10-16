import shutil
import os
import sys
import json
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

# Probe input AI video duration
probe = subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", in_mp4
]).decode().strip()
in_dur = float(probe)
time_scale = in_dur / dur

# Extract smoothly interpolated 30fps 1920x1080 frames from the Wan 2.2 AI clip
tmp_pattern = os.path.join(frames_dir, "raw_%04d.jpg")
subprocess.run([
    "ffmpeg", "-y", "-i", in_mp4,
    "-vf", f"setpts=PTS/{time_scale:.6f},fps=30,scale=1920:1080:flags=lanczos",
    "-frames:v", str(num_frames),
    "-q:v", "2", tmp_pattern
], check=True)

# Rename raw_0001..N to global frame_{f_start}..{f_end}.jpg
raw_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("raw_") and f.endswith(".jpg")])
while len(raw_files) < num_frames:
    # Duplicate last frame if 1 frame short due to rounding
    shutil.copy(os.path.join(frames_dir, raw_files[-1]), os.path.join(frames_dir, f"raw_{len(raw_files)+1:04d}.jpg"))
    raw_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("raw_") and f.endswith(".jpg")])

frame_paths = []
for i in range(num_frames):
    gf = f_start + i
    src = os.path.join(frames_dir, raw_files[i])
    dst = os.path.join(frames_dir, f"wan_frame_{gf:04d}.jpg")
    os.rename(src, dst)
    frame_paths.append(dst)

# Initial calibrated UV points at Frame 0 of each shot (matches rgb{shot_idx}.jpg)
SPLINE_UVS = {
    1: [(0.00, 0.595), (0.18, 0.535), (0.35, 0.472), (0.52, 0.412), (0.68, 0.355), (0.87, 0.285)],
    2: [(0.245, 0.615), (0.33, 0.635), (0.43, 0.655), (0.53, 0.640), (0.63, 0.585), (0.72, 0.505), (0.80, 0.415)],
    3: [(0.81, 0.545), (0.68, 0.525), (0.52, 0.500), (0.36, 0.478), (0.20, 0.452), (0.08, 0.435)],
    4: [(0.04, 0.525), (0.25, 0.468), (0.48, 0.402), (0.72, 0.330), (0.95, 0.255)],
    5: [(0.11, 0.475), (0.16, 0.505), (0.23, 0.675), (0.31, 0.855), (0.40, 0.935),
        (0.49, 0.940), (0.58, 0.855), (0.66, 0.695), (0.74, 0.530), (0.80, 0.495)],
}

ANCHOR_UVS = {
    1: {},
    2: {"marcia": (0.56, 0.45), "rome": (0.245, 0.615)},
    3: {"source": (0.80, 0.34), "rome": (0.14, 0.17)},
    4: {"pL": (0.08, 0.39), "pR": (0.86, 0.15), "mid": (0.44, 0.22)},
    5: {"ht_lbl": (0.15, 0.30), "ht_tank": (0.12, 0.46), "top50": (0.46, 0.48), "bot50": (0.46, 0.90)},
}

# Track global + local motion across frames using Pyramidal Lucas-Kanade Optical Flow
W, H = 960, 540
lk_params = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))

init_spline = SPLINE_UVS[shot_idx]
init_anchors = ANCHOR_UVS[shot_idx]
anchor_keys = list(init_anchors.keys())

all_uvs = list(init_spline) + [init_anchors[k] for k in anchor_keys]
pts_cur = np.array([[[u * W, v * H]] for u, v in all_uvs], dtype=np.float32)

prev_gray = cv2.cvtColor(cv2.resize(cv2.imread(frame_paths[0]), (W, H)), cv2.COLOR_BGR2GRAY)

tracked_frames = {}
for i, fp in enumerate(frame_paths):
    gf = f_start + i
    if i > 0:
        cur_gray = cv2.cvtColor(cv2.resize(cv2.imread(fp), (W, H)), cv2.COLOR_BGR2GRAY)
        pts_next, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, cur_gray, pts_cur, None, **lk_params)
        # Compute median shift for robustness against boundary drift
        deltas = pts_next - pts_cur
        valid = (st.flatten() == 1)
        if np.any(valid):
            med_dx = float(np.median(deltas[valid, 0, 0]))
            med_dy = float(np.median(deltas[valid, 0, 1]))
        else:
            med_dx, med_dy = 0.0, 0.0
        for idx_p in range(len(all_uvs)):
            if valid[idx_p] and abs(deltas[idx_p, 0, 0] - med_dx) < 8.0 and abs(deltas[idx_p, 0, 1] - med_dy) < 8.0:
                # Blend 65% local LK flow + 35% median rigid motion for rock-solid smooth spline tracking
                dx = 0.65 * float(deltas[idx_p, 0, 0]) + 0.35 * med_dx
                dy = 0.65 * float(deltas[idx_p, 0, 1]) + 0.35 * med_dy
            else:
                dx, dy = med_dx, med_dy
            pts_cur[idx_p, 0, 0] += dx
            pts_cur[idx_p, 0, 1] += dy
        prev_gray = cur_gray

    cur_uv_list = [(float(pts_cur[j, 0, 0] / W), float(pts_cur[j, 0, 1] / H)) for j in range(len(all_uvs))]
    sp_uvs = cur_uv_list[:len(init_spline)]
    an_uvs = {anchor_keys[k]: cur_uv_list[len(init_spline) + k] for k in range(len(anchor_keys))}
    tracked_frames[str(gf)] = {"spline": sp_uvs, "anchors": an_uvs}

with open(out_json, "w") as f:
    json.dump(tracked_frames, f)
print(f"Tracked {num_frames} frames for Shot {shot_idx} -> {out_json}")
