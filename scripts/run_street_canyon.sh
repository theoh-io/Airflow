#!/usr/bin/env bash
#
# Simple script to run the streetCanyon_CFD case
#
# Usage:
#   ./scripts/run_street_canyon.sh [options]
#
# Options:
#   --quick       Run quick test (2 time steps, writes at every step)
#   --full        Run full simulation (to endTime)
#   --time N      Run until time N (default: quick test)
#   --no-build    Skip solver build
#   --no-mesh     Skip mesh generation
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CASE_DIR="${REPO_ROOT}/cases/streetCanyon_CFD"

# Parse arguments
QUICK_MODE=true
QUICK_VALIDATION=false
NO_BUILD=false
NO_MESH=false
CUSTOM_TIME=""
CUSTOM_DELTA_T=""
CUSTOM_END_TIME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --quick-validation)
            QUICK_VALIDATION=true
            QUICK_MODE=true
            shift
            ;;
        --full)
            QUICK_MODE=false
            shift
            ;;
        --time)
            CUSTOM_TIME="$2"
            QUICK_MODE=false
            shift 2
            ;;
        --deltaT)
            CUSTOM_DELTA_T="$2"
            shift 2
            ;;
        --endTime)
            CUSTOM_END_TIME="$2"
            shift 2
            ;;
        --no-build)
            NO_BUILD=true
            shift
            ;;
        --no-mesh)
            NO_MESH=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick|--quick-validation|--full|--time N] [--deltaT N] [--endTime N] [--no-build] [--no-mesh]"
            exit 1
            ;;
    esac
done

cat <<EOF
============================================================
Running streetCanyon_CFD Case
============================================================
Case: $CASE_DIR
Mode: $([ "$QUICK_VALIDATION" = true ] && echo "Quick validation (CI-optimized)" || ([ "$QUICK_MODE" = true ] && echo "Quick test" || echo "Full run"))
Build: $([ "$NO_BUILD" = false ] && echo "Yes" || echo "Skip")
Mesh:  $([ "$NO_MESH" = false ] && echo "Generate" || echo "Skip")
============================================================
EOF

# Check if running in Docker or on host
if [ -f /.dockerenv ] || grep -Eq '/(lxc|docker)/[[:alnum:]]{64}' /proc/self/cgroup 2>/dev/null; then
    RUN_IN_DOCKER=true
else
    RUN_IN_DOCKER=false
fi

if [ "$RUN_IN_DOCKER" = false ]; then
    # Run in Docker
    docker compose run --rm dev bash -c "
        set +u && source /opt/openfoam8/etc/bashrc && set -u
        cd /workspace
        bash scripts/run_street_canyon.sh $([ "$QUICK_MODE" = true ] && echo "--quick" || echo "--full") $([ "$NO_BUILD" = true ] && echo "--no-build" || echo "") $([ "$NO_MESH" = true ] && echo "--no-mesh" || echo "") $([ -n "$CUSTOM_TIME" ] && echo "--time $CUSTOM_TIME" || echo "")
    "
    exit $?
fi

# Running inside Docker
cd "$CASE_DIR"

# Build solver if needed
if [ "$NO_BUILD" = false ]; then
    echo ""
    echo "Building solver..."
    cd /workspace
    bash scripts/build_all_solvers.sh urbanMicroclimateFoam 2>&1 | grep -E '(Building|up to date|built successfully|build failed)' || true
    echo ""
fi

# Ensure PATH includes FOAM_USER_APPBIN
export PATH=$FOAM_USER_APPBIN:$PATH

# Verify solver exists
if [ ! -f "$FOAM_USER_APPBIN/urbanMicroclimateFoam" ]; then
    echo "✗ Error: Solver not found at $FOAM_USER_APPBIN/urbanMicroclimateFoam"
    echo "  Please build the solver first or run without --no-build"
    exit 1
fi

cd "$CASE_DIR"

# Generate mesh if needed
if [ "$NO_MESH" = false ]; then
    # Check if mesh already exists and is up to date
    MESH_DIR="constant/polyMesh"
    BLOCKMESH_DICT="constant/polyMesh/blockMeshDict"
    
    if [ -f "${MESH_DIR}/points" ] && [ -f "${BLOCKMESH_DICT}" ]; then
        # Check if blockMeshDict is newer than mesh (mesh needs regeneration)
        if [ "${BLOCKMESH_DICT}" -nt "${MESH_DIR}/points" ]; then
            echo "Mesh exists but blockMeshDict is newer, regenerating mesh..."
            blockMesh -region air > /dev/null 2>&1
            createPatch -region air -overwrite > /dev/null 2>&1
            echo "✓ Mesh regenerated"
        else
            echo "✓ Mesh already exists and is up to date (skipping generation)"
        fi
    elif [ -f "${BLOCKMESH_DICT}" ]; then
        # Mesh doesn't exist, generate it
        echo "Generating mesh..."
        blockMesh -region air > /dev/null 2>&1
        createPatch -region air -overwrite > /dev/null 2>&1
        echo "✓ Mesh ready"
    else
        echo "⚠ Warning: blockMeshDict not found, skipping mesh generation"
    fi
    echo ""
