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
│   ├── microClimateFoam/   # Custom solver (incompressible flow + thermal transport)
│   │   ├── microClimateFoam.C
│   │   └── Make/
│   └── urbanMicroclimateFoam/  # urbanMicroclimateFoam solver (to be integrated)
│       └── (cloned from OpenFOAM-BuildingPhysics/urbanMicroclimateFoam)
├── custom_cases/           # Custom validation/test cases
│   └── heatedCavity/       # microClimateFoam validation case
├── cases/                  # Tutorial cases (from urbanMicroclimateFoam-tutorials)
│   └── (cloned from OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials)
├── scripts/                # Helper scripts for building, running, testing
└── docs/                   # Documentation
```

## Status & Roadmap

- ✅ **Phase 0 – Environment & Skeleton**: Docker image, Compose workflow, and minimal solver build are working.
- ✅ **Phase 1 – Flow Solver Core**: Incompressible momentum equation with PISO loop implemented and tested.
- ✅ **Phase 2 – Thermal Transport**: Temperature transport equation with Boussinesq buoyancy coupling implemented and tested.
- ✅ **Phase 3 – Verification & Tooling**: Automated regression testing and CI (GitHub Actions) implemented.
- ✅ **Phase 4 – Visualization & UX**: ParaView setup documentation, post-processing scripts, and visualization tools implemented.
- 🔄 **Phase 5 – Multi-Solver Integration**: Integrating `urbanMicroclimateFoam` solver and tutorial cases (in progress).

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
   ./test_env.sh          # Quick regression test: compilation, mesh generation, short solver run (5 steps)
   ./test_full.sh         # Full test: complete simulation to endTime, field validation, visualization generation
   ./test_parallel.sh     # Parallel execution test: serial vs parallel comparison
   ./test_docker.sh       # Lighter-weight smoke test
   ```

> **Test Scripts:**
> - `test_env.sh`: Quick regression test (5 time steps) - fast feedback for development
> - `test_full.sh`: Comprehensive test including:
>   - Full simulation run to `endTime`
>   - Field statistics validation (temperature, velocity ranges)
>   - Visualization image generation and validation
>   - PNG file structure verification
> - `test_parallel.sh`: Parallel execution test (serial vs parallel comparison)
> 
> All scripts are designed to run inside the container and are used by CI for automated testing.

### Heated Cavity One-Liner

To compile the solver, regenerate the heated cavity mesh, and run the tutorial case in one go:

```bash
./scripts/run_heated_cavity.sh
```

The script uses `docker compose run dev` under the hood and writes the solver log to `custom_cases/heatedCavity/log.microClimateFoam`.

> **Note:** The `cases/` directory will be renamed to `custom_cases/` to make room for tutorial cases from `urbanMicroclimateFoam-tutorials`.

### Generic Case Runner

For other cases, use the flexible helper:

```bash
# Build solver, run blockMesh + checkMesh (if present), and launch microClimateFoam
./scripts/run_case.sh custom_cases/heatedCavity

# Run in parallel mode (auto-creates decomposeParDict if missing)
./scripts/run_case.sh -p 4 custom_cases/heatedCavity

# Run a case with a different solver
./scripts/run_case.sh -n -B cases/tutorialCase urbanMicroclimateFoam

# Skip wmake, skip blockMesh, and run another solver with custom args
./scripts/run_case.sh -n -B custom_cases/myCase buoyantBoussinesqSimpleFoam -- -parallel

# Parallel run without reconstruction (keeps decomposed results)
./scripts/run_case.sh -p 2 -R custom_cases/myCase
```

> **Note:** After Phase 5 integration, cases will be organized as:
> - `custom_cases/` - Custom validation/test cases (e.g., `heatedCavity`)
> - `cases/` - Tutorial cases from `urbanMicroclimateFoam-tutorials`

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

See `docs/visualization.md` for complete visualization setup instructions. For a quick reference, see `docs/visualization_quickref.md`.

### Quick Start

1. **Create ParaView case file**:
   ```bash
   ./scripts/create_foam_file.sh custom_cases/heatedCavity
   ```

2. **Start ParaView** (Linux example):
   ```bash
   xhost +local:docker
   docker compose run --rm dev paraview
   ```

3. **Open the case**:
   - File → Open → `custom_cases/heatedCavity/heatedCavity.foam` (or `cases/[tutorialCase]/[tutorialCase].foam`)

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
python scripts/postprocess/plot_fields.py custom_cases/heatedCavity 200
# Or for tutorial cases:
python scripts/postprocess/plot_fields.py cases/[tutorialCase] [time]
```

### Platform-Specific Setup

- **Linux**: X11 forwarding (see `docs/visualization.md`)
- **macOS**: XQuartz installation and configuration
- **WSL2**: VcXsrv or X410 setup

Full details in `docs/visualization.md`.

## Documentation & Next Steps

- `docs/roadmap.md`: canonical tracker for phases and tasks.
- `docs/visualization.md`: complete visualization guide with platform-specific instructions.
- **Phase 5 In Progress**: Multi-solver integration with `urbanMicroclimateFoam` and tutorial cases
- **Future enhancements** (see `docs/roadmap.md`):
  - Case management and standardization (Phase 6)
  - Solver comparison and benchmarking (Phase 7)
  - Turbulence modeling (Phase 8)
  - Advanced features and optimizations (Phase 9)

Contributions should update both the roadmap and this section so users can quickly tell what’s done versus planned.

