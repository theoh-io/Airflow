# Quick Start Guide

This guide shows how to quickly run the streetCanyon_CFD case and generate visualizations.

## Simple Workflow

### 1. Build Solvers

```bash
./scripts/build_all_solvers.sh
```

The smart build system will only rebuild if source files have changed.

### 2. Run Quick Test

```bash
# Quick validation (CI-optimized, 5-15 minutes) - RECOMMENDED
./scripts/run_street_canyon.sh --quick-validation

# Or use the test script (also optimized for CI)
./test_env.sh

# Quick test (12 time steps, 1-6 hours) - for local testing
./scripts/run_street_canyon.sh --quick
```

**Quick validation mode** (recommended for CI and sanity checks):
- `deltaT=100s`, `endTime=200s` (2 time steps)
- Expected runtime: 5-15 minutes
- Writes at every time step
- Sanity check at 100 seconds (1 time step)
- **Smart caching**: Skips mesh generation if mesh already exists and is up to date

**Quick test mode** (for local testing):
- `deltaT=3600s`, `endTime=43200s` (12 time steps)
- Expected runtime: 1-6 hours
- Writes at every time step
- Sanity check at 36000 seconds (10 time steps)

### 3. Generate Visualizations

After the simulation completes, generate visualization images:

```bash
# For quick validation mode (1 time step = 100 seconds)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 100

# For quick validation mode (2 time steps = 200 seconds)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 200

# For quick test mode (10 time steps = 36000 seconds)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 36000
```

### 4. View Results

Images are saved in `cases/streetCanyon_CFD/images/`:
- `temperature_[time].png` - Temperature contour
- `velocity_[time].png` - Velocity vectors
- `streamlines_[time].png` - Streamlines
- `overview_[time].png` - Combined view

## Complete Example

**Quick validation (recommended for CI, 5-15 minutes):**
```bash
# 1. Build (only if needed)
./scripts/build_all_solvers.sh

# 2. Run quick validation
./scripts/run_street_canyon.sh --quick-validation

# 3. Generate visualizations
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 100  # 1 time step
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 200  # 2 time steps

# 4. Check results
ls -lh cases/streetCanyon_CFD/images/
```

**Quick test (for local testing, 1-6 hours):**
```bash
# 1. Build (only if needed)
./scripts/build_all_solvers.sh

# 2. Run quick test
./scripts/run_street_canyon.sh --quick

# 3. Generate visualizations
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 36000  # 10 time steps

# 4. Check results
ls -lh cases/streetCanyon_CFD/images/
```

## Options

### Launch Script Options

```bash
# Quick validation (CI-optimized, 5-15 minutes) - RECOMMENDED
./scripts/run_street_canyon.sh --quick-validation

# Quick test (12 time steps, 1-6 hours) - for local testing
./scripts/run_street_canyon.sh --quick

# Full simulation (24 time steps, 2-12+ hours)
./scripts/run_street_canyon.sh --full

# Custom configuration
./scripts/run_street_canyon.sh --deltaT 100 --endTime 200  # Custom time steps
./scripts/run_street_canyon.sh --time 7200                 # Custom endTime only

# Options
./scripts/run_street_canyon.sh --no-build   # Skip solver build
./scripts/run_street_canyon.sh --no-mesh    # Skip mesh generation
```

### Visualization Options

```bash
# Generate for specific time
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 3600

# Custom output directory
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 3600 --output-dir results/images

# Custom image size
docker compose run --rm dev bash -c "
  /opt/paraviewopenfoam56/bin/pvpython \
    scripts/postprocess/generate_images.py \
    cases/streetCanyon_CFD 3600 \
    --width 1920 --height 1080
"
```

## Quick Validation vs Quick Test

**Quick Validation** (CI-optimized, recommended):
- Configuration: `deltaT=100s`, `endTime=200s` (2 time steps)
- Runtime: 5-15 minutes
- Use case: CI/CD, quick sanity checks, fast feedback
- Sanity check: 100 seconds (1 time step)

**Quick Test** (local testing):
- Configuration: `deltaT=3600s`, `endTime=43200s` (12 time steps)
- Runtime: 1-6 hours
- Use case: Local validation, more thorough testing
- Sanity check: 36000 seconds (10 time steps)

**Full Simulation**:
- Configuration: `deltaT=3600s`, `endTime=86400s` (24 time steps)
- Runtime: 2-12+ hours
- Use case: Complete validation, production runs

All modes write at every time step for continuous validation.

## Troubleshooting

### Solver not found
```bash
# Build the solver
./scripts/build_all_solvers.sh urbanMicroclimateFoam
```

### No time steps available
- Check that the solver completed successfully
- Verify `controlDict` has correct `endTime` and `writeInterval`
- Check solver log for errors

### Visualization fails
- Ensure time step directory exists (e.g., `3600/air/`)
- Check that ParaView is available: `which pvpython`
- Verify case has `.foam` file: `ls cases/streetCanyon_CFD/*.foam`

