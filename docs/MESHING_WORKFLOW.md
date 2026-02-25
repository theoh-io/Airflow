# Meshing Workflow Documentation

This document describes the complete meshing workflow for OpenFOAM cases, including both rectangular and circular domain options.

## Overview

The meshing workflow consists of several steps:
1. **Background Mesh Generation** - Create initial structured mesh
2. **Feature Extraction** (optional) - Extract sharp edges from STL
3. **Mesh Refinement** - Refine and snap to geometry using snappyHexMesh
4. **Mesh Quality Check** - Validate mesh quality
5. **Boundary Setup** - Configure boundary patches

## Domain Types

### Rectangular Domain (Default)

The standard rectangular domain uses `blockMesh` to create a box-shaped background mesh.

**Configuration:**
- File: `constant/air/polyMesh/blockMeshDict`
- Shape: Rectangular box
- Boundaries: inlet, outlet, sides, ground, top

**Advantages:**
- Simple to set up
- Standard OpenFOAM workflow
- Well-documented

**Use Case:**
- Standard wind flow simulations
- Cases where rectangular domain is appropriate

### Circular Domain (New)

Circular domains use an octagonal approximation to create a cylindrical background mesh.

**Configuration:**
- Template: `constant/air/polyMesh/blockMeshDict.circular`
- Shape: Cylindrical (octagon approximation)
- Boundaries: inlet, outlet, walls, ground, top

**Advantages:**
- Reduced domain size
- Better for axisymmetric flows
- More natural for wind flow around structures

**Use Case:**
- Wind flow around buildings
- Cases where circular domain better matches physics
- When domain size reduction is important

## Meshing Steps

### Step 1: Background Mesh Generation

#### Rectangular Domain
```bash
blockMesh -region air
```

#### Circular Domain
```bash
# Option 1: Use template
cp constant/air/polyMesh/blockMeshDict.circular \
   constant/air/polyMesh/blockMeshDict
blockMesh -region air

# Option 2: Generate from geometry info
python scripts/mesh/create_circular_domain.py \
    geometry_info.txt \
    constant/air/polyMesh/blockMeshDict
blockMesh -region air

# Option 3: Use helper script
./scripts/mesh/switch_to_circular_domain.sh cases/Vidigal_CFD
blockMesh -region air
```

### Step 2: Feature Extraction (Optional)

Extract sharp edges from STL geometry:
```bash
surfaceFeatureExtract -region air
```

This creates `constant/triSurface/vidigal.eMesh` with feature edges.

**Note:** Can be skipped if using implicit feature detection in snappyHexMesh.

### Step 3: Mesh Refinement with snappyHexMesh

Refine and snap mesh to STL geometry:
```bash
snappyHexMesh -region air -dict system/snappyHexMeshDict -overwrite
```

**Configuration:** `system/snappyHexMeshDict`
- Surface refinement levels
- Snapping parameters
- Layer addition (optional)

**Expected Time:** 30 minutes to several hours depending on geometry complexity.

### Step 4: Mesh Quality Check

Validate mesh quality:
```bash
checkMesh -region air
```

**Checks:**
- Mesh connectivity
- Cell quality (skewness, non-orthogonality)
- Volume checks
- Boundary patch integrity

### Step 5: Boundary Patch Identification

After mesh generation, identify boundary patches:
```bash
cat constant/air/polyMesh/boundary
```

Update boundary conditions in `0/air/` files to match patch names.

## Complete Workflow Scripts

### Automated Mesh Generation

**For Vidigal_CFD case:**
```bash
cd cases/Vidigal_CFD
./generate_mesh.sh
```

This script:
1. Generates background mesh
2. Prepares for snappyHexMesh (handles multi-region structure)
3. Runs snappyHexMesh
4. Copies mesh back to region structure
5. Runs checkMesh

### Using Allrun Script

The `Allrun` script provides a complete workflow:
```bash
cd cases/Vidigal_CFD
./Allrun
```

