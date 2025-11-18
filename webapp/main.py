# webapp/main.py
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import tempfile, os, uuid
from hueforge.hueforge_logic import load_image, image_to_heightmap, heightmap_to_array
from hueforge.stl_generator import heightmap_to_watertight_stl

app = FastAPI()
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("webapp/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

def _cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

@app.post("/generate")
async def generate_stl(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    max_dim: int = Form(300),
    contrast: float = Form(1.0),
    blur: float = Form(0.0),
    invert: bool = Form(False),
    scale_xy: float = Form(0.5),
    z_scale: float = Form(10.0),
    base_thickness: float = Form(2.0),
):
    # Save uploaded file to a temp file
    suffix = os.path.splitext(file.filename)[1] or ".png"
    tmp_in = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_in.write(await file.read())
    tmp_in.flush()
    tmp_in.close()

    # create temp out stl
    tmp_out = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
    tmp_out_path = tmp_out.name
    tmp_out.close()

    # Process
    img = load_image(tmp_in.name)
    hm = image_to_heightmap(img, max_dim=int(max_dim), contrast=float(contrast), blur_radius=float(blur), invert=bool(invert))
    arr = heightmap_to_array(hm)
    heightmap_to_watertight_stl(arr, tmp_out_path, scale_xy=float(scale_xy), z_scale=float(z_scale), base_thickness=float(base_thickness))

    # schedule cleanup
    background_tasks.add_task(_cleanup_file, tmp_in.name)
    background_tasks.add_task(_cleanup_file, tmp_out_path)

    return FileResponse(tmp_out_path, filename=f"hueforge_{uuid.uuid4().hex}.stl", media_type="application/sla")
