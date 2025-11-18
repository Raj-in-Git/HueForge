Hueforge Full Project
This repository contains everything you asked for:
	• Full FastAPI project (API + static Web UI)
	• Tkinter desktop app
	• Web UI (HTML + JS) for file upload and preview
	• CLI tool packaged as hueforge-lite (setup.py + console script)
	• 3D STL generator script (converts a heightmap to an ASCII STL)

Project structure
hueforge_full_project/
├── README.md
├── requirements.txt
├── setup.py
├── hueforge/                          # Python package
│   ├── __init__.py
│   ├── hueforge_logic.py              # Core image -> heightmap logic
│   ├── stl_generator.py              # Heightmap -> ASCII STL exporter
│   ├── cli.py                         # CLI entrypoint
│   └── tkinter_app.py                 # Tkinter desktop app
├── fastapi_app/
│   ├── main.py                        # FastAPI app
│   └── static/
│       ├── index.html
│       └── script.js
└── examples/
    └── sample_input.jpg


requirements.txt
fastapi
uvicorn[standard]
pillow
numpy
python-multipart
	Note: The STL generator writes an ASCII STL file and uses only numpy + Pillow so no heavy 3D libraries are required.

setup.py (makes hueforge-lite installable)
from setuptools import setup, find_packages
setup(
    name='hueforge-lite',
    version='0.1.0',
    description='Hueforge-style image -> heightmap -> STL generator',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pillow',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'hueforge-cli = hueforge.cli:main',
        ],
    },
)

hueforge/__init__.py
__version__ = '0.1.0'

hueforge/hueforge_logic.py (core logic)
from PIL import Image, ImageOps, ImageFilter
import numpy as np
def load_image(path_or_bytes):
    img = Image.open(path_or_bytes).convert('RGB')
    return img
def image_to_heightmap(img, height_scale=1.0, contrast=1.0, blur_radius=0.0):
    # img: PIL Image
    gray = ImageOps.grayscale(img)
if contrast != 1.0:
        # simple contrast stretch around mean
        arr = np.array(gray, dtype=np.float32)
        mean = arr.mean()
        arr = (arr - mean) * contrast + mean
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        gray = Image.fromarray(arr)
if blur_radius and blur_radius > 0:
        gray = gray.filter(ImageFilter.GaussianBlur(radius=blur_radius))
arr = np.array(gray, dtype=np.float32)
    arr_norm = arr / 255.0
heightmap = (arr_norm * 255.0 * float(height_scale)).astype(np.uint8)
    return Image.fromarray(heightmap)
def save_heightmap(img, out_path):
    img.save(out_path)
def heightmap_to_array(img):
    return np.array(img, dtype=np.float32) / 255.0

hueforge/stl_generator.py (heightmap -> ASCII STL)
import numpy as np
# Simple ASCII STL exporter using two triangles per grid cell
def heightmap_to_stl_ascii(heightmap_array, scale_xy=1.0, height_scale=1.0, file_path='out.stl', solid_name='hueforge'):
    """heightmap_array: 2D numpy array, values in [0..1]
    Writes an ASCII STL file representing a surface mesh.
    """
    h, w = heightmap_array.shape
def vertex(i, j):
        x = j * scale_xy
        y = i * scale_xy
        z = float(heightmap_array[i, j]) * height_scale
        return (x, y, z)
def tri_normal(v1, v2, v3):
        v1 = np.array(v1); v2 = np.array(v2); v3 = np.array(v3)
        n = np.cross(v2 - v1, v3 - v1)
        norm = np.linalg.norm(n)
        if norm == 0:
            return (0.0, 0.0, 0.0)
        return tuple((n / norm).tolist())
with open(file_path, 'w') as f:
        f.write(f'solid {solid_name}\n')
        for i in range(h - 1):
            for j in range(w - 1):
                v00 = vertex(i, j)
                v10 = vertex(i+1, j)
                v11 = vertex(i+1, j+1)
                v01 = vertex(i, j+1)
