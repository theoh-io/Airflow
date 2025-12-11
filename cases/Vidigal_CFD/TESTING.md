# Vidigal_CFD Testing Guide

## Quick Validation

Run the configuration validation script:

```bash
cd cases/Vidigal_CFD
./test_mesh_config.sh
```

This checks all configuration files are present and correctly formatted.

## Mesh Generation Testing

### Full Mesh Generation Test

**Warning**: This may take 30 minutes to several hours!

```bash
cd cases/Vidigal_CFD

# Run complete mesh workflow
./Allrun
```

Or step-by-step:

```bash
cd cases/Vidigal_CFD

# 1. Generate background mesh
blockMesh -region air

# 2. Extract features from STL
surfaceFeatureExtract -region air

# 3. Refine and snap to STL (this takes the longest)
snappyHexMesh -region air -overwrite

# 4. Check mesh quality
checkMesh -region air
```

### Expected Output

**blockMesh**:
- Creates background hexahedral mesh
- ~6.4M cells (332 × 212 × 91)
- Output: `constant/air/polyMesh/`

**surfaceFeatureExtract**:
- Extracts sharp edges from STL
- Output: `constant/triSurface/vidigal.eMesh`

**snappyHexMesh**:
- Refines mesh near STL surfaces
- Snaps cells to geometry
- Removes cells inside solid regions
- Output: Refined mesh in `constant/air/polyMesh/`
- **Expected time**: 30 minutes to 3+ hours

**checkMesh**:
- Validates mesh quality
- Reports cell count, quality metrics
- Check for warnings or errors

### Quick Test (Reduced Mesh)

To test with a smaller mesh for faster iteration:

1. Edit `constant/air/polyMesh/blockMeshDict`
2. Reduce cell count (e.g., divide by 2 or 4):
   ```
   (
       166    // X: 1655.76 m / 10.0 m = 166 cells
       106    // Y: 1056.34 m / 10.0 m = 106 cells
       46     // Z: 451.38 m / 10.0 m = 46 cells
   )
   ```
3. This reduces background mesh to ~800K cells (faster to test)

## Verifying Results

### Check Mesh Quality

After `checkMesh`, look for:
- ✓ "Mesh OK" message
- Cell count (should be reasonable)
- Quality metrics (non-orthogonality, skewness, etc.)

### Check Patch Names

After mesh generation, check created patches:

```bash
cat constant/air/polyMesh/boundary
```

Look for patches created from STL surfaces. These patch names need to be used in boundary condition files (`0/air/*`).

### Visual Inspection

Open mesh in ParaView:

```bash
# Create ParaView case file
./scripts/create_foam_file.sh cases/Vidigal_CFD

# Open in ParaView
paraview cases/Vidigal_CFD/Vidigal_CFD.foam
```

Check:
- Mesh conforms to STL geometry
- No obvious mesh quality issues
- Patches are correctly identified

## Troubleshooting

### Issue: blockMesh fails

**Error**: Syntax error or invalid coordinates

**Solution**:
- Check `blockMeshDict` syntax
- Verify vertex coordinates
- Check face definitions are correct

### Issue: snappyHexMesh fails

**Error**: Geometry not found or refinement issues

**Solution**:
- Verify STL file path in `snappyHexMeshDict`
- Check STL file is readable
- Reduce refinement levels if mesh is too large
- Check `locationInMesh` point is inside air region

### Issue: Mesh quality warnings

**Warning**: High skewness or non-orthogonality

**Solution**:
- Adjust mesh refinement settings
- Reduce cell size near surfaces
- Check STL geometry quality

### Issue: Too many cells

**Problem**: Mesh has too many cells

**Solution**:
- Increase background cell size
- Reduce refinement levels
- Adjust `maxGlobalCells` in `snappyHexMeshDict`

## Performance Tips

1. **Start coarse**: Test with larger cell sizes first
2. **Parallel meshing**: Use parallel decomposition for large meshes
3. **Incremental refinement**: Start with level 1, then add level 2
4. **Monitor resources**: Watch memory and disk usage

## Next Steps After Successful Mesh Generation

1. ✅ Mesh generated successfully
2. ⏳ Check patch names in `constant/air/polyMesh/boundary`
3. ⏳ Update boundary conditions in `0/air/*` files
4. ⏳ Configure inlet/outlet/wall boundary conditions
5. ⏳ Run quick validation test

## Validation Scripts

- `./test_mesh_config.sh` - Validates configuration files
- `scripts/analyze_vidigal_stl.py` - Analyzes STL geometry
- `scripts/inspect_stl.sh` - Inspects STL file







