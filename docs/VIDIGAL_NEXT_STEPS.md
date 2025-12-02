# Vidigal_CFD Case Creation - Next Steps & Questions

## ✅ Phase 1: Complete
- Case directory structure created
- STL file (`vidigal.stl`) is in place (871 KB, binary format)
- Configuration files copied from `streetCanyon_CFD`
- Initial field files ready

---

## ✅ Phase 2: Mesh Generation Configuration - MOSTLY COMPLETE

**Progress Update (2024-12-02)**:

### Completed:
- ✅ STL geometry analyzed (bounds, dimensions, domain sizing)
- ✅ Background mesh generated (6.4M cells, 5.0m cell size)
- ✅ `snappyHexMeshDict` configured for STL-based meshing
- ✅ Mesh generation scripts created (`generate_mesh.sh`, `post_mesh_steps.sh`, etc.)
- ✅ Domain boundaries calculated based on geometry height (H = 75.23m)
- ✅ Surface refinement configuration set (Level 1-2)

### In Progress:
- ⚠️ snappyHexMesh refinement partially complete
  - Surface refinement iterations completed (6 iterations)
  - Mesh cleanup and baffle handling started
  - **NEXT**: Complete mesh refinement and snap phase

### Next Immediate Steps:
1. **Restart and complete mesh generation**
   - Run `./generate_mesh.sh` or restart snappyHexMesh
   - Monitor with `./monitor_mesh.sh`
   - Expected time: 30-60 minutes

2. **Post-process completed mesh**
   - Run `./post_mesh_steps.sh`
   - Check mesh quality with `checkMesh -region air`
   - Identify patch names for boundary conditions

3. **Update boundary conditions** (Phase 3)

See `docs/VIDIGAL_STATUS.md` for detailed status and next steps.

---

## 🔄 Phase 3: Boundary Conditions - NEXT STEP (After Mesh Completion)

This is the most critical phase where we configure STL-based mesh generation. To proceed, we need information about your STL geometry.

### Questions about Your STL Geometry

Please answer these questions about your `vidigal.stl` file:

#### 1. **Geometry Extent (Domain Bounds)**
   - **What are the approximate dimensions of your STL geometry?**
     - X-direction (length): ______ meters
     - Y-direction (width): ______ meters  
     - Z-direction (height): ______ meters
   
   - **What are the bounding box coordinates?**
     - Minimum X: ______
     - Maximum X: ______
     - Minimum Y: ______
     - Maximum Y: ______
     - Minimum Z: ______
     - Maximum Z: ______
   
   - **Note**: If you don't know, we can use OpenFOAM tools to inspect the STL file.

#### 2. **Domain Size (Computational Domain)**
   - **How much clearance do you want around your STL geometry?**
     - Inlet boundary (X-min): ______ meters before geometry
     - Outlet boundary (X-max): ______ meters after geometry
     - Lateral boundaries (Y-min/max): ______ meters on each side
     - Top boundary (Z-max): ______ meters above geometry
     - Bottom boundary (Z-min): Typically at ground level (Z=0) or below?
   
   - **Recommended**: 2-5x geometry size in streamwise direction, 1-2x in other directions

#### 3. **Mesh Resolution**
   - **What is the smallest important feature size in your geometry?** (e.g., building details, narrow gaps)
     - Smallest feature: ______ meters
   
   - **What mesh cell size do you want near surfaces?**
     - Surface cell size: ______ meters (typical: 0.5-2.0 m for urban flows)
   
   - **What background mesh cell size?**
     - Background cell size: ______ meters (typically 5-10x surface size)
   
   - **How many refinement levels?** (typically 2-3 levels)
     - Refinement levels: ______

#### 4. **Geometry Type**
   - **What does your STL represent?**
     - [ ] Buildings only (solid walls)
     - [ ] Ground surface
     - [ ] Both buildings and ground
     - [ ] Complete domain including boundaries
     - [ ] Other: ________________
   
   - **Is the geometry watertight (closed surfaces)?**
     - [ ] Yes, fully closed
     - [ ] No, open surfaces (like terrain)
     - [ ] Not sure

#### 5. **Regions (Multi-Region Setup)**
   - **Do you need solid regions (buildings/ground) or just fluid (air)?**
     - [ ] Single region: Air only (simpler)
     - [ ] Multi-region: Air + solid regions (buildings/ground)
   
   - **If multi-region, which regions do you need?**
     - [ ] Air (fluid)
     - [ ] Buildings (solid)
     - [ ] Ground (solid)
     - [ ] Other: ________________
   
   - **Note**: `streetCanyon_CFD` uses single fluid region. Multi-region is more complex but allows heat transfer through solids.