# Triangle 1: v00, v10, v11
                n1 = tri_normal(v00, v10, v11)
                f.write(f' facet normal {n1[0]} {n1[1]} {n1[2]}\n')
                f.write('  outer loop\n')
                f.write(f'   vertex {v00[0]} {v00[1]} {v00[2]}\n')
                f.write(f'   vertex {v10[0]} {v10[1]} {v10[2]}\n')
                f.write(f'   vertex {v11[0]} {v11[1]} {v11[2]}\n')
                f.write('  endloop\n')
                f.write(' endfacet\n')
# Triangle 2: v00, v11, v01
                n2 = tri_normal(v00, v11, v01)
                f.write(f' facet normal {n2[0]} {n2[1]} {n2[2]}\n')
                f.write('  outer loop\n')
                f.write(f'   vertex {v00[0]} {v00[1]} {v00[2]}\n')
                f.write(f'   vertex {v11[0]} {v11[1]} {v11[2]}\n')
                f.write(f'   vertex {v01[0]} {v01[1]} {v01[2]}\n')
                f.write('  endloop\n')
                f.write(' endfacet\n')
        f.write(f'endsolid {solid_name}\n')
return file_path

hueforge/cli.py (console script)
import argparse
from PIL import Image
import numpy as np
from .hueforge_logic import load_image, image_to_heightmap, heightmap_to_array
from .stl_generator import heightmap_to_stl_ascii
def main():
    parser = argparse.ArgumentParser(prog='hueforge-cli')
    parser.add_argument('input', help='Input image path')
    parser.add_argument('-o', '--output', default='heightmap.png')
    parser.add_argument('--scale', type=float, default=1.0, help='height scale multiplier')
    parser.add_argument('--contrast', type=float, default=1.0)
    parser.add_argument('--blur', type=float, default=0.0)
    parser.add_argument('--stl', help='Write an ASCII STL to the given path')
    parser.add_argument('--stl-scale', type=float, default=1.0, help='XY scale for STL grid')
    parser.add_argument('--stl-height-scale', type=float, default=10.0, help='Z multiplier for STL')
args = parser.parse_args()
img = load_image(args.input)
    hm = image_to_heightmap(img, height_scale=args.scale, contrast=args.contrast, blur_radius=args.blur)
    hm.save(args.output)
    print('Saved heightmap ->', args.output)
if args.stl:
        arr = heightmap_to_array(hm)
        heightmap_to_stl_ascii(arr, scale_xy=args.stl_scale, height_scale=args.stl_height_scale, file_path=args.stl)
        print('Saved STL ->', args.stl)
if __name__ == '__main__':
    main()

hueforge/tkinter_app.py
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageTk, Image
from .hueforge_logic import load_image, image_to_heightmap
def run_tk_app():
    root = tk.Tk()
    root.title('Hueforge Lite - Desktop')
img_label = tk.Label(root, text='No image loaded')
    img_label.pack()
def open_file():
        path = filedialog.askopenfilename(filetypes=[('Images', '*.png;*.jpg;*.jpeg;*.bmp')])
        if not path:
            return
        img = load_image(path)
        hm = image_to_heightmap(img, height_scale=1.0)
        hm.thumbnail((400, 400))
        tkimg = ImageTk.PhotoImage(hm)
        img_label.config(image=tkimg, text='')
        img_label.image = tkimg
out = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png')])
        if out:
            hm.save(out)
            messagebox.showinfo('Saved', f'Saved heightmap to {out}')
btn = tk.Button(root, text='Open Image', command=open_file)
    btn.pack(pady=10)
root.mainloop()
if __name__ == '__main__':
    run_tk_app()

