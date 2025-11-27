# Build and Mesh Caching

This document explains how the build and mesh caching system works to speed up development workflows.

## Overview

The project implements smart caching for:
1. **Solver builds**: Binaries are cached and only rebuilt when source files change
2. **Mesh generation**: Meshes are cached and only regenerated when `blockMeshDict` changes

This eliminates unnecessary rebuilds and mesh generation, making development and testing much faster.

## Solver Build Caching

### How It Works

1. **Build Directory Persistence**: 
   - The `docker-compose.yml` mounts `./build:/home/openfoam/platforms`
   - This persists all OpenFOAM build artifacts (solvers, libraries) across container runs
   - The `build/` directory is automatically created and ignored by git

2. **Smart Build Check**:
   - `scripts/build_all_solvers.sh` includes a `needs_rebuild()` function
   - Checks if binary exists and if source files are newer than binary
   - Only rebuilds when necessary

3. **Benefits**:
   - First build: ~2-5 minutes (compiles everything)
   - Subsequent builds: Instant if nothing changed
   - Only rebuilds when source files (`.C`, `.H`, `Make/files`, etc.) are modified

### Usage

```bash
# First time: builds everything
./scripts/build_all_solvers.sh

# Second time: skips if up to date
./scripts/build_all_solvers.sh
# Output: "✓ urbanMicroclimateFoam is up to date (skipping build)"

# After modifying source: automatically rebuilds
# Edit src/urbanMicroclimateFoam/urbanMicroclimateFoam.C
./scripts/build_all_solvers.sh
# Output: "Source files changed, rebuilding..."
```

### Build Directory Structure

```
build/
└── linux64GccDPInt32Opt/
    ├── bin/
    │   ├── urbanMicroclimateFoam
    │   └── microClimateFoam
    └── lib/
        ├── libsolarLoad.so
        └── ... (other libraries)
```

## Mesh Generation Caching

### How It Works

1. **Mesh Persistence**:
   - Mesh files are stored in `cases/[caseName]/constant/polyMesh/`
   - This directory is on the host (bind-mounted), so meshes persist

2. **Smart Mesh Check**:
   - Scripts check if `constant/polyMesh/points` exists
   - Compare modification time: `blockMeshDict` vs `points`
   - Only regenerate if:
     - Mesh doesn't exist, OR
     - `blockMeshDict` is newer than mesh

3. **Benefits**:
   - First run: Generates mesh (~10-30 seconds)
   - Subsequent runs: Skips if mesh exists and is up to date
   - Only regenerates when `blockMeshDict` changes

### Usage

```bash
# First run: generates mesh
./scripts/run_street_canyon.sh --quick-validation
# Output: "Generating mesh..." → "✓ Mesh ready"

# Second run: skips mesh generation
./scripts/run_street_canyon.sh --quick-validation
# Output: "✓ Mesh already exists and is up to date (skipping generation)"

# After modifying blockMeshDict: automatically regenerates
# Edit cases/streetCanyon_CFD/constant/polyMesh/blockMeshDict
./scripts/run_street_canyon.sh --quick-validation
# Output: "Mesh exists but blockMeshDict is newer, regenerating mesh..."
```

### Scripts with Smart Mesh Checking

- `scripts/run_street_canyon.sh`
- `scripts/run_case.sh`
- `test_env.sh`

All these scripts automatically check for existing meshes before running `blockMesh`.

## Manual Override

If you need to force a rebuild or mesh regeneration:

```bash
# Force solver rebuild (delete build directory)
rm -rf build/
./scripts/build_all_solvers.sh

# Force mesh regeneration (delete mesh)
rm -rf cases/streetCanyon_CFD/constant/polyMesh/
./scripts/run_street_canyon.sh --quick-validation

# Or use --no-mesh to skip mesh entirely
./scripts/run_street_canyon.sh --quick-validation --no-mesh
```

## CI/CD Considerations

In CI environments:
- Build artifacts persist within the same job/container
- Each new CI run starts fresh (no build cache)
- This is expected and acceptable for CI
- The caching primarily benefits local development

## Troubleshooting

### Build artifacts not persisting

**Problem**: Solver needs rebuilding every time

**Solution**: 
1. Check `docker-compose.yml` has the build volume: `./build:/home/openfoam/platforms`
2. Verify `build/` directory exists: `ls -la build/`
3. Check permissions: `ls -la build/linux64GccDPInt32Opt/bin/`

### Mesh not being cached

**Problem**: Mesh regenerates every time

**Solution**:
1. Check mesh exists: `ls -la cases/streetCanyon_CFD/constant/polyMesh/points`
2. Check permissions: Mesh files should be readable
3. Verify `blockMeshDict` exists: `ls -la cases/streetCanyon_CFD/constant/polyMesh/blockMeshDict`

### Build directory too large

**Problem**: `build/` directory is taking up space

**Solution**:
```bash
# Clean build directory (will force full rebuild next time)
rm -rf build/
```

The `build/` directory is already in `.gitignore`, so it won't be committed to git.

