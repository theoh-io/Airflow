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
BLUE='\033[0;34m'
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

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Detect if running inside Docker
DETECT_DOCKER=false
if [ -f /.dockerenv ] || grep -Eq '/(lxc|docker)/[[:alnum:]]{64}' /proc/self/cgroup 2>/dev/null; then
    DETECT_DOCKER=true
fi

# Check 0: Verify we're in Docker container
echo "[0/9] Checking execution environment..."
if [ "$DETECT_DOCKER" = true ]; then
    print_success "Running inside Docker container"
    echo "  Container detected via /.dockerenv or cgroup"
else
    print_error "NOT running inside Docker container"
    echo ""
    echo "This script must be run inside the Docker container where OpenFOAM is installed."
    echo ""
    echo "To fix this:"
    echo ""
    echo "1. If using Cursor Cloud Agent:"
    echo "   - The agent should automatically run commands inside the container"
    echo "   - Check that .cursor/environment.json is configured correctly"
    echo "   - Verify the Docker image is built: docker images | grep microclimatefoam"
    echo ""
    echo "2. If running manually on VM:"
    echo "   - Build the Docker image first:"
    echo "     cd /path/to/Airflow"
    echo "     docker build -f Dockerfile.cloud --build-arg USER_UID=\$(id -u) --build-arg USER_GID=\$(id -g) -t microclimatefoam:dev ."
    echo ""
    echo "   - Then run the script inside the container:"
    echo "     docker run --rm -it -v \$(pwd):/workspace microclimatefoam:dev bash -c 'bash scripts/verify_setup.sh'"
    echo ""
    echo "   - Or use docker-compose:"
    echo "     docker compose -f docker-compose.cloud.yml build"
    echo "     docker compose -f docker-compose.cloud.yml run --rm dev bash scripts/verify_setup.sh"
    echo ""
    echo "3. Check if Docker is available:"
    if command -v docker > /dev/null 2>&1; then
        print_info "Docker is installed: $(docker --version)"
        if docker images | grep -q microclimatefoam; then
            print_info "Docker image 'microclimatefoam' found"
        else
            print_warning "Docker image 'microclimatefoam' not found - you need to build it"
        fi
    else
        print_error "Docker is not installed or not in PATH"
    fi
    echo ""
    exit 1
fi
echo ""

# Check 1: OpenFOAM bashrc file exists
echo "[1/9] Checking OpenFOAM installation..."
if [ -f "/opt/openfoam8/etc/bashrc" ]; then
    print_success "OpenFOAM bashrc found at /opt/openfoam8/etc/bashrc"
else
    print_error "OpenFOAM bashrc not found at /opt/openfoam8/etc/bashrc"
    echo ""
    print_warning "This suggests the Docker image may not have been built correctly"
    echo "  Expected base image: openfoam/openfoam8-paraview56"
    echo "  Check Dockerfile.cloud to ensure it uses the correct base image"
    exit 1
fi
echo ""

# Check 2: Source OpenFOAM environment
echo "[2/9] Loading OpenFOAM environment..."
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
echo "[3/9] Checking OpenFOAM environment variables..."
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
echo "[4/9] Checking OpenFOAM commands availability..."
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
echo "[5/9] Checking OpenFOAM version..."
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
echo "[6/9] Checking workspace setup..."
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
echo "[7/9] Checking source code structure..."
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

# Check 8: Verify entrypoint script (for Dockerfile.cloud)
echo "[8/9] Checking cloud entrypoint configuration..."
if [ -f "/usr/local/bin/cloud-entrypoint.sh" ]; then
    print_success "Cloud entrypoint script found"
    if grep -q "source /opt/openfoam8/etc/bashrc" /usr/local/bin/cloud-entrypoint.sh; then
        print_success "Entrypoint script sources OpenFOAM correctly"
    else
        print_warning "Entrypoint script exists but may not source OpenFOAM"
    fi
else
    print_warning "Cloud entrypoint script not found (using standard Dockerfile instead of Dockerfile.cloud?)"
fi
echo ""

# Check 9: Test basic OpenFOAM functionality
echo "[9/9] Testing basic OpenFOAM functionality..."
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

