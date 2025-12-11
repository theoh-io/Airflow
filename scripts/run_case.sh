#!/usr/bin/env bash
#
# Generic adaptive case runner for OpenFOAM cases
# Supports single-region and multi-region cases, auto-detects solver, and provides
# various execution modes (quick-validation, quick, full, custom).
#
# Usage:
#   ./scripts/run_case.sh [options] <case-path> [solver [-- solver-args]]
#

set -eo pipefail  # Removed -u to allow unbound variables (needed for OpenFOAM environment)

print_usage() {
  cat <<'EOF'
Usage: run_case.sh [options] <case-path> [solver [-- solver-args]]

Options:
  -n, --no-build          Skip solver build (assumes solver already built)
  -B, --no-mesh           Skip mesh generation
  -p, --parallel [N]      Run in parallel mode (decomposePar, solver -parallel, reconstructPar)
                          Optional N specifies number of processors (default: 4)
  -R, --no-reconstruct    Skip reconstructPar after parallel run
  -v, --verbose           Use verbose solver execution with real-time monitoring
  --quick-validation      Quick validation mode (CI-optimized: deltaT=50s, endTime=50s)
  --quick                 Quick test mode (12 time steps with original deltaT)
  --full                  Full simulation mode (use original controlDict settings)
  --deltaT N              Set custom deltaT (time step size)
  --endTime N             Set custom endTime
  --sanity-check          Run sanity check after solver execution
  -h, --help              Show this help

Positional arguments:
  case-path                Case directory relative to repo root
  solver                   Solver executable (default: auto-detect from controlDict)
  -- solver-args           Everything after '--' is passed directly to the solver

Examples:
  # Basic usage (auto-detect solver)
  ./scripts/run_case.sh cases/streetCanyon_CFD

  # With verbose output
  ./scripts/run_case.sh -v cases/streetCanyon_CFD

  # Quick validation (CI-optimized)
  ./scripts/run_case.sh --quick-validation cases/streetCanyon_CFD

  # Quick test (12 time steps)
  ./scripts/run_case.sh --quick cases/streetCanyon_CFD

  # Custom time settings
  ./scripts/run_case.sh --deltaT 100 --endTime 200 cases/streetCanyon_CFD

  # Parallel execution with verbose output
  ./scripts/run_case.sh -p 4 -v cases/streetCanyon_CFD

  # With sanity check
  ./scripts/run_case.sh -v --sanity-check cases/streetCanyon_CFD
EOF
}

# Default values
NO_BUILD=0
RUN_MESH=1
PARALLEL=0
NPROCS=""
NO_RECONSTRUCT=0
VERBOSE=0
QUICK_VALIDATION=0
QUICK_MODE=0
FULL_MODE=0
CUSTOM_DELTA_T=""
CUSTOM_END_TIME=""
SANITY_CHECK=0

# Parse options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--no-build)
      NO_BUILD=1
      shift
      ;;
    -B|--no-mesh)
      RUN_MESH=0
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
    -v|--verbose)
      VERBOSE=1
      shift
      ;;
    --quick-validation)
      QUICK_VALIDATION=1
      shift
      ;;
    --quick)
      QUICK_MODE=1
      shift
      ;;
    --full)
      FULL_MODE=1
      shift
      ;;
    --deltaT)
      CUSTOM_DELTA_T="$2"
      shift 2
      ;;
    --endTime)
      CUSTOM_END_TIME="$2"
      shift 2
      ;;
    --sanity-check)
      SANITY_CHECK=1
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