fi

# Configure controlDict for quick validation or normal run
echo "Configuring controlDict..."
cp system/controlDict system/controlDict.orig

if [ "$QUICK_VALIDATION" = true ]; then
    # Quick validation mode: optimized for CI (3-5 minutes)
    DELTA_T="50"
    END_TIME="50"
    echo "  Quick validation mode (CI-optimized):"
    echo "    deltaT: ${DELTA_T}s"
    echo "    endTime: ${END_TIME}s (1 time step)"
    echo "    Expected runtime: 3-5 minutes"
elif [ -n "$CUSTOM_DELTA_T" ] && [ -n "$CUSTOM_END_TIME" ]; then
    # Custom deltaT and endTime
    DELTA_T="$CUSTOM_DELTA_T"
    END_TIME="$CUSTOM_END_TIME"
    echo "  Custom configuration:"
    echo "    deltaT: ${DELTA_T}s"
    echo "    endTime: ${END_TIME}s"
elif [ -n "$CUSTOM_TIME" ]; then
    # Custom endTime only
    DELTA_T=$(grep "^deltaT" system/controlDict | awk '{print $2}' | tr -d ';' || echo "3600")
    END_TIME="$CUSTOM_TIME"
    echo "  Custom endTime: ${END_TIME}s"
    echo "    deltaT: ${DELTA_T}s (unchanged)"
elif [ "$QUICK_MODE" = true ]; then
    # Quick test: run 12 time steps with original deltaT
    DELTA_T=$(grep "^deltaT" system/controlDict | awk '{print $2}' | tr -d ';' || echo "3600")
    DELTA_T_INT=${DELTA_T%.*}
    END_TIME=$((DELTA_T_INT * 12))
    echo "  Quick test mode:"
    echo "    deltaT: ${DELTA_T}s"
    echo "    endTime: ${END_TIME}s (12 time steps)"
    echo "    Note: This may take 1-6 hours. Use --quick-validation for faster CI testing."
else
    # Full run: use original settings
    DELTA_T=$(grep "^deltaT" system/controlDict | awk '{print $2}' | tr -d ';' || echo "3600")
    END_TIME=$(grep "^endTime" system/controlDict | awk '{print $2}' | tr -d ';' || echo "86400")
    echo "  Full run mode:"
    echo "    deltaT: ${DELTA_T}s"
    echo "    endTime: ${END_TIME}s"
fi

# Apply changes
sed -i "s/^deltaT[[:space:]]*[0-9.]*;/deltaT ${DELTA_T};/" system/controlDict
sed -i "s/^endTime[[:space:]]*[0-9.]*;/endTime ${END_TIME};/" system/controlDict
sed -i 's/^writeInterval[[:space:]]*[0-9.]*;/writeInterval 1;/' system/controlDict
echo "  writeInterval: 1 (writing at every time step)"
echo ""

# Run solver with verbose output
export PATH=$FOAM_USER_APPBIN:$PATH
echo "Starting solver..."
if ! bash /workspace/scripts/run_solver_verbose.sh "$FOAM_USER_APPBIN/urbanMicroclimateFoam" "$CASE_DIR" 2>&1 | tee /tmp/solver.log; then
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

# Quick sanity check at first time step
if [ "$QUICK_VALIDATION" = true ]; then
    SANITY_TIME="50"  # First time step with deltaT=50s
else
    DELTA_T_INT=${DELTA_T%.*}
    SANITY_TIME=$DELTA_T_INT  # First time step
fi

if [ -d "${SANITY_TIME}/air" ]; then
    echo "Quick sanity check: Time step ${SANITY_TIME} (1 time step)..."
    SANITY_FIELDS=("U" "p_rgh" "T" "h")
    ALL_PRESENT=true
    for field in "${SANITY_FIELDS[@]}"; do
        if [ ! -f "${SANITY_TIME}/air/$field" ]; then
            echo "  ⚠ Missing: $field"
            ALL_PRESENT=false
        fi
    done
    if [ "$ALL_PRESENT" = true ]; then
        echo "  ✓ All fields present at time ${SANITY_TIME}"
    fi
    echo ""
fi

echo "Time directories created:"
ls -1d [0-9]*/air 2>/dev/null | sed 's|/air||' | sort -n | head -15
echo ""

