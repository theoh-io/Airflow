# microClimateFoam

OpenFOAM 8 solver for microclimate simulations.

## Quick Start
```bash
# Start dev environment
docker-compose up -d
docker exec -it microclimatefoam-dev bash

# Inside container
source /opt/openfoam/etc/bashrc
cd /workspace/src/microClimateFoam
wmake
```

## Status
🚧 In development - basic solver structure