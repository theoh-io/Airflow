#!/usr/bin/env bash
#
# List available cases with their solver requirements
#
# Usage:
#   ./scripts/list_cases.sh
#   ./scripts/list_cases.sh --solver [solver-name]  # Filter by solver
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

CUSTOM_CASES_DIR="${REPO_ROOT}/custom_cases"
TUTORIAL_CASES_DIR="${REPO_ROOT}/cases"

# Detect solver from case directory
detect_solver() {
    local case_dir="$1"
    local case_name=$(basename "$case_dir")
    
    # Check controlDict for application
    if [ -f "${case_dir}/system/controlDict" ]; then
        local app=$(grep "^application" "${case_dir}/system/controlDict" 2>/dev/null | awk '{print $2}' | tr -d ';' || echo "unknown")
        echo "$app"
    else
        echo "unknown"
    fi
}

print_case_info() {
    local case_dir="$1"
    local case_name=$(basename "$case_dir")
    local case_type="$2"
    local solver=$(detect_solver "$case_dir")
    
    printf "  %-30s %-25s %s\n" "$case_name" "$solver" "$case_type"
}

echo "============================================================"
echo "Available Cases"
echo "============================================================"
echo ""
printf "  %-30s %-25s %s\n" "CASE NAME" "SOLVER" "TYPE"
echo "  $(printf '=%.0s' {1..80})"

if [ -d "$CUSTOM_CASES_DIR" ]; then
    echo ""
    echo "Custom Cases (custom_cases/):"
    for case_dir in "${CUSTOM_CASES_DIR}"/*/; do
        if [ -d "$case_dir" ] && [ -f "${case_dir}/system/controlDict" ]; then
            print_case_info "$case_dir" "custom"
        fi
    done
fi

if [ -d "$TUTORIAL_CASES_DIR" ]; then
    echo ""
    echo "Tutorial Cases (cases/):"
    for case_dir in "${TUTORIAL_CASES_DIR}"/*/; do
        if [ -d "$case_dir" ] && [ -f "${case_dir}/system/controlDict" ]; then
            print_case_info "$case_dir" "tutorial"
        fi
    done
fi

echo ""
echo "============================================================"
echo "Usage:"
echo "  ./scripts/run_case.sh <case-path> [solver]"
echo ""
echo "Examples:"
echo "  ./scripts/run_case.sh custom_cases/heatedCavity"
echo "  ./scripts/run_case.sh cases/streetCanyon_CFD urbanMicroclimateFoam"
echo "============================================================"

