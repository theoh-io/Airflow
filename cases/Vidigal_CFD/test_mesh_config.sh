#!/bin/bash
#
# Test script to validate mesh configuration
# This tests configuration files without running full mesh generation
#

set -e

CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CASE_DIR"

echo "=========================================="
echo "Vidigal_CFD Mesh Configuration Test"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Test 1: Check STL file exists
echo "Test 1: Checking STL file..."
if [ -f "constant/triSurface/vidigal.stl" ]; then
    SIZE=$(stat -c%s "constant/triSurface/vidigal.stl" 2>/dev/null || stat -f%z "constant/triSurface/vidigal.stl" 2>/dev/null)
    echo "  ✓ STL file found (size: $SIZE bytes)"
else
    echo "  ✗ ERROR: STL file not found!"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 2: Check blockMeshDict exists and has correct structure
echo "Test 2: Checking blockMeshDict..."
if [ -f "constant/air/polyMesh/blockMeshDict" ]; then
    echo "  ✓ blockMeshDict found"
    
    # Check for key sections
    if grep -q "vertices" constant/air/polyMesh/blockMeshDict; then
        VERTEX_COUNT=$(grep -c "^-.*$" constant/air/polyMesh/blockMeshDict || echo "0")
        echo "  ✓ Vertices section found"
    else
        echo "  ✗ ERROR: Vertices section missing!"
        ERRORS=$((ERRORS + 1))
    fi
    
    if grep -q "^blocks" constant/air/polyMesh/blockMeshDict; then
        echo "  ✓ Blocks section found"
    else
        echo "  ✗ ERROR: Blocks section missing!"
        ERRORS=$((ERRORS + 1))
    fi
    
    if grep -q "^boundary" constant/air/polyMesh/blockMeshDict; then
        echo "  ✓ Boundary section found"
    else
        echo "  ✗ ERROR: Boundary section missing!"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ✗ ERROR: blockMeshDict not found!"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 3: Check snappyHexMeshDict
echo "Test 3: Checking snappyHexMeshDict..."
if [ -f "system/snappyHexMeshDict" ]; then
    echo "  ✓ snappyHexMeshDict found"
    
    if grep -q "geometry" system/snappyHexMeshDict; then
        echo "  ✓ Geometry section found"
        
        # Check if STL file path is correct
        if grep -q "constant/triSurface/vidigal.stl" system/snappyHexMeshDict; then
            echo "  ✓ STL file path correctly referenced"
        else
            echo "  ⚠ WARNING: STL file path may be incorrect"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "  ✗ ERROR: Geometry section missing!"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ✗ ERROR: snappyHexMeshDict not found!"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 4: Check surfaceFeatureExtractDict
echo "Test 4: Checking surfaceFeatureExtractDict..."
if [ -f "system/surfaceFeatureExtractDict" ]; then
    echo "  ✓ surfaceFeatureExtractDict found"
else
    echo "  ✗ ERROR: surfaceFeatureExtractDict not found!"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 5: Check Allrun script
echo "Test 5: Checking Allrun script..."
if [ -f "Allrun" ] && [ -x "Allrun" ]; then
    echo "  ✓ Allrun script found and executable"
    
    # Check if it includes the STL workflow
    if grep -q "snappyHexMesh" Allrun; then
        echo "  ✓ snappyHexMesh command found in Allrun"
    else
        echo "  ⚠ WARNING: snappyHexMesh not found in Allrun"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "  ✗ ERROR: Allrun script not found or not executable!"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 6: Check regionProperties
echo "Test 6: Checking regionProperties..."
if [ -f "constant/regionProperties" ]; then
    echo "  ✓ regionProperties found"
    
    if grep -q "air" constant/regionProperties; then
        echo "  ✓ Air region configured"
    else
        echo "  ⚠ WARNING: Air region not found in regionProperties"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "  ✗ ERROR: regionProperties not found!"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✓ All critical checks passed!"
    if [ $WARNINGS -gt 0 ]; then
        echo "  (with $WARNINGS warning(s))"
    fi
    echo ""
    echo "Configuration appears ready for mesh generation."
    echo "Next step: Test mesh generation (blockMesh, surfaceFeatureExtract, snappyHexMesh)"
    exit 0
else
    echo "✗ Found $ERRORS error(s) and $WARNINGS warning(s)"
    echo ""
    echo "Please fix the errors before proceeding."
    exit 1
fi








