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

needs_rebuild() {
    local solver_dir="$1"
    local solver_name=$(basename "$solver_dir")
    local binary_path="$FOAM_USER_APPBIN/${solver_name}"
    
    # If binary doesn't exist, needs rebuild
    if [ ! -f "$binary_path" ]; then
        return 0  # true - needs rebuild
    fi
    
    # Check if any source files are newer than the binary
    local binary_mtime=$(stat -c %Y "$binary_path" 2>/dev/null || stat -f %m "$binary_path" 2>/dev/null || echo "0")
    
    # Check source files (common patterns)
    if find "$solver_dir" -type f \( -name "*.C" -o -name "*.H" -o -name "*.h" -o -name "Make/files" -o -name "Make/options" -o -name "Allwmake" \) -newer "$binary_path" 2>/dev/null | grep -q .; then
        return 0  # true - needs rebuild
    fi
    
    # Check for Allwmake dependencies (check _LIB directories)
    if [ -d "${solver_dir}/_LIB" ]; then
        if find "${solver_dir}/_LIB" -type f -name "*.C" -o -name "*.H" -newer "$binary_path" 2>/dev/null | grep -q .; then
            return 0  # true - needs rebuild
        fi
    fi
    
    return 1  # false - no rebuild needed
}

build_solver() {
    local solver_dir="$1"
    local solver_name=$(basename "$solver_dir")
    
    echo ""
    echo "============================================================"
    echo "Building solver: ${solver_name}"
    echo "============================================================"
    
    cd "$solver_dir"
    
    # Check if rebuild is needed
    if ! needs_rebuild "$solver_dir"; then
        echo "✓ ${solver_name} is up to date (skipping build)"
        echo "  Binary: $FOAM_USER_APPBIN/${solver_name}"
        return 0
    fi
    
    echo "  Source files changed, rebuilding..."
    
    # Check for Allwmake (urbanMicroclimateFoam style)
    if [ -f "Allwmake" ]; then
        echo "Found Allwmake, running ./Allwmake..."
        # Redirect output to log but also show progress
        if ./Allwmake 2>&1 | tee /tmp/build_${solver_name}.log | tail -5; then
            # Verify binary was created
            if [ -f "$FOAM_USER_APPBIN/${solver_name}" ]; then
                echo "✓ ${solver_name} built successfully (Allwmake)"
                echo "  Binary: $FOAM_USER_APPBIN/${solver_name}"
                return 0
            else
                echo "✗ ${solver_name} build completed but binary not found"
                echo "  Expected: $FOAM_USER_APPBIN/${solver_name}"
                return 1
            fi
        else
            echo "✗ ${solver_name} build failed (Allwmake)"
            cat /tmp/build_${solver_name}.log | tail -30
            return 1
        fi
    # Check for wmake (microClimateFoam style)
    elif [ -f "Make/files" ]; then
        echo "Found Make/files, running wmake..."
        if wmake > /tmp/build_${solver_name}.log 2>&1; then
            # Verify binary was created
            if command -v "${solver_name}" > /dev/null 2>&1 || [ -f "$FOAM_USER_APPBIN/${solver_name}" ]; then
                echo "✓ ${solver_name} built successfully (wmake)"
                return 0
            else
                echo "✗ ${solver_name} build completed but binary not found"
                return 1
            fi
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

