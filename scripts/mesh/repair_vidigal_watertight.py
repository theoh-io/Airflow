#!/usr/bin/env python3
"""
Create a watertight repair candidate for Vidigal STL using pymeshfix.

This script preserves the original STL and writes the repaired result to:
  cases/Vidigal_CFD/constant/triSurface/repair/vidigal_meshfix_default.stl
"""

from pathlib import Path

import trimesh
from pymeshfix import MeshFix


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "cases/Vidigal_CFD/constant/triSurface/vidigal.stl"
    out = (
        repo_root
        / "cases/Vidigal_CFD/constant/triSurface/repair/vidigal_meshfix_default.stl"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    mesh = trimesh.load(src, force="mesh", process=True)
    mfix = MeshFix(mesh.vertices.copy(), mesh.faces.copy())
    mfix.repair(joincomp=False, remove_smallest_components=True)

    repaired = trimesh.Trimesh(vertices=mfix.points, faces=mfix.faces, process=True)
    repaired.export(out)

    print(f"Input faces/verts: {len(mesh.faces)}/{len(mesh.vertices)}")
    print(f"Output faces/verts: {len(repaired.faces)}/{len(repaired.vertices)}")
    print(f"Output watertight: {repaired.is_watertight}")
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
