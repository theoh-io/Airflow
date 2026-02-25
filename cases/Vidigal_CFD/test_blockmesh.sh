#!/bin/bash
set -e
source /opt/openfoam8/etc/bashrc 2>&1 | grep -v "Welcome\|Further\|Produced\|OpenFOAM\|CFD\|Resources" > /dev/null || true
cd /workspace/cases/Vidigal_CFD
echo "=== Running blockMesh ==="
blockMesh -region air
echo "=== blockMesh completed ==="
ls -lh constant/air/polyMesh/*.gz constant/air/polyMesh/boundary 2>&1 | head -10
