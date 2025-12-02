# Cloud Deployment Guide

This guide explains how to deploy and run the microClimateFoam project in cloud environments using Docker.

## Overview

The project is configured to run in cloud environments without requiring X11 or display dependencies. All visualization and post-processing can be done headlessly using ParaView's Python API.

## Configuration Files

### `.cursor/environment.json`

This file configures Cursor's cloud agent for cloud execution using manual Dockerfile setup. It specifies:
- Docker build configuration (points to `Dockerfile`)
- Terminal configuration with OpenFOAM environment

**Note**: Cursor manages the workspace and checks out the correct commit automatically. The Dockerfile should NOT copy project files.

### `Dockerfile`

The main Dockerfile used for cloud deployment. It:
- Uses the `openfoam/openfoam8-paraview56` base image
- Sets up system-level dependencies (user/group alignment, workspace setup)
- Sources OpenFOAM in the user's `.bashrc` for automatic loading
- Does NOT copy project files (Cursor manages the workspace)

## Manual Setup with Dockerfile

For Cursor Cloud Agents, you configure the environment using the Dockerfile:

1. **Create/Edit Dockerfile**: Set up system-level dependencies (compiler versions, base OS image, etc.)
2. **Don't COPY project files**: Cursor manages the workspace and checks out the correct commit
3. **Take a snapshot manually**: After configuring, take a snapshot in Cursor
4. **Edit `.cursor/environment.json`**: Configure runtime settings (already done)

The Dockerfile is automatically used by Cursor when building the cloud environment.

## Executing Cases in Cloud

Once inside the Cursor cloud agent environment, all standard commands work:

```bash
# OpenFOAM is automatically sourced from .bashrc in interactive shells
# If needed, manually source: source /opt/openfoam8/etc/bashrc

# Build solvers
./scripts/build_all_solvers.sh

# Run a case
./scripts/run_case.sh --quick-validation -v cases/streetCanyon_CFD

# Generate visualizations (headless, no GUI needed)
./scripts/postprocess/generate_images.sh cases/streetCanyon_CFD 50

# Extract statistics
python scripts/postprocess/extract_stats.py cases/streetCanyon_CFD 50
```

## Key Differences from Local Development

1. **No X11/Display**: All visualization is done headlessly using ParaView's Python API
2. **No Interactive GUI**: ParaView GUI is not available, but all automated scripts work
3. **Network Configuration**: Uses default Docker networking instead of `host` mode
4. **Headless Execution**: All commands can run non-interactively

## Background Agent Configuration

The `.cursor/environment.json` file configures Cursor's background agent for cloud execution. The configuration:

- **Build Configuration**: Specifies the Dockerfile and build context
- **Terminal Configuration**: Provides a pre-configured terminal with OpenFOAM environment sourced

The minimal configuration ensures compatibility with Cursor's background agent while allowing Docker to handle volume mounts and environment setup automatically.

**Note**: Cursor's background agent automatically handles:
- Volume mounts (workspace and build directories)
- Working directory setup
- User permissions
- Environment variable propagation

## Troubleshooting

### Permission Issues

If you encounter permission issues, ensure the USER_UID and USER_GID match your host user:

```bash
docker build \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t microclimatefoam:dev .
```

### OpenFOAM Not Found

If OpenFOAM commands are not found:

1. **Check if OpenFOAM is loaded**: Run `foamVersion` - if it works, OpenFOAM is already loaded from `.bashrc`
2. **If not loaded**: The Dockerfile should have added OpenFOAM sourcing to `.bashrc`. Check:
   ```bash
   grep "openfoam8/etc/bashrc" ~/.bashrc
   ```
3. **Manual source**: If needed, manually source:
   ```bash
   source /opt/openfoam8/etc/bashrc
   ```
4. **Verify path**: If the path doesn't exist, check where OpenFOAM is installed:
   ```bash
   find /opt /usr -name "bashrc" -path "*openfoam*" 2>/dev/null
   ```

### Build Artifacts Not Persisting

Cursor automatically handles volume mounts. The build directory should persist automatically. If issues occur, check that the Dockerfile sets up the workspace correctly.

### Visualization Scripts Failing

All visualization scripts use headless ParaView, so they should work in cloud environments. If they fail, check:
1. ParaView Python is available: `/opt/paraviewopenfoam56/bin/pvpython`
2. Case files exist and are readable
3. Output directory is writable

## CI/CD Integration

The cloud configuration is compatible with CI/CD pipelines. See `.github/workflows/ci.yml` for an example GitHub Actions workflow.

## Next Steps

- Run quick validation tests: `./test_env.sh`
- Run full simulations: `./test_full.sh`
- Generate visualizations: `./scripts/postprocess/generate_images.sh`
- Extract statistics: `python scripts/postprocess/extract_stats.py`

