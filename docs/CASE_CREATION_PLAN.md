# Case Creation Plan: Vidigal_CFD

This document outlines the plan for creating the new `Vidigal_CFD` case based on the `streetCanyon_CFD` template, with STL-based geometry.

## Overview

**Case Name**: `Vidigal_CFD`  
**Location**: `cases/Vidigal_CFD/`  
**Solver**: `urbanMicroclimateFoam`  
**Template**: `cases/streetCanyon_CFD/`  
**Geometry Source**: STL file (to be provided by user)

## Directory Structure

The case will follow the standard OpenFOAM case structure for multi-region cases:

```
cases/Vidigal_CFD/
├── 0/                          # Initial conditions
│   ├── air/                    # Air region initial fields
│   │   ├── U                   # Velocity field
│   │   ├── p_rgh               # Modified pressure field
│   │   ├── T                   # Temperature field
│   │   └── k                   # Turbulent kinetic energy (if RANS)
│   ├── [solid_regions]/        # Solid region initial fields (if applicable)
│   └── ...
├── constant/
│   ├── regionProperties        # Multi-region configuration
│   ├── triSurface/             # STL geometry files (NEW)
│   │   └── vidigal.stl         # User-provided STL file
│   ├── air/                    # Air region constants
│   │   ├── polyMesh/           # Mesh (generated)
│   │   ├── g                   # Gravity vector
│   │   ├── momentumTransport   # Turbulence model
│   │   └── thermophysicalProperties
│   └── [solid_regions]/        # Solid region constants (if applicable)
├── system/
│   ├── controlDict             # Solver control
│   ├── fvSchemes               # Numerical schemes
│   ├── fvSolution              # Solver settings
│   ├── decomposeParDict        # Parallel decomposition
│   ├── air/                    # Air region system files
│   │   └── ...
│   └── meshDict/               # Mesh generation dictionary (NEW)
│       ├── snappyHexMeshDict   # SnappyHexMesh configuration
│       └── surfaceFeatureExtractDict
├── Allrun                      # Case execution script
├── Allclean                    # Case cleanup script
├── Vidigal_CFD.foam           # ParaView case file
└── README.md                   # Case documentation
```

## Implementation Steps

### Phase 1: Directory Setup and Template Copy

1. **Create case directory structure**
   ```bash
   mkdir -p cases/Vidigal_CFD/{0,constant/{triSurface,air},system}
   ```

2. **Copy base structure from streetCanyon_CFD**
   - Copy `0/` directory structure
   - Copy `constant/regionProperties`
   - Copy `constant/air/` directory (excluding `polyMesh/`)
   - Copy `system/controlDict`, `system/fvSchemes`, `system/fvSolution`
   - Copy `system/air/` directory contents
   - Copy `Allrun` and `Allclean` scripts
   - Copy ParaView `.foam` file template

3. **Place STL file**
   - User provides STL file
   - Place in `constant/triSurface/vidigal.stl` (or appropriate name)
   - Verify STL file format and units

### Phase 2: Mesh Generation Configuration

Since `streetCanyon_CFD` uses `blockMesh`, we need to set up STL-based meshing for `Vidigal_CFD`:

1. **Create background mesh**
   - Create `constant/air/polyMesh/blockMeshDict` for background/domain mesh
   - Define domain bounds based on STL geometry extent
   - Create a simple box mesh that encompasses the STL geometry

2. **Configure SnappyHexMesh**
   - Create `system/snappyHexMeshDict`
   - Reference STL file in `geometry` section
   - Configure mesh refinement levels
   - Set up surface snapping parameters
   - Define feature edge extraction if needed

3. **Update Allrun script**
   - Replace `blockMesh` + `createPatch` workflow with:
     - `blockMesh` (background mesh)
     - `surfaceFeatureExtract` (extract features from STL)
     - `snappyHexMesh` (refine and snap to STL surfaces)
     - `topoSet` / `createPatch` (if needed for region setup)

### Phase 3: Multi-Region Setup

1. **Determine regions**
   - Based on STL geometry, identify needed regions
   - Similar to `streetCanyon_CFD`: likely `air`, and solid regions (buildings, ground, etc.)

2. **Configure regionProperties**
   - Update `constant/regionProperties` with appropriate regions
   - Define fluid vs. solid regions

3. **Set up region boundaries**
   - Configure boundary conditions between regions
   - Set up interface patches

