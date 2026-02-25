#!/bin/bash
set -e
set +e
. /opt/openfoam8/etc/bashrc >/dev/null 2>&1
set -e

cd /workspace/cases/Vidigal_CFD

echo "=========================================="
echo "Running blockMesh for circular domain"
echo "=========================================="
echo ""

blockMesh -region air

echo ""
echo "Checking generated files..."
ls -lh constant/air/polyMesh/*.gz constant/air/polyMesh/boundary 2>&1 | head -10

echo ""
echo "Running checkMesh..."
checkMesh -region air | tail -30
