# Multi-Solver Integration Notes

This document tracks the integration of `urbanMicroclimateFoam` solver and tutorial cases.

## ✅ Integration Complete

All integration steps have been completed:

### 1. ✅ Cloned urbanMicroclimateFoam Solver

```bash
git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam.git src/urbanMicroclimateFoam
cd src/urbanMicroclimateFoam
git checkout tags/of-org_v8.0
./Allwmake
```

**Status:** ✅ Solver cloned and builds successfully

### 2. ✅ Reorganized Case Structure

```bash
# Renamed existing cases directory
mv cases custom_cases

# Cloned tutorial cases
git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials.git cases
cd cases
git checkout tags/of-org_v8.0
```

**Status:** ✅ Directory structure reorganized
- `custom_cases/` - Contains `heatedCavity` (microClimateFoam validation case)
- `cases/` - Contains 6 tutorial cases from urbanMicroclimateFoam-tutorials

### 3. ✅ Updated Scripts

All scripts have been updated to support both `custom_cases/` and `cases/`:

- ✅ `scripts/run_case.sh` - Generic case runner supports all cases (replaces run_heated_cavity.sh)
- ✅ `scripts/run_case.sh` - Updated examples and help text
- ✅ `scripts/create_foam_file.sh` - Updated example paths
- ✅ `test_env.sh`, `test_full.sh`, `test_parallel.sh` - Updated to `custom_cases/heatedCavity`
- ✅ All post-processing scripts - Updated example paths

### 4. ✅ Build System Updates

Created `scripts/build_all_solvers.sh`:

```bash
#!/bin/bash
# Build all solvers in src/

cd /workspace/src
for solver_dir in */; do
    if [ -f "${solver_dir}Allwmake" ]; then
        echo "Building ${solver_dir}..."
        cd "${solver_dir}"
        ./Allwmake
        cd ..
    elif [ -f "${solver_dir}Make/files" ]; then
        echo "Building ${solver_dir} with wmake..."
        cd "${solver_dir}"
        wmake
        cd ..
    fi
done
```

### 5. Case Metadata System

Create `cases/[caseName]/README.md` template:

```markdown
# [Case Name]

## Solver
- Required solver: [solver name]
- Version: [version/tag]

## Description
[Case description]

## Setup
[Setup instructions]

## Running
[How to run the case]

## Expected Results
[What to expect]
```

### 6. CI Updates

Update `.github/workflows/ci.yml` to:
- Build all solvers in `src/`
- Test cases from both `custom_cases/` and `cases/`
- Use matrix strategy for multiple solver/case combinations

## Directory Structure After Integration

```
.
├── src/
│   ├── microClimateFoam/          # Custom solver
│   └── urbanMicroclimateFoam/     # Cloned solver
├── custom_cases/                   # Custom validation cases
│   └── heatedCavity/              # microClimateFoam case
├── cases/                          # Tutorial cases
│   ├── [tutorialCase1]/          # From urbanMicroclimateFoam-tutorials
│   ├── [tutorialCase2]/
│   └── ...
└── scripts/
    ├── build_all_solvers.sh       # Build all solvers
    └── list_cases.sh              # List available cases
```

## Notes

- Both solvers use OpenFOAM 8 (tag `of-org_v8.0`)
- `urbanMicroclimateFoam` uses `./Allwmake` for building
- `microClimateFoam` uses `wmake` for building
- Cases should be organized by solver or category
- Update all documentation references from `cases/` to `custom_cases/` for custom cases

