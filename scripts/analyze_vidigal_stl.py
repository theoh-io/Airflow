#!/usr/bin/env python3
"""
Analyze STL geometry to determine bounds and maximum height (H)
for Vidigal_CFD case configuration.
"""

import sys
import os
import struct

def read_binary_stl_bounds(stl_path):
    """Read binary STL and extract bounding box."""
    bounds = {
        'x_min': float('inf'), 'x_max': float('-inf'),
        'y_min': float('inf'), 'y_max': float('-inf'),
        'z_min': float('inf'), 'z_max': float('-inf')
    }
    
    with open(stl_path, 'rb') as f:
        # Skip 80-byte header
        header = f.read(80)
        
        # Read triangle count (4 bytes, unsigned int)
        triangle_count = struct.unpack('<I', f.read(4))[0]
        
        print(f"Reading {triangle_count} triangles...")
        
        # Each triangle: 12 floats (normal vector) + 9 floats (3 vertices) + 2 bytes attribute
        for i in range(triangle_count):
            # Skip normal vector (12 bytes)
            f.read(12)
            
            # Read 3 vertices (9 floats = 36 bytes)
            for _ in range(3):
                x, y, z = struct.unpack('<fff', f.read(12))
                
                bounds['x_min'] = min(bounds['x_min'], x)
                bounds['x_max'] = max(bounds['x_max'], x)
                bounds['y_min'] = min(bounds['y_min'], y)
                bounds['y_max'] = max(bounds['y_max'], y)
                bounds['z_min'] = min(bounds['z_min'], z)
                bounds['z_max'] = max(bounds['z_max'], z)
            
            # Skip 2-byte attribute
            f.read(2)
    
    return bounds

def read_ascii_stl_bounds(stl_path):
    """Read ASCII STL and extract bounding box."""
    bounds = {
        'x_min': float('inf'), 'x_max': float('-inf'),
        'y_min': float('inf'), 'y_max': float('-inf'),
        'z_min': float('inf'), 'z_max': float('-inf')
    }
    
    with open(stl_path, 'r') as f:
        lines = f.readlines()
    
    triangle_count = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('vertex'):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    bounds['x_min'] = min(bounds['x_min'], x)
                    bounds['x_max'] = max(bounds['x_max'], x)
                    bounds['y_min'] = min(bounds['y_min'], y)
                    bounds['y_max'] = max(bounds['y_max'], y)
                    bounds['z_min'] = min(bounds['z_min'], z)
                    bounds['z_max'] = max(bounds['z_max'], z)
                except ValueError:
                    continue
        elif line.startswith('facet'):
            triangle_count += 1
    
    print(f"Read {triangle_count} triangles from ASCII STL")
    return bounds

def analyze_stl(stl_path):
    """Analyze STL file and return geometry information."""
    print(f"Analyzing STL file: {stl_path}")
    print("=" * 60)
    
    if not os.path.exists(stl_path):
        print(f"Error: STL file not found: {stl_path}")
        return None
    
    # Determine if binary or ASCII
    is_binary = False
    with open(stl_path, 'rb') as f:
        header = f.read(80)
        # Check if header contains only printable ASCII
        try:
            header.decode('ascii')
            # Check if it starts with 'solid'
            if header[:5].lower() == b'solid':
                is_binary = False
            else:
                # Likely binary if header doesn't start with 'solid'
                is_binary = True
        except UnicodeDecodeError:
            is_binary = True
    
    print(f"STL Format: {'Binary' if is_binary else 'ASCII'}")
    
    try:
        if is_binary:
            bounds = read_binary_stl_bounds(stl_path)
        else:
            bounds = read_ascii_stl_bounds(stl_path)
    except Exception as e:
        print(f"Error reading STL file: {e}")
        return None
    
    # Calculate dimensions
    dims = {
        'x': bounds['x_max'] - bounds['x_min'],
        'y': bounds['y_max'] - bounds['y_min'],
        'z': bounds['z_max'] - bounds['z_min']
    }
    
    # Maximum height (H)
    H = dims['z']
    
    print("\n" + "=" * 60)
    print("GEOMETRY BOUNDS:")
    print("=" * 60)
    print(f"X-direction: [{bounds['x_min']:.2f}, {bounds['x_max']:.2f}]  (length: {dims['x']:.2f} m)")
    print(f"Y-direction: [{bounds['y_min']:.2f}, {bounds['y_max']:.2f}]  (width:  {dims['y']:.2f} m)")
    print(f"Z-direction: [{bounds['z_min']:.2f}, {bounds['z_max']:.2f}]  (height: {dims['z']:.2f} m)")
    print("\n" + "=" * 60)
    print("KEY PARAMETERS:")
    print("=" * 60)
    print(f"Maximum Height (H): {H:.2f} m")
    print(f"\nDomain boundaries based on H = {H:.2f} m:")
    print(f"  Inlet (before):    5*H = {5*H:.2f} m")
    print(f"  Outlet (after):   15*H = {15*H:.2f} m")
    print(f"  Sides (each):      5*H = {5*H:.2f} m  (total: 10*H = {10*H:.2f} m)")
    print(f"  Top (above):       5*H = {5*H:.2f} m")
    
    # Calculate domain bounds
    domain_bounds = {
        'x_min': bounds['x_min'] - 5*H,
        'x_max': bounds['x_max'] + 15*H,
        'y_min': bounds['y_min'] - 5*H,
        'y_max': bounds['y_max'] + 5*H,
        'z_min': bounds['z_min'],  # Ground level
        'z_max': bounds['z_max'] + 5*H
    }
    
    print("\n" + "=" * 60)
    print("COMPUTATIONAL DOMAIN BOUNDS:")
    print("=" * 60)
    print(f"X: [{domain_bounds['x_min']:.2f}, {domain_bounds['x_max']:.2f}]")
    print(f"Y: [{domain_bounds['y_min']:.2f}, {domain_bounds['y_max']:.2f}]")
    print(f"Z: [{domain_bounds['z_min']:.2f}, {domain_bounds['z_max']:.2f}]")
    
    domain_dims = {
        'x': domain_bounds['x_max'] - domain_bounds['x_min'],
        'y': domain_bounds['y_max'] - domain_bounds['y_min'],
        'z': domain_bounds['z_max'] - domain_bounds['z_min']
    }
    print(f"\nDomain dimensions:")
    print(f"  Length (X): {domain_dims['x']:.2f} m")
    print(f"  Width  (Y): {domain_dims['y']:.2f} m")
    print(f"  Height (Z): {domain_dims['z']:.2f} m")
    
    return {
        'geometry_bounds': bounds,
        'geometry_dims': dims,
        'H': H,
        'domain_bounds': domain_bounds,
        'domain_dims': domain_dims
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_vidigal_stl.py <path-to-stl-file>")
        print("Example: python3 analyze_vidigal_stl.py cases/Vidigal_CFD/constant/triSurface/vidigal.stl")
        sys.exit(1)
    
    stl_path = sys.argv[1]
    result = analyze_stl(stl_path)
    
    if result:
        print("\n" + "=" * 60)
        print("✓ Analysis complete!")
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)

