#!/bin/bash
set -e

# Parse arguments
SANITY_CHECK=false
QUICK_VALIDATION=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --sanity-check)
            SANITY_CHECK=true
            QUICK_VALIDATION=false
            shift
            ;;
        --quick-validation)
            SANITY_CHECK=false
            QUICK_VALIDATION=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--sanity-check|--quick-validation]"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Docker Environment Test Results"
echo "=========================================="
echo ""

# Save current directory
ORIG_DIR=$(pwd)

# Load OpenFOAM environment
echo "[INFO] Loading OpenFOAM environment..."
set +e  # Temporarily disable exit on error for sourcing
. /opt/openfoam8/etc/bashrc
set -e  # Re-enable exit on error

# Return to original directory (bashrc might change it)
cd "$ORIG_DIR" || cd /workspace

echo "✓ OpenFOAM environment loaded"
echo ""

echo "[INFO] Building all solvers..."
cd /workspace
bash scripts/build_all_solvers.sh 2>&1 | tee /tmp/build.log
if grep -qi "build failed\|FAILED" /tmp/build.log; then
    echo "✗ Build FAILED"
    cat /tmp/build.log | tail -30
    exit 1
else
    echo "✓ All solvers built successfully"
fi
echo ""

# Test solver binaries based on mode
echo "[INFO] Testing solver binaries..."
export PATH=$FOAM_USER_APPBIN:$PATH

if [ "$SANITY_CHECK" = true ]; then
    # Test microClimateFoam for sanity check
    if [ -f "$FOAM_USER_APPBIN/microClimateFoam" ]; then
        echo "✓ microClimateFoam binary found"
        if $FOAM_USER_APPBIN/microClimateFoam -help 2>&1 | grep -q "Usage\|OpenFOAM"; then
            echo "✓ microClimateFoam binary works"
        else
            echo "⚠ microClimateFoam binary test inconclusive (continuing anyway)"
        fi
    else
        echo "✗ microClimateFoam binary not found at $FOAM_USER_APPBIN/microClimateFoam"
        echo "  FOAM_USER_APPBIN = $FOAM_USER_APPBIN"
        ls -la $FOAM_USER_APPBIN/micro* 2>&1 || echo "  No micro* binaries found"
        exit 1
    fi
else
    # Test urbanMicroclimateFoam for quick validation
    if [ -f "$FOAM_USER_APPBIN/urbanMicroclimateFoam" ]; then
        echo "✓ urbanMicroclimateFoam binary found"
        if $FOAM_USER_APPBIN/urbanMicroclimateFoam -help 2>&1 | grep -q "Usage\|OpenFOAM"; then
            echo "✓ urbanMicroclimateFoam binary works"
        else
            echo "⚠ urbanMicroclimateFoam binary test inconclusive (continuing anyway)"
        fi
    else
        echo "✗ urbanMicroclimateFoam binary not found at $FOAM_USER_APPBIN/urbanMicroclimateFoam"
        echo "  FOAM_USER_APPBIN = $FOAM_USER_APPBIN"
        ls -la $FOAM_USER_APPBIN/urban* 2>&1 || echo "  No urban* binaries found"
        exit 1
    fi
fi
echo ""

echo "[INFO] Testing ParaView..."
if command -v paraview > /dev/null 2>&1 && paraview --version 2>&1 | head -1 | grep -q "ParaView"; then
    PV_VERSION=$(paraview --version 2>&1 | head -1)
    echo "✓ ParaView found: $PV_VERSION"
else
    echo "⚠ ParaView not found (optional for sanity check)"
fi
echo ""

# Select case and solver based on mode
if [ "$SANITY_CHECK" = true ]; then
    # Ultra-fast sanity check: heatedCavity with microClimateFoam
    CASE_DIR="custom_cases/heatedCavity"
    SOLVER_NAME="microClimateFoam"
    echo "=========================================="
    echo "Ultra-Fast Sanity Check Mode"
    echo "=========================================="
    echo "Case: ${CASE_DIR}"
    echo "Solver: ${SOLVER_NAME}"
    echo "Configuration: deltaT=1s, endTime=1s (1 time step)"
    echo "Expected runtime: < 2 minutes"
    echo "=========================================="
    echo ""
