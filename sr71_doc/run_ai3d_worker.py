import sys, os, shutil, cv2
from gradio_client import Client, handle_file

def unwrap_path(x):
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        for k in ("path", "value", "video", "url"):
            if k in x and x[k]:
                return unwrap_path(x[k])
    return None

job_id = int(sys.argv[1])
out_dir = f"/tmp/ai3d_out_{job_id}"
os.makedirs(out_dir, exist_ok=True)

ROOT = os.path.dirname(os.path.abspath(__file__))
SR71_IMG = os.path.join(ROOT, "ai3d_refs", "sr71_ref_studio.png")
J58_IMG  = os.path.join(ROOT, "ai3d_refs", "j58_ref_studio.png")

JOBS = [
    (0, "trellis",    SR71_IMG, "sr71_trellis"),
    (1, "trellis",    J58_IMG,  "j58_trellis"),
    (2, "hunyuan2",   SR71_IMG, "sr71_hunyuan2"),
    (3, "hunyuan2",   J58_IMG,  "j58_hunyuan2"),
    (4, "triposr",    SR71_IMG, "sr71_triposr"),
    (5, "triposr",    J58_IMG,  "j58_triposr"),
]

_, engine, img_path, prefix = JOBS[job_id]
print(f"=== Running Job {job_id}: {engine} on {prefix} ===")
glb_out = os.path.join(out_dir, f"{prefix}.glb")

if engine == "trellis":
    c = Client("yonnel/text-to-3d_flux_trellis")
    res = c.predict(
        handle_file(img_path),
        42,
        7.5,
        12,
        3.0,
        12,
        api_name="/image_to_3d"
    )
    vid_d, mod_d, status_s, dl_d = res
    print("TRELLIS status:", status_s)
    vp = unwrap_path(vid_d)
    if vp and os.path.exists(vp):
        vdest = os.path.join(out_dir, f"{prefix}_gaussian360.mp4")
        shutil.copy(vp, vdest)
        cap = cv2.VideoCapture(vdest)
        tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 60
        for k, f_idx in enumerate([int(tot*0.18), int(tot*0.58)]):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, fr = cap.read()
            if ret: cv2.imwrite(os.path.join(out_dir, f"gs_frame_{k}.png"), fr)
        cap.release()
    gp = unwrap_path(dl_d) or unwrap_path(mod_d)
    if gp and os.path.exists(gp):
        shutil.copy(gp, glb_out)

elif engine == "hunyuan2":
    c = Client("tencent/Hunyuan3D-2")
    res = c.predict(
        "",
        handle_file(img_path),
        None, None, None, None,
        25, 5.5, 1234, 256,
        True, 8000, False,
        api_name="/shape_generation"
    )
    f_white, html_out, stats, _ = res
    print("Hunyuan3D-2 stats:", stats)
    gp = unwrap_path(f_white)
    if gp and os.path.exists(gp):
        shutil.copy(gp, glb_out)

elif engine == "triposr":
    c = Client("Pheerakarn/TripoSR")
    prep = c.predict(handle_file(img_path), True, 0.85, api_name="/preprocess")
    prep_p = unwrap_path(prep)
    obj_f, glb_f = c.predict(handle_file(prep_p), 256, api_name="/generate")
    gp = unwrap_path(glb_f)
    if gp and os.path.exists(gp):
        shutil.copy(gp, glb_out)
    op = unwrap_path(obj_f)
    if op and os.path.exists(op):
        shutil.copy(op, os.path.join(out_dir, f"{prefix}.obj"))

print("Generated files in", out_dir, ":", os.listdir(out_dir))
