# microClimateFoam Roadmap

> **Current Priority**: Vidigal_CFD Accuracy Validation & Advanced Physics Integration
> 
> Before running full simulations, ensure accuracy and integrate advanced physics models (radiation and humidity) into the Vidigal_CFD case. This includes mesh quality validation, radiation modeling setup, humidity transport configuration, and accuracy verification tests. See `docs/VIDIGAL_STATUS.md` for current status.

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

## Phase 5.2 — Vidigal_CFD Case Creation (✅ MOSTLY COMPLETE)

**Goal**: Create a new STL-based CFD case (`Vidigal_CFD`) for urban microclimate simulations using `urbanMicroclimateFoam` solver.

**Description**: This case uses STL geometry and implements STL-based meshing using `snappyHexMesh`, unlike the existing tutorial cases which use `blockMesh`. This demonstrates the workflow for creating custom cases with complex geometries.

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
  - [x] snappyHexMesh refinement completed ✅
- [x] **Phase 3**: Boundary conditions and initial fields
  - [x] Update initial field files in `0/` directory
  - [x] Configure boundary patch names from STL-based mesh
  - [x] Set up inlet/outlet and wall boundary conditions
- [x] **Phase 4**: Solver configuration
  - [x] Verify `urbanMicroclimateFoam` solver configuration
  - [x] Configure turbulence model
  - [x] Set thermophysical properties for Vidigal conditions
- [x] **Phase 5**: Scripts and automation
  - [x] Update `Allrun` script for STL-based workflow
  - [x] Update `Allclean` script
  - [x] Create case `README.md` documentation
- [x] **Phase 6**: Initial testing and validation
  - [x] Test mesh generation and verify mesh quality
  - [x] Run quick validation test (time step 50 completed)
  - [x] Generate initial visualizations

**Current Status**: Case is functional and has been successfully run. Quick validation completed (time step 50). Ready for accuracy validation and advanced physics integration.

**Documentation**:
- [x] Created comprehensive case creation plan (`docs/CASE_CREATION_PLAN.md`)
- [x] Updated `docs/SOLVERS/urbanMicroclimateFoam.md` with Vidigal_CFD case entry
- [x] Updated `README.md` to mention Vidigal_CFD case
- [x] Created validation and testing documentation
- [x] Created mesh generation status reports
- [x] Created `docs/VIDIGAL_STATUS.md` with detailed progress tracking

**See**: `docs/CASE_CREATION_PLAN.md` for detailed implementation guide

---

## Phase 5.3 — Vidigal_CFD Accuracy Validation & Advanced Physics Integration (🔄 CURRENT PRIORITY)

**Goal**: Ensure simulation accuracy and integrate advanced physics models (radiation and humidity) before running full production simulations.

**Description**: Before extending to full simulation runs, validate mesh quality, solution accuracy, and integrate radiation and humidity transport models. This ensures the case produces physically accurate results for urban microclimate analysis.

**Key Tasks**:

### Accuracy Validation
- [ ] **Mesh Quality Assessment**
  - [ ] Run comprehensive `checkMesh` analysis
  - [ ] Verify mesh quality metrics (skewness, non-orthogonality, aspect ratio)
  - [ ] Check mesh resolution adequacy for physics (boundary layer, surface refinement)
  - [ ] Document mesh statistics and quality metrics
- [ ] **Solution Accuracy Verification**
  - [ ] Grid convergence study (if needed)
  - [ ] Compare results with reference cases (streetCanyon_CFD)
  - [ ] Validate field ranges (temperature, velocity, pressure)
  - [ ] Check boundary condition implementation
  - [ ] Verify turbulence model behavior
- [ ] **Sensitivity Analysis**
  - [ ] Test different time step sizes
  - [ ] Verify solver convergence
  - [ ] Check numerical stability

### Radiation Modeling Integration
- [ ] **Radiation Configuration**
  - [ ] Create `constant/air/radiationProperties` file
  - [ ] Create `constant/air/solarLoadProperties` file
  - [ ] Configure view factor-based radiation model
  - [ ] Set up solar load model (direct and diffuse)
  - [ ] Configure emissivity and albedo properties
- [ ] **Radiation Fields Setup**
  - [ ] Add `qr` field (longwave radiation) to `0/air/`
  - [ ] Add `qs` field (shortwave/solar radiation) to `0/air/`
  - [ ] Configure radiation boundary conditions for all patches
  - [ ] Set up sky view factors
  - [ ] Configure sun position and solar radiation parameters
