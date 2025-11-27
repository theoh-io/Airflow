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

## Phase 3 — Verification & Tooling (🗓 Planned)
- [x] Seed heated cavity tutorial (`cases/heatedCavity`) with mesh and run instructions.
- [ ] Automate case regression inside the container (extend `test_env.sh`).
- [ ] Add CI (GitHub Actions) to build Docker image, run `wmake`, and execute the tutorial case headless.

## Phase 4 — Visualization & UX (🗓 Planned)
- [ ] Document ParaView / X11 setup for Linux, macOS, and WSL2.
- [ ] Provide ParaView state files for standard plots (wind vectors, temperature slices).
- [ ] Package post-processing scripts (Python or `foamToVTK`) for reproducible figures.

> Update this roadmap as phases complete or tasks evolve so that contributors have a single source of truth.

