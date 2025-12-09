#!/bin/bash
#
# Complete mesh generation workflow
# This script finishes the mesh generation process after snappyHexMesh completes
#

set -e

CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CASE_DIR"

echo "=========================================="
echo "Completing Vidigal_CFD Mesh Generation"
echo "=========================================="
echo ""

# Source OpenFOAM if in Docker
if [ -f "/opt/openfoam8/etc/bashrc" ]; then
    source /opt/openfoam8/etc/bashrc
fi

# Check if mesh generation completed
if [ ! -d "constant/polyMesh" ]; then
    echo "⚠ Warning: constant/polyMesh directory not found"
    echo "  Mesh generation may not have started or failed"
    exit 1
fi

# Check if snappyHexMesh completed by looking for final mesh files
if [ ! -f "constant/polyMesh/faces.gz" ] || [ ! -f "constant/polyMesh/boundary" ]; then
    echo "⚠ Warning: Mesh files not found in constant/polyMesh"
    echo "  snappyHexMesh may still be running or failed"
    exit 1
fi

echo "Step 1: Copying refined mesh back to region structure..."
echo "------------------------------------------------------------"

# Backup existing mesh
if [ -d "constant/air/polyMesh" ] && [ -f "constant/air/polyMesh/points.gz" ]; then
    echo "  Backing up existing mesh..."
    mv constant/air/polyMesh constant/air/polyMesh.backup
fi

# Create region directory
mkdir -p constant/air/polyMesh

# Copy refined mesh
echo "  Copying mesh files..."
cp -r constant/polyMesh/* constant/air/polyMesh/
echo "✓ Mesh copied to constant/air/polyMesh"

# Clean up temporary files
echo ""
echo "Step 2: Cleaning up temporary files..."
echo "------------------------------------------------------------"
rm -rf constant/polyMesh
rm -f system/fvSchemes system/fvSolution 2>/dev/null || true
echo "✓ Temporary files removed"

echo ""
echo "Step 3: Checking mesh quality..."
echo "------------------------------------------------------------"
checkMesh -region air || {
    echo "⚠ Warning: checkMesh found issues (see output above)"
    echo "  Mesh may still be usable, but review warnings"
}

echo ""
echo "=========================================="
echo "✓ Mesh generation workflow complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review patch names: cat constant/air/polyMesh/boundary"
echo "  2. Update boundary conditions in 0/air/ files"
echo "  3. Run quick validation: ./scripts/run_case.sh --quick-validation -v cases/Vidigal_CFD"






