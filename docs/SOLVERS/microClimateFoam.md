# microClimateFoam Solver Documentation

## Overview

`microClimateFoam` is a custom OpenFOAM solver designed for incompressible flow with thermal transport and Boussinesq buoyancy coupling. It is a lightweight, educational solver ideal for learning OpenFOAM solver development and running simple validation cases.

## Solver Type

- **Category**: Incompressible flow with thermal transport
- **Build System**: Standard OpenFOAM `wmake`
- **Complexity**: Simple, single-region solver
- **Maintainer**: Project-maintained

## Physics Models

### Flow Model
- **Type**: Incompressible flow
- **Method**: PISO (Pressure Implicit with Splitting of Operators)
- **Turbulence**: None (laminar flow only)

### Thermal Model
- **Type**: Temperature transport with Boussinesq buoyancy
- **Equation**: Scalar transport equation for temperature
- **Buoyancy**: Boussinesq approximation integrated into momentum equation

### Governing Equations

**Momentum Equation:**
```
∂U/∂t + ∇·(UU) - ν∇²U = βg(T - T_ref)
```

Where:
- `U` is the velocity vector
- `ν` is the kinematic viscosity
- `β` is the thermal expansion coefficient
- `g` is the gravitational acceleration vector
- `T` is the temperature
- `T_ref` is the reference temperature

**Temperature Transport:**
```
∂T/∂t + ∇·(UT) - α∇²T = 0
```

Where:
- `T` is the temperature
- `α` is the thermal diffusivity

**Pressure-Velocity Coupling:**
- PISO algorithm with configurable number of correctors
- Non-orthogonal correction support

## Fields and Variables

### Primary Fields
- **`U`**: Velocity vector field (m/s)
- **`p`**: Pressure scalar field (m²/s²)
- **`T`**: Temperature scalar field (K)
- **`phi`**: Surface flux field (m³/s)

### Transport Properties
Defined in `constant/transportProperties`:
- **`nu`**: Kinematic viscosity (m²/s)
- **`alpha`**: Thermal diffusivity (m²/s)
- **`rhoRef`**: Reference density (kg/m³)
- **`beta`**: Thermal expansion coefficient (1/K)
- **`TRef`**: Reference temperature (K)
- **`g`**: Gravitational acceleration vector (m/s²)

## Solution Algorithm

1. **Time Loop**: Iterates over time steps
2. **Courant Number**: Calculated for stability monitoring
3. **Momentum Equation**: Solved with Boussinesq buoyancy term
4. **PISO Loop**: Pressure-velocity coupling
   - Configurable number of correctors (default: 2)
   - Non-orthogonal correction support
5. **Temperature Equation**: Solved after momentum-pressure coupling
6. **Field Writing**: Output at specified intervals

## Boundary Conditions

Standard OpenFOAM boundary conditions are supported:
- **Velocity (`U`)**: `fixedValue`, `zeroGradient`, `slip`, `noSlip`, etc.
- **Pressure (`p`)**: `fixedValue`, `zeroGradient`, `totalPressure`, etc.
- **Temperature (`T`)**: `fixedValue`, `zeroGradient`, `mixed`, etc.

## Configuration

### controlDict Settings
- Standard OpenFOAM `controlDict` settings
- Time step control via `deltaT`
- Write control via `writeInterval`

### fvSolution Settings
- **PISO**: Number of correctors and non-orthogonal correctors
- **Relaxation Factors**: Optional relaxation for stability
  - `fields`: Field relaxation (e.g., `p`)
  - `equations`: Equation relaxation (e.g., `U`, `T`)

### fvSchemes Settings
- Standard OpenFOAM discretization schemes
- Recommended: Second-order schemes for accuracy

## Build Instructions

### Prerequisites
- OpenFOAM 8
- Standard OpenFOAM build environment

### Build Steps
```bash
# Source OpenFOAM environment
source /opt/openfoam8/etc/bashrc

# Navigate to solver directory
cd /workspace/src/microClimateFoam

# Build solver
wmake
```

The solver binary will be created at `$FOAM_USER_APPBIN/microClimateFoam`.

## Running Cases

### Basic Usage
```bash
# Using the generic case runner
./scripts/run_case.sh custom_cases/heatedCavity

# Or manually
cd custom_cases/heatedCavity
blockMesh
microClimateFoam
```

### Parallel Execution
```bash
# Using the case runner with parallel support
./scripts/run_case.sh -p 4 custom_cases/heatedCavity

# Or manually
decomposePar
mpirun -np 4 microClimateFoam -parallel
reconstructPar
```

## Available Cases

**⚠️ IMPORTANT: Case Compatibility**

`microClimateFoam` is designed for **single-region cases** in the `custom_cases/` directory. 

**Compatible:**
- `custom_cases/heatedCavity/` - Heated cavity validation case
- Any other cases in `custom_cases/` designed for single-region solvers

**Incompatible:**
- **DO NOT** use with cases in `cases/` directory (tutorial cases)
- Tutorial cases are multi-region and use `p_rgh` instead of `p`
- Tutorial cases require `urbanMicroclimateFoam` solver

### heatedCavity
- **Location**: `custom_cases/heatedCavity/`
- **Description**: Heated cavity validation case
- **Purpose**: Validation and testing
- **Mesh**: Structured hexahedral mesh (blockMesh)
- **Physics**: Natural convection in a heated cavity
- **Solver**: `microClimateFoam` (auto-detected)

## Limitations

1. **Single Region Only**: No multi-region support
2. **No Turbulence**: Laminar flow only
3. **No Advanced Physics**: No HAM, radiation, or vegetation modeling
4. **Incompressible Only**: No compressibility effects
5. **Simple Thermal Model**: Constant thermal properties

## Extending the Solver

The solver is designed to be easily extensible. Key files:
- `microClimateFoam.C`: Main solver loop
- `createFields.H`: Field creation and initialization
- `UEqn.H`: Momentum equation
- `pEqn.H`: Pressure equation
- `TEqn.H`: Temperature equation

To add features:
1. Modify the relevant equation file
2. Update `createFields.H` if new fields are needed
3. Rebuild with `wmake`

## Validation

The solver has been validated against:
- Heated cavity benchmark cases
- Natural convection problems

See `custom_cases/heatedCavity/` for validation case.

## Performance Tips

1. **Time Step**: Use appropriate `deltaT` based on Courant number
2. **Relaxation**: Use relaxation factors for stability if needed
3. **Mesh Quality**: Ensure good mesh quality for accurate results
4. **Parallel Execution**: Use parallel execution for larger cases

## Troubleshooting

### Common Issues

**Solver Diverges:**
- Reduce time step (`deltaT`)
- Add relaxation factors in `fvSolution`
- Check mesh quality
- Verify boundary conditions

**Temperature Not Transporting:**
- Check thermal diffusivity (`alpha`) in `transportProperties`
- Verify temperature boundary conditions
- Check flux field (`phi`) calculation

**Buoyancy Effects Not Visible:**
- Verify `beta` (thermal expansion coefficient) is non-zero
- Check `g` (gravity) vector is correct
- Ensure temperature differences are sufficient

## References

- OpenFOAM User Guide: [https://www.openfoam.com/documentation/](https://www.openfoam.com/documentation/)
- PISO Algorithm: See OpenFOAM documentation on pressure-velocity coupling
- Boussinesq Approximation: Standard CFD textbooks

## See Also

- [Solver Comparison](SOLVER_COMPARISON.md)
- [urbanMicroclimateFoam Documentation](urbanMicroclimateFoam.md)
- [Quick Start Guide](../quick_start.md)

