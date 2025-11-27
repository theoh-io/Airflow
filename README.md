# microClimateFoam

OpenFOAM 8 solver for microclimate simulations (wind, temperature around buildings).

## Quick Start

### Using Docker Compose
```bash
# Build and start dev environment
docker-compose up -d
docker exec -it microclimatefoam-dev bash

# Inside container
source /opt/openfoam/etc/bashrc
cd /workspace/src/microClimateFoam
wmake
```

### Using Docker directly
```bash
# Build image
docker build -t microclimatefoam:dev .

# Run container
docker run --rm -it -v $(pwd)/src:/workspace/src microclimatefoam:dev bash

# Inside container
source /opt/openfoam/etc/bashrc
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
   docker compose up -d
   docker compose exec dev bash
   ```
2. **Inside container**
   ```bash
   source /opt/openfoam/etc/bashrc
   cd /workspace/src/microClimateFoam
   wmake
   ```
3. **Test environment**
   ```bash
   ./test_env.sh          # runs wmake + binary sanity checks
   ./test_docker.sh       # lighter-weight smoke test
   ```

> `test_env.sh` is written to run inside the container root (`/workspace`). It suppresses the OpenFOAM welcome banner so CI logs stay readable.

## Documentation & Next Steps

- `docs/roadmap.md`: canonical tracker for phases and tasks.
- Upcoming work:
  - implement `createFields.H` and the incompressible momentum loop
  - add temperature transport with optional buoyancy
  - ship at least one tutorial case plus run instructions
  - extend test scripts to execute the tutorial case and capture residuals
  - document ParaView/X11 setup for Linux, macOS, and WSL2 users

Contributions should update both the roadmap and this section so users can quickly tell what’s done versus planned.