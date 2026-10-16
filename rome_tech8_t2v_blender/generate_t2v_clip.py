import os
import sys
import time
import shutil
from gradio_client import Client

shot_idx = int(sys.argv[1])
out_mp4 = sys.argv[2]

PROMPTS = {
    1: "Wide cinematic aerial drone shot flying smoothly along a monumental ancient Roman two-tier stone aqueduct bridge spanning a green Mediterranean valley at golden hour sunset, crystal clear water flowing inside the open stone channel along the top, photorealistic 3D historical documentary, 8k",
    2: "Cinematic 3D aerial view sweeping over a dark obsidian 3D relief map of ancient Italy and the Apennine mountains with glowing golden rivers leading to the ancient city of Rome, smooth orbital camera motion, photorealistic 3D documentary",
    3: "Photorealistic 3D architectural cutaway diorama of a Roman stone aqueduct bridge connecting a glowing cyan mountain spring water basin on the right hill to a classical Roman marble temple on the left hill, smooth 3D orbital camera motion",
    4: "Clean architectural 3D studio model of a two-tier Roman travertine stone aqueduct bridge with carved stone arches on a bright studio floor, smooth dolly camera gliding alongside the stone arches, photorealistic 3D documentary",
    5: "Photorealistic 3D geological cross-section of a deep green valley with an ancient Roman stone aqueduct bridge at the bottom and a stone header tank on the left cliff ridge, smooth 3D orbital camera motion, 8k"
}

prompt = PROMPTS[shot_idx]
neg_prompt = "worst quality, inconsistent motion, blurry, jittery, distorted, text, watermark, signature"

SPACES = [
    ("Lightricks/ltx-video-distilled", "ltx_std"),
    ("DeepRat/LTX-Video-ZeroGPU-Optimized", "ltx_opt"),
    ("TIGER-Lab/T2V-Turbo-V2", "t2v_turbo"),
]

for attempt in range(3):
    for sp, mode in SPACES:
        try:
            t0 = time.time()
            print(f"[T2V Shot {shot_idx} | Attempt {attempt+1}] Calling {sp} ({mode})...")
            c = Client(sp)
            if mode == "ltx_std":
                res = c.predict(
                    prompt=prompt,
                    negative_prompt=neg_prompt,
                    input_image_filepath=None,
                    input_video_filepath=None,
                    height_ui=512,
                    width_ui=896,
                    mode="text-to-video",
                    duration_ui=4.0,
                    ui_frames_to_use=9,
                    seed_ui=200 + shot_idx,
                    randomize_seed=False,
                    ui_guidance_scale=1.0,
                    improve_texture_flag=True,
                    api_name="/text_to_video"
                )
                vid_path = res[0]["video"] if isinstance(res[0], dict) else res[0]
            elif mode == "ltx_opt":
                res = c.predict(
                    prompt=prompt,
                    negative_prompt=neg_prompt,
                    input_image_filepath=None,
                    input_video_filepath=None,
                    height_ui=512,
                    width_ui=896,
                    mode="text-to-video",
                    duration_ui=4.0,
                    ui_frames_to_use=9,
                    seed_ui=200 + shot_idx,
                    randomize_seed=False,
                    ui_guidance_scale=1.0,
                    improve_texture_flag=True,
                    slow_motion_flag=False,
                    api_name="/text_to_video"
                )
                vid_path = res[0]["video"] if isinstance(res[0], dict) else res[0]
            else:
                res = c.predict(
                    prompt,
                    7.5,
                    0.5,
                    16,
                    16,
                    200 + shot_idx,
                    False,
                    "bf16",
                    api_name="/predict"
                )
                vid_path = res[0]["video"] if isinstance(res[0], dict) else res[0]

            shutil.copy(vid_path, out_mp4)
            print(f"SUCCESS T2V Shot {shot_idx} via {sp} in {round(time.time()-t0, 1)}s -> {os.path.getsize(out_mp4)} bytes")
            sys.exit(0)
        except Exception as e:
            print(f"  Warning on {sp}: {e}")
            time.sleep(2)

raise RuntimeError(f"All Text-to-Video spaces failed for Shot {shot_idx}")
