# hueforge/stl_generator.py
import numpy as np
from typing import Tuple
import math

def _tri_normal(a, b, c):
    a = np.array(a); b = np.array(b); c = np.array(c)
    n = np.cross(b - a, c - a)
    norm = np.linalg.norm(n)
    if norm == 0:
        return (0.0, 0.0, 0.0)
    n = n / norm
    return (float(n[0]), float(n[1]), float(n[2]))

def write_ascii_stl(filename: str, facets: list, solid_name="hueforge"):
    """facets: list of tuples (normal, v1, v2, v3)"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"solid {solid_name}\n")
        for normal, v1, v2, v3 in facets:
            f.write(f" facet normal {normal[0]} {normal[1]} {normal[2]}\n")
            f.write("  outer loop\n")
            f.write(f"   vertex {v1[0]} {v1[1]} {v1[2]}\n")
            f.write(f"   vertex {v2[0]} {v2[1]} {v2[2]}\n")
            f.write(f"   vertex {v3[0]} {v3[1]} {v3[2]}\n")
            f.write("  endloop\n")
            f.write(" endfacet\n")
        f.write(f"endsolid {solid_name}\n")

def heightmap_to_watertight_stl(
    heightmap: np.ndarray,
    out_path: str,
    scale_xy: float = 0.5,
    z_scale: float = 10.0,
    base_thickness: float = 2.0,
    solid_name: str = "hueforge_model"
):
    """
    Create a watertight ASCII STL from a heightmap (2D numpy array in [0..1]).
    - scale_xy: distance between grid points in X and Y (mm)
    - z_scale: multiplier mapping heightmap value to mm for Z (top surface)
    - base_thickness: thickness of the flat bottom base (mm)
    """

    h, w = heightmap.shape
    # Precompute vertex coordinates for top surface
    top_vertices = [[(j * scale_xy, i * scale_xy, float(heightmap[i, j]) * z_scale) for j in range(w)] for i in range(h)]

    facets = []

    # Top surface triangles (two per cell)
    for i in range(h - 1):
        for j in range(w - 1):
            v00 = top_vertices[i][j]
            v10 = top_vertices[i+1][j]
            v11 = top_vertices[i+1][j+1]
            v01 = top_vertices[i][j+1]

            # triangle 1: v00, v10, v11
            n1 = _tri_normal(v00, v10, v11)
            facets.append((n1, v00, v10, v11))

            # triangle 2: v00, v11, v01
            n2 = _tri_normal(v00, v11, v01)
            facets.append((n2, v00, v11, v01))

    # Base rectangle coordinates (flat) at z = -base_thickness
    # We'll create an outer rectangle with corners aligned to grid extents
    x0, y0 = 0.0, 0.0
    x1, y1 = (w - 1) * scale_xy, (h - 1) * scale_xy
    zb = -abs(base_thickness)

    # Bottom face (two triangles)
    vbl = (x0, y0, zb)  # bottom-left
    vbr = (x1, y0, zb)  # bottom-right
    vtr = (x1, y1, zb)  # top-right
    vtl = (x0, y1, zb)  # top-left

    # Note: normals for bottom face point downwards
    n_bot = _tri_normal(vbl, vtr, vbr)
    facets.append((n_bot, vbl, vtr, vbr))
    n_bot2 = _tri_normal(vbl, vtl, vtr)
    facets.append((n_bot2, vbl, vtl, vtr))

    # Side walls: connect base rectangle edges to top surface outer perimeter
    # For each edge cell along top perimeter, create quads (two triangles) between base edge and top edge vertices.
    # Bottom perimeter vertices (aligned to top grid at same XY coordinates but zb z)
    bottom_perimeter = []
    # We'll build walls by iterating edges around the perimeter (clockwise)
    # Top perimeter vertices in same ordering:
    top_perimeter = []

    # top row left->right
    for j in range(w):
        top_perimeter.append(top_vertices[0][j])
        bottom_perimeter.append((top_vertices[0][j][0], top_vertices[0][j][1], zb))
    # right column top->bottom (skip first because included)
    for i in range(1, h):
        top_perimeter.append(top_vertices[i][w-1])
        bottom_perimeter.append((top_vertices[i][w-1][0], top_vertices[i][w-1][1], zb))
    # bottom row right->left (skip corner already included)
    for j in range(w-2, -1, -1):
        top_perimeter.append(top_vertices[h-1][j])
        bottom_perimeter.append((top_vertices[h-1][j][0], top_vertices[h-1][j][1], zb))
    # left column bottom->top (skip corner)
    for i in range(h-2, 0, -1):
        top_perimeter.append(top_vertices[i][0])
        bottom_perimeter.append((top_vertices[i][0][0], top_vertices[i][0][1], zb))

    # Create quads between consecutive perimeter points: top_i -> top_{i+1} and bottom_i -> bottom_{i+1}
    per_len = len(top_perimeter)
    for k in range(per_len):
        t0 = top_perimeter[k]
        t1 = top_perimeter[(k + 1) % per_len]
        b0 = bottom_perimeter[k]
        b1 = bottom_perimeter[(k + 1) % per_len]

        # Quad (b0, b1, t1, t0) -> two triangles
        nA = _tri_normal(b0, b1, t1)
        facets.append((nA, b0, b1, t1))
        nB = _tri_normal(b0, t1, t0)
        facets.append((nB, b0, t1, t0))

    # Also create side walls between edge of top surface and the base edges (closing any small gaps)
    # (The perimeter loop above already connects top perimeter to bottom perimeter directly.)

    # Optional: add small vertical walls to ensure a flat contact with print bed: already covered by bottom and side walls

    # Write to file
    write_ascii_stl(out_path, facets, solid_name)

    return out_path
