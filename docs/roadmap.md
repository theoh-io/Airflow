# microClimateFoam Roadmap

> **Current Priority**: Vidigal_CFD Case Creation
> 
> Create new STL-based case `cases/Vidigal_CFD/` using `streetCanyon_CFD` as a template. This involves setting up STL-based meshing with `snappyHexMesh`, configuring multi-region setup, and integrating with the `urbanMicroclimateFoam` solver. See `docs/CASE_CREATION_PLAN.md` for detailed implementation plan.

## Phase 0 — Environment & Skeleton (✅ Done)
- Docker image (`openfoam/openfoam8-paraview56`) builds successfully.
- `docker-compose.yml` provides a dev container with bind-mounted `src`.
- Minimal solver skeleton (`microClimateFoam.C`) compiles via `wmake`.
- Utility scripts (`test_env.sh`) validate the container.

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

## Phase 5 — Multi-Solver Integration (✅ Done, 🔄 Optimization in Progress)
- [x] Clone and integrate `urbanMicroclimateFoam` solver:
  - [x] Clone repository: `git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam.git`
  - [x] Checkout OpenFOAM 8 tag: `git checkout tags/of-org_v8.0`
  - [x] Integrate into `src/urbanMicroclimateFoam/`
  - [x] Ensure `./Allwmake` builds successfully in Docker environment
  - [x] Document build requirements and dependencies
- [x] Reorganize case structure:
  - [x] Rename `cases/` to `custom_cases/` (for custom/validation cases)
  - [x] Clone tutorial cases: `git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials.git`
  - [x] Checkout OpenFOAM 8 tag: `git checkout tags/of-org_v8.0`
  - [x] Integrate tutorial cases into project structure
  - [x] Organize cases by solver or category
- [x] Update build system for multiple solvers:
  - [x] Create `scripts/build_all_solvers.sh` to build all solvers
  - [x] Support both `Allwmake` (urbanMicroclimateFoam) and `wmake` (microClimateFoam)
  - [x] Ensure both solvers can coexist and build independently
- [x] Update helper scripts:
  - [x] Update `run_case.sh` examples and help text
  - [x] Create `scripts/list_cases.sh` to show available cases with solver info
  - [x] Update all case runner scripts for multi-solver support
  - [x] Update all test scripts to use `custom_cases/`
- [x] Update CI/CD:
  - [x] Build all solvers in CI pipeline
  - [x] Test cases for each solver (default: streetCanyon_CFD with urbanMicroclimateFoam)
  - [x] Visualization testing with multi-region cases
  - [ ] **PRIORITY**: Optimize CI for quick validation (1-2 time steps, 5-15 min)
  - [ ] **PRIORITY**: Configure quick sanity check (deltaT=100s, endTime=200s)
  - [ ] Matrix strategy for multiple solvers/cases (future enhancement)
- [x] Documentation:
  - [x] Case catalog with descriptions and solver requirements
  - [x] Update README with multi-solver architecture
  - [x] Integration notes document created
  - [x] Solver comparison table (features, use cases) - See `docs/SOLVER_COMPARISON.md`
  - [x] Solver-specific documentation sections - See `docs/SOLVERS/`

## Phase 5.1 — CI/CD Optimization & Quick Validation (✅ Done)

**Goal**: Optimize CI/CD pipeline and test scripts for fast feedback (5-15 minutes instead of hours).

**Problem**: Current test setup runs 12 time steps (43200 seconds) which takes too long for CI and sanity checks. Each time step with `deltaT=3600s` can take 5-30+ minutes depending on mesh size.

**Recommendations**:
- Quick sanity check: `deltaT=100s`, `endTime=200s` (2 time steps, ~5-15 min)
- CI should run 1-2 time steps only (not full simulations)
- Full runs should be separate (nightly builds, manual runs)
- Focus on: compilation, mesh generation, solver startup, field writing

**Tasks**:
- [x] **PRIORITY**: Optimize `test_env.sh` for quick validation:
  - [x] Reduce `deltaT` to 100 seconds
  - [x] Set `endTime` to 200 seconds (2 time steps)
  - [x] Target completion time: 5-15 minutes
  - [x] Keep `writeInterval=1` for early validation
  - [x] Document expected runtime
- [x] **PRIORITY**: Update CI workflow (`.github/workflows/ci.yml`):
  - [x] Run quick validation only (1-2 time steps)
  - [x] Move `test_full.sh` to optional/separate workflow (nightly or manual trigger)
  - [x] Set appropriate timeout (20 minutes)
  - [x] Focus on: build, mesh, solver startup, field writing
  - [x] Make full test suite optional (only on schedule/workflow_dispatch)
- [x] **PRIORITY**: Create quick validation configuration:
  - [x] Implemented via script modifications (deltaT=50s, endTime=50s for tutorial cases)
  - [x] Document quick vs full test distinction
  - [x] Added `--quick-validation` option to `run_case.sh`