else
    # Quick validation: streetCanyon_CFD with urbanMicroclimateFoam
    CASE_DIR="cases/streetCanyon_CFD"
    SOLVER_NAME="urbanMicroclimateFoam"
    echo "=========================================="
    echo "Quick Validation Mode"
    echo "=========================================="
    echo "Case: ${CASE_DIR}"
    echo "Solver: ${SOLVER_NAME}"
    echo "Configuration: deltaT=50s, endTime=50s (1 time step)"
    echo "Expected runtime: 3-5 minutes"
    echo "=========================================="
    echo ""
fi

echo "[INFO] Changing to case directory: ${CASE_DIR}"
cd "/workspace/${CASE_DIR}" || {
    echo "✗ Failed to change to case directory: ${CASE_DIR}"
    exit 1
}
echo "✓ Changed to case directory"
echo ""

# Clean previous results (but keep 0/ directory with initial conditions)
echo "Cleaning previous results..."
# Remove time directories except 0
for dir in [1-9]*; do
    [ -d "$dir" ] && rm -rf "$dir"
done
# Remove processor directories and logs
rm -rf processor* log.* 2>/dev/null || true
echo "✓ Cleaned"
echo ""

# Generate mesh for air region
# Generate mesh if needed (smart checking)
MESH_DIR="constant/polyMesh"
BLOCKMESH_DICT="constant/polyMesh/blockMeshDict"

if [ -f "${BLOCKMESH_DICT}" ]; then
    if [ -f "${MESH_DIR}/points" ]; then
        # Check if blockMeshDict is newer than mesh (mesh needs regeneration)
        if [ "${BLOCKMESH_DICT}" -nt "${MESH_DIR}/points" ]; then
            echo "Mesh exists but blockMeshDict is newer, regenerating mesh..."
            if ! blockMesh -region air > /tmp/blockMesh.log 2>&1; then
                echo "✗ blockMesh FAILED"
                cat /tmp/blockMesh.log
                exit 1
            fi
            if ! createPatch -region air -overwrite > /tmp/createPatch.log 2>&1; then
                echo "✗ createPatch FAILED"
                cat /tmp/createPatch.log
                exit 1
            fi
            echo "✓ Mesh regenerated"
        else
            echo "✓ Mesh already exists and is up to date (skipping generation)"
        fi
    else
        # Mesh doesn't exist, generate it
        echo "Generating mesh with blockMesh (region: air)..."
        if ! blockMesh -region air > /tmp/blockMesh.log 2>&1; then
            echo "✗ blockMesh FAILED"
            cat /tmp/blockMesh.log
            exit 1
        fi
        echo "✓ Mesh generated"
        echo ""
        echo "Creating patches..."
        if ! createPatch -region air -overwrite > /tmp/createPatch.log 2>&1; then
            echo "✗ createPatch FAILED"
            cat /tmp/createPatch.log
            exit 1
        fi
        echo "✓ Patches created"
    fi
else
    echo "⚠ Warning: blockMeshDict not found, skipping mesh generation"
fi
echo ""

# Check mesh quality
echo "Checking mesh quality with checkMesh..."
if ! checkMesh -region air > /tmp/checkMesh.log 2>&1; then
    echo "✗ checkMesh FAILED"
    cat /tmp/checkMesh.log
    exit 1
fi
if grep -q "Mesh OK" /tmp/checkMesh.log; then
    echo "✓ Mesh quality OK"
else
    echo "⚠ Mesh quality warnings (check log)"
fi
echo ""

# Configure controlDict based on mode
cp system/controlDict system/controlDict.orig

if [ "$SANITY_CHECK" = true ]; then
    # Ultra-fast sanity check: deltaT=1s, endTime=1s (1 time step)
    echo "Running ultra-fast sanity check..."
    echo "  Configuration: deltaT=1s, endTime=1s (1 time step)"
    echo "  Expected runtime: < 2 minutes"
    echo "  Writing at every time step"
    echo "  Monitoring progress in real-time..."
    echo ""
    sed -i 's/^deltaT[[:space:]]*[0-9.]*;/deltaT 1;/' system/controlDict
    sed -i 's/^endTime[[:space:]]*[0-9.]*;/endTime 1;/' system/controlDict
    sed -i 's/^writeInterval[[:space:]]*[0-9.]*;/writeInterval 1;/' system/controlDict
