#!/usr/bin/env bash
#
# Build all solvers in src/ directory
#
# This script builds all OpenFOAM solvers found in src/:
# - Solvers with Allwmake (like urbanMicroclimateFoam)
# - Solvers with wmake (like microClimateFoam)
#
# Usage:
#   ./scripts/build_all_solvers.sh
#   ./scripts/build_all_solvers.sh [solver-name]  # Build specific solver
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${REPO_ROOT}/src"

# Check if running inside Docker or need to use docker compose
if [ -f /.dockerenv ] || grep -Eq '/(lxc|docker)/[[:alnum:]]{64}' /proc/self/cgroup 2>/dev/null; then
    RUN_IN_DOCKER=true
else
    RUN_IN_DOCKER=false
fi

build_solver() {
    local solver_dir="$1"
    local solver_name=$(basename "$solver_dir")
    
    echo ""
    echo "============================================================"
    echo "Building solver: ${solver_name}"
    echo "============================================================"
    
    cd "$solver_dir"
    
    # Check for Allwmake (urbanMicroclimateFoam style)
    if [ -f "Allwmake" ]; then
        echo "Found Allwmake, running ./Allwmake..."
        if ./Allwmake > /tmp/build_${solver_name}.log 2>&1; then
            echo "✓ ${solver_name} built successfully (Allwmake)"
            return 0
        else
            echo "✗ ${solver_name} build failed (Allwmake)"
            cat /tmp/build_${solver_name}.log | tail -30
            return 1
        fi
    # Check for wmake (microClimateFoam style)
    elif [ -f "Make/files" ]; then
        echo "Found Make/files, running wmake..."
        if wmake > /tmp/build_${solver_name}.log 2>&1; then
            echo "✓ ${solver_name} built successfully (wmake)"
            return 0
        else
            echo "✗ ${solver_name} build failed (wmake)"
            cat /tmp/build_${solver_name}.log | tail -30
            return 1
        fi
    else
        echo "⚠ ${solver_name}: No build system found (no Allwmake or Make/files)"
        return 0  # Don't fail, just skip
    fi
}

if [ "$RUN_IN_DOCKER" = true ]; then
    # Running inside Docker
    set +u  # Temporarily disable unbound variable check for bashrc
    source /opt/openfoam8/etc/bashrc
    set -u  # Re-enable
    
    if [ $# -gt 0 ]; then
        # Build specific solver
        SOLVER_NAME="$1"
        SOLVER_DIR="${SRC_DIR}/${SOLVER_NAME}"
        if [ ! -d "$SOLVER_DIR" ]; then
            echo "Error: Solver directory not found: ${SOLVER_DIR}"
            exit 1
        fi
        build_solver "$SOLVER_DIR"
    else
        # Build all solvers
        echo "Building all solvers in ${SRC_DIR}..."
        FAILED=0
        for solver_dir in "${SRC_DIR}"/*/; do
            if [ -d "$solver_dir" ]; then
                if ! build_solver "$solver_dir"; then
                    FAILED=1
                fi
            fi
        done
        
        if [ $FAILED -eq 1 ]; then
            echo ""
            echo "✗ Some solvers failed to build"
            exit 1
        else
            echo ""
            echo "============================================================"
            echo "✓ All solvers built successfully!"
            echo "============================================================"
        fi
    fi
else
    # Running on host, use docker compose
    if [ $# -gt 0 ]; then
        SOLVER_NAME="$1"
        docker compose run --rm dev bash -c "
            source /opt/openfoam8/etc/bashrc
            cd /workspace
            bash scripts/build_all_solvers.sh ${SOLVER_NAME}
        "
    else
        docker compose run --rm dev bash -c "
            source /opt/openfoam8/etc/bashrc
            cd /workspace
            bash scripts/build_all_solvers.sh
        "
    fi
fi

