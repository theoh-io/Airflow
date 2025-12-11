#!/bin/bash
#
# Monitor mesh generation progress
#

LOG_FILE="/tmp/snappy_run.log"
CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Monitoring mesh generation progress..."
echo "=========================================="
echo ""

while true; do
    # Check if process is running
    if ps aux | grep -E "snappyHexMesh" | grep -v grep > /dev/null; then
        echo "$(date '+%H:%M:%S') - snappyHexMesh is running..."
        
        # Show last few lines of log
        if [ -f "$LOG_FILE" ]; then
            echo "Latest log output:"
            tail -3 "$LOG_FILE" | sed 's/^/  /'
        fi
        
        # Check mesh file sizes
        if [ -d "$CASE_DIR/constant/polyMesh" ]; then
            SIZE=$(du -sh "$CASE_DIR/constant/polyMesh" 2>/dev/null | awk '{print $1}')
            echo "  Mesh size: $SIZE"
        fi
        
        echo ""
        sleep 30
    else
        echo "$(date '+%H:%M:%S') - snappyHexMesh process not found"
        echo ""
        echo "Checking if mesh generation completed..."
        
        if [ -f "$LOG_FILE" ]; then
            # Check for completion indicators
            if grep -q "Mesh OK\|End\|Finished" "$LOG_FILE"; then
                echo "✓ Mesh generation appears to have completed"
                tail -20 "$LOG_FILE"
                exit 0
            elif grep -q "FATAL\|Error" "$LOG_FILE"; then
                echo "✗ Error detected in log"
                tail -30 "$LOG_FILE"
                exit 1
            else
                echo "Process stopped but completion status unclear"
                tail -30 "$LOG_FILE"
                exit 1
            fi
        else
            echo "Log file not found"
            exit 1
        fi
    fi
done







