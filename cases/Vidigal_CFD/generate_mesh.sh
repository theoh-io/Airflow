#!/bin/bash
#
# Generate mesh for Vidigal_CFD case
# This script handles the multi-region to single-region conversion for snappyHexMesh
#

set -e

CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CASE_DIR/../.." && pwd)"
cd "$CASE_DIR"

echo "=========================================="
echo "Vidigal_CFD Mesh Generation"
echo "=========================================="
echo ""

# Source OpenFOAM if in Docker
if [ -f "/opt/openfoam8/etc/bashrc" ]; then
    source /opt/openfoam8/etc/bashrc
fi

# Step 1: Generate background mesh
echo "Step 1/5: Generating background mesh with blockMesh..."
echo "------------------------------------------------------------"
blockMesh -region air || {
    echo "✗ blockMesh FAILED"
    exit 1
}
echo "✓ Background mesh generated"
echo ""

# Step 2: Prepare temporary single-region structure for snappyHexMesh
echo "Step 2/5: Preparing mesh for snappyHexMesh (multi-region to single-region)..."
echo "------------------------------------------------------------"

# Create temporary polyMesh directory in case root
if [ -d "constant/polyMesh" ]; then
    echo "  Removing old temporary mesh..."
    rm -rf constant/polyMesh
fi

echo "  Copying mesh from constant/air/polyMesh to constant/polyMesh..."
mkdir -p constant/polyMesh
cp -r constant/air/polyMesh/* constant/polyMesh/

# Copy system files needed for snappyHexMesh to case root
echo "  Setting up system files..."
# snappyHexMeshDict is already in system/

echo "✓ Mesh prepared for snappyHexMesh"
echo ""

# Step 3: Extract features (optional - skip if tool not available)
echo "Step 3/5: Feature extraction (skipped - using implicit feature detection)..."
echo "------------------------------------------------------------"
echo "  Using implicit feature detection in snappyHexMesh"
echo ""

# Step 4: Run snappyHexMesh
echo "Step 4/5: Refining and snapping mesh to STL geometry..."
echo "------------------------------------------------------------"
echo "  This may take 30 minutes to several hours..."
echo "  Progress will be shown below..."
echo ""

snappyHexMesh -dict system/snappyHexMeshDict -overwrite || {
    echo "✗ snappyHexMesh FAILED"
    echo "  Restoring original mesh..."
    rm -rf constant/polyMesh
    exit 1
}

echo "✓ Mesh refined and snapped"
echo ""

# Step 5: Copy mesh back to region structure
echo "Step 5/5: Copying refined mesh back to region structure..."
echo "------------------------------------------------------------"
cp -r constant/polyMesh/* constant/air/polyMesh/
rm -rf constant/polyMesh
echo "✓ Mesh copied to constant/air/polyMesh"
echo ""

# Step 6: Check mesh quality
echo "Step 6/6: Checking mesh quality..."
echo "------------------------------------------------------------"
checkMesh -region air || {
    echo "⚠ checkMesh found issues (see output above)"
}
echo ""

echo "=========================================="
echo "✓ Mesh generation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Check patch names: cat constant/air/polyMesh/boundary"
echo "  2. Update boundary conditions in 0/air/ files"
echo "  3. Run solver: ./Allrun"
