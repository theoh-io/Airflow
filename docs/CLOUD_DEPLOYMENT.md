# Cloud Deployment Guide

This guide explains how to deploy and run the microClimateFoam project in cloud environments using Docker.

## Overview

The project is configured to run in cloud environments without requiring X11 or display dependencies. All visualization and post-processing can be done headlessly using ParaView's Python API.

## Configuration Files

### `.cursor/environment.json`

This file configures Cursor's background agent for cloud execution. It specifies:
- Docker build configuration
- Volume mounts for workspace and build artifacts
- Working directory and user settings

### `Dockerfile.cloud`

A cloud-optimized Dockerfile that:
- Removes X11 dependencies
- Includes a cloud entrypoint script that automatically sources OpenFOAM
- Optimized for non-interactive execution

### `docker-compose.cloud.yml`

Cloud-optimized Docker Compose configuration that:
- Removes X11 forwarding and display dependencies
- Removes `network_mode: host` for better cloud compatibility
- Maintains all necessary volume mounts

## Building for Cloud

### Option 1: Use Standard Dockerfile (Recommended)

The standard `Dockerfile` already works for cloud deployment:

```bash
docker build \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t microclimatefoam:dev .
```

### Option 2: Use Cloud-Optimized Dockerfile

```bash
docker build \
  -f Dockerfile.cloud \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t microclimatefoam:dev .
```

## Running in Cloud

### Using Docker Compose (Cloud)

```bash
# Use cloud-optimized compose file
docker compose -f docker-compose.cloud.yml up -d
docker compose -f docker-compose.cloud.yml exec dev bash
```

### Using Docker Directly

```bash
docker run --rm -it \
  -v $(pwd):/workspace \
  -v $(pwd)/build:/home/openfoam/platforms \
  -w /workspace \
  microclimatefoam:dev \
  bash -c "source /opt/openfoam8/etc/bashrc && bash"
```

## Executing Cases in Cloud

Once inside the container, all standard commands work:

```bash
# Source OpenFOAM (already done if using cloud entrypoint)
source /opt/openfoam8/etc/bashrc

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

If OpenFOAM commands are not found, ensure you source the environment:

```bash
source /opt/openfoam8/etc/bashrc
```

This is automatically done in the cloud entrypoint script.

### Build Artifacts Not Persisting

Ensure the build volume is properly mounted:

```yaml
volumes:
  - ./build:/home/openfoam/platforms
```

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