#### 6. **Boundary Conditions**
   - **What type of flow simulation?**
     - [ ] Wind flow around buildings
     - [ ] Natural convection
     - [ ] Forced convection
     - [ ] Other: ________________
   
   - **Wind/Boundary conditions:**
     - Inlet velocity: ______ m/s
     - Wind direction: ______ degrees (0° = X+, 90° = Y+)
     - Inlet turbulence intensity: ______ % (typical: 5-10%)
     - Outlet type: [ ] Zero gradient / [ ] Fixed pressure
   
   - **Temperature conditions:**
     - Ambient temperature: ______ K (or °C: ______)
     - Surface temperatures (if known): ________________

#### 7. **Computational Resources**
   - **What are your computational constraints?**
     - Target cell count: ______ (typical: 100K-10M cells)
     - Available RAM: ______ GB
     - Will run in parallel? [ ] Yes, [ ] No
     - Number of processors (if parallel): ______

#### 8. **Coordinate System**
   - **What are the units in your STL file?**
     - [ ] Meters
     - [ ] Centimeters
     - [ ] Millimeters
     - [ ] Other: ________________
   
   - **What is the origin/coordinate system?**
     - Origin location: ________________
     - Ground level at Z = ______

---

## What We'll Create Based on Your Answers

Once you provide this information, we'll create:

1. **Background Mesh (`constant/air/polyMesh/blockMeshDict`)**
   - Domain boundaries based on your geometry extent + clearance
   - Cell size based on your resolution requirements

2. **SnappyHexMesh Configuration (`system/snappyHexMeshDict`)**
   - Geometry reference to `vidigal.stl`
   - Refinement levels near surfaces
   - Surface snapping parameters
   - Mesh quality settings

3. **Surface Feature Extraction (`system/surfaceFeatureExtractDict`)**
   - Feature angle detection (for sharp edges)
   - Edge extraction settings

4. **Updated Allrun Script**
   - Complete mesh generation workflow:
     ```
     blockMesh -region air              # Background mesh
     surfaceFeatureExtract -region air  # Extract features
     snappyHexMesh -region air          # Refine and snap
     checkMesh -region air              # Verify quality
     ```

5. **Region Configuration** (if multi-region)
   - Update `constant/regionProperties`
   - Configure region interfaces

6. **Boundary Condition Updates**
   - Update initial fields in `0/air/` with patch names from mesh
   - Configure inlet/outlet/wall boundaries

---

## Tools to Inspect Your STL File (Optional)

If you need to inspect the STL file, you can use:

### 1. Check STL Geometry (OpenFOAM)
```bash
checkGeometry constant/triSurface/vidigal.stl
```
This will show:
- Bounding box
- Number of triangles
- Surface area
- Volume (if closed)
- Edge statistics

### 2. Visualize in ParaView
```bash
# Open ParaView
paraview

# File → Open → Select vidigal.stl
# Will show geometry visualization
```

### 3. Basic Info Command
```bash
# Get file info
file constant/triSurface/vidigal.stl
ls -lh constant/triSurface/vidigal.stl
```

---

## Recommended Defaults (If You're Unsure)

If you're not sure about some parameters, here are reasonable defaults for urban CFD:

- **Domain clearance**: 3-5x geometry size in streamwise, 1-2x in other directions
- **Surface cell size**: 1.0 m (good balance for urban flows)
- **Background cell size**: 5.0 m (5x surface size)
- **Refinement levels**: 2 levels
- **Single region (air only)**: Simpler to start, can add solids later
- **Wind speed**: 2-5 m/s (typical)
- **Inlet turbulence**: 5% intensity

---

## Next Actions

**Please provide answers to the questions above**, and I will:

1. Create the mesh generation configuration files
2. Update the `Allrun` script with the STL-based workflow
3. Set up boundary conditions based on your requirements
4. Create a summary document of the configuration

**Alternative**: If you prefer, I can create a basic configuration with reasonable defaults that you can adjust later. Just let me know!

---

## File Locations Reference

- STL file: `cases/Vidigal_CFD/constant/triSurface/vidigal.stl`
- Case directory: `cases/Vidigal_CFD/`
- Detailed plan: `docs/CASE_CREATION_PLAN.md`
- This document: `docs/VIDIGAL_NEXT_STEPS.md`

