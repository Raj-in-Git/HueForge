# hueforge/hueforge_logic.py
from PIL import Image, ImageOps, ImageFilter
import numpy as np
from typing import Tuple

def load_image(path_or_file) -> Image.Image:
    """Load image from path or file-like object (UploadFile.file)."""
    img = Image.open(path_or_file).convert("RGB")
    return img

def image_to_heightmap(
    img: Image.Image,
    max_dim: int = 300,
    contrast: float = 1.0,
    blur_radius: float = 0.0,
    invert: bool = False
) -> Image.Image:
    """
    Convert RGB image to grayscale heightmap.
    - max_dim limits larger images for manageable STL size (downscale preserving aspect).
    - contrast: 1.0 = unchanged, >1 increases contrast.
    - blur_radius: gaussian blur to smooth the heightmap.
    Returns a PIL grayscale ('L') image with values 0..255.
    """
    if img is None:
        raise ValueError("No image provided")

    # Resize so the larger side == max_dim (preserve aspect ratio)
    w, h = img.size
    scale = min(1.0, float(max_dim) / max(w, h))
    if scale < 1.0:
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)

    gray = ImageOps.grayscale(img)

    # Contrast adjustment (simple linear around mean)
    if contrast != 1.0:
        arr = np.array(gray, dtype=np.float32)
        mean = arr.mean()
        arr = (arr - mean) * float(contrast) + mean
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        gray = Image.fromarray(arr)

    if blur_radius and blur_radius > 0.0:
        gray = gray.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    if invert:
        gray = ImageOps.invert(gray)

    return gray  # mode 'L', range 0..255

def heightmap_to_array(img: Image.Image) -> np.ndarray:
    """Return float array in range [0..1]"""
    arr = np.array(img, dtype=np.float32)
    return arr / 255.0
