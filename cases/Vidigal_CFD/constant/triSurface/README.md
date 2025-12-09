# STL Geometry Files

This directory is for STL geometry files used by `snappyHexMesh` to create the computational mesh.

## Adding Your STL File

1. Place your STL file in this directory (`constant/triSurface/`)
2. Recommended name: `vidigal.stl` (or your preferred name)
3. Update the `system/snappyHexMeshDict` file to reference your STL file name

## STL File Requirements

- **Format**: ASCII or binary STL (ASCII recommended for debugging)
- **Units**: Meters (consistent with OpenFOAM units)
- **Orientation**: Surface normals should point outward from solid regions
- **Quality**: 
  - Watertight (no gaps or holes)
  - No overlapping or intersecting surfaces
  - Clean geometry (no degenerate triangles)

## Verification

Before meshing, you can check your STL file with:
```bash
checkGeometry constant/triSurface/vidigal.stl
```

## Mesh Generation

The STL file will be used during the mesh generation process:
- Background mesh is created with `blockMesh`
- Features are extracted with `surfaceFeatureExtract`
- Final mesh is created with `snappyHexMesh` using this STL geometry

For detailed setup instructions, see `docs/CASE_CREATION_PLAN.md`.

