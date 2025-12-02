#!/usr/bin/env bash
#
# Get STL geometry bounds using OpenFOAM tools
# Usage: ./scripts/get_stl_bounds.sh <path-to-stl-file>
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path-to-stl-file>"
    echo "Example: $0 cases/Vidigal_CFD/constant/triSurface/vidigal.stl"
    exit 1
fi

STL_FILE="$1"

if [[ ! -f "$STL_FILE" ]]; then
    echo "Error: STL file not found: $STL_FILE"
    exit 1
fi

echo "Inspecting STL geometry: $STL_FILE"
echo "=========================================="
echo ""

# Check if we're running inside Docker or have direct access
if command -v checkGeometry &> /dev/null; then
    # Direct OpenFOAM access
    source /opt/openfoam8/etc/bashrc 2>/dev/null || true
    checkGeometry "$STL_FILE"
elif docker compose ps | grep -q "dev.*Up" 2>/dev/null; then
    # Running via Docker Compose
    echo "Running checkGeometry in Docker container..."
    docker compose exec -T dev bash -c "source /opt/openfoam8/etc/bashrc && checkGeometry $STL_FILE" 2>&1
else
    echo "Error: OpenFOAM not available and Docker container is not running."
    echo "Please either:"
    echo "  1. Start the container: docker compose up -d"
    echo "  2. Or source OpenFOAM: source /opt/openfoam8/etc/bashrc"
    exit 1
fi

