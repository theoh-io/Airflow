# urbanMicroclimateFoam Solver Documentation

## Overview

`urbanMicroclimateFoam` is an advanced multi-region OpenFOAM solver for coupled physical processes modeling urban microclimate. It combines computational fluid dynamics (CFD) for air flow with heat, air, and moisture (HAM) transport in porous building materials, radiation modeling, and vegetation effects.

## Solver Type

- **Category**: Multi-region urban microclimate solver
- **Build System**: Custom `Allwmake` build system
- **Complexity**: Advanced, production-ready
- **Maintainer**: OpenFOAM-BuildingPhysics (external project)
- **Source**: [https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam)

## Physics Models

### Flow Model
- **Type**: Incompressible turbulent flow
- **Method**: PISO with advanced coupling
- **Turbulence**: Multiple turbulence models supported (RANS)

### Thermal Model
- **Type**: Enthalpy-based transport (not temperature)
- **Equation**: Enthalpy transport equation
- **Coupling**: Coupled with solid regions via HAM

### Heat, Air, and Moisture (HAM) Model
- **Type**: Coupled heat and moisture transport in porous materials
- **Regions**: Solid regions (buildings, ground, street, etc.)
- **Materials**: Building material models (e.g., Hamstad5Brick, HamstadConcrete)

### Radiation Model
- **Type**: Longwave and shortwave radiation
- **Method**: View factor approach
- **Features**: Sky view factors, sun position, solar radiation

### Vegetation Model
- **Type**: Simplified vegetation model (optional)
- **Features**: Leaf area index (LAI), vegetation energy balance
- **Coupling**: Coupled with air region

## Governing Equations

### Air Region (CFD)
- Incompressible momentum equation with turbulence
- Enthalpy transport equation
- Moisture transport equation (optional)

### Solid Regions (HAM)
- Heat transport in porous materials
- Moisture transport in porous materials
- Coupled boundary conditions with air region

### Vegetation Region (Optional)
- Energy balance equation
- Coupled with air region for heat and moisture exchange

## Fields and Variables

### Primary Fields (Air Region)
- **`U`**: Velocity vector field (m/s)
- **`p_rgh`**: Pressure relative to hydrostatic (m²/s²)
- **`h`**: Enthalpy field (J/kg)
- **`T`**: Temperature (derived from enthalpy) (K)
- **`w`**: Moisture content (kg/kg) (optional)

### Solid Region Fields
- **`Ts`**: Solid temperature (K)
- **`pc`**: Capillary pressure (Pa)
- Additional fields for HAM transport

### Vegetation Region Fields
- **`T`**: Vegetation temperature (K)
- **`qr`**: Radiation fields
- Additional fields for vegetation energy balance

## Solution Algorithm

1. **Multi-Region Setup**: Initialize all regions
2. **Time Loop**: Iterate over time steps
3. **Air Region**: Solve CFD equations
4. **Solid Regions**: Solve HAM equations
5. **Coupling**: Exchange boundary conditions between regions
6. **Radiation**: Calculate radiation fluxes
7. **Vegetation**: Solve vegetation equations (if present)
8. **Field Writing**: Output at specified intervals

## Regions

The solver supports multiple regions:

### Air Region
- **Name**: `air`
- **Type**: Fluid (CFD)
- **Purpose**: Main fluid domain for wind and thermal flow

### Solid Regions
- **Examples**: `buildings`, `ground`, `street`, `windward`, `leeward`
- **Type**: Porous material (HAM)
- **Purpose**: Building materials with heat and moisture transport

### Vegetation Region (Optional)
- **Name**: `vegetation`
- **Type**: Vegetation model
- **Purpose**: Vegetation effects on microclimate

## Boundary Conditions

### Air-Solid Coupling
- **Type**: `CFDHAMfluidTemperatureCoupledMixed`
- **Purpose**: Coupled temperature boundary condition
- **Type**: `CFDHAMfluidMoistureCoupledImpermeable`
- **Purpose**: Coupled moisture boundary condition

### Solid-Solid Coupling
- **Type**: `CFDHAMsolidTemperatureCoupledMixed`
- **Purpose**: Coupled temperature between solid regions
- **Type**: `CFDHAMsolidMoistureCoupledImpermeable`
- **Purpose**: Coupled moisture between solid regions

### Radiation Boundaries
- View factor-based radiation
- Solar radiation with sun position
- Sky radiation

## Configuration

### controlDict Settings
Special solver controls:
- **`initialSolidTimestepFactor`**: Initial time step factor for solid regions
- **`minDeltaT`**: Minimum time step
- **`maxDeltaT`**: Maximum time step
- **`minFluidIteration`**: Minimum fluid iterations
- **`maxFluidIteration`**: Maximum fluid iterations

### regionProperties
Defines regions and their types:
```cpp
regions
(
    air (fluid)
    buildings (solid)
    ground (solid)
    vegetation (vegetation)
);
```

### Transport Properties
- Air region: Standard fluid properties
- Solid regions: Building material models (e.g., `Hamstad5Brick`, `HamstadConcrete`)
- Vegetation: Vegetation properties

## Build Instructions

### Prerequisites
- OpenFOAM 8
- Standard OpenFOAM build environment

### Build Steps
```bash
# Source OpenFOAM environment
source /opt/openfoam8/etc/bashrc

# Navigate to solver directory
cd /workspace/src/urbanMicroclimateFoam

# Checkout correct version (if needed)
git checkout tags/of-org_v8.0

# Build solver
./Allwmake
```

