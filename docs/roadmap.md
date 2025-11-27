# microClimateFoam Roadmap

## Phase 0 — Environment & Skeleton (✅ Done)
- Docker image (`openfoam/openfoam8-paraview56`) builds successfully.
- `docker-compose.yml` provides a dev container with bind-mounted `src`.
- Minimal solver skeleton (`microClimateFoam.C`) compiles via `wmake`.
- Utility scripts (`test_env.sh`, `test_docker.sh`) validate the container.

## Phase 1 — Flow Solver Core (✅ Done)
- [x] Add `createFields.H` to instantiate velocity, pressure, and turbulence fields.
- [x] Implement incompressible momentum equation (PISO loop) with residual logging.
- [x] Provide consistent boundary-condition templates in `0/` for tutorial case (`cases/heatedCavity`).

## Phase 2 — Thermal Transport (✅ Done)
- [x] Introduce temperature scalar transport equation coupled to the flow solution.
- [x] Support buoyancy via Boussinesq approximation (integrated into momentum equation).
- [x] Document energy-specific stabilisation / relaxation controls (via fvSolution relaxationFactors).

## Phase 3 — Verification & Tooling (✅ Done)
- [x] Seed heated cavity tutorial (`cases/heatedCavity`) with mesh and run instructions.
- [x] Automate case regression inside the container (extend `test_env.sh`).
- [x] Add CI (GitHub Actions) to build Docker image, run `wmake`, and execute the tutorial case headless.
- [x] Comprehensive testing suite:
  - [x] Full simulation test (`test_full.sh`) - runs to endTime with field validation
  - [x] Visualization testing - automated image generation and validation
  - [x] Field statistics validation - temperature and velocity range checks
  - [x] Image validation - PNG structure and file size verification
  - [x] Parallel execution test (`test_parallel.sh`) - serial vs parallel comparison

## Phase 4 — Visualization & UX (✅ Done)
- [x] Document ParaView / X11 setup for Linux, macOS, and WSL2.
- [x] Provide ParaView state files for standard plots (wind vectors, temperature slices) - see `docs/paraview/README.md`.
- [x] Package post-processing scripts (Python scripts for field extraction and visualization setup).
- [x] Implement automated headless image generation with adaptive scaling:
  - [x] Adaptive velocity vector scaling based on domain size and velocity magnitude
  - [x] Adaptive temperature range detection with intelligent boundary handling
  - [x] Adaptive mesh density adjustment for optimal vector visualization
  - [x] Works automatically across different test cases and configurations

## Phase 5 — Multi-Solver Integration (🔄 IN PROGRESS)
- [ ] Clone and integrate `urbanMicroclimateFoam` solver:
  - [ ] Clone repository: `git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam.git`
  - [ ] Checkout OpenFOAM 8 tag: `git checkout tags/of-org_v8.0`
  - [ ] Integrate into `src/urbanMicroclimateFoam/`
  - [ ] Ensure `./Allwmake` builds successfully in Docker environment
  - [ ] Document build requirements and dependencies
- [ ] Reorganize case structure:
  - [ ] Rename `cases/` to `custom_cases/` (for custom/validation cases)
  - [ ] Clone tutorial cases: `git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials.git`
  - [ ] Checkout OpenFOAM 8 tag: `git checkout tags/of-org_v8.0`
  - [ ] Integrate tutorial cases into project structure
  - [ ] Organize cases by solver or category
- [ ] Update build system for multiple solvers:
  - [ ] Create `scripts/build_all_solvers.sh` to build all solvers
  - [ ] Update `wmake` workflow to support multiple solvers
  - [ ] Ensure both solvers can coexist and build independently
- [ ] Update helper scripts:
  - [ ] Enhance `run_case.sh` to auto-detect solver from case metadata
  - [ ] Create `scripts/list_cases.sh` to show available cases with solver info
  - [ ] Update case runner scripts for multi-solver support
- [ ] Update CI/CD:
  - [ ] Build all solvers in CI pipeline
  - [ ] Test cases for each solver
  - [ ] Matrix strategy for multiple solvers/cases
- [ ] Documentation:
  - [ ] Solver comparison table (features, use cases)
  - [ ] Case catalog with descriptions and solver requirements
  - [ ] Update README with multi-solver architecture
  - [ ] Solver-specific documentation sections

## Phase 6 — Case Management & Standardization (PLANNED)
- [ ] Case metadata system:
  - [ ] `README.md` template for each case
  - [ ] `metadata.json` with solver, description, tags, requirements
  - [ ] Case validation script
- [ ] Standardized case structure:
  - [ ] Consistent naming conventions
  - [ ] Required files checklist
  - [ ] Case template generator
- [ ] Case testing framework:
  - [ ] Extend `test_full.sh` to work with any case/solver combination
  - [ ] Case-specific validation rules
  - [ ] Automated case regression tests
- [ ] Case visualization:
  - [ ] Extend `generate_images.sh` to work with all cases
  - [ ] Case-specific visualization presets
  - [ ] Automated figure generation for case catalog

## Phase 7 — Solver Comparison & Benchmarking (PLANNED)
- [ ] Benchmark suite:
  - [ ] Common test cases run with all solvers
  - [ ] Performance comparison (speed, memory usage)
  - [ ] Results comparison (field values, convergence rates)
- [ ] Validation framework:
  - [ ] Reference solutions database
  - [ ] Automated comparison scripts
  - [ ] Validation reports generation

## Phase 8 — Turbulence Modeling (DEFERRED)
- [ ] Evaluate turbulence capabilities in `urbanMicroclimateFoam`
- [ ] Add turbulence models to `microClimateFoam` if needed
- [ ] Or leverage turbulence from `urbanMicroclimateFoam` implementation
- [ ] Document turbulence model selection and usage

## Phase 9 — Advanced Features (DEFERRED)
- [ ] Advanced boundary conditions
- [ ] Performance optimization
- [ ] Extended post-processing tools
- [ ] Additional physics models

> Update this roadmap as phases complete or tasks evolve so that contributors have a single source of truth.

