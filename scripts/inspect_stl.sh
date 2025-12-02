#!/usr/bin/env bash
#
# Inspect STL geometry file and provide key information
# Usage: ./scripts/inspect_stl.sh <path-to-stl-file>
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

echo "=========================================="
echo "STL Geometry Inspection"
echo "=========================================="
echo ""
echo "File: $STL_FILE"
echo ""

# Check if we're in Docker or have OpenFOAM available
if command -v checkGeometry &> /dev/null; then
    echo "Running OpenFOAM checkGeometry..."
    echo "----------------------------------------"
    checkGeometry "$STL_FILE" 2>&1 || echo "Note: checkGeometry may require OpenFOAM environment"
    echo ""
fi

# Basic file info
echo "File Information:"
echo "----------------------------------------"
file "$STL_FILE"
ls -lh "$STL_FILE"
echo ""

# Try to get basic stats from STL (for ASCII STL)
if grep -q "solid" "$STL_FILE" 2>/dev/null; then
    echo "STL Format: ASCII"
    echo ""
    echo "Triangle Count:"
    grep -c "facet normal" "$STL_FILE" 2>/dev/null || echo "  (Could not count triangles)"
    echo ""
else
    echo "STL Format: Binary"
    echo "  (Use OpenFOAM checkGeometry for detailed analysis)"
    echo ""
fi

echo "=========================================="
echo ""
echo "For detailed geometry analysis, use:"
echo "  checkGeometry $STL_FILE"
echo ""
echo "Or visualize in ParaView:"
echo "  paraview"
echo "  Then: File → Open → $STL_FILE"
echo ""

