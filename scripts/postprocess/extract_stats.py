#!/usr/bin/env python3
"""
Extract statistics from OpenFOAM case results.

Usage:
    python scripts/postprocess/extract_stats.py <case-directory> [time-directory]

Example:
    python scripts/postprocess/extract_stats.py custom_cases/heatedCavity 200
"""

import sys
import os
import numpy as np
from pathlib import Path

try:
    import pyvista as pv
    HAS_PYVISTA = True
except ImportError:
    HAS_PYVISTA = False
    print("Warning: pyvista not available. Install with: pip install pyvista")
    print("Falling back to basic file reading...")

def read_field_file(field_path):
    """Read OpenFOAM field file and extract values."""
    if not os.path.exists(field_path):
        return None
    
    values = []
    in_data_section = False
    bracket_count = 0
    collecting = False
    
    with open(field_path, 'r') as f:
        content = f.read()
    
    # Find internalField section
    start_idx = content.find('internalField')
    if start_idx == -1:
        return None
    
    # Skip to the data (after 'uniform' or 'nonuniform')
    data_start = content.find('uniform', start_idx)
    if data_start == -1:
        data_start = content.find('nonuniform', start_idx)
        if data_start == -1:
            return None
        # For nonuniform, find the list
        list_start = content.find('(', data_start)
        if list_start == -1:
            return None
        # Extract all numbers from the list
        i = list_start + 1
        current_num = ""
        while i < len(content) and content[i] != ';':
            char = content[i]
            if char in '0123456789.+-eE':
                current_num += char
            elif current_num:
                try:
                    values.append(float(current_num))
                except ValueError:
                    pass
                current_num = ""
            i += 1
        if current_num:
            try:
                values.append(float(current_num))
            except ValueError:
                pass
    else:
        # For uniform, extract the single value
        value_start = data_start + len('uniform')
        # Skip whitespace
        while value_start < len(content) and content[value_start] in ' \t\n':
            value_start += 1
        # Extract number
        num_str = ""
        i = value_start
        while i < len(content) and content[i] not in ' \t\n;':
            num_str += content[i]
            i += 1
        if num_str:
            try:
                values.append(float(num_str))
            except ValueError:
                pass
    
    return np.array(values) if values else None

def extract_stats_pyvista(case_dir, time_dir):
    """Extract statistics using PyVista (preferred method)."""
    case_path = Path(case_dir)
    time_path = case_path / time_dir
    
    if not time_path.exists():
        print(f"Error: Time directory '{time_path}' does not exist")
        return None
    
    # Try to read as OpenFOAM case
    try:
        reader = pv.OpenFOAMReader(str(case_path / f"{case_path.name}.foam"))
        reader.set_active_time_value(float(time_dir))
        mesh = reader.read()
        
        stats = {}
        for field_name in ['U', 'p', 'T']:
            if field_name in mesh.array_names:
                data = mesh[field_name]
                if data.ndim == 1:
                    # Scalar field
                    stats[field_name] = {
                        'min': float(np.min(data)),
                        'max': float(np.max(data)),
                        'mean': float(np.mean(data)),
                        'std': float(np.std(data))
                    }
                elif data.ndim == 2:
                    # Vector field - compute magnitude
                    magnitude = np.linalg.norm(data, axis=1)
                    stats[field_name] = {
                        'min': float(np.min(magnitude)),
                        'max': float(np.max(magnitude)),
                        'mean': float(np.mean(magnitude)),
                        'std': float(np.std(magnitude))
                    }
        
        return stats
    except Exception as e:
        print(f"PyVista reading failed: {e}")
        return None

def extract_stats_basic(case_dir, time_dir):
    """Extract statistics using basic file reading (fallback)."""
    case_path = Path(case_dir)
    time_path = case_path / time_dir
    
    stats = {}
    
    # Read temperature
    T_path = time_path / 'T'
    T_data = read_field_file(T_path)
    if T_data is not None:
        stats['T'] = {
            'min': float(np.min(T_data)),
            'max': float(np.max(T_data)),
            'mean': float(np.mean(T_data)),
            'std': float(np.std(T_data))
        }
    
    # Read pressure
    p_path = time_path / 'p'
    p_data = read_field_file(p_path)
    if p_data is not None:
        stats['p'] = {
            'min': float(np.min(p_data)),
            'max': float(np.max(p_data)),
            'mean': float(np.mean(p_data)),
            'std': float(np.std(p_data))
        }
    
    # Read velocity (vector field - simplified)
    U_path = time_path / 'U'
    if U_path.exists():
        # For vector fields, we'd need more complex parsing
        # This is a simplified version
        stats['U'] = {
            'note': 'Vector field - magnitude statistics require PyVista'
        }
    
    return stats

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    case_dir = sys.argv[1]
    time_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Find latest time directory if not specified
    if time_dir is None:
        case_path = Path(case_dir)
        time_dirs = [d for d in case_path.iterdir() 
                    if d.is_dir() and d.name.replace('.', '').isdigit()]
        if not time_dirs:
            print(f"Error: No time directories found in '{case_dir}'")
            sys.exit(1)
        time_dir = max(time_dirs, key=lambda x: float(x.name)).name
        print(f"Using latest time directory: {time_dir}")
    
    # Try PyVista first, fall back to basic reading
    if HAS_PYVISTA:
        stats = extract_stats_pyvista(case_dir, time_dir)
        if stats is None:
            stats = extract_stats_basic(case_dir, time_dir)
    else:
        stats = extract_stats_basic(case_dir, time_dir)
    
    if not stats:
        print("Error: Could not extract statistics")
        sys.exit(1)
    
    # Print results
    print(f"\nField Statistics for {case_dir} at time {time_dir}")
    print("=" * 60)
    for field_name, field_stats in stats.items():
        print(f"\n{field_name}:")
        if 'note' in field_stats:
            print(f"  {field_stats['note']}")
        else:
            print(f"  Min:  {field_stats['min']:.6e}")
            print(f"  Max:  {field_stats['max']:.6e}")
            print(f"  Mean: {field_stats['mean']:.6e}")
            print(f"  Std:  {field_stats['std']:.6e}")
    
    # Save to CSV
    csv_path = Path(case_dir) / f"stats_{time_dir}.csv"
    with open(csv_path, 'w') as f:
        f.write("Field,Min,Max,Mean,Std\n")
        for field_name, field_stats in stats.items():
            if 'note' not in field_stats:
                f.write(f"{field_name},{field_stats['min']:.6e},"
                       f"{field_stats['max']:.6e},{field_stats['mean']:.6e},"
                       f"{field_stats['std']:.6e}\n")
    
    print(f"\nStatistics saved to: {csv_path}")

if __name__ == '__main__':
    main()

