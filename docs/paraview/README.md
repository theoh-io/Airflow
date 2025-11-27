# ParaView State Files

This directory contains ParaView state files (`.pvsm`) for visualizing microClimateFoam results.

## Creating a State File

1. **Open your case in ParaView**:
   - File → Open → Select `cases/heatedCavity/heatedCavity.foam`
   - Click OK

2. **Set up your visualization**:
   - Apply filters (Slice, Glyph, Stream Tracer, etc.)
   - Adjust color maps and views
   - Configure legends and annotations

3. **Save the state**:
   - File → Save State
   - Save as `heated_cavity.pvsm` in this directory
   - When loading, ParaView will prompt for the data file location

## Loading a State File

1. **Start ParaView**

2. **Load the state**:
   - File → Load State
   - Select the `.pvsm` file
   - When prompted, point to your case directory (e.g., `cases/heatedCavity`)

3. **The visualization will be restored** with all filters and settings

## Recommended Visualizations

### Temperature Contour with Velocity Vectors

1. Load the case
2. Apply "Slice" filter (normal: Z, position: center)
3. Color by "T" (temperature)
4. Apply "Glyph" filter to slice
5. Set glyph to "Arrow", orient by "U", scale by "U" magnitude

### Streamlines

1. Load the case
2. Apply "Stream Tracer" filter
3. Set velocity field to "U"
4. Adjust seed points (e.g., line source along hot wall)

### Multi-View Layout

1. Create multiple views (View → Create View)
2. Set up different visualizations in each view
3. Save state to preserve the layout

## State File Template

A basic state file structure includes:
- Reader configuration (OpenFOAM case)
- Filter pipeline (Slice, Glyph, etc.)
- Color maps and transfer functions
- View settings and camera positions
- Legends and annotations

For a complete example, create a visualization in ParaView and save the state file.

