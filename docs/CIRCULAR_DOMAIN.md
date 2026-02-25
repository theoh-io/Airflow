# Circular Domain Meshing Guide

This document describes how to create circular (cylindrical) domains for OpenFOAM CFD simulations.

## Overview

Circular domains are useful for:
- Wind flow around buildings/structures
- Axisymmetric or near-axisymmetric geometries
- Reducing domain size while maintaining adequate clearance
- Cases where a circular domain better matches the flow physics

## Implementation Approaches

### Approach 1: Inner Square + Outer Circle with blockMesh

The recommended approach uses `blockMesh` with an inner square transitioning to an outer circle. This creates a cylindrical domain with:
- Inner square: Encompasses geometry with small clearance (better for rectangular geometries)
- Outer circle: Full domain boundary with adequate clearance (better for wind flow)
- Four connecting blocks: Transition smoothly from square to circle
- Three vertical levels: Allows vertical stretching for better resolution

**Advantages:**
- Better suited for rectangular geometries (buildings)
- Smooth circular outer boundary
- Flexible vertical stretching
- Works with standard OpenFOAM tools
- Can be refined with snappyHexMesh

**Limitations:**
- More complex block structure
- Requires careful vertex and edge definition

### Approach 2: Circular STL with snappyHexMesh

Create a circular domain using a cylindrical STL surface and use `snappyHexMesh` to generate the mesh.

**Advantages:**
- Perfectly circular boundary
- More flexible geometry

**Limitations:**
- Requires creating STL geometry
- More complex setup

## Current Implementation

We use **Approach 1** (inner square + outer circle) as it's better suited for urban geometries and provides smooth circular boundaries while maintaining good mesh quality near rectangular buildings.

### Template File

A template circular domain `blockMeshDict` is available at:
```
cases/Vidigal_CFD/templates/blockMeshDict.circular
```

### Generation Script

A Python script is available to generate circular domain configurations:
```
scripts/mesh/create_circular_domain.py
```

## Usage

### Option 1: Use the Template

1. Copy the template:
   ```bash
   cp cases/Vidigal_CFD/templates/blockMeshDict.circular \
      cases/Vidigal_CFD/constant/air/polyMesh/blockMeshDict
   ```

2. Edit the parameters:
   - Center point (X, Y, Z)
   - Radius
   - Vertical extent (Z_min, Z_max)
   - Cell counts

3. Generate mesh:
   ```bash
   blockMesh -region air
   ```

### Option 2: Use the Generation Script

1. Run the script with geometry information:
   ```bash
   python scripts/mesh/create_circular_domain.py \
       cases/Vidigal_CFD/geometry_info.txt \
       cases/Vidigal_CFD/constant/air/polyMesh/blockMeshDict
   ```

2. The script will:
   - Read geometry bounds from the info file
   - Calculate domain center and radius
   - Generate appropriate cell counts
   - Create the blockMeshDict

3. Generate mesh:
   ```bash
   blockMesh -region air
   ```

## Domain Parameters

### Center Point
- Typically the center of your geometry
- For Vidigal_CFD: Calculated from geometry bounds

### Radius
- Should encompass geometry with adequate clearance
- Recommended: `max(geometry_extent) / 2 + 5*H`
  where H is the maximum geometry height

### Vertical Extent
- Z_min: Ground level (or slightly below)
- Z_max: Geometry height + clearance (typically 5*H)

### Cell Counts
- **Radial cells**: `radius / cell_size` (typically 100-200)
- **Circumferential cells**: 8 (one per octant) or more for smoother circle
- **Vertical cells**: `height / cell_size` (typically 50-100)

## Boundary Patches

The circular domain creates the following boundary patches:

- **inletOutlet**: Cylindrical wall surface (single patch for all directions)
  - This is a single patch that encompasses the entire circular boundary
  - Flow direction can be set via boundary conditions (e.g., wind direction)
- **ground**: Bottom surface (wall)
- **top**: Top surface (patch)

**Note:** Unlike rectangular domains with separate inlet/outlet patches, circular domains use a single `inletOutlet` patch for the cylindrical wall. The flow direction is controlled through boundary conditions rather than patch geometry.

## Integration with snappyHexMesh

After creating the circular background mesh, you can use `snappyHexMesh` to:
1. Refine near geometry surfaces
2. Snap to STL geometry
3. Add boundary layers

The workflow remains the same as rectangular domains:
```bash
blockMesh -region air
snappyHexMesh -region air -dict system/snappyHexMeshDict
checkMesh -region air
```

## Example: Vidigal_CFD Circular Domain

For the Vidigal_CFD case:

**Geometry:**
- Center: (6.52, -3.25, 133.11)
- Extent: 151.16 m × 304.04 m × 75.23 m
- H = 75.23 m

**Domain:**
- Inner square: 400m × 400m (centered on geometry)
- Outer circle radius: 950 m (encompasses geometry + 10H clearance)
- Height: 451.38 m (Z: 133.11 to 584.49)
- Three vertical levels: bottom (z=133.11), middle (z=300.0), top (z=584.49)

**Cells:**
- Inner square: 40 × 40 cells
- Inner to outer: 20 cells (radial direction)
- Vertical bottom: 30 cells
- Vertical top: 50 cells
- Total: ~9 blocks with varying cell counts

## Advantages of Circular Domain

1. **Reduced Domain Size**: Circular domain can be smaller than rectangular while maintaining clearance
2. **Better Flow Physics**: More natural for wind flow around structures
3. **Reduced Cell Count**: Fewer cells than equivalent rectangular domain
4. **Symmetric Boundary Conditions**: Easier to apply symmetric boundary conditions

## Limitations

1. **Block Structure**: More complex than simple rectangular domains
2. **Setup Complexity**: Requires careful vertex and edge definition
3. **Boundary Conditions**: Single `inletOutlet` patch requires boundary condition setup for flow direction
4. **Parameter Tuning**: Inner square size and outer circle radius need to be adjusted for each geometry

## Future Enhancements

- [ ] Support for hexadecagon (16-sided) approximation
- [ ] Automatic radius calculation based on geometry
- [ ] Integration with case setup scripts
- [ ] Validation against rectangular domain results

## References

- OpenFOAM User Guide: blockMesh
- OpenFOAM Tutorials: Cylindrical domains
- `cases/Vidigal_CFD/MESH_CONFIGURATION.md` - Current mesh configuration
