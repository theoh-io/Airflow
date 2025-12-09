#!/bin/bash
#
# Post-mesh generation steps
# Run this after mesh generation completes
#

set -e

CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CASE_DIR"

echo "=========================================="
echo "Post-Mesh Generation Steps"
echo "=========================================="
echo ""

# Source OpenFOAM if in Docker
if [ -f "/opt/openfoam8/etc/bashrc" ]; then
    source /opt/openfoam8/etc/bashrc
fi

# Step 1: Copy mesh back to region structure
echo "Step 1: Copying mesh to region structure..."
if [ -d "constant/polyMesh" ] && [ -f "constant/polyMesh/faces.gz" ]; then
    echo "  Found refined mesh in constant/polyMesh"
    
    # Backup existing mesh
    if [ -d "constant/air/polyMesh" ] && [ -f "constant/air/polyMesh/points.gz" ]; then
        echo "  Backing up existing mesh..."
        mv constant/air/polyMesh constant/air/polyMesh.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Copy mesh
    echo "  Copying mesh files..."
    mkdir -p constant/air/polyMesh
    cp -r constant/polyMesh/* constant/air/polyMesh/
    echo "✓ Mesh copied"
    
    # Clean up
    echo "  Cleaning up temporary files..."
    rm -rf constant/polyMesh
    rm -f system/fvSchemes system/fvSolution 2>/dev/null || true
    echo "✓ Cleanup complete"
else
    echo "⚠ Warning: Refined mesh not found in constant/polyMesh"
    echo "  Mesh generation may not have completed yet"
    exit 1
fi

# Step 2: Check mesh quality
echo ""
echo "Step 2: Checking mesh quality..."
echo "------------------------------------------------------------"
checkMesh -region air

# Step 3: Show mesh statistics
echo ""
echo "Step 3: Mesh Statistics"
echo "------------------------------------------------------------"
if [ -f "constant/air/polyMesh/points.gz" ]; then
    echo "Mesh files found:"
    ls -lh constant/air/polyMesh/*.gz | awk '{print "  " $9 " - " $5}'
    echo ""
    echo "To view patch names:"
    echo "  cat constant/air/polyMesh/boundary"
fi

echo ""
echo "=========================================="
echo "✓ Post-mesh steps complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review patch names: cat constant/air/polyMesh/boundary"
echo "  2. Update boundary conditions in 0/air/ files"
echo "  3. Run quick validation: ./scripts/run_case.sh --quick-validation -v cases/Vidigal_CFD"