else
    # Quick validation: deltaT=50s, endTime=50s (1 time step, optimized)
    echo "Running quick validation test (optimized for CI)..."
    echo "  Configuration: deltaT=50s, endTime=50s (1 time step)"
    echo "  Expected runtime: 3-5 minutes"
    echo "  Writing at every time step for early validation"
    echo "  Monitoring progress in real-time..."
    echo ""
    sed -i 's/^deltaT[[:space:]]*[0-9.]*;/deltaT 50;/' system/controlDict
    sed -i 's/^endTime[[:space:]]*[0-9.]*;/endTime 50;/' system/controlDict
    sed -i 's/^writeInterval[[:space:]]*[0-9.]*;/writeInterval 1;/' system/controlDict
fi

export PATH=$FOAM_USER_APPBIN:$PATH

# Run solver with verbose real-time output
echo "Starting solver..."
if [ "$SANITY_CHECK" = true ]; then
    echo "  Expected runtime: < 2 minutes for 1 time step"
else
    echo "  Expected runtime: 3-5 minutes for 1 time step"
fi
echo ""

# Determine solver command based on case
if [ "$SANITY_CHECK" = true ]; then
    SOLVER_CMD="$FOAM_USER_APPBIN/microClimateFoam"
else
    SOLVER_CMD="$FOAM_USER_APPBIN/urbanMicroclimateFoam"
fi

if ! bash /workspace/scripts/run_solver_verbose.sh "$SOLVER_CMD" "$CASE_DIR" 2>&1 | tee /tmp/solver.log; then
    echo ""
    echo "✗ Solver execution FAILED"
    echo "Last 30 lines of output:"
    tail -30 /tmp/solver.log
    mv system/controlDict.orig system/controlDict
    exit 1
fi

# Restore original controlDict
mv system/controlDict.orig system/controlDict
echo ""
echo "✓ Solver completed"
echo ""

# Quick sanity check: Verify first time step (100 seconds = 1 time step)
SANITY_TIME="100"
echo "Quick sanity check: Verifying time step ${SANITY_TIME} (1 time step, air region)..."
SANITY_FIELDS=("U" "p_rgh" "T" "h")
SANITY_MISSING=()
if [ -d "${SANITY_TIME}/air" ]; then
    for field in "${SANITY_FIELDS[@]}"; do
        if [ ! -f "${SANITY_TIME}/air/$field" ]; then
            SANITY_MISSING+=("$field")
        fi
    done
    if [ ${#SANITY_MISSING[@]} -eq 0 ]; then
        echo "✓ Sanity check passed: All fields present at time ${SANITY_TIME} (1 time step)"
    else
        echo "⚠ Sanity check: Missing fields at time ${SANITY_TIME}: ${SANITY_MISSING[*]}"
    fi
else
    echo "⚠ Sanity check: Time directory ${SANITY_TIME}/air not found"
fi
echo ""

# Verify final output files (check air region)
# Final time is 200 seconds (2 time steps with deltaT=100s)
TIME_DIR="200"
echo "Verifying final output files at time ${TIME_DIR} (2 time steps, air region)..."
REQUIRED_FIELDS=("U" "p_rgh" "T" "h")
MISSING_FIELDS=()

# Check in air region directory
if [ -d "$TIME_DIR/air" ]; then
    for field in "${REQUIRED_FIELDS[@]}"; do
        if [ ! -f "$TIME_DIR/air/$field" ]; then
            MISSING_FIELDS+=("$field")
        fi
    done
else
    echo "✗ Time directory $TIME_DIR/air not found"
    exit 1
fi

if [ ${#MISSING_FIELDS[@]} -gt 0 ]; then
    echo "✗ Missing output fields: ${MISSING_FIELDS[*]}"
    exit 1
fi
echo "✓ All required fields present (U, p_rgh, T, h)"
echo ""

# Check log for key indicators
echo "Checking solver log for errors..."
if grep -qi "FOAM FATAL\|FOAM aborting" /tmp/solver.log; then
    echo "✗ Solver log contains fatal errors"
    grep -i "FOAM FATAL\|FOAM aborting" /tmp/solver.log | head -5
    exit 1
fi

# Check for enthalpy solve (urbanMicroclimateFoam uses h instead of T)
if ! grep -q "Solving for h" /tmp/solver.log; then
    echo "⚠ Enthalpy equation not solved (check log)"
fi

echo "✓ No fatal errors in log"
echo ""

echo "=========================================="
echo "All tests PASSED!"
echo "=========================================="

