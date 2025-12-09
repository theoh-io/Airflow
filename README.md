# microClimateFoam

OpenFOAM 8 solver for microclimate simulations (wind, temperature around buildings).

## Quick Start

### Using Docker Compose (recommended)
```bash
# Build and start dev environment
docker compose build              # UID/GID-aware build (see note below)
docker compose up -d
docker compose exec dev bash

# Inside container
source /opt/openfoam8/etc/bashrc
cd /workspace/src/microClimateFoam
wmake
```

> **Note on Build Persistence**: The `docker-compose.yml` mounts a `build/` directory to persist solver binaries across container runs. This means:
> - Solver binaries are cached and only rebuilt when source files change
> - The `build/` directory is automatically created and ignored by git
> - Mesh files are also cached - scripts check if mesh exists before regenerating
> - See `docs/BUILD_CACHING.md` for detailed information

> The image aligns the container `openfoam` user with your host UID/GID so bind mounts stay writable. When building manually (without `docker compose build`), pass your IDs explicitly:
> ```bash
> docker build \
>   --build-arg USER_UID=$(id -u) \
>   --build-arg USER_GID=$(id -g) \
>   -t microclimatefoam:dev .
> ```

### Using Docker directly
```bash
# Build image
docker build -t microclimatefoam:dev .

# Run container
docker run --rm -it -v $(pwd)/src:/workspace/src microclimatefoam:dev bash

# Inside container
source /opt/openfoam8/etc/bashrc
cd /workspace/src/microClimateFoam
wmake
```

## Project Structure

```
.
├── Dockerfile              # OpenFOAM 8 + ParaView 5.6.0 container
├── docker-compose.yml      # Docker Compose configuration
├── src/
│   ├── microClimateFoam/          # Custom solver (wmake build)
│   │   ├── microClimateFoam.C
│   │   └── Make/
│   └── urbanMicroclimateFoam/     # urbanMicroclimateFoam solver (Allwmake build)
│       └── (cloned from OpenFOAM-BuildingPhysics/urbanMicroclimateFoam)
│       └── See docs/DEPENDENCY_MANAGEMENT.md for dependency management approach
├── custom_cases/                  # Custom validation/test cases
│   └── heatedCavity/             # microClimateFoam validation case
├── cases/                         # Tutorial cases (from urbanMicroclimateFoam-tutorials) + custom cases
│   ├── streetCanyon_CFD/         # Street canyon CFD
│   ├── streetCanyon_CFDHAM/      # Street canyon with HAM
│   ├── windAroundBuildings_CFDHAM/ # Wind around buildings
│   ├── Vidigal_CFD/              # Custom case: STL-based geometry (created for this project)
│   └── ... (6 tutorial cases total)
├── scripts/                       # Helper scripts
│   ├── build_all_solvers.sh      # Build all solvers
│   ├── list_cases.sh             # List available cases
│   └── ...
└── docs/                          # Documentation
```

## Status & Roadmap

- ✅ **Phase 0 – Environment & Skeleton**: Docker image, Compose workflow, and minimal solver build are working.
- ✅ **Phase 1 – Flow Solver Core**: Incompressible momentum equation with PISO loop implemented and tested.
- ✅ **Phase 2 – Thermal Transport**: Temperature transport equation with Boussinesq buoyancy coupling implemented and tested.
- ✅ **Phase 3 – Verification & Tooling**: Automated regression testing and CI (GitHub Actions) implemented.
- ✅ **Phase 4 – Visualization & UX**: ParaView setup documentation, post-processing scripts, and visualization tools implemented.
- ✅ **Phase 5 – Multi-Solver Integration**: `urbanMicroclimateFoam` solver and tutorial cases integrated.
- ✅ **Phase 5.1 – CI/CD Optimization**: Test suite optimized for quick validation (5-15 min), CI workflow updated, and documentation enhanced.

See `docs/roadmap.md` for the detailed checklist.

## Development Workflow

1. **Start dev container**
   ```bash
   docker compose up -d    # falls back to docker-compose if needed
   docker compose exec dev bash
   ```
2. **Inside container**
   ```bash
   source /opt/openfoam8/etc/bashrc
   cd /workspace/src/microClimateFoam
   wmake
   ```
3. **Test environment**
   ```bash
   ./test_env.sh          # Quick regression test: compilation, mesh generation, short solver run (12 steps)
   ./test_full.sh         # Full test: complete simulation to endTime, field validation, visualization generation
   ./test_parallel.sh     # Parallel execution test: serial vs parallel comparison
   ```

