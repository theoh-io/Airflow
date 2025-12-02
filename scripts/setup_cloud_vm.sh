#!/bin/bash
# Setup script for cloud VM - builds Docker image and verifies setup
# Usage: ./scripts/setup_cloud_vm.sh

set -e

echo "=========================================="
echo "Cloud VM Setup Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }

# Check if Docker is installed
echo "[1/4] Checking Docker installation..."
if ! command -v docker > /dev/null 2>&1; then
    print_error "Docker is not installed"
    echo "  Please install Docker first:"
    echo "  https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed: $(docker --version)"

if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    print_warning "Docker Compose not found (optional, but recommended)"
else
    print_success "Docker Compose is available"
fi
echo ""

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Check if Dockerfile.cloud exists
echo "[2/4] Checking Dockerfile.cloud..."
if [ ! -f "Dockerfile.cloud" ]; then
    print_error "Dockerfile.cloud not found in $SCRIPT_DIR"
    exit 1
fi
print_success "Dockerfile.cloud found"
echo ""

# Build Docker image
echo "[3/4] Building Docker image..."
print_info "This may take several minutes on first build..."
print_info "Building with Dockerfile.cloud..."

# Get user UID/GID (default to 1000 if not available)
USER_UID=${UID:-1000}
USER_GID=${GID:-$(id -g 2>/dev/null || echo 1000)}

print_info "Using USER_UID=$USER_UID, USER_GID=$USER_GID"

if docker build \
    -f Dockerfile.cloud \
    --build-arg USER_UID="$USER_UID" \
    --build-arg USER_GID="$USER_GID" \
    -t microclimatefoam:dev \
    . 2>&1 | tee /tmp/docker-build.log; then
    print_success "Docker image built successfully"
else
    print_error "Docker build failed"
    echo "Last 20 lines of build log:"
    tail -20 /tmp/docker-build.log
    exit 1
fi
echo ""

# Verify the image
echo "[4/4] Verifying Docker image..."
if docker images | grep -q microclimatefoam; then
    print_success "Docker image 'microclimatefoam:dev' is available"
    docker images | grep microclimatefoam
else
    print_error "Docker image not found after build"
    exit 1
fi
echo ""

# Run verification script inside container
echo "=========================================="
echo "Running verification inside container..."
echo "=========================================="
echo ""

if docker run --rm \
    -v "$SCRIPT_DIR:/workspace" \
    -w /workspace \
    microclimatefoam:dev \
    bash -c "bash scripts/verify_setup.sh"; then
    echo ""
    print_success "Setup complete! Your cloud VM is ready."
    echo ""
    echo "Next steps:"
    echo "  1. For Cursor Cloud Agent: The agent should now work automatically"
    echo "  2. To run commands manually:"
    echo "     docker run --rm -it -v \$(pwd):/workspace microclimatefoam:dev bash"
    echo "  3. To use docker-compose:"
    echo "     docker compose -f docker-compose.cloud.yml up -d"
    echo "     docker compose -f docker-compose.cloud.yml exec dev bash"
else
    print_error "Verification failed - check the output above"
    exit 1
fi