FastAPI app: fastapi_app/main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uuid
from PIL import Image
from hueforge.hueforge_logic import load_image, image_to_heightmap
app = FastAPI()
app.mount('/static', StaticFiles(directory='fastapi_app/static'), name='static')
@app.get('/')
async def index():
    with open('fastapi_app/static/index.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())
@app.post('/hueforge')
async def hueforge_endpoint(file: UploadFile = File(...), scale: float = 1.0):
    input_path = f'temp_{uuid.uuid4().hex}.png'
    output_path = f'temp_out_{uuid.uuid4().hex}.png'
    content = await file.read()
    with open(input_path, 'wb') as f:
        f.write(content)
img = load_image(input_path)
    hm = image_to_heightmap(img, height_scale=scale)
    hm.save(output_path)
return FileResponse(output_path, media_type='image/png')

Web UI: fastapi_app/static/index.html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Hueforge Lite - Web UI</title>
</head>
<body>
  <h1>Hueforge Lite - Web UI</h1>
  <input id="file" type="file" accept="image/*" />
  <br/>
  <label>Height scale: <input id="scale" type="number" value="1.0" step="0.1"/></label>
  <br/>
  <button id="upload">Upload & Generate</button>
  <div>
    <h3>Result</h3>
    <img id="result" style="max-width:600px;" />
  </div>
  <script src="/static/script.js"></script>
</body>
</html>

fastapi_app/static/script.js
const fileInput = document.getElementById('file');
const uploadBtn = document.getElementById('upload');
const resultImg = document.getElementById('result');
uploadBtn.addEventListener('click', async () => {
  if (!fileInput.files[0]) {
    alert('Select a file first');
    return;
  }
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  form.append('scale', document.getElementById('scale').value || '1.0');
const res = await fetch('/hueforge', {
    method: 'POST',
    body: form
  });
  if (!res.ok) {
    alert('Upload failed');
    return;
  }
  const blob = await res.blob();
  resultImg.src = URL.createObjectURL(blob);
});

README: quick run guide
# Install dependencies
python -m pip install -r requirements.txt
# Run FastAPI app
uvicorn fastapi_app.main:app --reload
# open http://127.0.0.1:8000
# Tkinter desktop app
python -m hueforge.tkinter_app
# CLI usage (after pip install -e . or python -m)
# Example: create a heightmap and an STL
hueforge-cli examples/sample_input.jpg -o output_height.png --scale 1.0 --stl output.stl --stl-height-scale 12.0
# Install package locally
pip install -e .

Notes, caveats & possible enhancements
	• The STL exporter is a simple surface mesh (no bottom or walls). For 3D-printable solid parts you may want to add a base plate and side walls, or use a library like trimesh or numpy-stl.
	• For more accurate Hueforge-style results you can add color-layering and dithering; this code produces a heightmap (grayscale image) which is the core building block.
	• The FastAPI app writes temporary files; in production use a proper temp directory and cleanup.

If you want, I can also:
	• produce a ZIP of the project (I can generate the files into a downloadable archive),
	• add the STL base/sidewall generator to make the mesh watertight,
	• add unit tests and CI config,
	• or convert the package to use pyproject.toml + poetry/flit for modern builds.


All done — I created the full project in a canvas titled Hueforge Full Project (you can open it on the right). It includes:
	• FastAPI app (with static Web UI)
	• Tkinter desktop app
	• CLI + setup.py so you can pip install -e . and get hueforge-cli
	• Simple ASCII STL generator
	• README, requirements, and example usage
Next steps (quick commands):
	1. Install dependencies:
python -m pip install -r requirements.txt
	2. Run the FastAPI web app:
uvicorn fastapi_app.main:app --reload
# then open http://127.0.0.1:8000
	3. Run the Tkinter app:
python -m hueforge.tkinter_app
	4. Install the CLI locally and use it:
pip install -e .
hueforge-cli examples/sample_input.jpg -o output_height.png --stl output.stl --stl-height-scale 12.0
If you'd like, I can now:
	• produce a downloadable ZIP of the project,
	• add an STL base/walls to make the mesh printable,
	• or modify any part of the code (improve contrast/dithering, add progress UI, make the FastAPI return an STL, etc).
Which follow-up would you like me to do now?