> **Test Scripts:**
> - `test_env.sh`: Quick regression test (2 time steps) - fast feedback for development
>   - Shows real-time solver output and progress
>   - Monitors time step creation in real-time
>   - **Quick sanity check**: Validates output at time 3600 (first time step)
> - `test_full.sh`: Comprehensive test (separate from CI, for nightly/manual runs)
>   - Full simulation run to `endTime` with verbose progress
>   - Real-time monitoring of time directory creation
>   - Field statistics validation (temperature, velocity ranges)
>   - Visualization image generation and validation
>   - PNG file structure verification
>   - Note: Not run in main CI (too long), use for comprehensive validation
> - `test_parallel.sh`: Parallel execution test (serial vs parallel comparison)
> 
> **Verbose Output:**
> All test scripts now use `scripts/run_solver_verbose.sh` which provides:
> - Real-time solver output (all lines shown as they occur)
> - Background monitoring of time directory creation
> - Progress indicators highlighting time steps and execution time
> - Immediate notification when time steps are written
> 
> **Smart Build System:**
> The build system (`scripts/build_all_solvers.sh`) now:
> - Checks if source files have changed before rebuilding
> - Skips rebuild if binary is up to date (faster test runs)
> - Only rebuilds when necessary (source files newer than binary)
> 
> All scripts are designed to run inside the container and are used by CI for automated testing.

### Quick Start: Tutorial Cases (urbanMicroclimateFoam)

**Note:** Tutorial cases in `cases/` are designed for `urbanMicroclimateFoam` and are **incompatible** with `microClimateFoam`.

The default solver is `urbanMicroclimateFoam` and the default test case is `streetCanyon_CFD`.

**Build all solvers:**
```bash
./scripts/build_all_solvers.sh
```

**Run the default test case:**
```bash
# Quick validation (CI-optimized, 3-5 minutes) - RECOMMENDED
./scripts/run_case.sh --quick-validation -v cases/streetCanyon_CFD

# Quick test (12 time steps, 1-6 hours) - for local testing
./scripts/run_case.sh --quick -v cases/streetCanyon_CFD

# Full simulation (24 time steps, 2-12+ hours)
./scripts/run_case.sh --full -v cases/streetCanyon_CFD

# Using the test scripts
./test_env.sh      # Quick validation (2 time steps, 5-15 min) - optimized for CI
./test_full.sh     # Full simulation with visualization (separate from CI)

# Or manually (solver auto-detected from controlDict)
./scripts/run_case.sh cases/streetCanyon_CFD
```

**Generate visualizations:**
```bash
# After quick validation (deltaT=100s)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 100   # 1 time step
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 200  # 2 time steps

# After quick test (deltaT=3600s)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 3600   # 1 time step
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 36000  # 10 time steps
```

See `docs/quick_start.md` for a complete workflow example.

### Custom Cases (microClimateFoam)

**Note:** Custom cases in `custom_cases/` are designed for `microClimateFoam` (our custom solver) and are **incompatible** with `urbanMicroclimateFoam`.

To compile the microClimateFoam solver and run a custom case:

```bash
# Run heated cavity case (designed for microClimateFoam)
./scripts/run_case.sh custom_cases/heatedCavity

# The solver is auto-detected from controlDict, or specify explicitly:
./scripts/run_case.sh custom_cases/heatedCavity microClimateFoam
```

This uses the generic case runner and writes the solver log to `custom_cases/heatedCavity/log.microClimateFoam`.

### Generic Case Runner

The `run_case.sh` script automatically detects the correct solver from the case's `controlDict`. Use it for any case:

**For Custom Cases (microClimateFoam):**
```bash
# Auto-detects microClimateFoam from controlDict
./scripts/run_case.sh custom_cases/heatedCavity

# Run in parallel mode (auto-creates decomposeParDict if missing)
./scripts/run_case.sh -p 4 custom_cases/heatedCavity

# With verbose output and quick validation
./scripts/run_case.sh -v --quick-validation custom_cases/heatedCavity
```

**For Tutorial Cases (urbanMicroclimateFoam):**
```bash
# Auto-detects urbanMicroclimateFoam from controlDict
./scripts/run_case.sh cases/streetCanyon_CFD

# Or specify explicitly
./scripts/run_case.sh cases/streetCanyon_CFD urbanMicroclimateFoam

# With verbose output and quick validation
./scripts/run_case.sh -v --quick-validation cases/streetCanyon_CFD
```

