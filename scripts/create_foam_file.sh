#!/usr/bin/env bash
#
# Helper script to create a .foam file for ParaView
# Usage: ./scripts/create_foam_file.sh <case-directory>
#

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <case-directory>"
    echo "Example: $0 custom_cases/heatedCavity"
    exit 1
fi

CASE_DIR="$1"
CASE_NAME=$(basename "$CASE_DIR")
FOAM_FILE="${CASE_DIR}/${CASE_NAME}.foam"

if [[ ! -d "$CASE_DIR" ]]; then
    echo "Error: Case directory '$CASE_DIR' does not exist"
    exit 1
fi

# Create .foam file (it's just an empty file, ParaView recognizes it by extension)
touch "$FOAM_FILE"

echo "Created ParaView case file: $FOAM_FILE"
echo "You can now open this file in ParaView to visualize the case."

