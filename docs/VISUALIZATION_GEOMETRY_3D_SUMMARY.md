# Geometry 3D Visualization Development Summary

## Overview
This document summarizes the development and refinement of the `geometry_3d` visualization for the `streetCanyon_CFD` case. The goal was to create a clean, focused 3D visualization showing the street canyon geometry with temperature on surfaces and flow patterns, without cluttering domain boundaries.

## Initial Problem
The user reported that the ParaView visualization had several issues:
1. **Temperature displayed as full volume rendering** - filling the entire simulation domain, making it impossible to see the canyon geometry or flow
2. **No clear view of canyon interior** - walls/buildings blocking the view
3. **Domain boundaries cluttering the view** - inlet/outlet/top surfaces visible
4. **No focus on canyon region** - camera showing full domain instead of zoomed canyon view

## Solution Development Process

### Phase 1: Removing Volume Rendering
**Problem:** Temperature was being rendered as a volume, filling the entire domain.

**Solution:**
- Changed from volume rendering to **surface-only temperature display**
- Temperature is now shown **only on building walls and street ground** (surface projection)
- No volumetric color blocks

**Implementation:**
- Used `ExtractSurface` to get boundary surfaces
- Applied temperature coloring directly to surfaces using `ColorArrayName = ['CELLS', 'T']` or `['POINTS', 'T']`
- Removed any volume-based rendering approaches

### Phase 2: Filtering Domain Boundaries
**Problem:** Inlet, outlet, and top surfaces were visible, cluttering the visualization.

**Solution:**
- Implemented **geometric filtering using Box clipping**
- Clipped the volume first, then extracted surfaces from the clipped volume
- This approach preserves walls near boundaries while removing inlet/outlet/top

**Implementation Details:**
```python
# Clip volume to exclude boundary regions
buffer = 0.5  # 50cm buffer
clip_volume = pv.Clip(Input=reader)
clip_volume.ClipType = 'Box'
clip_volume.ClipType.Bounds = [
    x_min + buffer, x_max - buffer,  # X: exclude boundaries
    y_min, y_max,                       # Y: keep full range
    z_min, z_max - buffer              # Z: exclude top, keep ground
]
# Then extract surfaces from clipped volume
extractSurface = pv.ExtractSurface(Input=clip_volume)
```

**Result:**
- Only walls/buildings and ground remain visible
- Inlet/outlet/top boundaries are hidden
- Walls near boundaries are preserved

### Phase 3: Flow Visualization
**Problem:** Need to show wind flow patterns inside the canyon.

**Initial Approach:** Velocity glyphs (arrows) on a slice
- Created glyphs on a horizontal slice through the volume
- Adaptive scaling based on velocity magnitude and domain size

**Final Approach:** Streamlines
- Replaced glyphs with **streamlines** for better flow visualization
- Streamlines show flow around and above the canyon
- Colored by temperature to show thermal flow patterns

**Implementation:**
```python
# Create line source for seed points
line1 = pv.Line()
line1.Point1 = [x_min + buffer, y_min, center[2]]
line1.Point2 = [x_max - buffer, y_max, center[2]]
line1.Resolution = 15  # Multiple seed points

# Create stream tracer
streamTracer1 = pv.StreamTracer(Input=clip_volume, SeedType=line1)
streamTracer1.Vectors = ['CELLS', 'U']
streamTracer1.MaximumStreamlineLength = adaptive_length
streamTracer1.IntegrationDirection = 'BOTH'
```

**Streamline Properties:**
- Line width: 4.0 (thick for visibility)
- Fully opaque (opacity 1.0)
- Colored by temperature
- Adaptive length based on domain size

### Phase 4: Transparency and Visibility
**Problem:** Fully opaque surfaces blocked the view of canyon interior and streamlines.

**Solution Evolution:**
1. **Initial:** Fully opaque (opacity 1.0) - blocked interior view
2. **First adjustment:** Semi-transparent (opacity 0.6) - better but still limited visibility
3. **Final:** Highly transparent (opacity 0.3) - clear view of interior and streamlines

**Additional Enhancements:**
- Added edge highlighting (black edges) to maintain geometry definition even with high transparency
- Made streamlines fully opaque and thicker to stand out through transparent surfaces

**Implementation:**
```python
surfaceDisplay.Opacity = 0.3  # Highly transparent
surfaceDisplay.EdgeColor = [0.0, 0.0, 0.0]  # Black edges for definition
streamDisplay.LineWidth = 4.0  # Thick streamlines
streamDisplay.Opacity = 1.0  # Fully opaque streamlines
```

### Phase 5: Camera and Zoom
**Problem:** Camera showed full domain instead of focusing on the canyon region.

**Solution:**
- **Zoomed camera to canyon region** using surface bounds (not full domain bounds)
- Reduced camera distance from `max_size * 2.0` to `max_size * 1.2`
- Added additional zoom factor: `camera.Zoom(1.5)` (50% more zoom)
- Isometric view maintained (45° elevation, 45° azimuth)