# Get solver (auto-detect if not provided)
if [[ $# -gt 0 && "$1" != "--" ]]; then
  SOLVER="$1"
  shift
else
  # Auto-detect solver from controlDict
  if [[ -f "${REPO_ROOT}/${CASE_PATH}/system/controlDict" ]]; then
    SOLVER=$(grep "^application" "${REPO_ROOT}/${CASE_PATH}/system/controlDict" 2>/dev/null | awk '{print $2}' | tr -d ';' || echo "microClimateFoam")
  else
    SOLVER="microClimateFoam"
  fi
fi

if [[ $# -gt 0 && "$1" == "--" ]]; then
  shift
fi

SOLVER_ARGS=()
if [[ $# -gt 0 ]]; then
  SOLVER_ARGS=("$@")
fi

if [[ ! -d "${REPO_ROOT}/${CASE_PATH}" ]]; then
  echo "Error: case directory '${CASE_PATH}' not found from repo root" >&2
  exit 1
fi

# Detect if running in Docker
if [ -f /.dockerenv ] || grep -Eq '/(lxc|docker)/[[:alnum:]]{64}' /proc/self/cgroup 2>/dev/null; then
  RUN_IN_DOCKER=true
else
  RUN_IN_DOCKER=false
fi

# If not in Docker, run inside Docker
if [ "$RUN_IN_DOCKER" = false ]; then
  # Build command with all options
  DOCKER_CMD="bash scripts/run_case.sh"
  [[ $NO_BUILD -eq 1 ]] && DOCKER_CMD+=" -n"
  [[ $RUN_MESH -eq 0 ]] && DOCKER_CMD+=" -B"
  [[ $PARALLEL -eq 1 ]] && DOCKER_CMD+=" -p${NPROCS:+ $NPROCS}"
  [[ $NO_RECONSTRUCT -eq 1 ]] && DOCKER_CMD+=" -R"
  [[ $VERBOSE -eq 1 ]] && DOCKER_CMD+=" -v"
  [[ $QUICK_VALIDATION -eq 1 ]] && DOCKER_CMD+=" --quick-validation"
  [[ $QUICK_MODE -eq 1 ]] && DOCKER_CMD+=" --quick"
  [[ $FULL_MODE -eq 1 ]] && DOCKER_CMD+=" --full"
  [[ -n "$CUSTOM_DELTA_T" ]] && DOCKER_CMD+=" --deltaT $CUSTOM_DELTA_T"
  [[ -n "$CUSTOM_END_TIME" ]] && DOCKER_CMD+=" --endTime $CUSTOM_END_TIME"
  [[ $SANITY_CHECK -eq 1 ]] && DOCKER_CMD+=" --sanity-check"
  DOCKER_CMD+=" ${CASE_PATH}"
  [[ -n "$SOLVER" && "$SOLVER" != "microClimateFoam" ]] && DOCKER_CMD+=" $SOLVER"
  [[ ${#SOLVER_ARGS[@]} -gt 0 ]] && DOCKER_CMD+=" -- ${SOLVER_ARGS[*]}"
  
  docker compose run --rm dev bash -c "
    set +u && source /opt/openfoam8/etc/bashrc && set -u
    cd /workspace
    $DOCKER_CMD
  "
  exit $?
fi

# Running inside Docker from here
# OpenFOAM bashrc executes diagnostic pipelines that can return 1; temporarily
# relax -e/pipefail while sourcing, then restore.
set +e
set +o pipefail
set +u  # Temporarily disable for bashrc
source /opt/openfoam8/etc/bashrc
set -u
set -e
set -o pipefail

cd /workspace

# Display configuration
MODE_DESC="Normal"
if [[ $QUICK_VALIDATION -eq 1 ]]; then
  MODE_DESC="Quick validation (CI-optimized)"
elif [[ $QUICK_MODE -eq 1 ]]; then
  MODE_DESC="Quick test (12 time steps)"
elif [[ $FULL_MODE -eq 1 ]]; then
  MODE_DESC="Full simulation"
fi

cat <<EOF
============================================================
OpenFOAM Case Runner
------------------------------------------------------------
Case        : ${CASE_PATH}
Solver      : ${SOLVER} (auto-detected)
Mode        : ${MODE_DESC}
Build       : $([[ $NO_BUILD -eq 0 ]] && echo "Yes" || echo "Skip")
Mesh        : $([[ $RUN_MESH -eq 1 ]] && echo "Generate" || echo "Skip")
Parallel    : $([[ $PARALLEL -eq 1 ]] && echo "yes${NPROCS:+ (${NPROCS} procs)}" || echo "no")
Reconstruct : $([[ $PARALLEL -eq 1 && $NO_RECONSTRUCT -eq 0 ]] && echo "yes" || echo "no")
Verbose     : $([[ $VERBOSE -eq 1 ]] && echo "yes" || echo "no")
Sanity Check: $([[ $SANITY_CHECK -eq 1 ]] && echo "yes" || echo "no")
Args        : ${SOLVER_ARGS[*]:-(none)}
============================================================
EOF

cd "${CASE_PATH}"

# Build solver if needed
if [[ $NO_BUILD -eq 0 ]]; then
  echo ""
  echo "Building solver: ${SOLVER}..."
  cd /workspace
  bash scripts/build_all_solvers.sh "${SOLVER}" 2>&1 | tee /tmp/build.log | grep -E '(Building|up to date|built successfully|build failed)' || true
  echo ""
fi

# Ensure PATH includes FOAM_USER_APPBIN
export PATH=$FOAM_USER_APPBIN:$PATH

# Verify solver exists
if [ ! -f "$FOAM_USER_APPBIN/${SOLVER}" ]; then
  echo "✗ Error: Solver not found at $FOAM_USER_APPBIN/${SOLVER}"
  echo "  Please build the solver first or run without --no-build"
  exit 1
fi

cd "${CASE_PATH}"

# Detect if multi-region case
MULTI_REGION=false
PRIMARY_REGION=""
if [ -f "constant/regionProperties" ]; then
  MULTI_REGION=true
  # Get first region (typically 'air')
  PRIMARY_REGION=$(grep -A 10 "^regions" constant/regionProperties 2>/dev/null | grep -E "^\s+[a-zA-Z]" | head -1 | awk '{print $1}' | tr -d '();' || echo "air")
  # If the first token is a group name (e.g., 'fluid') but an 'air' region
  # directory exists, prefer 'air' as the primary region to match mesh layout.
  if [ "$PRIMARY_REGION" = "fluid" ] && [ -d "constant/air" ]; then
    PRIMARY_REGION="air"
  fi
elif [ -d "0" ]; then
  # Check if 0/ contains region directories
  REGIONS=$(find 0 -maxdepth 1 -type d ! -name "0" ! -name "polyMesh" ! -name "include" 2>/dev/null | sed 's|0/||' | head -1)
  if [ -n "$REGIONS" ]; then
    MULTI_REGION=true
    PRIMARY_REGION="$REGIONS"
  fi
fi

# Generate mesh if needed
if [[ $RUN_MESH -eq 1 ]]; then
  echo ""
  if [ "$MULTI_REGION" = true ]; then
    # Multi-region case
    echo "Multi-region case detected (primary region: ${PRIMARY_REGION})"
    MESH_DIR="constant/${PRIMARY_REGION}/polyMesh"
    BLOCKMESH_DICT="constant/${PRIMARY_REGION}/polyMesh/blockMeshDict"
    
    if [ -f "${BLOCKMESH_DICT}" ]; then
      if [ -f "${MESH_DIR}/points" ]; then
        if [ "${BLOCKMESH_DICT}" -nt "${MESH_DIR}/points" ]; then
          echo "Mesh exists but blockMeshDict is newer, regenerating mesh..."
          blockMesh -region "${PRIMARY_REGION}" > /tmp/blockMesh.log 2>&1 || {
            echo "✗ blockMesh FAILED"
            cat /tmp/blockMesh.log
            exit 1
          }
          if [ -f "system/${PRIMARY_REGION}/createPatchDict" ] || [ -f "system/createPatchDict" ]; then
            createPatch -region "${PRIMARY_REGION}" -overwrite > /tmp/createPatch.log 2>&1 || {
              echo "✗ createPatch FAILED"
              cat /tmp/createPatch.log
              exit 1
            }
          fi
          echo "✓ Mesh regenerated"
        else
          echo "✓ Mesh already exists and is up to date (skipping generation)"
        fi
      else
        echo "Generating mesh for region ${PRIMARY_REGION}..."
        blockMesh -region "${PRIMARY_REGION}" > /tmp/blockMesh.log 2>&1 || {
          echo "✗ blockMesh FAILED"
          cat /tmp/blockMesh.log
          exit 1
        }
        if [ -f "system/${PRIMARY_REGION}/createPatchDict" ] || [ -f "system/createPatchDict" ]; then
          createPatch -region "${PRIMARY_REGION}" -overwrite > /tmp/createPatch.log 2>&1 || {
            echo "✗ createPatch FAILED"
            cat /tmp/createPatch.log
            exit 1
          }
        fi
        echo "✓ Mesh ready"
      fi
    else
      echo "⚠ Warning: blockMeshDict not found for region ${PRIMARY_REGION}, skipping mesh generation"
    fi
  else
    # Single-region case
    if [ -f "constant/polyMesh/blockMeshDict" ]; then
      if [ -f "constant/polyMesh/points" ]; then
        if [ "constant/polyMesh/blockMeshDict" -nt "constant/polyMesh/points" ]; then
          echo "Mesh exists but blockMeshDict is newer, regenerating mesh..."
          blockMesh > /tmp/blockMesh.log 2>&1 || {
            echo "✗ blockMesh FAILED"
            cat /tmp/blockMesh.log
            exit 1
          }
          echo "✓ Mesh regenerated"
        else
          echo "✓ Mesh already exists and is up to date (skipping generation)"
        fi
      else
        echo "Generating mesh..."
        blockMesh > /tmp/blockMesh.log 2>&1 || {
          echo "✗ blockMesh FAILED"
          cat /tmp/blockMesh.log
          exit 1
        }
        echo "✓ Mesh ready"
      fi
      echo ""
      echo "Running checkMesh..."
      checkMesh > /tmp/checkMesh.log 2>&1 || {
        echo "✗ checkMesh FAILED"
        cat /tmp/checkMesh.log
        exit 1
      }
      if grep -q "Mesh OK" /tmp/checkMesh.log; then
        echo "✓ Mesh quality OK"
      else
        echo "⚠ Mesh quality warnings (check log)"
      fi
    else
      echo "⚠ Warning: blockMeshDict not found, skipping mesh generation"
    fi
  fi
  echo ""
fi

# Configure controlDict if needed
CONTROLDICT_MODIFIED=0
if [[ $QUICK_VALIDATION -eq 1 || $QUICK_MODE -eq 1 || -n "$CUSTOM_DELTA_T" || -n "$CUSTOM_END_TIME" ]]; then
  if [ ! -f "system/controlDict" ]; then
    echo "⚠ Warning: controlDict not found, skipping modification"
  else
    echo "Configuring controlDict..."
    cp system/controlDict system/controlDict.orig
    CONTROLDICT_MODIFIED=1
    
    if [[ $QUICK_VALIDATION -eq 1 ]]; then
      # Quick validation mode: optimized for CI (3-5 minutes)
      DELTA_T="50"
      END_TIME="50"
      echo "  Quick validation mode (CI-optimized):"
      echo "    deltaT: ${DELTA_T}s"
      echo "    endTime: ${END_TIME}s (1 time step)"
      echo "    Expected runtime: 3-5 minutes"
    elif [[ -n "$CUSTOM_DELTA_T" && -n "$CUSTOM_END_TIME" ]]; then
      # Custom deltaT and endTime
      DELTA_T="$CUSTOM_DELTA_T"
      END_TIME="$CUSTOM_END_TIME"
      echo "  Custom configuration:"
      echo "    deltaT: ${DELTA_T}s"
      echo "    endTime: ${END_TIME}s"
    elif [[ -n "$CUSTOM_END_TIME" ]]; then
      # Custom endTime only
      DELTA_T=$(grep "^deltaT" system/controlDict | awk '{print $2}' | tr -d ';' || echo "3600")
      END_TIME="$CUSTOM_END_TIME"
      echo "  Custom endTime: ${END_TIME}s"
      echo "    deltaT: ${DELTA_T}s (unchanged)"
    elif [[ -n "$CUSTOM_DELTA_T" ]]; then
      # Custom deltaT only
      DELTA_T="$CUSTOM_DELTA_T"
      END_TIME=$(grep "^endTime" system/controlDict | awk '{print $2}' | tr -d ';' || echo "86400")
      echo "  Custom deltaT: ${DELTA_T}s"
      echo "    endTime: ${END_TIME}s (unchanged)"
    elif [[ $QUICK_MODE -eq 1 ]]; then
      # Quick test: run 12 time steps with original deltaT
      DELTA_T=$(grep "^deltaT" system/controlDict | awk '{print $2}' | tr -d ';' || echo "3600")
      DELTA_T_INT=${DELTA_T%.*}
      END_TIME=$((DELTA_T_INT * 12))
      echo "  Quick test mode:"
      echo "    deltaT: ${DELTA_T}s"
      echo "    endTime: ${END_TIME}s (12 time steps)"
      echo "    Note: This may take 1-6 hours. Use --quick-validation for faster CI testing."
    fi
    
    # Apply changes
    sed -i "s/^deltaT[[:space:]]*[0-9.]*;/deltaT ${DELTA_T};/" system/controlDict
    sed -i "s/^endTime[[:space:]]*[0-9.]*;/endTime ${END_TIME};/" system/controlDict
    sed -i 's/^writeInterval[[:space:]]*[0-9.]*;/writeInterval 1;/' system/controlDict
    # Ensure we start from 0 for quick validation to guarantee a new time step
    if [[ $QUICK_VALIDATION -eq 1 ]]; then
      sed -i 's/^startFrom[[:space:]]*.*/startFrom       startTime;/' system/controlDict
      sed -i 's/^startTime[[:space:]]*[0-9.]*;/startTime       0;/' system/controlDict
      # Reduce maxFluidIteration for faster completion in quick validation
      if grep -q "^maxFluidIteration" system/controlDict; then
        sed -i 's/^maxFluidIteration[[:space:]]*[0-9.]*;/maxFluidIteration    100;/' system/controlDict
        echo "  maxFluidIteration: 100 (reduced for quick validation)"
      fi
      echo "  startFrom: startTime (ensuring run from time 0)"
    fi
    echo "  writeInterval: 1 (writing at every time step)"
    echo ""
  fi
fi

# Parallel setup
if [[ $PARALLEL -eq 1 ]]; then
  echo "Setting up parallel execution..."
  NP="${NPROCS:-4}"
  
  if [ "$MULTI_REGION" = true ]; then
    # Multi-region parallel
    if [[ ! -f "system/decomposeParDict" ]]; then
      cat > system/decomposeParDict <<EOFDICT
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}
numberOfSubdomains ${NP};
method          simple;
simpleCoeffs
{
    n               (${NP} 1 1);
    delta           0.001;
}
EOFDICT
    fi
    decomposePar -allRegions -force > /tmp/decomposePar.log 2>&1 || {
      echo "✗ decomposePar FAILED"
      cat /tmp/decomposePar.log
      exit 1
    }
  else
    # Single-region parallel
    if [[ ! -f "system/decomposeParDict" ]]; then
      cat > system/decomposeParDict <<EOFDICT
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}
numberOfSubdomains ${NP};
method          simple;
simpleCoeffs
{
    n               (${NP} 1 1);
    delta           0.001;
}
EOFDICT
    fi
    decomposePar -force > /tmp/decomposePar.log 2>&1 || {
      echo "✗ decomposePar FAILED"
      cat /tmp/decomposePar.log
      exit 1
    }
  fi
  echo ""
fi

# Run solver
echo "Starting solver..."
echo "Solver command will be: $FOAM_USER_APPBIN/${SOLVER}"
rm -f log.${SOLVER}

SOLVER_CMD="$FOAM_USER_APPBIN/${SOLVER}"
if [[ $PARALLEL -eq 1 ]]; then
  SOLVER_CMD+=" -parallel"
fi

# Add solver args
SOLVER_ARGS_STR=""
if [[ ${#SOLVER_ARGS[@]} -gt 0 ]]; then
  for arg in "${SOLVER_ARGS[@]}"; do
    SOLVER_ARGS_STR+=" $(printf '%q' "$arg")"
  done
  SOLVER_CMD+="${SOLVER_ARGS_STR}"
fi

if [[ $VERBOSE -eq 1 ]]; then
  # Use verbose execution
  REGION_ARG=""
  if [ "$MULTI_REGION" = true ] && [ -n "$PRIMARY_REGION" ]; then
    REGION_ARG="$PRIMARY_REGION"
  fi
  if ! bash /workspace/scripts/run_solver_verbose.sh "$SOLVER_CMD" "$(pwd)" "$REGION_ARG" 2>&1 | tee /tmp/solver.log; then
    echo ""
    echo "✗ Solver execution FAILED"
    echo "Last 30 lines of output:"
    tail -30 /tmp/solver.log
    [[ $CONTROLDICT_MODIFIED -eq 1 ]] && mv system/controlDict.orig system/controlDict
    exit 1
  fi
else
  # Simple execution
  if ! $SOLVER_CMD 2>&1 | tee log.${SOLVER}; then
    echo ""
    echo "✗ Solver execution FAILED"
    [[ $CONTROLDICT_MODIFIED -eq 1 ]] && mv system/controlDict.orig system/controlDict
    exit 1
  fi
fi

# Restore original controlDict if modified
if [[ $CONTROLDICT_MODIFIED -eq 1 ]]; then
  mv system/controlDict.orig system/controlDict
fi

# Parallel reconstruction
if [[ $PARALLEL -eq 1 && $NO_RECONSTRUCT -eq 0 ]]; then
  echo ""
  echo "Reconstructing parallel results..."
  if [ "$MULTI_REGION" = true ]; then
    reconstructPar -allRegions > /tmp/reconstructPar.log 2>&1 || {
      echo "✗ reconstructPar FAILED"
      cat /tmp/reconstructPar.log
      exit 1
    }
  else
    reconstructPar > /tmp/reconstructPar.log 2>&1 || {
      echo "✗ reconstructPar FAILED"
      cat /tmp/reconstructPar.log
      exit 1
    }
  fi
  echo "✓ Reconstruction complete"
fi

echo ""
echo "✓ Solver completed"
echo ""

# Sanity check
if [[ $SANITY_CHECK -eq 1 ]]; then
  echo "Running sanity check..."
  
  # Determine first time step
  if [[ $QUICK_VALIDATION -eq 1 ]]; then
    SANITY_TIME="50"
  elif [[ -n "$CUSTOM_END_TIME" ]]; then
    DELTA_T=$(grep "^deltaT" system/controlDict 2>/dev/null | awk '{print $2}' | tr -d ';' || echo "3600")
    DELTA_T_INT=${DELTA_T%.*}
    SANITY_TIME=$DELTA_T_INT
  else
    DELTA_T=$(grep "^deltaT" system/controlDict 2>/dev/null | awk '{print $2}' | tr -d ';' || echo "3600")
    DELTA_T_INT=${DELTA_T%.*}
    SANITY_TIME=$DELTA_T_INT
  fi
  
  if [ "$MULTI_REGION" = true ] && [ -n "$PRIMARY_REGION" ]; then
    if [ -d "${SANITY_TIME}/${PRIMARY_REGION}" ]; then
      echo "Checking time step ${SANITY_TIME} (${PRIMARY_REGION} region)..."
      SANITY_FIELDS=("U" "p_rgh" "T" "h")
      ALL_PRESENT=true
      for field in "${SANITY_FIELDS[@]}"; do
        if [ ! -f "${SANITY_TIME}/${PRIMARY_REGION}/$field" ]; then
          echo "  ⚠ Missing: $field"
          ALL_PRESENT=false
        fi
      done
      if [ "$ALL_PRESENT" = true ]; then
        echo "  ✓ All fields present at time ${SANITY_TIME}"
      fi
    else
      echo "  ⚠ Time directory ${SANITY_TIME}/${PRIMARY_REGION} not found"
    fi
  else
    if [ -d "${SANITY_TIME}" ]; then
      echo "Checking time step ${SANITY_TIME}..."
      SANITY_FIELDS=("U" "p" "T")
      ALL_PRESENT=true
      for field in "${SANITY_FIELDS[@]}"; do
        if [ ! -f "${SANITY_TIME}/$field" ]; then
          echo "  ⚠ Missing: $field"
          ALL_PRESENT=false
        fi
      done
      if [ "$ALL_PRESENT" = true ]; then
        echo "  ✓ All fields present at time ${SANITY_TIME}"
      fi
    else
      echo "  ⚠ Time directory ${SANITY_TIME} not found"
    fi
  fi
  echo ""
fi

# Show time directories
echo "Time directories created:"
if [ "$MULTI_REGION" = true ] && [ -n "$PRIMARY_REGION" ]; then
  ls -1d [0-9]*/${PRIMARY_REGION} 2>/dev/null | sed "s|/${PRIMARY_REGION}||" | sort -n | head -15
else
  ls -1d [0-9]* 2>/dev/null | sort -n | head -15
fi
echo ""
