# Vidigal_CFD Mesh Configuration Summary

## Geometry Information

**STL File**: `constant/triSurface/vidigal.stl`
- Format: Binary STL
- Triangles: 17,424
- Geometry bounds:
  - X: [-69.06, 82.09] m (151.16 m length)
  - Y: [-155.27, 148.77] m (304.04 m width)
  - Z: [133.11, 208.34] m (75.23 m height)

**Maximum Height (H)**: 75.23 m

## Computational Domain

Based on H = 75.23 m, the domain boundaries are:
- **Inlet (before)**: 5*H = 376.15 m
- **Outlet (after)**: 15*H = 1,128.45 m
- **Sides (each)**: 5*H = 376.15 m (total: 10*H = 752.30 m)
- **Top (above)**: 5*H = 376.15 m

**Domain Bounds**:
- X: [-445.21, 1210.54] m (1,655.76 m length)
- Y: [-531.42, 524.92] m (1,056.34 m width)
- Z: [133.11, 584.49] m (451.38 m height)

## Mesh Parameters

- **Smallest feature**: 1.0 m
- **Surface cell size**: 1.0 m
- **Background cell size**: 5.0 m
- **Refinement levels**: 2 levels

## Mesh Generation Workflow

1. **blockMesh**: Creates background hexahedral mesh
   - Cell count: ~332 × 212 × 91 = ~6.4M cells (background)
   - Configuration: `constant/air/polyMesh/blockMeshDict`

2. **surfaceFeatureExtract**: Extracts sharp edges from STL
   - Feature angle: 120°
   - Output: `vidigal.eMesh`
   - Configuration: `system/surfaceFeatureExtractDict`

3. **snappyHexMesh**: Refines and snaps mesh to STL surfaces
   - Surface refinement: Level 1-2
   - Inside refinement: Level 1
   - Max cells: 50M
   - Configuration: `system/snappyHexMeshDict`

4. **checkMesh**: Validates mesh quality
   - Checks orthogonality, skewness, volume
   - Reports mesh statistics

## Expected Mesh Size

After snappyHexMesh:
- **Estimated cells**: 5-20 million (depending on refinement)
- **Surface patches**: Created automatically from STL
- **Cell count will be reduced** from background mesh due to:
  - Removal of cells inside solid regions
  - Refinement near surfaces

## Configuration Files

- `constant/air/polyMesh/blockMeshDict` - Background mesh
- `system/surfaceFeatureExtractDict` - Feature extraction
- `system/snappyHexMeshDict` - Mesh refinement and snapping
- `Allrun` - Mesh generation workflow script

## Running Mesh Generation

```bash
cd cases/Vidigal_CFD
./Allrun
```

Or step by step:

```bash
blockMesh -region air
surfaceFeatureExtract -region air
snappyHexMesh -region air -overwrite
checkMesh -region air
```

## Notes

- **Watertight check**: See `WATERTIGHT_CHECK.md` for verifying geometry
- **Single fluid region**: Currently configured for air only
- **Patch names**: Will be created automatically from STL surfaces
- **Boundary conditions**: Need to be updated after mesh generation based on patch names

