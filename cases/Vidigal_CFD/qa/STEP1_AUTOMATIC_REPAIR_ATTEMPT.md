# Step 1A - Automatic Repair Attempt (vidigal.stl)

Date: 2026-02-25
Case: `cases/Vidigal_CFD`
Input geometry: `constant/triSurface/vidigal.stl`

## Requested Sequence

1. Reorient normals
2. Recheck geometry
3. Auto patch at 30 degrees
4. Recheck patched surface

## Commands Executed

All commands were run in Docker image `microclimatefoam:dev`.

```bash
surfaceOrient constant/triSurface/vidigal.stl \
  constant/triSurface/repair/vidigal_fixed.stl "(200 200 300)"

surfaceCheck constant/triSurface/repair/vidigal_fixed.stl

surfaceAutoPatch constant/triSurface/repair/vidigal_fixed.stl \
  constant/triSurface/repair/vidigal_patched.stl 30

surfaceCheck constant/triSurface/repair/vidigal_patched.stl
```

## Evidence Files

- `qa/auto_repair/01_surfaceOrient_output.txt`
- `qa/auto_repair/02_surfaceCheck_fixed_output.txt`
- `qa/auto_repair/03_surfaceAutoPatch_output.txt`
- `qa/auto_repair/04_surfaceCheck_patched_output.txt`

Generated repaired surfaces:

- `constant/triSurface/repair/vidigal_fixed.stl`
- `constant/triSurface/repair/vidigal_patched.stl`

## Comparison (fixed vs patched)

`surfaceCheck` reported the same core defects before and after `surfaceAutoPatch`:

- Triangles: 17424 (unchanged)
- Vertices: 10796 (unchanged)
- Open edges (connected to one face): 3540 (unchanged)
- Non-manifold edges (connected to >2 faces): 133 (unchanged)
- Conflicting face labels: 4080 (unchanged)
- Unconnected parts: 405 (unchanged)
- Normal-orientation zones: 490 with mixed orientation (unchanged)

## Conclusion

Automatic repair with `surfaceOrient` + `surfaceAutoPatch 30` did not resolve the
watertightness defects for `vidigal.stl`. A more robust geometry-cleaning step
is required before meshing (manual CAD cleanup or dedicated mesh-repair tools).
