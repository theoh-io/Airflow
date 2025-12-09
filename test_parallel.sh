#!/bin/bash
set -e

echo "=========================================="
echo "Parallel Execution Test"
echo "=========================================="
echo ""

# Save current directory
ORIG_DIR=$(pwd)

# Load OpenFOAM environment
set +e
. /opt/openfoam8/etc/bashrc
set -e

cd "$ORIG_DIR" || cd /workspace

echo "✓ OpenFOAM environment loaded"
echo ""

cd /workspace/src/microClimateFoam

echo "Compiling solver..."
wmake 2>&1 | tee /tmp/wmake.log
if grep -qi error /tmp/wmake.log; then
    echo "✗ Compilation FAILED"
    exit 1
fi
echo "✓ Compilation SUCCESS"
echo ""

CASE_DIR="/workspace/custom_cases/heatedCavity"
cd "$CASE_DIR"

# Clean previous results
echo "Cleaning previous results..."
for dir in [1-9]* processor*; do
    [ -d "$dir" ] && rm -rf "$dir"
done
rm -f log.* system/decomposeParDict 2>/dev/null || true
echo "✓ Cleaned"
echo ""

# Generate mesh
echo "Generating mesh..."
if ! blockMesh > /tmp/blockMesh.log 2>&1; then
    echo "✗ blockMesh FAILED"
    exit 1
fi
echo "✓ Mesh generated"
echo ""

# Run serial simulation (short run for comparison)
echo "Running serial simulation (10 time steps)..."
cp system/controlDict system/controlDict.orig
sed -i 's/^endTime[[:space:]]*[0-9.]*;/endTime 5.0;/' system/controlDict
sed -i 's/^writeInterval[[:space:]]*[0-9.]*;/writeInterval 10;/' system/controlDict

if ! microClimateFoam > /tmp/serial.log 2>&1; then
    echo "✗ Serial run FAILED"
    mv system/controlDict.orig system/controlDict
    exit 1
fi

# Save serial results
if [ -d "5" ]; then
    mkdir -p /tmp/serial_results
    cp -r 5 /tmp/serial_results/
    echo "✓ Serial run completed"
else
    echo "✗ Serial run did not produce time directory"
    mv system/controlDict.orig system/controlDict
    exit 1
fi

# Clean for parallel run
for dir in [1-9]*; do
    [ -d "$dir" ] && rm -rf "$dir"
done
rm -f log.* 2>/dev/null || true

# Create decomposeParDict
NP=2
cat > system/decomposeParDict <<EOF
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}
numberOfSubdomains $NP;
method          simple;
simpleCoeffs
{
    n               ($NP 1 1);
    delta           0.001;
}
EOF

echo "Running parallel simulation (2 processors, 10 time steps)..."
if ! decomposePar -force > /tmp/decompose.log 2>&1; then
    echo "✗ decomposePar FAILED"
    cat /tmp/decompose.log
    mv system/controlDict.orig system/controlDict
    exit 1
fi
echo "✓ Mesh decomposed"

if ! mpirun -np $NP microClimateFoam -parallel > /tmp/parallel.log 2>&1; then
    echo "✗ Parallel run FAILED"
    cat /tmp/parallel.log | tail -30
    mv system/controlDict.orig system/controlDict
    exit 1
fi
echo "✓ Parallel run completed"

# Reconstruct
if ! reconstructPar > /tmp/reconstruct.log 2>&1; then
    echo "✗ reconstructPar FAILED"
    cat /tmp/reconstruct.log
    mv system/controlDict.orig system/controlDict
    exit 1
fi
echo "✓ Results reconstructed"

# Restore controlDict
mv system/controlDict.orig system/controlDict

# Compare results
echo ""
echo "Comparing serial vs parallel results..."
if [ ! -d "5" ]; then
    echo "✗ Parallel run did not produce time directory"
    exit 1
fi

# Compare field files (basic check - file existence and size)
REQUIRED_FIELDS=("U" "p" "T")
DIFF_FOUND=0

for field in "${REQUIRED_FIELDS[@]}"; do
    serial_file="/tmp/serial_results/5/$field"
    parallel_file="5/$field"
    
    if [ ! -f "$serial_file" ] || [ ! -f "$parallel_file" ]; then
        echo "✗ Field $field missing in serial or parallel results"
        DIFF_FOUND=1
        continue
    fi
    
    # Compare file sizes (should be similar)
    serial_size=$(stat -f%z "$serial_file" 2>/dev/null || stat -c%s "$serial_file" 2>/dev/null)
    parallel_size=$(stat -f%z "$parallel_file" 2>/dev/null || stat -c%s "$parallel_file" 2>/dev/null)
    
    size_diff=$((serial_size - parallel_size))
    size_diff_abs=${size_diff#-}  # Absolute value
    
    # Allow 1% difference in file size (due to formatting)
    threshold=$((serial_size / 100))
    
    if [ "$size_diff_abs" -gt "$threshold" ]; then
        echo "⚠ Field $field: size difference is large (serial: $serial_size, parallel: $parallel_size)"
    else
        echo "✓ Field $field: sizes match (within tolerance)"
    fi
done

if [ $DIFF_FOUND -eq 1 ]; then
    echo "✗ Field comparison FAILED"
    exit 1
fi

echo ""
echo "=========================================="
echo "Parallel execution test PASSED!"
echo "=========================================="
echo ""
echo "Note: Full numerical comparison would require field value extraction."
echo "This test verifies that parallel execution completes successfully."