- [ ] **Radiation Testing**
  - [ ] Run quick validation with radiation enabled
  - [ ] Verify radiation field initialization
  - [ ] Check radiation boundary condition coupling
  - [ ] Validate radiation energy balance

### Humidity/Moisture Transport Integration
- [ ] **Humidity Configuration Review**
  - [ ] Verify existing `w` field configuration (already present)
  - [ ] Review humidity boundary conditions
  - [ ] Check humidity transport properties
  - [ ] Verify coupling with temperature/enthalpy
- [ ] **Humidity Boundary Conditions**
  - [ ] Configure inlet humidity conditions
  - [ ] Set up wall humidity boundary conditions
  - [ ] Verify humidity transport in air region
  - [ ] Test humidity field evolution
- [ ] **Humidity Testing**
  - [ ] Run quick validation with humidity transport
  - [ ] Verify humidity field initialization
  - [ ] Check humidity conservation
  - [ ] Validate humidity-temperature coupling

### Combined Physics Validation
- [ ] **Integrated Model Testing**
  - [ ] Run quick validation with radiation + humidity enabled
  - [ ] Verify all physics models work together
  - [ ] Check energy balance (radiation + convection + humidity)
  - [ ] Validate field interactions
- [ ] **Accuracy Metrics**
  - [ ] Compare results with/without advanced physics
  - [ ] Document impact of radiation and humidity on results
  - [ ] Verify physical realism of combined model
- [ ] **Performance Assessment**
  - [ ] Measure computational cost of advanced physics
  - [ ] Optimize solver settings if needed
  - [ ] Document expected runtime with full physics

### Documentation
- [ ] **Configuration Documentation**
  - [ ] Document radiation setup and parameters
  - [ ] Document humidity configuration
  - [ ] Create accuracy validation report
  - [ ] Update case README with physics models
- [ ] **Validation Report**
  - [ ] Document mesh quality metrics
  - [ ] Record accuracy validation results
  - [ ] Create comparison with reference cases
  - [ ] Document recommended settings for production runs

**Success Criteria**:
- Mesh quality validated and documented
- Solution accuracy verified
- Radiation modeling integrated and tested
- Humidity transport integrated and tested
- Combined physics model validated
- Accuracy validation report completed
- Case ready for full production simulations

**Estimated Timeline**: 6-10 hours (depending on validation requirements and physics integration complexity)

**Note**: Vegetation modeling is deferred until tree/vegetation data is available. Current focus is on radiation and humidity in the air region only.

**See**: 
- `docs/VIDIGAL_STATUS.md` for current status
- `cases/streetCanyon_CFDHAM/` for reference implementation
- `docs/SOLVERS/urbanMicroclimateFoam.md` for solver capabilities

## Phase 5.4 — Vidigal_CFD Full Production Simulation (PLANNED - After Phase 5.3)

**Goal**: Run full production simulations with validated accuracy and integrated advanced physics.

**Description**: Once accuracy is validated and advanced physics (radiation, humidity) are integrated and tested, extend simulation time for full production runs and comprehensive analysis.

**Key Tasks**:
- [ ] **Simulation Configuration**
  - [ ] Set appropriate `endTime` for full simulation (e.g., 24-48 hours)
  - [ ] Configure `deltaT` for stability and accuracy
  - [ ] Set up field output intervals
  - [ ] Configure post-processing functions
- [ ] **Production Run**
  - [ ] Execute full simulation
  - [ ] Monitor convergence and stability
  - [ ] Handle any runtime issues
- [ ] **Results Analysis**
  - [ ] Generate comprehensive visualizations
  - [ ] Extract field statistics
  - [ ] Analyze pedestrian-level conditions
  - [ ] Compare with validation data (if available)
- [ ] **Documentation**
  - [ ] Document simulation parameters
  - [ ] Create results summary
  - [ ] Update case documentation

**Prerequisites**: Phase 5.3 must be completed (accuracy validated, radiation and humidity integrated)

---

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
- [ ] Vegetation modeling (when tree/vegetation data available)
  - [ ] Add vegetation region to Vidigal_CFD
  - [ ] Configure vegetation properties
  - [ ] Integrate vegetation energy balance
  - [ ] Couple with air region for heat and moisture exchange

> Update this roadmap as phases complete or tasks evolve so that contributors have a single source of truth.

