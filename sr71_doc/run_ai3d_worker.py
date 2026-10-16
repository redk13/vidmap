import sys, os, shutil, cv2
from gradio_client import Client, handle_file

job_id = int(sys.argv[1])
out_dir = f"/tmp/ai3d_out_{job_id}"
os.makedirs(out_dir, exist_ok=True)

ROOT = os.path.dirname(os.path.abspath(__file__))
SR71_IMG = os.path.join(ROOT, "ai3d_refs", "sr71_ref_studio.png")
J58_IMG  = os.path.join(ROOT, "ai3d_refs", "j58_ref_studio.png")

JOBS = [
    (0, "trellis_oa",   SR71_IMG, "sr71_trellis"),
    (1, "trellis_oa",   J58_IMG,  "j58_trellis"),
    (2, "flux_trellis", SR71_IMG, "sr71_trellis_gs"),
    (3, "flux_trellis", J58_IMG,  "j58_trellis_gs"),
    (4, "hunyuan2",     SR71_IMG, "sr71_hunyuan2"),
    (5, "triposr",      J58_IMG,  "j58_triposr"),
]

_, engine, img_path, prefix = JOBS[job_id]
print(f"=== Running Job {job_id}: {engine} on {prefix} ===")
glb_out = os.path.join(out_dir, f"{prefix}.glb")

if engine == "trellis_oa":
    c = Client("Louischong/Trellis-OA")
    tid, prep = c.predict(image=handle_file(img_path), api_name="/preprocess_image")
    vid = c.predict(
        trial_id=tid,
        seed=42,
        randomize_seed=False,
        ss_guidance_strength=7.5,
        ss_sampling_steps=12,
        slat_guidance_strength=3.0,
        slat_sampling_steps=12,
        api_name="/image_to_3d"
    )
    if isinstance(vid, dict) and vid.get("video"):
        vpath = os.path.join(out_dir, f"{prefix}_gaussian360.mp4")
        shutil.copy(vid["video"], vpath)
        # Extract 2 frames from the 3D Gaussian Splatting turntable video
        cap = cv2.VideoCapture(vpath)
        tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 60
        for k, f_idx in enumerate([int(tot*0.15), int(tot*0.55)]):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, fr = cap.read()
            if ret: cv2.imwrite(os.path.join(out_dir, f"gs_frame_{k}.png"), fr)
        cap.release()
    try:
        glb_lit, glb_dl = c.predict(mesh_simplify=0.95, texture_size=1024, api_name="/extract_glb")
        if glb_dl and os.path.exists(glb_dl):
            shutil.copy(glb_dl, glb_out)
    except Exception as e:
        print("extract_glb note:", e)

elif engine == "flux_trellis":
    c = Client("gokaygokay/Flux-TRELLIS")
    try: c.predict(api_name="/start_session")
    except Exception: pass
    vid = c.predict(
        image=handle_file(img_path),
        seed=42,
        ss_guidance_strength=7.5,
        ss_sampling_steps=12,
        slat_guidance_strength=3.0,
        slat_sampling_steps=12,
        api_name="/image_to_3d"
    )
    if isinstance(vid, dict) and vid.get("video"):
        vpath = os.path.join(out_dir, f"{prefix}_gaussian360.mp4")
        shutil.copy(vid["video"], vpath)
        cap = cv2.VideoCapture(vpath)
        tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 60
        for k, f_idx in enumerate([int(tot*0.15), int(tot*0.55)]):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, fr = cap.read()
            if ret: cv2.imwrite(os.path.join(out_dir, f"gs_frame_{k}.png"), fr)
        cap.release()
    try:
        gs_lit, gs_dl = c.predict(api_name="/extract_gaussian")
        if gs_dl and os.path.exists(gs_dl):
            shutil.copy(gs_dl, os.path.join(out_dir, f"{prefix}.ply"))
    except Exception as e:
        print("extract_gaussian note:", e)

elif engine == "hunyuan2":
    c = Client("tencent/Hunyuan3D-2")
    # Generate both SR-71 and J58 shapes (40s each, or SR-71 first)
    f_white, _, stats, _ = c.predict(
        caption="",
        image=handle_file(img_path),
        mv_image_front=None, mv_image_back=None, mv_image_left=None, mv_image_right=None,
        steps=25, guidance_scale=5.5, seed=1234, octree_resolution=256,
        check_box_rembg=True, num_chunks=8000, randomize_seed=False,
        api_name="/shape_generation"
    )
    if f_white and os.path.exists(f_white):
        shutil.copy(f_white, glb_out)
    print("Hunyuan3D-2 stats:", stats)

elif engine == "triposr":
    c = Client("Pheerakarn/TripoSR")
    prep = c.predict(input_image=handle_file(img_path), remove_background=True, foreground_ratio=0.85, api_name="/preprocess")
    obj_f, glb_f = c.predict(processed_image=handle_file(prep), marching_cubes_resolution=256, api_name="/generate")
    if glb_f and os.path.exists(glb_f):
        shutil.copy(glb_f, glb_out)
    if obj_f and os.path.exists(obj_f):
        shutil.copy(obj_f, os.path.join(out_dir, f"{prefix}.obj"))

print("Generated files in", out_dir, ":", os.listdir(out_dir))
