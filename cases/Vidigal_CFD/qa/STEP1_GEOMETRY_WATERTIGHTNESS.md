# Step 1 - Geometry Watertightness (vidigal.stl)

Date: 2026-02-25
Case: `cases/Vidigal_CFD`
Geometry: `constant/triSurface/vidigal.stl`

## Command Used

Run inside Docker image `microclimatefoam:dev`:

```bash
docker run --rm --user $(id -u):$(id -g) \
  --entrypoint /bin/bash \
  -v /home/theo/Airflow:/workspace \
  -w /workspace/cases/Vidigal_CFD \
  microclimatefoam:dev \
  -lc "source /opt/openfoam8/etc/bashrc && surfaceCheck constant/triSurface/vidigal.stl"
```

## Result

Status: FAIL (not watertight)

Key findings from `qa/step1_surfaceCheck_output.txt`:

- Triangles: 17424
- Vertices: 10796
- Illegal triangles: none
- Surface closure: NOT closed
  - edges connected to one face: 3540
  - edges connected to more than two faces: 133
- Conflicting face labels: 4080
- Unconnected parts: 405
- Normal consistency zones: 490, with more than one normal orientation
- Very low minimum triangle quality reported (`1.43903e-21`)

Generated diagnostics:

- `badFaces`
- `problemFaces`

## Conclusion

`vidigal.stl` is not watertight and is not ready for production snappyHexMesh
usage without cleanup/repair.

## Next Action

Proceed to Step 2 (surface orientation) only after deciding whether to:

1. repair `vidigal.stl` geometry first, or
2. continue orientation diagnostics to quantify all surface issues before repair.
