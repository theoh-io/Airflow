#!/usr/bin/env python3
"""
Generate circular domain blockMeshDict for OpenFOAM.

This script creates a cylindrical domain blockMeshDict based on geometry bounds
and desired clearance. The domain is approximated using an octagon (8-sided polygon)
which can be refined for smoother circular boundaries.

Usage:
    python create_circular_domain.py <geometry_bounds_file> <output_blockMeshDict>
    
    Or use as a module:
    from create_circular_domain import create_circular_blockMeshDict
    create_circular_blockMeshDict(center, radius, z_min, z_max, n_radial, n_circum, n_vertical)
"""

import math
import sys
import os


def create_circular_blockMeshDict(center_x, center_y, center_z, radius, z_min, z_max,
                                  n_radial=120, n_circum=8, n_vertical=91,
                                  n_vertices=8):
    """
    Create blockMeshDict content for a circular (cylindrical) domain.
    
    Parameters:
    -----------
    center_x, center_y, center_z : float
        Center point of the circular domain
    radius : float
        Radius of the circular domain
    z_min, z_max : float
        Vertical extent of the domain
    n_radial : int
        Number of cells in radial direction
    n_circum : int
        Number of cells in circumferential direction (per octant)
    n_vertical : int
        Number of cells in vertical direction
    n_vertices : int
        Number of vertices used to approximate circle (8 = octagon, 16 = hexadecagon)
        More vertices = smoother circle but more complex mesh
    
    Returns:
    --------
    str : blockMeshDict content
    """
    
    # Calculate vertex positions for bottom and top circles
    vertices_bottom = []
    vertices_top = []
    
    for i in range(n_vertices):
        angle = 2 * math.pi * i / n_vertices
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices_bottom.append((x, y, z_min))
        vertices_top.append((x, y, z_max))
    
    # Generate vertices section
    vertices_str = "vertices\n(\n"
    for v in vertices_bottom:
        vertices_str += f"    ({v[0]:.2f} {v[1]:.2f} {v[2]:.2f})   // {len(vertices_bottom) - len(vertices_bottom) + vertices_bottom.index(v)}\n"
    for v in vertices_top:
        vertices_str += f"    ({v[0]:.2f} {v[1]:.2f} {v[2]:.2f})   // {len(vertices_bottom) + vertices_top.index(v)}\n"
    vertices_str += ");\n"
    
    # Generate blocks section
    # For circular domain, we create one block connecting all vertices
    vertex_list = " ".join([str(i) for i in range(n_vertices * 2)])
    blocks_str = f"""blocks
(
    hex ({vertex_list})
    (
        {n_radial}   // Radial cells
        {n_vertices}  // Circumferential cells (one per octant)
        {n_vertical}  // Vertical cells
    )
    simpleGrading (1 1 1)
);
"""
    
    # Generate arc edges
    edges_str = "edges\n(\n"
    # Bottom circle arcs
    for i in range(n_vertices):
        next_i = (i + 1) % n_vertices
        # Arc center is at domain center
        edges_str += f"    arc {i} {next_i} ({center_x + radius * math.cos(math.pi * (2*i + 1) / n_vertices):.2f} {center_y + radius * math.sin(math.pi * (2*i + 1) / n_vertices):.2f} {z_min:.2f})\n"
    
    # Top circle arcs
    for i in range(n_vertices):
        next_i = (i + 1) % n_vertices
        top_i = i + n_vertices
        top_next = next_i + n_vertices
        edges_str += f"    arc {top_i} {top_next} ({center_x + radius * math.cos(math.pi * (2*i + 1) / n_vertices):.2f} {center_y + radius * math.sin(math.pi * (2*i + 1) / n_vertices):.2f} {z_max:.2f})\n"
    edges_str += ");\n"
    
    # Generate boundary faces
    # Inlet: negative X direction (upstream)
    # Outlet: positive X direction (downstream)
    # Walls: cylindrical surface
    # Ground: bottom circle
    # Top: top circle
    
    # Find inlet and outlet faces based on X direction
    inlet_faces = []
    outlet_faces = []
    wall_faces = []
    
    for i in range(n_vertices):
        next_i = (i + 1) % n_vertices
        top_i = i + n_vertices
        top_next = next_i + n_vertices
        
        # Wall face (radial)
        wall_faces.append(f"            ({i} {next_i} {top_next} {top_i})")
        
        # Determine if this face is inlet or outlet based on X coordinate
        face_center_x = (vertices_bottom[i][0] + vertices_bottom[next_i][0]) / 2
        if face_center_x < center_x:
            inlet_faces.append(f"            ({i} {next_i} {top_next} {top_i})")
        elif face_center_x > center_x:
            outlet_faces.append(f"            ({i} {next_i} {top_next} {top_i})")
    
    # Ground face (bottom circle)
    ground_faces = []
    for i in range(n_vertices - 2):
        ground_faces.append(f"            (0 {i+1} {i+2} 0)")
    
    # Top face (top circle)
    top_faces = []
    top_base = n_vertices
    for i in range(n_vertices - 2):
        top_faces.append(f"            ({top_base} {top_base + i + 1} {top_base + i + 2} {top_base})")
    
    boundary_str = """boundary
(
    inlet
    {
        type patch;
        faces
        (
"""
    boundary_str += "\n".join(inlet_faces) + "\n"
    boundary_str += """        );
    }
    
    outlet
    {
        type patch;
        faces
        (
"""
    boundary_str += "\n".join(outlet_faces) + "\n"
    boundary_str += """        );
    }
    
    walls
    {
        type wall;
        faces
        (
"""
    boundary_str += "\n".join(wall_faces) + "\n"
    boundary_str += """        );
    }
    
    ground
    {
        type wall;
        faces
        (
"""
    boundary_str += "\n".join(ground_faces) + "\n"
    boundary_str += """        );
    }
    
    top
    {
        type patch;
        faces
        (
"""
    boundary_str += "\n".join(top_faces) + "\n"
    boundary_str += """        );
    }
);

mergePatchPairs
(
);

// ************************************************************************* //
"""
    
    # Assemble full blockMeshDict
    header = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  2.2.2                                 |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters 1;

