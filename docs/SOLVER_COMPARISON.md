# Solver Comparison

This document provides a comprehensive comparison of the two solvers available in this project: `microClimateFoam` and `urbanMicroclimateFoam`.

## Quick Reference Table

| Feature | microClimateFoam | urbanMicroclimateFoam |
|---------|------------------|----------------------|
| **Type** | Custom solver | External solver (OpenFOAM-BuildingPhysics) |
| **Build System** | `wmake` (standard OpenFOAM) | `Allwmake` (custom build system) |
| **Complexity** | Simple, lightweight | Advanced, feature-rich |
| **Regions** | Single region only | Multi-region (air, solid, vegetation) |
| **Physics Models** | | |
| - Incompressible flow | ✅ | ✅ |
| - Temperature transport | ✅ | ✅ |
| - Boussinesq buoyancy | ✅ | ✅ |
| - Turbulence models | ❌ | ✅ |
| - Heat, Air, Moisture (HAM) | ❌ | ✅ |
| - Radiation (longwave/shortwave) | ❌ | ✅ |
| - Vegetation modeling | ❌ | ✅ |
| - Building material models | ❌ | ✅ |
| **Solution Method** | PISO | PISO (with advanced coupling) |
| **Primary Variables** | U, p, T | U, p_rgh, h (enthalpy), w (moisture) |
| **Use Cases** | | |
| - Simple validation cases | ✅ Ideal | ✅ Supported |
| - Heated cavity problems | ✅ Ideal | ✅ Supported |
| - Street canyon CFD | ⚠️ Limited | ✅ Ideal |
| - Urban microclimate | ❌ | ✅ Ideal |
| - Building physics | ❌ | ✅ Ideal |
| - Vegetation effects | ❌ | ✅ Ideal |
| - Radiation effects | ❌ | ✅ Ideal |
| **Learning Curve** | Low | High |
| **Performance** | Fast (simple physics) | Slower (complex physics) |
| **Documentation** | Project-specific | External wiki + project docs |
| **Maintenance** | Project-maintained | External project (OpenFOAM-BuildingPhysics) |

## Detailed Feature Comparison

### microClimateFoam

**Strengths:**
- Simple, easy to understand and modify
- Fast execution for basic thermal-fluid problems
- Ideal for learning OpenFOAM solver development
- Minimal dependencies
- Good for validation and educational purposes

**Limitations:**
- Single region only (no multi-region support)
- No turbulence modeling
- No advanced physics (HAM, radiation, vegetation)
- Limited to incompressible flow with thermal transport

**Best For:**
- Educational purposes and learning OpenFOAM
- Simple validation cases (e.g., heated cavity)
- Quick prototyping of thermal-fluid coupling
- Cases where complex building physics are not needed

**Example Cases:**
- `custom_cases/heatedCavity/` - Heated cavity validation case

### urbanMicroclimateFoam

**Strengths:**
- Comprehensive urban microclimate modeling
- Multi-region support (air, solid, vegetation)
- Advanced physics: HAM transport, radiation, vegetation
- Production-ready for real-world applications
- Extensive tutorial cases available

**Limitations:**
- More complex to set up and configure
- Slower execution due to complex physics
- Requires understanding of multi-region OpenFOAM
- External dependency (maintained by OpenFOAM-BuildingPhysics)

**Best For:**
- Real-world urban microclimate simulations
- Street canyon studies with building physics
- Cases requiring radiation modeling
- Vegetation impact studies
- Building material heat and moisture transport

**Example Cases:**
- `cases/streetCanyon_CFD/` - Basic street canyon CFD
- `cases/streetCanyon_CFDHAM/` - Street canyon with HAM
- `cases/streetCanyon_CFDHAM_veg/` - Street canyon with HAM and vegetation
- `cases/windAroundBuildings_CFDHAM/` - Wind around buildings with HAM
- `cases/windAroundBuildings_CFDHAM_veg/` - Wind around buildings with HAM and vegetation

## When to Use Which Solver?

### Use microClimateFoam when:
1. You need a simple, fast solver for basic thermal-fluid problems
2. You're learning OpenFOAM solver development
3. You're prototyping new features or modifications
4. Your case doesn't require multi-region or advanced physics
5. You need full control over the solver code

### Use urbanMicroclimateFoam when:
1. You need realistic urban microclimate simulations
2. Your case requires building material physics (HAM)
3. Radiation effects are important
4. Vegetation modeling is needed
5. You need multi-region capabilities
6. You're working on production research or engineering applications

## Technical Details

### microClimateFoam

**Equations Solved:**
- Incompressible momentum equation with Boussinesq buoyancy
- Temperature transport equation
- Pressure-velocity coupling via PISO algorithm

**Fields:**
- `U` - Velocity vector field
- `p` - Pressure scalar field
- `T` - Temperature scalar field
- `phi` - Flux field

**Boundary Conditions:**
- Standard OpenFOAM boundary conditions
- Temperature-dependent buoyancy via Boussinesq approximation

### urbanMicroclimateFoam

**Equations Solved:**
- Incompressible momentum equation (with turbulence)
- Enthalpy transport (instead of temperature)
- Moisture transport (in air and solid regions)
- Heat and moisture transport in porous building materials (HAM)
- Radiation balance (longwave and shortwave)
- Vegetation energy balance

**Fields:**
- `U` - Velocity vector field
- `p_rgh` - Pressure (relative to hydrostatic)
- `h` - Enthalpy field
- `T` - Temperature (derived from enthalpy)
- `w` - Moisture content
- Additional fields for radiation and vegetation

**Regions:**
- `air` - Fluid region (CFD)
- `solid` regions (e.g., `buildings`, `ground`, `street`) - Porous material regions (HAM)
- `vegetation` - Vegetation region (optional)

**Boundary Conditions:**
- Advanced coupled boundary conditions for fluid-solid interfaces
- CFDHAM coupling for heat and moisture transfer
- Radiation boundary conditions
- Vegetation boundary conditions

## Performance Considerations

### microClimateFoam
- **Speed**: Fast (simple physics, single region)
- **Memory**: Low (single region, fewer fields)
- **Scalability**: Good (standard OpenFOAM parallelization)
- **Typical runtime**: Minutes to hours (depending on case size)

### urbanMicroclimateFoam
- **Speed**: Slower (complex physics, multi-region coupling)
- **Memory**: Higher (multiple regions, more fields)
- **Scalability**: Good (supports parallel execution with `decomposePar`)
- **Typical runtime**: Hours to days (depending on case complexity)

## Getting Started

### microClimateFoam
```bash
# Build solver
cd /workspace/src/microClimateFoam
wmake

# Run case
./scripts/run_case.sh custom_cases/heatedCavity
```

### urbanMicroclimateFoam
```bash
# Build solver
cd /workspace/src/urbanMicroclimateFoam
./Allwmake

# Run case
./scripts/run_case.sh cases/streetCanyon_CFD urbanMicroclimateFoam
```

## Further Reading

- **microClimateFoam**: See `docs/SOLVERS/microClimateFoam.md`
- **urbanMicroclimateFoam**: See `docs/SOLVERS/urbanMicroclimateFoam.md` and [official wiki](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam/wiki)