**Other Options:**
```bash
# List all available cases with their solvers
./scripts/list_cases.sh

# Skip build and mesh generation
./scripts/run_case.sh -n -B cases/streetCanyon_CFD

# Parallel run without reconstruction
./scripts/run_case.sh -p 2 -R custom_cases/heatedCavity
```

**⚠️ Important:** Always use the correct solver for each case type:
- `custom_cases/*` → `microClimateFoam` (auto-detected)
- `cases/*` → `urbanMicroclimateFoam` (auto-detected)

**Case Organization:**

**IMPORTANT: Solver-Case Compatibility**

- **`custom_cases/`** - Custom validation/test cases designed for **`microClimateFoam`** (our custom solver)
  - These cases are single-region and use standard OpenFOAM fields (`p`, `U`, `T`)
  - Example: `custom_cases/heatedCavity/` - designed for `microClimateFoam`
  - **DO NOT** run tutorial cases (`cases/`) with `microClimateFoam` - they are incompatible

- **`cases/`** - Tutorial cases from `urbanMicroclimateFoam-tutorials` designed for **`urbanMicroclimateFoam`** (external solver)
  - These cases are multi-region and use advanced fields (`p_rgh`, `h`, etc.)
  - Examples: `cases/streetCanyon_CFD/`, `cases/streetCanyon_CFDHAM/`, etc. (6 tutorial cases)
  - Also includes custom cases like `cases/Vidigal_CFD/` (STL-based geometry)
  - **DO NOT** run custom cases (`custom_cases/`) with `urbanMicroclimateFoam` - they may not work correctly

**Features:**
- Automatically runs `checkMesh` after `blockMesh` to validate mesh quality
- Parallel run support: `-p [N]` runs `decomposePar`, solver with `-parallel`, and `reconstructPar`
- Auto-creates `system/decomposeParDict` if missing (defaults to 4 processors)
- Use `-R` to skip reconstruction and keep decomposed results

Logs are written to `log.<solver>` inside the case directory. Run `./scripts/run_case.sh --help` for all options.

### WSL / Docker Desktop fallback

Compose should now work out of the box (bind mounting the entire repo at `/workspace`). If Docker Desktop integration ever regresses, you can still stream the necessary directories into a short-lived container:

```bash
tar -cf - src custom_cases/heatedCavity | \
docker run --rm --entrypoint "" -i microclimatefoam:dev bash -lc '
  mkdir -p /tmp/workdir && cd /tmp/workdir
  tar -xf -
  source /opt/openfoam8/etc/bashrc
  cd src/microClimateFoam && wmake
  cd /tmp/workdir/custom_cases/heatedCavity
  blockMesh
  microClimateFoam
'
```

## Continuous Integration

The project includes GitHub Actions CI (`.github/workflows/ci.yml`) that automatically:

- Builds the Docker image on every push and pull request
- Runs the full regression test suite (`test_env.sh`)
- Validates solver compilation, mesh generation, and case execution
- Verifies output files are generated correctly

