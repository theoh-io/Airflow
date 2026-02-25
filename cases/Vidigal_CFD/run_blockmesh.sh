#!/bin/bash
source /opt/openfoam8/etc/bashrc >/dev/null 2>&1
cd /workspace/cases/Vidigal_CFD
blockMesh -region air 2>&1 | tee /workspace/cases/Vidigal_CFD/blockmesh_output.log
echo "Exit code: $?" >> /workspace/cases/Vidigal_CFD/blockmesh_output.log