The solver binary will be created at `$FOAM_USER_APPBIN/urbanMicroclimateFoam`.

## Running Cases

### Basic Usage
```bash
# Using the generic case runner
./scripts/run_case.sh cases/streetCanyon_CFD urbanMicroclimateFoam

# Or manually
cd cases/streetCanyon_CFD
# Follow case-specific setup (Allprepare, Allrun, etc.)
```

### Case Setup
Most tutorial cases require preparation:
```bash
cd cases/streetCanyon_CFD
./Allprepare  # Prepare mesh and regions
./Allrun       # Run simulation
```

### Parallel Execution
```bash
# Decompose for all regions
decomposePar -allRegions

# Run in parallel
mpirun -np 4 urbanMicroclimateFoam -parallel

# Reconstruct
reconstructPar -allRegions
```

## Available Cases

**⚠️ IMPORTANT: Case Compatibility**

`urbanMicroclimateFoam` is designed for **multi-region cases** in the `cases/` directory.

**Compatible:**
- All tutorial cases in `cases/` directory
- Cases with `constant/regionProperties` (multi-region setup)
- Cases using `p_rgh`, `h` (enthalpy), and other advanced fields

**Incompatible:**
- **DO NOT** use with cases in `custom_cases/` directory
- Custom cases are single-region and use `p` instead of `p_rgh`
- Custom cases require `microClimateFoam` solver

### streetCanyon_CFD
- **Location**: `cases/streetCanyon_CFD/`
- **Description**: Basic street canyon CFD simulation
- **Regions**: `air`, `street`, `windward`, `leeward`
- **Physics**: CFD only (no HAM)

### streetCanyon_CFDHAM
- **Location**: `cases/streetCanyon_CFDHAM/`
- **Description**: Street canyon with HAM transport
- **Regions**: `air`, `street`, `windward`, `leeward` (with HAM)
- **Physics**: CFD + HAM

### streetCanyon_CFDHAM_veg
- **Location**: `cases/streetCanyon_CFDHAM_veg/`
- **Description**: Street canyon with HAM and vegetation
- **Regions**: `air`, `street`, `windward`, `leeward`, `vegetation`
- **Physics**: CFD + HAM + Vegetation

### windAroundBuildings_CFDHAM
- **Location**: `cases/windAroundBuildings_CFDHAM/`
- **Description**: Wind around buildings with HAM
- **Regions**: `air`, `buildings`, `ground`
- **Physics**: CFD + HAM

### windAroundBuildings_CFDHAM_veg
- **Location**: `cases/windAroundBuildings_CFDHAM_veg/`
- **Description**: Wind around buildings with HAM and vegetation
- **Regions**: `air`, `buildings`, `ground`, `vegetation`
- **Physics**: CFD + HAM + Vegetation

## Features and Capabilities

### Multi-Region Support
- Fluid regions (air)
- Solid regions (buildings, ground, etc.)
- Vegetation regions (optional)
- Automatic region coupling

### Advanced Physics
- Heat, Air, and Moisture (HAM) transport
- Radiation modeling (longwave and shortwave)
- Vegetation effects
- Building material models

### Boundary Conditions
- Coupled fluid-solid boundaries
- Radiation boundaries
- Vegetation boundaries
- Advanced moisture transport boundaries

## Limitations

1. **Complexity**: Requires understanding of multi-region OpenFOAM
2. **Setup Time**: Cases require careful preparation
3. **Computational Cost**: Slower than simple solvers
4. **External Dependency**: Maintained by external project

## Performance Tips

1. **Time Step**: Use appropriate `deltaT` (solver has adaptive time stepping)
2. **Mesh Quality**: Critical for multi-region cases
3. **Parallel Execution**: Essential for large cases
4. **Region Coupling**: Monitor coupling convergence
5. **Radiation**: Pre-compute view factors if possible

## Troubleshooting

### Common Issues

**Region Not Found:**
- Check `regionProperties` file
- Verify region directories exist in `0/` and `constant/`

**Coupling Diverges:**
- Check boundary condition types
- Verify material properties
- Reduce time step

**Radiation Not Working:**
- Run view factor generation (`viewFactorsGen`)
- Check solar radiation setup
- Verify vegetation region setup (if used)

**HAM Transport Issues:**
- Check building material models
- Verify transport properties
- Check boundary conditions

## Documentation

### Official Documentation
- **Wiki**: [https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam/wiki](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam/wiki)
- **Tutorials**: [https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials)

### Project Documentation
- [Solver Comparison](SOLVER_COMPARISON.md)
- [Integration Notes](../INTEGRATION_NOTES.md)
- [Quick Start Guide](../quick_start.md)

## References

- OpenFOAM-BuildingPhysics: [https://github.com/OpenFOAM-BuildingPhysics](https://github.com/OpenFOAM-BuildingPhysics)
- Chair of Building Physics, ETH Zurich: [https://carmeliet.ethz.ch](https://carmeliet.ethz.ch)
- OpenFOAM Documentation: [https://www.openfoam.com/documentation/](https://www.openfoam.com/documentation/)

## See Also

- [Solver Comparison](SOLVER_COMPARISON.md)
- [microClimateFoam Documentation](microClimateFoam.md)
- [Quick Start Guide](../quick_start.md)

