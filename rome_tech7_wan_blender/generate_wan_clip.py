import os
import sys
import time
import shutil
import subprocess
from gradio_client import Client, handle_file

shot_idx = int(sys.argv[1])
out_mp4 = sys.argv[2]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../rome_ai_3d/assets"))
img_p = os.path.join(ASSETS_DIR, f"rgb{shot_idx}.jpg")

PROMPTS = {
    1: "Smooth cinematic aerial drone camera flying forward and gently orbiting along the ancient Roman stone aqueduct bridge in warm golden hour sunlight, crystal water flowing in top channel, photorealistic 3D historical documentary",
    2: "Smooth cinematic 3D orbital camera sweeping across a dark obsidian 3D relief map of ancient Italy and the Apennine mountains with glowing golden rivers, photorealistic 3D documentary",
    3: "Smooth cinematic 3D camera orbiting around a photorealistic 3D architectural cutaway diorama of a Roman marble aqueduct bridge connecting a glowing cyan mountain spring to a classical Roman temple",
    4: "Smooth cinematic dolly camera gliding alongside a photorealistic 3D studio model of a two-tier Roman travertine stone aqueduct bridge on a clean studio floor, architectural documentary",
    5: "Smooth cinematic 3D orbital camera moving across a deep geological valley cutaway with a Roman stone aqueduct bridge and green cypress trees on the ridges, photorealistic 3D documentary"
}

prompt = PROMPTS[shot_idx]

# If pre-cached wan_shot_1.mp4 exists in repo, use it directly for shot 1
cached = os.path.join(SCRIPT_DIR, f"wan_shot_{shot_idx}.mp4")
if os.path.exists(cached) and os.path.getsize(cached) > 200000:
    print(f"Using pre-generated Wan 2.2 clip for Shot {shot_idx}: {cached}")
    shutil.copy(cached, out_mp4)
    sys.exit(0)

SPACES = [
    ("zerogpu-aoti/wan2-2-fp8da-aoti-faster", "wan22"),
    ("r3gm/wan2-2-fp8da-aoti-preview", "wan22"),
    ("r3gm/wan2-2-fp8da-aoti-preview2", "wan22"),
    ("multimodalart/wan2-1-fast", "wan21"),
    ("Lightricks/ltx-video-distilled", "ltx"),
]

for attempt in range(3):
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
                    seed=42 + shot_idx,
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
                    seed=42 + shot_idx,
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
                    seed_ui=42 + shot_idx,
                    randomize_seed=False,
                    ui_guidance_scale=1.0,
                    improve_texture_flag=True,
                    api_name="/image_to_video"
                )
            vid_path = res[0]["video"] if isinstance(res[0], dict) else res[0]
            shutil.copy(vid_path, out_mp4)
            print(f"SUCCESS generating Shot {shot_idx} via {sp} -> {out_mp4} ({os.path.getsize(out_mp4)} bytes)")
            sys.exit(0)
        except Exception as e:
            print(f"  Warning on {sp}: {e}")
            time.sleep(3)

raise RuntimeError(f"All AI video spaces failed for Shot {shot_idx}")
