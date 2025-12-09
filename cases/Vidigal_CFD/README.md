# Vidigal_CFD Case

CFD simulation case based on STL geometry using the `urbanMicroclimateFoam` solver.

## Status

✅ **Configuration Validated** - Case structure created, STL geometry analyzed, mesh configuration validated. Background mesh generated (6.4M cells). Mesh refinement (snappyHexMesh) is currently running.

## Solver

- **Required solver**: `urbanMicroclimateFoam`
- **Version**: OpenFOAM 8 (of-org_v8.0)

## Description

This case performs CFD simulation using STL-based geometry. Unlike tutorial cases that use `blockMesh`, this case uses `snappyHexMesh` to generate an unstructured mesh from STL geometry files.

## Setup

### Prerequisites

1. STL geometry file (to be placed in `constant/triSurface/`)
2. `urbanMicroclimateFoam` solver built and available
3. OpenFOAM 8 environment sourced

### Adding STL File

1. Place your STL file in `constant/triSurface/`
2. Recommended name: `vidigal.stl`
3. See `constant/triSurface/README.md` for STL requirements

### Mesh Configuration

✅ **Complete** - All mesh configuration files are set up:

1. **Background mesh** (`constant/air/polyMesh/blockMeshDict`) ✅
   - Domain: 1,655.76 m × 1,056.34 m × 451.38 m
   - Background cell size: 5.0 m (~6.4M cells)
   
2. **SnappyHexMesh** (`system/snappyHexMeshDict`) ✅
   - STL file referenced: `constant/triSurface/vidigal.stl`
   - Surface cell size: 1.0 m
   - Refinement levels: 2

3. **Feature extraction** (`system/surfaceFeatureExtractDict`) ✅
   - Feature angle: 120°
   - Configured for edge extraction

4. **Mesh workflow** (`Allrun` script) ✅
   - Complete workflow: `blockMesh` → `surfaceFeatureExtract` → `snappyHexMesh` → `checkMesh`

See `MESH_CONFIGURATION.md` for detailed mesh settings.

## Regions

Currently configured for single fluid region:
- `air` - Fluid region

Additional regions (solid, vegetation) can be added as needed based on STL geometry.

## Running

### Build Solvers First

```bash
./scripts/build_all_solvers.sh
```

### Quick Validation (Recommended for Testing)

```bash
./scripts/run_case.sh --quick-validation -v cases/Vidigal_CFD
```

### Full Run

```bash
cd cases/Vidigal_CFD
./Allrun
```

Or using the generic runner:

```bash
./scripts/run_case.sh cases/Vidigal_CFD urbanMicroclimateFoam
```

## Mesh Generation Workflow

The case will use the following mesh generation workflow:

1. `blockMesh` - Create background mesh
2. `surfaceFeatureExtract` - Extract features from STL
3. `snappyHexMesh` - Refine and snap to STL surfaces
4. `checkMesh` - Verify mesh quality
5. `createPatch` (if needed) - Set up patches for regions

**Note**: The `Allrun` script has been updated for STL-based meshing workflow.

## Boundary Conditions

Boundary patch names will be determined from the STL-based mesh. Initial field files in `0/air/` may need to be updated with the correct patch names after mesh generation.

## Visualization

After running the case, generate visualization images:

```bash
./scripts/postprocess/generate_images.sh cases/Vidigal_CFD [time]
```

Or open in ParaView:

```bash
# Create ParaView case file (if not already created)
./scripts/create_foam_file.sh cases/Vidigal_CFD

# Open in ParaView
paraview cases/Vidigal_CFD/Vidigal_CFD.foam
```

## Documentation

- Case documentation:
  - `MESH_CONFIGURATION.md` - Detailed mesh configuration
  - `VALIDATION_REPORT.md` - Configuration validation results
  - `WATERTIGHT_CHECK.md` - Geometry verification guide
  - `SETUP_COMPLETE.md` - Setup summary
- Project documentation:
  - Detailed implementation plan: `docs/CASE_CREATION_PLAN.md`
  - Solver documentation: `docs/SOLVERS/urbanMicroclimateFoam.md`

## Next Steps

1. ✅ Case structure created
2. ✅ STL file added to `constant/triSurface/`
3. ✅ Mesh generation configured (blockMeshDict, snappyHexMeshDict)
4. ✅ Allrun script updated for STL-based workflow
5. ✅ Configuration validated (`./test_mesh_config.sh`)
6. 🔄 **Next**: Test mesh generation (blockMesh → surfaceFeatureExtract → snappyHexMesh)
7. ⏳ Update boundary conditions after mesh generation
8. ⏳ Run quick validation test