This includes mesh generation and solver execution.

## Domain Selection Guide

### When to Use Rectangular Domain

- Standard wind flow simulations
- Cases with rectangular geometry
- When simplicity is preferred
- Standard OpenFOAM tutorials

### When to Use Circular Domain

- Wind flow around isolated structures
- Axisymmetric or near-axisymmetric flows
- When domain size reduction is important
- Cases where circular boundary better matches physics

## Mesh Parameters

### Background Mesh Cell Size

**Typical Values:**
- Surface cell size: 0.5-2.0 m (near geometry)
- Background cell size: 5.0-10.0 m (away from geometry)
- Ratio: Background ≈ 5-10× surface size

### Refinement Levels

**snappyHexMesh Refinement:**
- Level 0: Background mesh
- Level 1: First refinement (2× smaller cells)
- Level 2: Second refinement (4× smaller cells)
- Level 3: Third refinement (8× smaller cells)

**Typical Configuration:**
- Surface refinement: Level 1-2
- Inside refinement: Level 1
- Max cells: 10-50 million

### Domain Clearance

**Recommended Clearances:**
- Inlet (upstream): 5×H (H = maximum geometry height)
- Outlet (downstream): 15×H
- Sides: 5×H each
- Top: 5×H

**For Circular Domain:**
- Radius: max(geometry_extent)/2 + 5×H

## Troubleshooting

### Mesh Generation Fails

1. **Check STL file:**
   ```bash
   checkGeometry constant/triSurface/vidigal.stl
   ```

2. **Verify blockMeshDict:**
   ```bash
   blockMesh -region air -checkGeometry
   ```

3. **Check snappyHexMeshDict:**
   - Verify STL file path
   - Check refinement levels
   - Verify max cell limits

### Poor Mesh Quality

1. **Run checkMesh:**
   ```bash
   checkMesh -region air
   ```

2. **Common Issues:**
   - High skewness: Increase surface refinement
   - Non-orthogonality: Adjust snapping parameters
   - Negative volumes: Check STL geometry

3. **Solutions:**
   - Increase refinement levels
   - Adjust snapping parameters
   - Check STL geometry quality

### Boundary Patches Not Found

1. **List patches:**
   ```bash
   cat constant/air/polyMesh/boundary
   ```

2. **Update boundary conditions:**
   - Match patch names in `0/air/` files
   - Verify patch types (patch, wall, etc.)

## Performance Considerations

### Mesh Size

- **Small cases:** < 1M cells (quick testing)
- **Medium cases:** 1-10M cells (standard simulations)
- **Large cases:** 10-50M cells (production runs)
- **Very large:** > 50M cells (high-resolution studies)

### Generation Time

- **blockMesh:** Seconds to minutes
- **snappyHexMesh:** 30 minutes to several hours
- **checkMesh:** Minutes

### Memory Requirements

- **1M cells:** ~500 MB RAM
- **10M cells:** ~5 GB RAM
- **50M cells:** ~25 GB RAM

## Best Practices

1. **Start with Coarse Mesh:**
   - Use larger cell sizes initially
   - Validate workflow
   - Refine later if needed

2. **Validate Geometry:**
   - Check STL quality before meshing
   - Verify geometry bounds
   - Ensure adequate clearance

3. **Monitor Progress:**
   - Use `monitor_mesh.sh` for long runs
   - Check intermediate results
   - Save checkpoints

4. **Document Parameters:**
   - Record cell sizes
   - Document refinement levels
   - Note any issues encountered

5. **Version Control:**
   - Keep mesh configuration files in Git
   - Document mesh generation parameters
   - Track mesh quality metrics

## References

- `cases/Vidigal_CFD/MESH_CONFIGURATION.md` - Vidigal_CFD mesh configuration
- `docs/CIRCULAR_DOMAIN.md` - Circular domain guide
- OpenFOAM User Guide: blockMesh, snappyHexMesh
- OpenFOAM Tutorials: Mesh generation examples
