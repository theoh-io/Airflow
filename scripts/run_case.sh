#!/usr/bin/env bash
#
# Generic helper to rebuild the solver (optional), regenerate a case mesh,
# and run a solver inside the docker-compose dev container.
#
# Usage:
#   ./scripts/run_case.sh <case-path> [solver-name] [solver-args...]
#
# Examples:
#   ./scripts/run_case.sh cases/heatedCavity
#   ./scripts/run_case.sh cases/customCase pisoFoam -- -parallel
#

set -euo pipefail

print_usage() {
  cat <<'EOF'
Usage: run_case.sh [options] <case-path> [solver [-- solver-args]]

Options:
  -n, --no-build       Skip wmake (assumes solver already built)
  -B, --no-blockMesh   Skip blockMesh step
  -h, --help           Show this help

Positional arguments:
  case-path            Case directory relative to repo root (e.g. cases/heatedCavity)
  solver               Solver executable (default: microClimateFoam)
  -- solver-args       Everything after '--' is passed directly to the solver

Examples:
  ./scripts/run_case.sh cases/heatedCavity
  ./scripts/run_case.sh cases/myCase buoyantBoussinesqSimpleFoam -- -parallel
EOF
}

NO_BUILD=0
RUN_BLOCKMESH=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--no-build)
      NO_BUILD=1
      shift
      ;;
    -B|--no-blockMesh)
      RUN_BLOCKMESH=0
      shift
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      print_usage
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 1 ]]; then
  echo "Error: case path is required" >&2
  print_usage
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_PATH="$1"; shift
if [[ $# -gt 0 && "$1" != "--" ]]; then
  SOLVER="$1"
  shift
else
  SOLVER="microClimateFoam"
fi

if [[ $# -gt 0 && "$1" == "--" ]]; then
  shift
fi

SOLVER_ARGS=()
if [[ $# -gt 0 ]]; then
  # Whatever remains (after an explicit --) are solver args
  SOLVER_ARGS=("$@")
fi

if [[ ! -d "${REPO_ROOT}/${CASE_PATH}" ]]; then
  echo "Error: case directory '${CASE_PATH}' not found from repo root" >&2
  exit 1
fi

cat <<EOF
============================================================
 microClimateFoam - Case Runner
------------------------------------------------------------
 Case   : ${CASE_PATH}
 Solver : ${SOLVER}
 Build  : $([[ $NO_BUILD -eq 0 ]] && echo "wmake" || echo "skip")
 Mesh   : $([[ $RUN_BLOCKMESH -eq 1 ]] && echo "blockMesh" || echo "skip")
 Args   : ${SOLVER_ARGS[*]:-(none)}
============================================================
EOF

SOLVER_ARGS_STR=""
if [[ ${#SOLVER_ARGS[@]} -gt 0 ]]; then
  for arg in "${SOLVER_ARGS[@]}"; do
    SOLVER_ARGS_STR+=" $(printf '%q' "$arg")"
  done
fi

docker compose run --rm dev bash -lc "
  source /opt/openfoam8/etc/bashrc
  set -e
  cd /workspace/src/microClimateFoam
  if [[ ${NO_BUILD} -eq 0 ]]; then
    wmake
  fi
  cd /workspace/${CASE_PATH}
  if [[ ${RUN_BLOCKMESH} -eq 1 && -f constant/polyMesh/blockMeshDict ]]; then
    blockMesh
  fi
  rm -f log.${SOLVER}
  ${SOLVER}${SOLVER_ARGS_STR} | tee log.${SOLVER}
"