The CI runs on Ubuntu latest and tests the complete workflow from compilation to case execution. Check the [Actions tab](https://github.com/your-repo/actions) in your GitHub repository to see CI status.

## Visualization

See `docs/visualization.md` for complete visualization setup instructions. For a quick start guide, see `docs/quick_start.md`.

### Quick Start

1. **Create ParaView case file**:
   ```bash
   # For default case (streetCanyon_CFD)
   ./scripts/create_foam_file.sh cases/streetCanyon_CFD
   
   # For other cases
   ./scripts/create_foam_file.sh custom_cases/heatedCavity
   ```

2. **Start ParaView** (Linux example):
   ```bash
   xhost +local:docker
   docker compose run --rm dev paraview
   ```

3. **Open the case**:
   - File → Open → `cases/streetCanyon_CFD/streetCanyon_CFD.foam` (default)
   - Or `custom_cases/heatedCavity/heatedCavity.foam` for microClimateFoam case

### Post-Processing Scripts

**Generate visualization images** (automated, no GUI required, adaptive scaling):
```bash
./scripts/postprocess/generate_images.sh custom_cases/heatedCavity 200
# Or for tutorial cases:
./scripts/postprocess/generate_images.sh cases/[tutorialCase] [time]
```
Generates 4 standard images: temperature contour, velocity vectors, streamlines, and overview. The script automatically adapts to different test cases:
- **Adaptive velocity scaling**: Automatically calculates optimal vector size based on domain and velocity magnitude
- **Adaptive temperature range**: Auto-detects and focuses on internal field variation
- **Adaptive mesh density**: Adjusts vector density based on mesh size
- Perfect for quick inspection, CI integration, and works across different case configurations

**Extract field statistics**:
```bash
python scripts/postprocess/extract_stats.py custom_cases/heatedCavity 200
# Or for tutorial cases:
python scripts/postprocess/extract_stats.py cases/[tutorialCase] [time]
```

**Generate visualization setup**:
```bash
python scripts/postprocess/extract_stats.py custom_cases/heatedCavity 200
# Or for tutorial cases:
python scripts/postprocess/extract_stats.py cases/[tutorialCase] [time]
```

### Platform-Specific Setup

- **Linux**: X11 forwarding (see `docs/visualization.md`)
- **macOS**: XQuartz installation and configuration
- **WSL2**: VcXsrv or X410 setup

Full details in `docs/visualization.md`.

## Multi-Solver Architecture

This project integrates multiple OpenFOAM solvers for microclimate simulations:

- **`urbanMicroclimateFoam`**: Advanced solver from OpenFOAM-BuildingPhysics with extended urban microclimate capabilities
  - Build: `./Allwmake` (custom build system)
  - **Cases:** `cases/streetCanyon_*`, `cases/windAroundBuildings_*` (6 tutorial cases), plus custom cases like `cases/Vidigal_CFD/`
  - **Designed for:** Multi-region cases with HAM, radiation, and vegetation
  - **Default test case:** `cases/streetCanyon_CFD/`
  - **⚠️ DO NOT use with `custom_cases/`** - incompatible field types
  
- **`microClimateFoam`**: Custom solver for incompressible flow with thermal transport and Boussinesq buoyancy
  - Build: `wmake` (standard OpenFOAM build)
  - **Cases:** `custom_cases/heatedCavity/` and other custom cases
  - **Designed for:** Single-region cases with simple thermal-fluid coupling
  - **⚠️ DO NOT use with `cases/`** - incompatible (multi-region, different field types)

**Build all solvers:**
```bash
./scripts/build_all_solvers.sh
```

**List available cases:**
```bash
./scripts/list_cases.sh
```

**Run the default test case:**
```bash
./scripts/run_case.sh cases/streetCanyon_CFD urbanMicroclimateFoam
# Or use the test scripts which use streetCanyon_CFD by default:
./test_env.sh      # Quick test
./test_full.sh     # Full test with visualization
```

See `docs/roadmap.md` for integration status and `docs/INTEGRATION_NOTES.md` for detailed integration information.

**Solver Documentation:**
- [Solver Comparison](docs/SOLVER_COMPARISON.md) - Comprehensive comparison of both solvers
- [microClimateFoam Documentation](docs/SOLVERS/microClimateFoam.md) - Detailed documentation for microClimateFoam
- [urbanMicroclimateFoam Documentation](docs/SOLVERS/urbanMicroclimateFoam.md) - Detailed documentation for urbanMicroclimateFoam

## Documentation & Next Steps

- `docs/roadmap.md`: canonical tracker for phases and tasks.
- `docs/visualization.md`: complete visualization guide with platform-specific instructions.
- `docs/BUILD_CACHING.md`: build and mesh caching system documentation.
- `docs/quick_start.md`: quick start guide for running cases.
- `docs/DEPENDENCY_MANAGEMENT.md`: dependency management approach and future recommendations.
- `docs/SOLVER_COMPARISON.md`: comprehensive comparison of both solvers.
- `docs/SOLVERS/`: solver-specific documentation.
  - `docs/SOLVERS/microClimateFoam.md`: microClimateFoam solver documentation.
  - `docs/SOLVERS/urbanMicroclimateFoam.md`: urbanMicroclimateFoam solver documentation.
- **Phase 5 Complete**: Multi-solver integration with `urbanMicroclimateFoam` and tutorial cases
- **Future enhancements** (see `docs/roadmap.md`):
  - Case management and standardization (Phase 6)
  - Solver comparison and benchmarking (Phase 7)
  - Turbulence modeling (Phase 8)
  - Advanced features and optimizations (Phase 9)

Contributions should update both the roadmap and this section so users can quickly tell what’s done versus planned.

