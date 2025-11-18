# hueforge/cli.py
import argparse
import tempfile
import os
from PIL import Image
from .hueforge_logic import load_image, image_to_heightmap, heightmap_to_array
from .stl_generator import heightmap_to_watertight_stl

def main():
    parser = argparse.ArgumentParser(prog="hueforge-cli")
    parser.add_argument("input", help="input image path")
    parser.add_argument("-o", "--out", default="out.stl", help="output stl file path")
    parser.add_argument("--max-dim", type=int, default=300, help="max image dimension (px)")
    parser.add_argument("--contrast", type=float, default=1.0)
    parser.add_argument("--blur", type=float, default=0.0)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--scale-xy", type=float, default=0.5, help="mm per pixel (X/Y)")
    parser.add_argument("--z-scale", type=float, default=10.0, help="mm height for value 1.0")
    parser.add_argument("--base-thickness", type=float, default=2.0, help="mm")
    args = parser.parse_args()

    img = load_image(args.input)
    hm_img = image_to_heightmap(img, max_dim=args.max_dim, contrast=args.contrast, blur_radius=args.blur, invert=args.invert)
    arr = heightmap_to_array(hm_img)

    # create stl
    heightmap_to_watertight_stl(arr, args.out, scale_xy=args.scale_xy, z_scale=args.z_scale, base_thickness=args.base_thickness)
    print("Wrote:", args.out)

if __name__ == "__main__":
    main()
