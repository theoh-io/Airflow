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

## Status

✅ **Basic solver structure complete**
- Minimal OpenFOAM solver skeleton implemented
- Docker development environment configured
- Build system configured (wmake)

🚧 **Next steps**
- Implement incompressible flow equations
- Add temperature transport
- Create test cases