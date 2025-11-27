#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

cat <<'EOF'
============================================================
 microClimateFoam - Heated Cavity Tutorial
============================================================
This script rebuilds the solver, regenerates the cavity mesh,
and runs the microClimateFoam solver inside the dev container.
============================================================
EOF

docker compose run --rm dev bash -lc "
  source /opt/openfoam8/etc/bashrc
  set -e
  cd /workspace/src/microClimateFoam
  wmake
  cd /workspace/custom_cases/heatedCavity
  rm -f log.microClimateFoam
  blockMesh
  microClimateFoam | tee log.microClimateFoam
"