- [x] Update `test_full.sh`:
  - [x] Marked as optional/separate workflow in CI
  - [x] Documented that it's for comprehensive validation, not CI
  - [x] Configured to run only on schedule/workflow_dispatch
  - [x] Kept current behavior for full validation runs
- [x] Enhanced `run_case.sh` (replaced `run_street_canyon.sh`):
  - [x] Added `--quick-validation` option (deltaT=50s, endTime=50s for tutorial cases)
  - [x] Added `--quick` for quick test mode (12 time steps)
  - [x] Added `--full` for full simulation mode
  - [x] Added `--verbose` for real-time monitoring
  - [x] Added `--deltaT` and `--endTime` options for flexibility
  - [x] Added auto-detection of solver from controlDict
  - [x] Added multi-region support
  - [x] Removed redundant `run_street_canyon.sh` script
- [x] Documentation:
  - [x] Updated `docs/quick_start.md` with quick validation times
  - [x] Documented CI best practices (quick validation in CI, full runs separately)
  - [x] Updated `README.md` with new test modes and times
  - [x] Documented expected runtimes for different configurations

**Success Criteria**:
- CI completes in < 15 minutes
- Quick sanity check completes in 5-15 minutes
- Full runs remain available but separate from CI
- Clear distinction between quick validation and full tests
- Users can easily run quick validation locally

**Time Expectations**:
- Quick validation (deltaT=100s, 2 steps): 5-15 minutes
- Current quick test (deltaT=3600s, 12 steps): 1-6 hours (too long for CI)
- Full simulation (deltaT=3600s, 24 steps): 2-12+ hours (not for CI)

## Phase 5.2 — Vidigal_CFD Case Creation (IN PROGRESS)

**Goal**: Create a new STL-based CFD case (`Vidigal_CFD`) for urban microclimate simulations using `urbanMicroclimateFoam` solver.

**Description**: This case will use STL geometry provided by the user and implement STL-based meshing using `snappyHexMesh`, unlike the existing tutorial cases which use `blockMesh`. This demonstrates the workflow for creating custom cases with complex geometries.

**Key Tasks**:
- [x] **Phase 1**: Directory setup and template copy from `streetCanyon_CFD`
  - [x] Create `cases/Vidigal_CFD/` directory structure
  - [x] Copy and adapt base structure from `streetCanyon_CFD`
  - [x] Place user-provided STL file in `constant/triSurface/`
- [x] **Phase 2**: Mesh generation configuration
  - [x] Analyze STL geometry and calculate domain bounds
  - [x] Create background mesh using `blockMeshDict`
  - [x] Configure `snappyHexMeshDict` for STL-based meshing
  - [x] Set up mesh generation automation scripts
  - [x] Generate background mesh (6.4M cells) ✅
  - [~] snappyHexMesh refinement (IN PROGRESS - partially complete, needs restart)
    - [x] Surface refinement iterations completed
    - [x] Mesh cleanup and baffle handling started
    - [ ] Final mesh refinement and snap phase completion
- [ ] **Phase 3**: Multi-region setup
  - [ ] Determine required regions based on STL geometry
  - [ ] Configure `constant/regionProperties`
  - [ ] Set up region boundaries and interface patches
- [ ] **Phase 4**: Boundary conditions and initial fields
  - [ ] Update initial field files in `0/` directory
  - [ ] Configure boundary patch names from STL-based mesh
  - [ ] Set up inlet/outlet and wall boundary conditions
- [ ] **Phase 5**: Solver configuration
  - [ ] Verify `urbanMicroclimateFoam` solver configuration
  - [ ] Configure turbulence model
  - [ ] Set thermophysical properties for Vidigal conditions
- [ ] **Phase 6**: Scripts and automation
  - [ ] Update `Allrun` script for STL-based workflow
  - [ ] Update `Allclean` script
  - [ ] Create case `README.md` documentation
- [ ] **Phase 7**: Testing and validation
  - [ ] Test mesh generation and verify mesh quality
  - [ ] Run quick validation test (`--quick-validation`)
  - [ ] Generate visualizations and validate results

**Documentation**:
- [x] Created comprehensive case creation plan (`docs/CASE_CREATION_PLAN.md`)
- [x] Updated `docs/SOLVERS/urbanMicroclimateFoam.md` with Vidigal_CFD case entry
- [x] Updated `README.md` to mention Vidigal_CFD case
- [x] Created validation and testing documentation
- [x] Created mesh generation status reports
- [x] Created `docs/VIDIGAL_STATUS.md` with detailed progress tracking

**Success Criteria**:
- Case directory structure created and organized
- STL file integrated and meshing successful
- Multi-region setup working with `urbanMicroclimateFoam`
- Quick validation run completes successfully
- Case documented and ready for use

**Estimated Timeline**: 8-14 hours (depending on STL complexity and mesh refinement)

**See**: `docs/CASE_CREATION_PLAN.md` for detailed implementation guide

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

