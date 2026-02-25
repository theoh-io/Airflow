#!/bin/bash
#
# Switch Vidigal_CFD case to use circular domain
# This script backs up the current blockMeshDict and replaces it with circular version
#

set -e

CASE_DIR="${1:-cases/Vidigal_CFD}"
CIRCULAR_TEMPLATE="${CASE_DIR}/templates/blockMeshDict.circular"
BLOCKMESHDICT="${CASE_DIR}/constant/air/polyMesh/blockMeshDict"

if [ ! -d "$CASE_DIR" ]; then
    echo "Error: Case directory not found: $CASE_DIR"
    exit 1
fi

if [ ! -f "$CIRCULAR_TEMPLATE" ]; then
    echo "Error: Circular template not found: $CIRCULAR_TEMPLATE"
    exit 1
fi

echo "=========================================="
echo "Switching to Circular Domain"
echo "=========================================="
echo ""
echo "Case directory: $CASE_DIR"
echo ""

# Backup current blockMeshDict if it exists
if [ -f "$BLOCKMESHDICT" ]; then
    BACKUP="${BLOCKMESHDICT}.rectangular.backup"
    echo "Backing up current blockMeshDict to: $BACKUP"
    cp "$BLOCKMESHDICT" "$BACKUP"
    echo "✓ Backup created"
else
    echo "No existing blockMeshDict found (creating new one)"
fi

# Check if we should generate from geometry info
GEOMETRY_INFO="${CASE_DIR}/geometry_info.txt"
if [ -f "$GEOMETRY_INFO" ] && command -v python3 &> /dev/null; then
    echo ""
    echo "Generating circular domain from geometry info..."
    python3 scripts/mesh/create_circular_domain.py "$GEOMETRY_INFO" "$BLOCKMESHDICT"
    echo "✓ Generated circular domain blockMeshDict"
else
    echo ""
    echo "Copying circular domain template..."
    cp "$CIRCULAR_TEMPLATE" "$BLOCKMESHDICT"
    echo "✓ Copied template (you may need to adjust parameters)"
    echo ""
    echo "⚠  Note: Edit $BLOCKMESHDICT to adjust:"
    echo "   - Center point (X, Y, Z)"
    echo "   - Radius"
    echo "   - Vertical extent"
    echo "   - Cell counts"
fi

echo ""
echo "=========================================="
echo "✓ Switched to circular domain"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review blockMeshDict: $BLOCKMESHDICT"
echo "  2. Generate mesh: blockMesh -region air"
echo "  3. Continue with snappyHexMesh workflow"
echo ""
