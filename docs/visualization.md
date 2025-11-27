# Visualization Guide

This guide explains how to visualize microClimateFoam results using ParaView, which is included in the Docker image.

## ParaView Setup

### Linux (Native)

ParaView is available in the Docker container. To use the GUI:

1. **Install X11 forwarding** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install x11-apps
   
   # Fedora/RHEL
   sudo dnf install xorg-x11-apps
   ```

2. **Allow X11 connections**:
   ```bash
   xhost +local:docker
   ```

3. **Run ParaView from container**:
   ```bash
   docker compose run --rm dev paraview
   ```

### macOS

1. **Install XQuartz** (X11 server for macOS):
   ```bash
   brew install --cask xquartz
   ```

2. **Start XQuartz** and allow connections:
   ```bash
   # In XQuartz preferences, enable "Allow connections from network clients"
   xhost +localhost
   ```

3. **Set DISPLAY** and run ParaView:
   ```bash
   export DISPLAY=:0
   docker compose run --rm -e DISPLAY=host.docker.internal:0 dev paraview
   ```

### WSL2 (Windows)

1. **Install VcXsrv or X410** (X11 server for Windows):
   - VcXsrv: Download from https://sourceforge.net/projects/vcxsrv/
   - X410: Available from Microsoft Store (paid)

2. **Configure X server**:
   - Start VcXsrv with "Disable access control" enabled
   - Note the display number (usually :0)

3. **Set DISPLAY in WSL2**:
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
   ```

4. **Run ParaView**:
   ```bash
   docker compose run --rm -e DISPLAY=$DISPLAY dev paraview
   ```

## Opening Results in ParaView

### Method 1: Direct File Access

1. **Start ParaView** (using one of the methods above)

2. **Open the case**:
   - File → Open
   - Navigate to your case directory (e.g., `cases/heatedCavity`)
   - Select the `.foam` file (create it if it doesn't exist - see below)
   - Click OK

3. **Create `.foam` file** (if missing):
   ```bash
   # Inside case directory
   touch cases/heatedCavity/heatedCavity.foam
   ```
   The `.foam` file is a simple text file that tells ParaView this is an OpenFOAM case.

### Method 2: Using ParaView State Files

Pre-configured state files are available in `docs/paraview/`:

1. **Load the state file**:
   - File → Load State
   - Select `docs/paraview/heated_cavity.pvsm`
   - ParaView will prompt for the data file - point it to your case directory

2. **State files include**:
   - Temperature contour slices
   - Velocity vectors
   - Streamlines
   - Color maps and legends

## Standard Visualizations

### Temperature Contour

1. Load the case in ParaView
2. Apply "Slice" filter
3. Set normal to (0, 0, 1) for 2D view
4. Color by "T" (temperature)
5. Adjust color map (Blue-Red for temperature)

### Velocity Vectors

1. Load the case
2. Apply "Glyph" filter
3. Set orientation to "U" (velocity)
4. Set scale to "U" magnitude
5. Adjust glyph size and density

### Streamlines

1. Load the case
2. Apply "Stream Tracer" filter
3. Set velocity field to "U"
4. Adjust seed points and integration parameters

### Combined View

Use the provided ParaView state file (`docs/paraview/heated_cavity.pvsm`) for a pre-configured multi-view setup showing:
- Temperature contours
- Velocity vectors
- Streamlines
- All with appropriate color maps and legends

## Post-Processing Scripts

Python scripts are available in `scripts/postprocess/` for automated analysis:

### Extract Field Statistics

```bash
python scripts/postprocess/extract_stats.py cases/heatedCavity
```

This generates:
- Min/max values for U, p, T
- Average values
- Statistics at specific locations
- CSV output for further analysis

### Generate Plots

```bash
python scripts/postprocess/plot_fields.py cases/heatedCavity
```

Creates publication-ready figures:
- Temperature distribution
- Velocity magnitude
- Pressure contours

## Troubleshooting

### ParaView won't start / "Cannot connect to X server"

- **Linux**: Check `xhost` permissions and X11 forwarding
- **macOS**: Ensure XQuartz is running and `DISPLAY` is set correctly
- **WSL2**: Verify VcXsrv is running and `DISPLAY` points to the correct IP

### No data visible in ParaView

- Ensure the case has been run (time directories exist)
- Check that the `.foam` file exists in the case directory
- Verify field files (U, p, T) are present in time directories

### Colors look wrong

- Reset color map: View → Reset View
- Adjust color scale: Right-click on color bar → Edit Color Map
- Check data range: Information panel shows min/max values

## Headless Visualization

For CI or server environments without display:

```bash
# Export to VTK format
docker compose run --rm dev bash -c "
  source /opt/openfoam8/etc/bashrc
  cd /workspace/cases/heatedCavity
  foamToVTK -time 200
"
```

This creates VTK files that can be visualized later or processed with Python tools like `pyvista` or `mayavi`.

