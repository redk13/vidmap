import sys, os, shutil, math
from gradio_client import Client, handle_file

job_id = int(sys.argv[1])
out_dir = f"/tmp/ai3d_out_{job_id}"
os.makedirs(out_dir, exist_ok=True)

ROOT = os.path.dirname(os.path.abspath(__file__))
SR71_IMG = os.path.join(ROOT, "ai3d_refs", "sr71_ref_studio.png")
J58_IMG  = os.path.join(ROOT, "ai3d_refs", "j58_ref_studio.png")

JOBS = [
    (0, "trellis1", SR71_IMG, "sr71_trellis1"),
    (1, "trellis1", J58_IMG,  "j58_trellis1"),
    (2, "trellis2", SR71_IMG, "sr71_trellis2"),
    (3, "trellis2", J58_IMG,  "j58_trellis2"),
    (4, "hunyuan2", SR71_IMG, "sr71_hunyuan2"),
    (5, "hunyuan2", J58_IMG,  "j58_hunyuan2"),
]

_, engine, img_path, prefix = JOBS[job_id]
print(f"=== Running Job {job_id}: {engine} on {prefix} ===")

glb_out = os.path.join(out_dir, f"{prefix}.glb")

if engine == "trellis1":
    c = Client("trellis-community/TRELLIS")
    try: c.predict(api_name="/start_session")
    except Exception: pass
    prep = c.predict(image=handle_file(img_path), api_name="/preprocess_image")
    prep_p = prep["path"] if isinstance(prep, dict) else prep
    res = c.predict(
        image=handle_file(prep_p),
        multiimages=[],
        seed=42,
        ss_guidance_strength=7.5,
        ss_sampling_steps=12,
        slat_guidance_strength=3.0,
        slat_sampling_steps=12,
        multiimage_algo="stochastic",
        mesh_simplify=0.95,
        texture_size=1024,
        api_name="/generate_and_extract_glb"
    )
    vid_info, glb_lit, glb_dl = res
    if isinstance(vid_info, dict) and vid_info.get("video"):
        shutil.copy(vid_info["video"], os.path.join(out_dir, f"{prefix}_gaussian360.mp4"))
    if glb_dl and os.path.exists(glb_dl):
        shutil.copy(glb_dl, glb_out)

elif engine == "trellis2":
    c = Client("microsoft/TRELLIS.2")
    try: c.predict(api_name="/start_session")
    except Exception: pass
    prep = c.predict(input=handle_file(img_path), api_name="/preprocess_image")
    prep_p = prep["path"] if isinstance(prep, dict) else prep
    c.predict(
        image=handle_file(prep_p),
        seed=42,
        resolution="1024",
        ss_guidance_strength=7.5,
        ss_guidance_rescale=0.7,
        ss_sampling_steps=12,
        ss_rescale_t=5.0,
        shape_slat_guidance_strength=7.5,
        shape_slat_guidance_rescale=0.5,
        shape_slat_sampling_steps=12,
        shape_slat_rescale_t=3.0,
        tex_slat_guidance_strength=1.0,
        tex_slat_guidance_rescale=0.0,
        tex_slat_sampling_steps=12,
        tex_slat_rescale_t=3.0,
        api_name="/image_to_3d"
    )
    glb_prev, glb_dl = c.predict(decimation_target=250000, texture_size=2048, api_name="/extract_glb")
    if glb_dl and os.path.exists(glb_dl):
        shutil.copy(glb_dl, glb_out)

elif engine == "hunyuan2":
    # Try Hunyuan3D-2 /shape_generation first (fast & fits ZeroGPU free quota), and also try /generation_all if allowed
    c = Client("tencent/Hunyuan3D-2")
    try:
        res = c.predict(
            caption="",
            image=handle_file(img_path),
            mv_image_front=None, mv_image_back=None, mv_image_left=None, mv_image_right=None,
            steps=20, guidance_scale=5.5, seed=1234, octree_resolution=256,
            check_box_rembg=True, num_chunks=8000, randomize_seed=False,
            api_name="/generation_all"
        )
        f_white, f_tex, _, stats, _ = res
        if f_tex and os.path.exists(f_tex):
            shutil.copy(f_tex, glb_out)
        elif f_white and os.path.exists(f_white):
            shutil.copy(f_white, glb_out)
    except Exception as e:
        print("generation_all fallback to shape_generation:", e)
        res = c.predict(
            caption="",
            image=handle_file(img_path),
            mv_image_front=None, mv_image_back=None, mv_image_left=None, mv_image_right=None,
            steps=20, guidance_scale=5.5, seed=1234, octree_resolution=256,
            check_box_rembg=True, num_chunks=8000, randomize_seed=False,
            api_name="/shape_generation"
        )
        f_white, _, stats, _ = res
        if f_white and os.path.exists(f_white):
            shutil.copy(f_white, glb_out)

print("Generated files in", out_dir, ":", os.listdir(out_dir))