### Phase 4: Boundary Conditions and Initial Fields

1. **Initial conditions (0/ directory)**
   - Copy and modify initial field files from `streetCanyon_CFD`
   - Update boundary patch names to match STL-based mesh
   - Adjust field values as needed for Vidigal case

2. **Boundary conditions**
   - Identify boundary patches from STL-based mesh
   - Configure inlet/outlet boundaries
   - Set wall boundary conditions
   - Configure region interface boundaries

### Phase 5: Solver Configuration

1. **Update controlDict**
   - Verify `application` is `urbanMicroclimateFoam`
   - Set appropriate time step and end time
   - Configure output settings

2. **Turbulence model**
   - Copy from `streetCanyon_CFD` or configure as needed
   - Update in `constant/air/momentumTransport`

3. **Thermophysical properties**
   - Copy from `streetCanyon_CFD` or configure for Vidigal conditions
   - Update in `constant/air/thermophysicalProperties`

### Phase 6: Scripts and Automation

1. **Update Allrun script**
   - Replace mesh generation commands
   - Update region names if different
   - Add appropriate checks and error handling

2. **Update Allclean script**
   - Clean mesh directories
   - Clean results directories
   - Keep STL file and configurations

3. **Create README.md**
   - Document case setup
   - Describe geometry source
   - Provide run instructions
   - List key parameters

### Phase 7: Testing and Validation

1. **Mesh generation test**
   - Run mesh generation steps manually
   - Verify mesh quality with `checkMesh`
   - Check region setup

2. **Initial run test**
   - Run with `--quick-validation` flag
   - Verify solver starts correctly
   - Check for errors

3. **Full validation**
   - Run complete case
   - Generate visualizations
   - Compare with reference if available

## Key Differences from streetCanyon_CFD

| Aspect | streetCanyon_CFD | Vidigal_CFD |
|--------|------------------|-------------|
| **Mesh Generation** | `blockMesh` (structured) | `snappyHexMesh` (STL-based, unstructured) |
| **Geometry** | Defined in `blockMeshDict` | Provided as STL file |
| **Mesh Quality** | Structured hex mesh | Unstructured mesh around STL |
| **Setup Complexity** | Simpler (block-based) | More complex (surface meshing) |

## STL File Requirements

1. **File Format**: ASCII or binary STL (preferably ASCII for debugging)
2. **Units**: Consistent with OpenFOAM units (typically meters)
3. **Orientation**: Surface normals pointing outward from solid
4. **Quality**: Watertight, no gaps or overlaps
5. **Size**: Reasonable file size for meshing performance

## Configuration Files to Create/Modify

### New Files:
- `constant/triSurface/vidigal.stl` (user provided)
- `system/snappyHexMeshDict`
- `system/surfaceFeatureExtractDict`
- `constant/air/polyMesh/blockMeshDict` (background mesh)

### Modified Files:
- `system/controlDict` (case-specific settings)
- `constant/regionProperties` (region configuration)
- `0/air/*` (initial fields with correct patch names)
- `Allrun` (mesh generation workflow)
- `Vidigal_CFD.foam` (ParaView case file name)

## Dependencies

- OpenFOAM 8 (or compatible version)
- `urbanMicroclimateFoam` solver (built)
- STL geometry file from user
- Understanding of:
  - SnappyHexMesh configuration
  - Multi-region OpenFOAM setup
  - Surface mesh quality requirements

## Timeline Estimate

- **Phase 1-2** (Directory setup + Mesh config): 2-4 hours
- **Phase 3-4** (Regions + BCs): 2-3 hours
- **Phase 5** (Solver config): 1-2 hours
- **Phase 6** (Scripts): 1 hour
- **Phase 7** (Testing): 2-4 hours

**Total**: ~8-14 hours (depending on STL complexity and mesh refinement requirements)

## Notes and Considerations

1. **Mesh Quality**: STL-based meshing may require more tuning than blockMesh
2. **Performance**: Unstructured meshes may be slower than structured
3. **Refinement**: Need to balance mesh quality vs. computational cost
4. **Regions**: May need `topoSet` or `setSet` to define regions from STL
5. **Boundary Names**: Patch names will come from STL, may differ from template

## Next Steps

1. User provides STL file
2. Inspect STL file (units, quality, size)
3. Begin implementation starting with Phase 1
4. Iterate on mesh generation until quality is acceptable
5. Test with quick validation run
6. Document in case README

