#!/usr/bin/env bash
#
# Generic helper to rebuild the solver (optional), regenerate a case mesh,
# and run a solver inside the docker-compose dev container.
#
# Usage:
#   ./scripts/run_case.sh <case-path> [solver-name] [solver-args...]
#
# Examples:
#   ./scripts/run_case.sh custom_cases/heatedCavity
#   ./scripts/run_case.sh cases/customCase pisoFoam -- -parallel
#

set -euo pipefail

print_usage() {
  cat <<'EOF'
Usage: run_case.sh [options] <case-path> [solver [-- solver-args]]

Options:
  -n, --no-build       Skip wmake (assumes solver already built)
  -B, --no-blockMesh   Skip blockMesh step
  -p, --parallel [N]   Run in parallel mode (decomposePar, solver -parallel, reconstructPar)
                        Optional N specifies number of processors (default: auto-detect)
  -R, --no-reconstruct Skip reconstructPar after parallel run
  -h, --help           Show this help

Positional arguments:
  case-path            Case directory relative to repo root (e.g. custom_cases/heatedCavity or cases/[tutorialCase])
  solver               Solver executable (default: microClimateFoam)
  -- solver-args       Everything after '--' is passed directly to the solver

Examples:
  ./scripts/run_case.sh custom_cases/heatedCavity
  ./scripts/run_case.sh -p 4 custom_cases/heatedCavity
  ./scripts/run_case.sh cases/myCase buoyantBoussinesqSimpleFoam -- -parallel
EOF
}

NO_BUILD=0
RUN_BLOCKMESH=1
PARALLEL=0
NPROCS=""
NO_RECONSTRUCT=0

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
    -p|--parallel)
      PARALLEL=1
      shift
      # Check if next argument is a number (processor count)
      if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
        NPROCS="$1"
        shift
      fi
      ;;
    -R|--no-reconstruct)
      NO_RECONSTRUCT=1
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
 Case        : ${CASE_PATH}
 Solver      : ${SOLVER}
 Build       : $([[ $NO_BUILD -eq 0 ]] && echo "wmake" || echo "skip")
 Mesh        : $([[ $RUN_BLOCKMESH -eq 1 ]] && echo "blockMesh + checkMesh" || echo "skip")
 Parallel    : $([[ $PARALLEL -eq 1 ]] && echo "yes${NPROCS:+ (${NPROCS} procs)}" || echo "no")
 Reconstruct : $([[ $PARALLEL -eq 1 && $NO_RECONSTRUCT -eq 0 ]] && echo "yes" || echo "no")
 Args        : ${SOLVER_ARGS[*]:-(none)}
============================================================
EOF

SOLVER_ARGS_STR=""
if [[ ${#SOLVER_ARGS[@]} -gt 0 ]]; then
  for arg in "${SOLVER_ARGS[@]}"; do
    SOLVER_ARGS_STR+=" $(printf '%q' "$arg")"
  done
fi

# Set number of processors for parallel runs
if [[ ${PARALLEL} -eq 1 ]]; then
  NP="${NPROCS:-4}"
else
  NP=""
fi

ENV_VARS=()
if [[ -n "${NP}" ]]; then
  ENV_VARS=(-e "NP=${NP}")
fi

docker compose run --rm "${ENV_VARS[@]}" dev bash -lc "
  source /opt/openfoam8/etc/bashrc
  set -e
  cd /workspace/src/microClimateFoam
  if [[ ${NO_BUILD} -eq 0 ]]; then
    wmake
  fi
  cd /workspace/${CASE_PATH}
  if [[ ${RUN_BLOCKMESH} -eq 1 && -f constant/polyMesh/blockMeshDict ]]; then
    blockMesh
    echo ''
    echo 'Running checkMesh...'
    checkMesh
  fi
  if [[ ${PARALLEL} -eq 1 ]]; then
    echo ''
    echo 'Decomposing mesh for parallel run...'
    if [[ ! -f system/decomposeParDict ]]; then
      NP_VAL=\${NP:-4}
      cat > system/decomposeParDict <<EOFDICT
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}
numberOfSubdomains \${NP_VAL};
method          simple;
simpleCoeffs
{
    n               (\${NP_VAL} 1 1);
    delta           0.001;
}
EOFDICT
    fi
    decomposePar -force
  fi
  rm -f log.${SOLVER}
  if [[ ${PARALLEL} -eq 1 ]]; then
    ${SOLVER} -parallel${SOLVER_ARGS_STR} | tee log.${SOLVER}
  else
    ${SOLVER}${SOLVER_ARGS_STR} | tee log.${SOLVER}
  fi
  if [[ ${PARALLEL} -eq 1 && ${NO_RECONSTRUCT} -eq 0 ]]; then
    echo ''
    echo 'Reconstructing parallel results...'
    reconstructPar
  fi
"

