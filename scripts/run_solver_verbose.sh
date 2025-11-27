#!/usr/bin/env bash
#
# Run OpenFOAM solver with verbose real-time progress monitoring
#
# Usage:
#   ./scripts/run_solver_verbose.sh <solver> <case-dir> [region]
#
# Example:
#   ./scripts/run_solver_verbose.sh urbanMicroclimateFoam /workspace/cases/streetCanyon_CFD air
#
set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <solver> <case-dir> [region]"
    exit 1
fi

SOLVER="$1"
CASE_DIR="$2"
REGION="${3:-}"

cd "$CASE_DIR"

echo "============================================================"
echo "Running solver: $SOLVER"
echo "Case directory: $CASE_DIR"
[ -n "$REGION" ] && echo "Region: $REGION"
echo "============================================================"
echo ""

# Build solver command
# Note: urbanMicroclimateFoam handles regions internally, no -region flag needed
# The region is specified in the case setup (blockMesh -region air, etc.)
SOLVER_CMD="$SOLVER"

# Get expected time steps from controlDict
if [ -f "system/controlDict" ]; then
    DELTA_T=$(grep "^deltaT" system/controlDict | awk '{print $2}' | tr -d ';' || echo "3600")
    WRITE_INTERVAL=$(grep "^writeInterval" system/controlDict | awk '{print $2}' | tr -d ';' || echo "1")
    END_TIME=$(grep "^endTime" system/controlDict | awk '{print $2}' | tr -d ';' || echo "86400")
    
    echo "Simulation parameters:"
    echo "  deltaT: $DELTA_T"
    echo "  writeInterval: $WRITE_INTERVAL"
    echo "  endTime: $END_TIME"
    echo ""
    
    # Calculate expected time steps (simplified, no bc required)
    EXPECTED_TIMES=("0")
    DELTA_T_INT=${DELTA_T%.*}
    WRITE_INTERVAL_INT=${WRITE_INTERVAL%.*}
    WRITE_STEP=$((DELTA_T_INT * WRITE_INTERVAL_INT))
    END_TIME_INT=${END_TIME%.*}
    
    TIME_STEP=$WRITE_STEP
    while [ $TIME_STEP -le $END_TIME_INT ]; do
        EXPECTED_TIMES+=("$TIME_STEP")
        TIME_STEP=$((TIME_STEP + WRITE_STEP))
        # Safety check
        if [ ${#EXPECTED_TIMES[@]} -gt 50 ]; then
            break
        fi
    done
    
    if [ ${#EXPECTED_TIMES[@]} -gt 0 ] && [ ${#EXPECTED_TIMES[@]} -le 20 ]; then
        echo "Expected time steps: ${EXPECTED_TIMES[*]}"
        echo ""
    elif [ ${#EXPECTED_TIMES[@]} -gt 20 ]; then
        FIRST=${EXPECTED_TIMES[0]}
        LAST=${EXPECTED_TIMES[-1]}
        echo "Expected time steps: $FIRST ... $LAST (${#EXPECTED_TIMES[@]} total)"
        echo ""
    fi
fi

echo "Starting solver..."
echo "  Monitoring progress in real-time..."
echo "  Watching for time directory creation..."
echo ""

# Clean up any previous monitor files
rm -f /tmp/time_*_reported_$$

# Function to check time directories
check_time_dirs() {
    local region_path="$1"
    for time_dir in "${EXPECTED_TIMES[@]}"; do
        if [ -d "${time_dir}${region_path:+/$region_path}" ] && [ ! -f "/tmp/time_${time_dir}_reported_$$" ]; then
            echo ""
            echo "  ✓✓ Time step ${time_dir}${region_path:+ ($region_path region)} written ✓✓"
            touch "/tmp/time_${time_dir}_reported_$$"
        fi
    done
}

# Run solver with real-time output
(
    $SOLVER_CMD 2>&1 | while IFS= read -r line; do
        # Always show the line
        echo "$line"
        
        # Highlight important progress indicators
        if echo "$line" | grep -qE "^Time ="; then
            TIME_VAL=$(echo "$line" | grep -oE "Time = [0-9.]+" | grep -oE "[0-9.]+" | head -1)
            if [ -n "$TIME_VAL" ]; then
                echo "  →→ Processing time: $TIME_VAL →→"
            fi
        fi
        
        # Highlight execution time updates
        if echo "$line" | grep -qE "ExecutionTime ="; then
            EXEC_TIME=$(echo "$line" | grep -oE "ExecutionTime = [0-9.]+ s" || echo "")
            if [ -n "$EXEC_TIME" ]; then
                echo "  →→ $EXEC_TIME →→"
            fi
        fi
        
        # Highlight convergence
        if echo "$line" | grep -qE "No Iterations 0|converged"; then
            echo "  ✓ $(echo "$line" | sed 's/^[[:space:]]*//')"
        fi
    done
) &
SOLVER_PID=$!

# Monitor time directory creation in background
(
    REGION_PATH=""
    [ -n "$REGION" ] && REGION_PATH="$REGION"
    
    while kill -0 $SOLVER_PID 2>/dev/null; do
        check_time_dirs "$REGION_PATH"
        sleep 2
    done
    
    # Final check after solver completes
    sleep 1
    check_time_dirs "$REGION_PATH"
    
    # Report final status
    echo ""
    if [ -n "$REGION" ]; then
        if [ -d "${END_TIME}/${REGION}" ]; then
            echo "  ✓✓ Final time step ${END_TIME} written (${REGION} region) ✓✓"
        else
            echo "  ⚠ Final time step ${END_TIME} not found in ${REGION} region"
        fi
    else
        if [ -d "${END_TIME}" ]; then
            echo "  ✓✓ Final time step ${END_TIME} written ✓✓"
        else
            echo "  ⚠ Final time step ${END_TIME} not found"
        fi
    fi
) &
MONITOR_PID=$!

# Wait for solver to complete
wait $SOLVER_PID
SOLVER_EXIT=$?

# Stop monitor
kill $MONITOR_PID 2>/dev/null || true
wait $MONITOR_PID 2>/dev/null || true

# Clean up
rm -f /tmp/time_*_reported_$$

# Return solver exit code
exit $SOLVER_EXIT

