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
│   └── microClimateFoam/   # Solver source code
│       ├── microClimateFoam.C  # Main solver file
│       └── Make/           # Build configuration
│           ├── files       # Source files to compile
│           └── options     # Compiler flags and libraries
└── README.md
```

## Status & Roadmap

- ✅ **Phase 0 – Environment & Skeleton**: Docker image, Compose workflow, and minimal solver build are working.
- 🚧 **Phase 1 – Flow Solver Core**: Implementing incompressible equations and field creation.
- 🗓 **Phase 2 – Thermal Transport**: Coupled temperature solve and buoyancy models.
- 🗓 **Phase 3 – Verification & Tooling**: Tutorial cases, automated regression, CI.
- 🗓 **Phase 4 – Visualization & UX**: ParaView guidance and post-processing scripts.

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
   ./test_env.sh          # runs wmake + binary sanity checks
   ./test_docker.sh       # lighter-weight smoke test
   ```

> `test_env.sh` is written to run inside the container root (`/workspace`). It suppresses the OpenFOAM welcome banner so CI logs stay readable.

### Heated Cavity One-Liner

To compile the solver, regenerate the heated cavity mesh, and run the tutorial case in one go:

```bash
./scripts/run_heated_cavity.sh
```

The script uses `docker compose run dev` under the hood and writes the solver log to `cases/heatedCavity/log.microClimateFoam`.

### WSL / Docker Desktop fallback

Compose should now work out of the box (bind mounting the entire repo at `/workspace`). If Docker Desktop integration ever regresses, you can still stream the necessary directories into a short-lived container:

```bash
tar -cf - src cases/heatedCavity | \
docker run --rm --entrypoint "" -i microclimatefoam:dev bash -lc '
  mkdir -p /tmp/workdir && cd /tmp/workdir
  tar -xf -
  source /opt/openfoam8/etc/bashrc
  cd src/microClimateFoam && wmake
  cd /tmp/workdir/cases/heatedCavity
  blockMesh
  microClimateFoam
'
```

## Documentation & Next Steps

- `docs/roadmap.md`: canonical tracker for phases and tasks.
- Upcoming work:
  - implement `createFields.H` and the incompressible momentum loop
  - add temperature transport with optional buoyancy
  - fix Docker Desktop ↔ WSL integration so `docker compose` and bind mounts work without the tar workaround
  - extend test scripts to execute the tutorial case and capture residuals
  - document ParaView/X11 setup for Linux, macOS, and WSL2 users

Contributions should update both the roadmap and this section so users can quickly tell what’s done versus planned.

## Heated Cavity Tutorial Case

A validation case that mirrors `hotRoom` from `buoyantBoussinesqSimpleFoam` lives in `cases/heatedCavity`.

Inside the dev container:

```bash
cd /workspace/cases/heatedCavity
blockMesh
microClimateFoam
```

Key features:
- 1×1×0.01 m cavity mesh (40×40×1 cells) with `empty` front/back to approximate 2D.
- Hot wall (`315 K`) on the left, cold wall (`285 K`) on the right, adiabatic top/bottom.
- Laminar, transient configuration with Boussinesq buoyancy parameters in `constant/transportProperties`.

Use this case to iterate on solver coupling between `U`, `p`, and `T`. Update the roadmap once the solver reproduces the expected buoyant plume.