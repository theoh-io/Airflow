# Quick Start Guide

This guide shows how to quickly run cases with both solvers. **Important:** Custom cases and tutorial cases are designed for different solvers and are **not interchangeable**.

## Case-Solver Compatibility

**⚠️ CRITICAL: Use the correct solver for each case type**

- **`custom_cases/`** → **`microClimateFoam`** (our custom solver)
  - Single-region cases
  - Uses standard fields: `p`, `U`, `T`
  - Example: `custom_cases/heatedCavity/`

- **`cases/`** → **`urbanMicroclimateFoam`** (external solver)
  - Multi-region cases
  - Uses advanced fields: `p_rgh`, `h`, etc.
  - Examples: `cases/streetCanyon_CFD/`, `cases/streetCanyon_CFDHAM/`, etc.

**DO NOT** mix solvers and cases - they are incompatible!

---

## Tutorial Cases (urbanMicroclimateFoam)

### Simple Workflow

#### 1. Build Solvers

```bash
./scripts/build_all_solvers.sh
```

The smart build system will only rebuild if source files have changed.

#### 2. Run Quick Test

```bash
# Quick validation (CI-optimized, 5-15 minutes) - RECOMMENDED
./scripts/run_case.sh --quick-validation -v cases/streetCanyon_CFD

# Or use the test script (also optimized for CI)
./test_env.sh

# Quick test (12 time steps, 1-6 hours) - for local testing
./scripts/run_case.sh --quick -v cases/streetCanyon_CFD
```

**Quick validation mode** (recommended for CI and sanity checks):
- `deltaT=50s`, `endTime=50s` (1 time step)
- Expected runtime: 3-5 minutes
- Writes at every time step
- **Smart caching**: Skips mesh generation if mesh already exists and is up to date

**Quick test mode** (for local testing):
- `deltaT=3600s`, `endTime=43200s` (12 time steps)
- Expected runtime: 1-6 hours
- Writes at every time step

#### 3. Generate Visualizations

After the simulation completes, generate visualization images:

```bash
# For quick validation mode (1 time step = 50 seconds)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 50

# For quick test mode (10 time steps = 36000 seconds)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 36000
```

#### 4. View Results

Images are saved in `cases/streetCanyon_CFD/images/`:
- `temperature_[time].png` - Temperature contour
- `velocity_[time].png` - Velocity vectors
- `streamlines_[time].png` - Streamlines
- `overview_[time].png` - Combined view

### Complete Example: Tutorial Case

**Quick validation (recommended for CI, 3-5 minutes):**
```bash
# 1. Build (only if needed)
./scripts/build_all_solvers.sh

# 2. Run quick validation
./scripts/run_case.sh --quick-validation -v cases/streetCanyon_CFD

# 3. Generate visualizations
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 50  # 1 time step

# 4. Check results
ls -lh cases/streetCanyon_CFD/images/
```

**Quick test (for local testing, 1-6 hours):**
```bash
# 1. Build (only if needed)
./scripts/build_all_solvers.sh

# 2. Run quick test
./scripts/run_case.sh --quick -v cases/streetCanyon_CFD

# 3. Generate visualizations
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 36000  # 10 time steps

# 4. Check results
ls -lh cases/streetCanyon_CFD/images/
```

---

## Custom Cases (microClimateFoam)

### Simple Workflow

#### 1. Build Solvers

```bash
./scripts/build_all_solvers.sh
```

#### 2. Run Custom Case

```bash
# Run heated cavity case (auto-detects microClimateFoam)
./scripts/run_case.sh custom_cases/heatedCavity

# With verbose output
./scripts/run_case.sh -v custom_cases/heatedCavity

# With quick validation mode
./scripts/run_case.sh --quick-validation -v custom_cases/heatedCavity

# In parallel
./scripts/run_case.sh -p 4 custom_cases/heatedCavity
```

#### 3. Generate Visualizations

```bash
# Generate images for a specific time step
./scripts/postprocess/generate_images.sh custom_cases/heatedCavity 200
```

### Complete Example: Custom Case

**Run heated cavity case:**
```bash
# 1. Build (only if needed)
./scripts/build_all_solvers.sh

# 2. Run case (auto-detects microClimateFoam from controlDict)
./scripts/run_case.sh -v custom_cases/heatedCavity

# 3. Generate visualizations
./scripts/postprocess/generate_images.sh custom_cases/heatedCavity 200

# 4. Check results
ls -lh custom_cases/heatedCavity/images/
```

---

## Case Runner Options

The `run_case.sh` script supports many options:

```bash
# Quick validation (CI-optimized, 3-5 minutes) - RECOMMENDED
./scripts/run_case.sh --quick-validation cases/streetCanyon_CFD

# Quick test (12 time steps, 1-6 hours) - for local testing
./scripts/run_case.sh --quick cases/streetCanyon_CFD

# Full simulation (24 time steps, 2-12+ hours)
./scripts/run_case.sh --full cases/streetCanyon_CFD

# Custom configuration
./scripts/run_case.sh --deltaT 100 --endTime 200 cases/streetCanyon_CFD
./scripts/run_case.sh --endTime 7200 cases/streetCanyon_CFD

# Options
./scripts/run_case.sh -v --verbose          # Verbose output with real-time monitoring
./scripts/run_case.sh -n --no-build        # Skip solver build
./scripts/run_case.sh -B --no-mesh         # Skip mesh generation
./scripts/run_case.sh -p 4 --parallel      # Parallel execution (4 processors)
./scripts/run_case.sh --sanity-check       # Run sanity check after execution

# List all available cases
./scripts/list_cases.sh
```

## Quick Validation vs Quick Test vs Full

**Quick Validation** (CI-optimized, recommended):
- Configuration: `deltaT=50s`, `endTime=50s` (1 time step) for tutorial cases
- Runtime: 3-5 minutes
- Use case: CI/CD, quick sanity checks, fast feedback

**Quick Test** (local testing):
- Configuration: `deltaT=3600s`, `endTime=43200s` (12 time steps) for tutorial cases
- Runtime: 1-6 hours
- Use case: Local validation, more thorough testing

**Full Simulation**:
- Configuration: Uses original `controlDict` settings
- Runtime: 2-12+ hours
- Use case: Complete validation, production runs

All modes write at every time step for continuous validation.

## Troubleshooting

### Solver not found
```bash
# Build the solver
./scripts/build_all_solvers.sh

# Or build specific solver
./scripts/build_all_solvers.sh microClimateFoam
./scripts/build_all_solvers.sh urbanMicroclimateFoam
```

### Wrong solver for case
- **Error:** Case fails to start or produces errors
- **Solution:** Check case type:
  - `custom_cases/*` → Use `microClimateFoam` (auto-detected)
  - `cases/*` → Use `urbanMicroclimateFoam` (auto-detected)
- **Check:** `./scripts/list_cases.sh` shows which solver each case uses

### No time steps available
- Check that the solver completed successfully
- Verify `controlDict` has correct `endTime` and `writeInterval`
- Check solver log for errors: `cat cases/streetCanyon_CFD/log.urbanMicroclimateFoam`

### Visualization fails
- Ensure time step directory exists (e.g., `3600/air/` for multi-region, `3600/` for single-region)
- Check that ParaView is available: `which pvpython`
- Verify case has `.foam` file: `ls cases/streetCanyon_CFD/*.foam`

### Multi-region vs single-region confusion
- **Multi-region cases** (`cases/`): Have `constant/regionProperties` and `0/air/` directories
- **Single-region cases** (`custom_cases/`): Have `0/` directly (no region subdirectories)
- Use the correct solver for each type!
