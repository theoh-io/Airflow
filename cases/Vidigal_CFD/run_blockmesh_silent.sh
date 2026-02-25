#!/bin/bash
set -e

# Suppress welcome message by redirecting bashrc output
exec 3>&1
exec 4>&2

# Source OpenFOAM environment, redirecting welcome message
. /opt/openfoam8/etc/bashrc >&4 2>&4 || true

# Change to case directory
cd /workspace/cases/Vidigal_CFD

# Run blockMesh and capture output
echo "Running blockMesh..." >&3
blockMesh -region air >&3 2>&3
EXIT_CODE=$?

echo "blockMesh exit code: $EXIT_CODE" >&3

# Check for generated files
if [ -f "constant/air/polyMesh/points.gz" ]; then
    echo "SUCCESS: Mesh files created" >&3
    ls -lh constant/air/polyMesh/*.gz constant/air/polyMesh/boundary >&3
else
    echo "ERROR: Mesh files not created" >&3
fi

exit $EXIT_CODE
