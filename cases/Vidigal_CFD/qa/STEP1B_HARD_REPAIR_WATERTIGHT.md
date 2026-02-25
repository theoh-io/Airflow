# Step 1B - Hard Repair to Watertight STL (vidigal)

Date: 2026-02-25
Case: `cases/Vidigal_CFD`

## Goal

Produce a watertight geometry from `constant/triSurface/vidigal.stl`.

## Method

Used `pymeshfix` (MeshFix algorithm) after loading the STL as a connected mesh:

- `joincomp=False`
- `remove_smallest_components=True`

Output file:

- `constant/triSurface/repair/vidigal_meshfix_default.stl`

Validation was done with `surfaceCheck`.

## Results

Original (`vidigal.stl`):

- Triangles: 17424
- Vertices: 10796
- Not closed
- Open edges (`connected to one face`): 3540
- Non-manifold edges (`connected to >2 faces`): 133
- Unconnected parts: 405
- Normal zones: 490 (mixed orientation)

Repaired (`repair/vidigal_meshfix_default.stl`):

- Triangles: 6242
- Vertices: 3123
- Closed surface (`Surface is closed. All edges connected to two faces.`)
- Unconnected parts: 1
- Normal zones: 1

## Important Tradeoff

The repaired watertight geometry is topologically cleaner but does not preserve
all original disconnected details (face count and bounding extent are reduced).
This is suitable for a watertight meshing baseline, but should be reviewed in
ParaView before production runs.

## Evidence

- `qa/hard_repair/vidigal_surfaceCheck.txt`
- `qa/hard_repair/vidigal_meshfix_default_surfaceCheck.txt`

## Case Configuration Update

The case now points snappy and feature extraction to the repaired geometry:

- `system/snappyHexMeshDict` -> `repair/vidigal_meshfix_default.stl`
- `system/surfaceFeatureExtractDict` -> `repair/vidigal_meshfix_default.stl`
