# Visualization Quick Reference

Quick reference guide for common visualization tasks.

## Setup Checklist

- [ ] Install X11 server (Linux: X11 apps, macOS: XQuartz, WSL2: VcXsrv)
- [ ] Configure X11 forwarding (`xhost +local:docker` for Linux)
- [ ] Create `.foam` file: `./scripts/create_foam_file.sh custom_cases/heatedCavity`
- [ ] Start ParaView: `docker compose run --rm dev paraview`

## Common Commands

```bash
# Create ParaView case file
./scripts/create_foam_file.sh custom_cases/heatedCavity

# Generate visualization images (automated, no GUI, adaptive scaling)
./scripts/postprocess/generate_images.sh custom_cases/heatedCavity 200

# Extract field statistics
python scripts/postprocess/extract_stats.py custom_cases/heatedCavity 200

# Generate visualization script
python scripts/postprocess/plot_fields.py custom_cases/heatedCavity 200

# Convert to VTK (headless)
docker compose run --rm dev bash -c "
  source /opt/openfoam8/etc/bashrc
  cd /workspace/custom_cases/heatedCavity
  foamToVTK -time 200
"
```

## ParaView Workflow

1. **Open case**: File → Open → `custom_cases/heatedCavity/heatedCavity.foam` (or `cases/[tutorialCase]/[tutorialCase].foam`)
2. **Apply filters**:
   - Slice (for 2D view)
   - Glyph (for vectors)
   - Stream Tracer (for streamlines)
3. **Color by field**: T (temperature), U (velocity magnitude), p (pressure)
4. **Save state**: File → Save State (for reproducibility)

## Standard Visualizations

| Visualization | Filter | Color By | Notes |
|--------------|--------|----------|-------|
| Temperature contour | Slice | T | Normal: Z-axis |
| Velocity vectors | Glyph | T or \|U\| | Arrow, scale by U |
| Streamlines | Stream Tracer | T or \|U\| | Seed along boundaries |
| Pressure | Slice | p | Shows pressure gradients |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to X server" | Check `xhost` permissions, verify X server running |
| No data visible | Check time directories exist, verify `.foam` file |
| Colors look wrong | Reset color map, check data range in Info panel |

## File Locations

- Custom cases: `custom_cases/heatedCavity/`
- Tutorial cases: `cases/[tutorialCase]/` (after Phase 5 integration)
- Case file: `custom_cases/heatedCavity/heatedCavity.foam`
- Statistics: `custom_cases/heatedCavity/stats_*.csv`
- Visualization script: `custom_cases/heatedCavity/visualize_*.py`
- VTK files: `custom_cases/heatedCavity/VTK/` (if using foamToVTK)

## Documentation

- Full guide: `docs/visualization.md`
- ParaView state files: `docs/paraview/README.md`
- Post-processing scripts: See docstrings in `scripts/postprocess/`