**Implementation:**
```python
# Get bounds of filtered surface (canyon region, not full domain)
surfaceBounds = surfaceInfo.GetBounds()
x_center = (x_min_surf + x_max_surf) / 2.0
y_center = (y_min_surf + y_max_surf) / 2.0
z_center = (z_min_surf + z_max_surf) / 2.0

# Closer camera distance
distance = max_size * 1.2  # Reduced from 2.0

# Additional zoom
camera.Zoom(1.5)  # 50% more zoom
renderView.ResetCamera(surfaceBounds)  # Focus on canyon bounds
```

## Final Implementation

### Key Features
1. **Surface-only temperature display**
   - Temperature shown only on walls/buildings/ground
   - No volume rendering
   - Color map: Blue (cold) → White (mid) → Red (hot)

2. **Filtered geometry**
   - Only canyon walls/buildings and ground visible
   - Inlet/outlet/top boundaries removed
   - 0.5m buffer to preserve walls near boundaries

3. **Highly transparent surfaces**
   - Opacity: 0.3 (70% transparent)
   - Black edges for geometry definition
   - Clear view of canyon interior

4. **Streamline flow visualization**
   - Streamlines showing flow around and above canyon
   - Thick (4.0), fully opaque lines
   - Colored by temperature
   - Adaptive length based on domain size

5. **Focused camera view**
   - Zoomed to canyon region (not full domain)
   - Isometric 3D view (45° elevation, 45° azimuth)
   - Tight focus on canyon geometry

### Function: `create_geometry_3d_view()`
**Location:** `scripts/postprocess/generate_images.py` (line 730)

**Parameters:**
- `reader`: ParaView OpenFOAM reader object
- `output_path`: Path to save the image
- `width`: Image width in pixels (default: 1200)
- `height`: Image height in pixels (default: 800)
- `case_path`: Optional case directory path for bounds

**Output:**
- Generates `geometry_3d_<time>.png` image
- Shows canyon geometry with temperature on surfaces
- Displays streamlines showing flow patterns
- Clean, focused isometric 3D view

## Technical Details

### Clipping Strategy
- **Method:** Box clipping on volume, then surface extraction
- **Buffer:** 0.5m from domain boundaries
- **Preserves:** Walls/buildings near boundaries
- **Removes:** Inlet (X boundaries), outlet (X boundaries), top (Z boundary)
- **Keeps:** Ground (Z=0), all Y range

### Temperature Range Detection
- Tries to get range from filtered surfaces first
- Falls back to original surfaces if needed
- Uses both CELLS and POINTS arrays (OpenFOAM compatibility)
- Default range: 290-320 K if detection fails

### Streamline Configuration
- **Seed line:** Spans canyon region at mid-height
- **Resolution:** 15 seed points
- **Integration:** BOTH directions
- **Length:** Adaptive (50% of characteristic length, min 10m, max 500m)

### Camera Configuration
- **View type:** Isometric (45° elevation, 45° azimuth)
- **Focus:** Canyon center (from surface bounds)
- **Distance:** `max_size * 1.2` (close view)
- **Zoom:** Additional 1.5x factor
- **Bounds:** Reset to surface bounds (canyon region only)

## Results

### Before
- Volume rendering filling entire domain
- Domain boundaries cluttering view
- No clear view of canyon interior
- Full domain view (too zoomed out)

### After
- ✅ Temperature on surfaces only (no volume rendering)
- ✅ Clean view focused on canyon geometry
- ✅ Clear view of canyon interior and streamlines
- ✅ Tight zoom on canyon region
- ✅ Streamlines showing flow patterns
- ✅ Isometric 3D view

### Image Output
- **File:** `cases/streetCanyon_CFD/images/geometry_3d_<time>.png`
- **Size:** ~160KB (varies with complexity)
- **Format:** PNG, 1200x800 pixels
- **Content:** Canyon geometry (transparent), streamlines, temperature coloring

## Usage

The visualization is automatically generated when running:
```bash
python scripts/postprocess/generate_images.py cases/streetCanyon_CFD <time>
```

Or as part of the full image generation:
```bash
docker compose run --rm dev bash -c "cd /workspace && /opt/paraviewopenfoam56/bin/pvpython scripts/postprocess/generate_images.py cases/streetCanyon_CFD 50"
```

## Future Enhancements (Potential)

1. **Selective transparency:** Different opacity for walls vs. ground
2. **Multiple streamline seed regions:** More comprehensive flow visualization
3. **Animation support:** Time-series visualization
4. **Interactive parameters:** Configurable transparency, zoom, streamline density
5. **Patch-based filtering:** More precise boundary filtering using patch names

## Files Modified

- `scripts/postprocess/generate_images.py`
  - Function: `create_geometry_3d_view()` (lines 730-1000+)
  - Changes: Complete rewrite of geometry visualization approach

## Related Documentation

- `docs/visualization.md` - General visualization guide
- `docs/quick_start.md` - Quick start guide with visualization examples
- `docs/SOLVERS/urbanMicroclimateFoam.md` - Solver documentation for streetCanyon_CFD case

---

**Last Updated:** 2024-11-28  
**Status:** ✅ Complete and functional