// Circular domain parameters
// Center: ({:.2f}, {:.2f}, {:.2f})
// Radius: {:.2f} m
// Height: {:.2f} m (Z: {:.2f} to {:.2f})
// Cells: {} radial × {} circumferential × {} vertical

""".format(center_x, center_y, center_z, radius, z_max - z_min, z_min, z_max,
           n_radial, n_vertices, n_vertical)
    
    return header + vertices_str + "\n" + blocks_str + "\n" + edges_str + "\n" + boundary_str


def read_geometry_bounds(filepath):
    """Read geometry bounds from a text file."""
    bounds = {}
    with open(filepath, 'r') as f:
        for line in f:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Try to extract numeric values
                try:
                    if 'X:' in key or 'x:' in key.lower():
                        # Parse range like "[-69.06, 82.09]"
                        if '[' in value:
                            values = value.replace('[', '').replace(']', '').split(',')
                            bounds['x_min'] = float(values[0].strip())
                            bounds['x_max'] = float(values[1].strip())
                    elif 'Y:' in key or 'y:' in key.lower():
                        if '[' in value:
                            values = value.replace('[', '').replace(']', '').split(',')
                            bounds['y_min'] = float(values[0].strip())
                            bounds['y_max'] = float(values[1].strip())
                    elif 'Z:' in key or 'z:' in key.lower():
                        if '[' in value:
                            values = value.replace('[', '').replace(']', '').split(',')
                            bounds['z_min'] = float(values[0].strip())
                            bounds['z_max'] = float(values[1].strip())
                except:
                    pass
    return bounds


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 3:
        print("Usage: python create_circular_domain.py <geometry_info_file> <output_blockMeshDict>")
        print("\nExample:")
        print("  python create_circular_domain.py cases/Vidigal_CFD/geometry_info.txt cases/Vidigal_CFD/constant/air/polyMesh/blockMeshDict")
        sys.exit(1)
    
    geometry_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Read geometry bounds
    if os.path.exists(geometry_file):
        bounds = read_geometry_bounds(geometry_file)
        print(f"Read geometry bounds from {geometry_file}")
        print(f"  X: [{bounds.get('x_min', 0)}, {bounds.get('x_max', 0)}]")
        print(f"  Y: [{bounds.get('y_min', 0)}, {bounds.get('y_max', 0)}]")
        print(f"  Z: [{bounds.get('z_min', 0)}, {bounds.get('z_max', 0)}]")
    else:
        print(f"Warning: Geometry file {geometry_file} not found. Using default values.")
        bounds = {
            'x_min': -69.06, 'x_max': 82.09,
            'y_min': -155.27, 'y_max': 148.77,
            'z_min': 133.11, 'z_max': 208.34
        }
    
    # Calculate domain parameters
    center_x = (bounds['x_min'] + bounds['x_max']) / 2
    center_y = (bounds['y_min'] + bounds['y_max']) / 2
    center_z = bounds['z_min']  # Ground level
    
    # Calculate geometry extent
    geom_width = bounds['x_max'] - bounds['x_min']
    geom_depth = bounds['y_max'] - bounds['y_min']
    geom_height = bounds['z_max'] - bounds['z_min']
    
    # Calculate radius (encompass geometry + clearance)
    # Use maximum extent and add clearance (e.g., 5H where H is height)
    H = geom_height
    clearance = 5 * H
    radius = max(geom_width, geom_depth) / 2 + clearance
    
    # Calculate vertical extent
    z_min = bounds['z_min'] - 0.1 * H  # Small clearance below
    z_max = bounds['z_max'] + 5 * H   # 5H clearance above
    
    # Cell counts (adjust based on desired resolution)
    cell_size = 5.0  # meters
    n_radial = int(radius / cell_size)
    n_circum = 8  # 8 cells around circumference (one per octant)
    n_vertical = int((z_max - z_min) / cell_size)
    
    print(f"\nDomain parameters:")
    print(f"  Center: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")
    print(f"  Radius: {radius:.2f} m")
    print(f"  Height: {z_max - z_min:.2f} m (Z: {z_min:.2f} to {z_max:.2f})")
    print(f"  Cells: {n_radial} radial × {8} circumferential × {n_vertical} vertical")
    
    # Generate blockMeshDict
    content = create_circular_blockMeshDict(
        center_x, center_y, center_z,
        radius, z_min, z_max,
        n_radial, n_circum, n_vertical,
        n_vertices=8
    )
    
    # Write output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"\n✓ Created circular domain blockMeshDict: {output_file}")


if __name__ == '__main__':
    main()
