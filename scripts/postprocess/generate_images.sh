#!/usr/bin/env bash
#
# Wrapper script to run generate_images.py with pvpython
#
# Usage:
#   ./scripts/postprocess/generate_images.sh <case-directory> [time-directory] [options]
#
# Example:
#   ./scripts/postprocess/generate_images.sh cases/heatedCavity 200
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Check if running in Docker or need to use docker compose
if [ -f "/opt/paraviewopenfoam56/bin/pvpython" ]; then
    # Running inside container
    cd "$REPO_ROOT"
    /opt/paraviewopenfoam56/bin/pvpython "${SCRIPT_DIR}/generate_images.py" "$@"
elif command -v pvpython &> /dev/null; then
    # pvpython in PATH
    cd "$REPO_ROOT"
    pvpython "${SCRIPT_DIR}/generate_images.py" "$@"
else
    # Need to run in Docker
    echo "Running in Docker container..."
    docker compose run --rm dev bash -c "
        cd /workspace
        /opt/paraviewopenfoam56/bin/pvpython scripts/postprocess/generate_images.py $*
    "
fi

