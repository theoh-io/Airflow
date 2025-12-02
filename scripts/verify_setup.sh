#!/bin/bash
# Quick verification script to check OpenFOAM setup and availability
# Usage: ./scripts/verify_setup.sh

set -e

echo "=========================================="
echo "OpenFOAM Setup Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if all checks pass
ALL_PASSED=true

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
    ALL_PASSED=false
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check 1: OpenFOAM bashrc file exists
echo "[1/8] Checking OpenFOAM installation..."
if [ -f "/opt/openfoam8/etc/bashrc" ]; then
    print_success "OpenFOAM bashrc found at /opt/openfoam8/etc/bashrc"
else
    print_error "OpenFOAM bashrc not found at /opt/openfoam8/etc/bashrc"
    exit 1
fi
echo ""

# Check 2: Source OpenFOAM environment
echo "[2/8] Loading OpenFOAM environment..."
set +e  # Temporarily disable exit on error for sourcing
. /opt/openfoam8/etc/bashrc 2>&1
SOURCE_EXIT=$?
set -e  # Re-enable exit on error

if [ $SOURCE_EXIT -eq 0 ]; then
    print_success "OpenFOAM environment loaded successfully"
else
    print_error "Failed to source OpenFOAM environment"
    exit 1
fi
echo ""

# Check 3: Verify OpenFOAM environment variables
echo "[3/8] Checking OpenFOAM environment variables..."
REQUIRED_VARS=("FOAM_RUN" "FOAM_USER_APPBIN" "WM_PROJECT_VERSION" "WM_PROJECT")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    print_success "All required environment variables are set"
    echo "  FOAM_RUN: $FOAM_RUN"
    echo "  FOAM_USER_APPBIN: $FOAM_USER_APPBIN"
    echo "  WM_PROJECT_VERSION: $WM_PROJECT_VERSION"
    echo "  WM_PROJECT: $WM_PROJECT"
else
    print_error "Missing environment variables: ${MISSING_VARS[*]}"
fi
echo ""

# Check 4: Verify OpenFOAM commands are available
echo "[4/8] Checking OpenFOAM commands availability..."
REQUIRED_CMDS=("blockMesh" "checkMesh" "wmake" "foamVersion")
MISSING_CMDS=()

for cmd in "${REQUIRED_CMDS[@]}"; do
    if ! command -v "$cmd" > /dev/null 2>&1; then
        MISSING_CMDS+=("$cmd")
    fi
done

if [ ${#MISSING_CMDS[@]} -eq 0 ]; then
    print_success "All required OpenFOAM commands are available"
    echo "  blockMesh: $(which blockMesh)"
    echo "  checkMesh: $(which checkMesh)"
    echo "  wmake: $(which wmake)"
    echo "  foamVersion: $(foamVersion)"
else
    print_error "Missing OpenFOAM commands: ${MISSING_CMDS[*]}"
fi
echo ""

# Check 5: Verify OpenFOAM version
echo "[5/8] Checking OpenFOAM version..."
if command -v foamVersion > /dev/null 2>&1; then
    OF_VERSION=$(foamVersion)
    print_success "OpenFOAM version: $OF_VERSION"
    if [[ "$OF_VERSION" == *"8"* ]]; then
        print_success "OpenFOAM 8 detected (correct version)"
    else
        print_warning "Expected OpenFOAM 8, but found: $OF_VERSION"
    fi
else
    print_error "foamVersion command not available"
fi
echo ""

# Check 6: Verify workspace directory
echo "[6/8] Checking workspace setup..."
if [ -d "/workspace" ]; then
    print_success "Workspace directory exists: /workspace"
    if [ -w "/workspace" ]; then
        print_success "Workspace is writable"
    else
        print_error "Workspace is not writable"
    fi
else
    print_error "Workspace directory /workspace does not exist"
fi
echo ""

# Check 7: Verify source code directory
echo "[7/8] Checking source code structure..."
if [ -d "/workspace/src" ]; then
    print_success "Source directory exists: /workspace/src"
    if [ -d "/workspace/src/microClimateFoam" ]; then
        print_success "microClimateFoam solver directory found"
    else
        print_warning "microClimateFoam solver directory not found (may need to be created)"
    fi
    if [ -d "/workspace/src/urbanMicroclimateFoam" ]; then
        print_success "urbanMicroclimateFoam solver directory found"
    else
        print_warning "urbanMicroclimateFoam solver directory not found (may need to be cloned)"
    fi
else
    print_error "Source directory /workspace/src does not exist"
fi
echo ""

# Check 8: Test basic OpenFOAM functionality
echo "[8/8] Testing basic OpenFOAM functionality..."
if command -v blockMesh > /dev/null 2>&1; then
    # Test blockMesh help (should work without a case)
    if blockMesh -help > /dev/null 2>&1; then
        print_success "blockMesh command works correctly"
    else
        print_warning "blockMesh help test failed (may still be functional)"
    fi
else
    print_error "blockMesh command not available"
fi

if command -v checkMesh > /dev/null 2>&1; then
    # Test checkMesh help
    if checkMesh -help > /dev/null 2>&1; then
        print_success "checkMesh command works correctly"
    else
        print_warning "checkMesh help test failed (may still be functional)"
    fi
else
    print_error "checkMesh command not available"
fi
echo ""

# Final summary
echo "=========================================="
if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✓ All checks PASSED!${NC}"
    echo ""
    echo "Your OpenFOAM environment is properly configured."
    echo "You can now:"
    echo "  - Build solvers: ./scripts/build_all_solvers.sh"
    echo "  - Run cases: ./scripts/run_case.sh cases/streetCanyon_CFD"
    echo "  - Run tests: ./test_env.sh"
    exit 0
else
    echo -e "${RED}✗ Some checks FAILED!${NC}"
    echo ""
    echo "Please review the errors above and fix the issues."
    exit 1
fi

