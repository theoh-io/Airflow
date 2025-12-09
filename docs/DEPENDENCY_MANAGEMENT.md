# Dependency Management

This document explains how external dependencies are managed in this project, particularly the `urbanMicroclimateFoam` solver.

## Current Approach: Direct Inclusion

Currently, the `urbanMicroclimateFoam` solver is included directly in the repository at `src/urbanMicroclimateFoam/`. This means:

- ✅ **Simple workflow**: No special git commands needed to clone or update
- ✅ **Easy for team members**: Standard `git clone` works out of the box
- ✅ **CI/CD simplicity**: No submodule initialization required
- ✅ **Full control**: Can modify the solver code directly if needed

### Source

The solver was cloned from:
- **Repository**: [OpenFOAM-BuildingPhysics/urbanMicroclimateFoam](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam)
- **Version/Tag**: `of-org_v8.0` (OpenFOAM 8 compatible)

### Current Status

The solver is tracked as part of this repository's history. When cloning this repository, you get the solver code directly without any additional steps.

## Future Recommendation: Git Submodule

**⚠️ Best Practice for Future**: As the project matures, we recommend migrating `urbanMicroclimateFoam` to a git submodule. This would provide:

- 🔄 **Easier upstream updates**: Track updates from the original repository
- 📦 **Clearer separation**: Explicitly shows it's an external dependency
- 🎯 **Version pinning**: Lock to specific commits/branches from upstream
- 📊 **Smaller repo size**: Avoids duplicating external code history

### Migration Path (Future)

If/when we migrate to submodules, the process would be:

1. **Remove the current directory** (preserving history):
   ```bash
   git rm -r --cached src/urbanMicroclimateFoam
   ```

2. **Add as submodule**:
   ```bash
   git submodule add https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam.git src/urbanMicroclimateFoam
   cd src/urbanMicroclimateFoam
   git checkout tags/of-org_v8.0
   cd ../..
   git commit -m "Migrate urbanMicroclimateFoam to git submodule"
   ```

3. **Update CI/CD** to handle submodules:
   ```yaml
   - uses: actions/checkout@v3
     with:
       submodules: recursive
   ```

4. **Update documentation** to include submodule initialization:
   ```bash
   git clone --recurse-submodules <repo-url>
   # Or if already cloned:
   git submodule update --init --recursive
   ```

### Why Not Now?

The current direct inclusion approach is maintained because:
- The project is in active development
- Simplicity is prioritized during the initial integration phase
- The solver code may need custom modifications
- Team familiarity with submodules may vary

## Other Dependencies

### Tutorial Cases

The tutorial cases in `cases/` were originally cloned from [OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials](https://github.com/OpenFOAM-BuildingPhysics/urbanMicroclimateFoam-tutorials) (tag `of-org_v8.0`), but are now directly included in this repository.

**Current State:**
- ✅ **Tutorial cases included**: All 6 tutorial cases from the upstream repository are tracked
- ✅ **Custom case added**: `cases/Vidigal_CFD/` is a custom case created for this project and should be kept in the repository
- ✅ **Configuration files tracked**: Case setup files, boundary conditions, and mesh configurations are version controlled
- ❌ **Results excluded**: Simulation results (time directories, logs, meshes, visualization images) are excluded via `.gitignore`

**What's Tracked:**
- Case configuration files (`system/`, `constant/` configs, `0/` initial conditions)
- Custom scripts and documentation
- Custom cases like `Vidigal_CFD/`
- **STL geometry files**: Tracked using Git LFS (see [Large File Handling](#large-file-handling) below)

**What's Excluded:**
- Simulation results (`[0-9]*/` time directories)
- Generated meshes (`constant/*/polyMesh/`)
- Log files and solver output
- Visualization images (`images/` directories)
- Post-processing results (`postProcessing/`)

**Future Consideration:**
Similar to the solver, tutorial cases could be migrated to a git submodule in the future. However, since we've added custom cases (like `Vidigal_CFD`) and may modify tutorial cases, direct inclusion is currently more practical.

### Custom Solver

The `microClimateFoam` solver in `src/microClimateFoam/` is a custom solver developed for this project and should remain directly in the repository.

## Large File Handling

### STL Geometry Files

STL (Stereolithography) files are 3D geometry files used in OpenFOAM cases for defining complex geometries. These files can range from ~500KB to several MB.

**Current Approach: Git LFS**

All STL files (`.stl` and `.STL`) are tracked using [Git LFS](https://git-lfs.github.com/) to ensure efficient repository management:

- ✅ **Efficient storage**: Large binary files are stored separately, keeping the main repository lightweight
- ✅ **Faster clones**: Only LFS pointer files are downloaded initially; actual files are fetched on demand
- ✅ **Version control**: Full history is maintained without bloating the repository

**Configuration:**
- `.gitattributes` file configures Git LFS for `*.stl` and `*.STL` files
- Git LFS must be installed on systems cloning the repository
- Files are automatically handled by Git LFS when added to the repository

**For Contributors:**
```bash
# Ensure Git LFS is installed
git lfs install

# Clone with LFS files (automatic with standard clone)
git clone <repo-url>

# If LFS files weren't downloaded, fetch them:
git lfs pull
```

**File Sizes:**
Current STL files in the repository range from ~500KB to ~1MB. All are managed via Git LFS regardless of size to maintain consistency and prepare for potentially larger files in the future.

**Note:** If you need to add very large STL files (>10MB), ensure Git LFS is properly configured and that your Git hosting service (GitHub, GitLab, etc.) supports Git LFS with sufficient quota.

## Summary

- **Current**: Direct inclusion for simplicity and ease of use
  - Solver: `src/urbanMicroclimateFoam/` (cloned from upstream)
  - Tutorial cases: `cases/` (cloned from upstream, includes custom `Vidigal_CFD` case)
- **Future**: Consider migrating to git submodules for better dependency management
  - Solver and tutorial cases could become submodules if upstream tracking becomes important
  - Custom cases (like `Vidigal_CFD`) should remain directly in the repo
- **Custom code**: Always keep custom solvers and custom cases directly in the repo
- **Generated files**: Simulation results, meshes, and visualizations are excluded via `.gitignore`

This approach balances current development needs with future maintainability best practices.

