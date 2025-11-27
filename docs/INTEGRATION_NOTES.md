# Multi-Solver Integration Notes

This document tracks the integration of `urbanMicroclimateFoam` solver and tutorial cases.

## Integration Steps

### 1. Clone urbanMicroclimateFoam Solver

```bash
cd /workspace
git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam.git src/urbanMicroclimateFoam
cd src/urbanMicroclimateFoam
git checkout tags/of-org_v8.0
./Allwmake
```

### 2. Reorganize Case Structure

```bash
# Rename existing cases directory
mv cases custom_cases

# Clone tutorial cases
git clone https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials.git cases
cd cases
git checkout tags/of-org_v8.0
```

### 3. Update Scripts

After integration, update the following scripts to support both `custom_cases/` and `cases/`:

- `scripts/run_heated_cavity.sh` - Update path to `custom_cases/heatedCavity`
- `scripts/run_case.sh` - Already supports custom paths, but update examples
- `scripts/create_foam_file.sh` - Update example paths
- `test_env.sh`, `test_full.sh` - Update case paths to `custom_cases/heatedCavity`

### 4. Build System Updates

Create `scripts/build_all_solvers.sh`:

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

