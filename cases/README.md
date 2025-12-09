# Cases Directory

This directory contains OpenFOAM cases for the `urbanMicroclimateFoam` solver.

## Contents

### Tutorial Cases

The following tutorial cases are included from [OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials) (tag `of-org_v8.0`):

- `streetCanyon_CFD/` - Street canyon CFD simulation
- `streetCanyon_CFDHAM/` - Street canyon with Heat and Moisture (HAM) transport
- `streetCanyon_CFDHAM_grass/` - Street canyon with HAM and grass surface
- `streetCanyon_CFDHAM_veg/` - Street canyon with HAM and vegetation
- `windAroundBuildings_CFDHAM/` - Wind flow around buildings with HAM
- `windAroundBuildings_CFDHAM_veg/` - Wind flow around buildings with HAM and vegetation

### Custom Cases

- `Vidigal_CFD/` - Custom case using STL-based geometry (created for this project)

## Solver Requirements

All cases require the `urbanMicroclimateFoam` solver, which is included in this project at `src/urbanMicroclimateFoam/`.

**OpenFOAM Version**: OpenFOAM 8 (of-org_v8.0)

## Usage

See the main project [README.md](../README.md) for instructions on:
- Building the solver
- Running cases
- Generating visualizations

## Dependency Management

These cases were originally cloned from the upstream repository but are now directly included in this project. See `docs/DEPENDENCY_MANAGEMENT.md` for details on the dependency management approach and future recommendations.

## Original Source

The tutorial cases were originally from:
- **Repository**: [OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials)
- **Version/Tag**: `of-org_v8.0`
- **Solver**: [OpenFOAM-BuildingPhysics/urbanMicroclimateFoam](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam)

