#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated image generation for ParaView visualization pipeline.

This script generates standard visualization images without opening ParaView GUI,
using headless rendering via paraview.simple API.

Usage:
    python scripts/postprocess/generate_images.py <case-directory> [time-directory] [options]

Options:
    --output-dir DIR    Output directory for images (default: images/)
    --width W          Image width in pixels (default: 1200)
    --height H         Image height in pixels (default: 800)
    --no-overview      Skip overview image generation
    --fields FIELDS    Comma-separated list of fields to visualize (default: T,U,p)

Example:
    python scripts/postprocess/generate_images.py custom_cases/heatedCavity 200
    python scripts/postprocess/generate_images.py custom_cases/heatedCavity 200 --output-dir results/images
"""

import sys
import os
import argparse
import time
import math

def isfinite(x):
    """Check if a number is finite (works across Python versions)."""
    try:
        return math.isfinite(x) if hasattr(math, 'isfinite') else (x == x and abs(x) != float('inf'))
    except:
        return False

try:
    import paraview.simple as pv
    HAS_PARAVIEW = True
except ImportError:
    HAS_PARAVIEW = False
    print("Error: paraview.simple not available.")
    print("This script must be run with pvpython (ParaView's Python interpreter).")
    print("Run: docker compose run --rm dev pvpython scripts/postprocess/generate_images.py ...")
    print("Or use the wrapper: ./scripts/postprocess/generate_images.sh ...")
    sys.exit(1)


def get_domain_size(source):
    """
    Get the domain size from a ParaView source.
    Returns: (x_size, y_size, z_size, characteristic_length)
    """
    try:
        source.UpdatePipeline()
        dataInfo = source.GetDataInformation()
        if dataInfo:
            bounds = dataInfo.GetBounds()
            if bounds and len(bounds) >= 6:
                x_size = abs(bounds[1] - bounds[0])
                y_size = abs(bounds[3] - bounds[2])
                z_size = abs(bounds[5] - bounds[4])
                # Characteristic length is the largest dimension
                char_length = max(x_size, y_size, z_size)
                return (x_size, y_size, z_size, char_length)
    except:
        pass
    return (None, None, None, None)


def is_3d_case(bounds, case_path=None):
    """
    Determine if a case is 3D (has significant vertical extent) or 2D.
    
    Args:
        bounds: Domain bounds [x_min, x_max, y_min, y_max, z_min, z_max] or None
        case_path: Optional case directory path for fallback detection
    
    Returns:
        True if 3D case (should generate vertical slices), False if 2D case
    """
    # First check known cases (most reliable)
    if case_path:
        case_name = os.path.basename(case_path)
        known_3d_cases = ['streetCanyon_CFD', 'streetcanyon', 'Vidigal_CFD', 'vidigal']
        known_2d_cases = ['heatedCavity', 'heatedcavity']
        
        if any(name.lower() in case_name.lower() for name in known_3d_cases):
            return True
        if any(name.lower() in case_name.lower() for name in known_2d_cases):
            return False
    
    # Then check bounds if available
    if bounds and len(bounds) >= 6:
        x_size = abs(bounds[1] - bounds[0])
        y_size = abs(bounds[3] - bounds[2])
        z_size = abs(bounds[5] - bounds[4])
        
        # Calculate aspect ratio: Z / max(X, Y)
        max_horizontal = max(x_size, y_size)
        if max_horizontal > 0:
            aspect_ratio = z_size / max_horizontal
            # If vertical dimension is > 10% of horizontal, consider it 3D
            return aspect_ratio > 0.1
    
    # Default: assume 2D if uncertain
    return False


def get_domain_bounds_and_center(source, case_path=None):
    """
    Get the domain bounds and center from a ParaView source.
    Returns: (bounds, center) where:
        bounds = [x_min, x_max, y_min, y_max, z_min, z_max]
        center = [x_center, y_center, z_center]
    
    For OpenFOAM readers, ParaView bounds are often invalid until data is rendered.
    We try multiple methods: ParaView bounds, reading from mesh, or case-specific defaults.
    """
    # Method 1: Try to get bounds from ParaView (may not work for OpenFOAM readers)
    try:
        source.UpdatePipeline()
        
        # Create a temporary slice to force data loading
        # Try to get better initial guess from case_path if available
        initial_guess = [100.0, 100.0, 30.0]  # Default guess
        if case_path:
            case_name = os.path.basename(case_path)
            if 'Vidigal' in case_name or 'vidigal' in case_name:
                # Vidigal_CFD domain center approximation
                initial_guess = [382.67, -3.25, 358.80]
        
        temp_slice = pv.Slice(Input=source)
        temp_slice.SliceType = 'Plane'
        temp_slice.SliceType.Origin = initial_guess
        temp_slice.SliceType.Normal = [0.0, 0.0, 1.0]
        temp_slice.UpdatePipeline()
        
        # Try getting bounds from slice (sometimes more reliable)
        sliceInfo = temp_slice.GetDataInformation()
        if sliceInfo:
            bounds = sliceInfo.GetBounds()
            if bounds and len(bounds) >= 6:
                max_valid = 1e10
                if all(isfinite(b) and abs(b) < max_valid for b in bounds):
                    if bounds[0] < bounds[1] and bounds[2] < bounds[3] and bounds[4] < bounds[5]:
                        # These are slice bounds, but we can use them to estimate domain
                        # For a horizontal slice, X and Y bounds should be correct
                        # Z bounds will be limited to slice plane, so we'll estimate full domain
                        # Assume domain extends reasonably in Z
                        z_span = max(bounds[5] - bounds[4], 10.0)  # At least 10m
                        full_bounds = [
                            bounds[0], bounds[1],  # X
                            bounds[2], bounds[3],  # Y
                            bounds[4] - z_span/2, bounds[5] + z_span/2  # Z (extended)
                        ]
                        center = [
                            (full_bounds[0] + full_bounds[1]) / 2.0,
                            (full_bounds[2] + full_bounds[3]) / 2.0,
                            (full_bounds[4] + full_bounds[5]) / 2.0
                        ]
                        pv.Delete(temp_slice)
                        return (full_bounds, center)
        
        pv.Delete(temp_slice)
    except:
        try:
            pv.Delete(temp_slice)
        except:
            pass
    
    # Method 2: Try reading from case directory if provided
    if case_path:
        try:
            # Try to read bounds from geometry_info.txt if available
            geometry_info_path = os.path.join(case_path, 'geometry_info.txt')
            if os.path.exists(geometry_info_path):
                try:
                    with open(geometry_info_path, 'r') as f:
                        content = f.read()
                        # Parse domain bounds from geometry_info.txt
                        # Format: X: [-445.21, 1210.54]
                        import re
                        x_match = re.search(r'X:\s*\[([-\d.]+),\s*([-\d.]+)\]', content)
                        y_match = re.search(r'Y:\s*\[([-\d.]+),\s*([-\d.]+)\]', content)
                        z_match = re.search(r'Z:\s*\[([-\d.]+),\s*([-\d.]+)\]', content)
                        if x_match and y_match and z_match:
                            bounds = [
                                float(x_match.group(1)), float(x_match.group(2)),  # X
                                float(y_match.group(1)), float(y_match.group(2)),  # Y
                                float(z_match.group(1)), float(z_match.group(2))   # Z
                            ]
                            center = [
                                (bounds[0] + bounds[1]) / 2.0,
                                (bounds[2] + bounds[3]) / 2.0,
                                (bounds[4] + bounds[5]) / 2.0
                            ]
                            print("  Using bounds from geometry_info.txt")
                            return (bounds, center)
                except:
                    pass
            
            # Try to read bounds from checkMesh output or mesh files
            # This is a fallback - we'll use known defaults for common cases
            case_name = os.path.basename(case_path)
            
            # Known case bounds (from checkMesh output)
            # Format: (bounds, center) where bounds = [x_min, x_max, y_min, y_max, z_min, z_max]
            known_bounds = {
                'streetCanyon_CFD': ([0, 230, 0, 250, 0, 60], [115, 125, 30]),
                'heatedCavity': ([0, 1, 0, 1, 0, 0.01], [0.5, 0.5, 0.005]),
                'Vidigal_CFD': ([-445.21, 1210.54, -531.42, 524.92, 133.11, 584.49], [382.67, -3.25, 358.80]),
            }
            
            # Also check if case name contains these strings (for variations)
            for known_name, (known_b, known_c) in known_bounds.items():
                if known_name.lower() in case_name.lower():
                    bounds, center = known_b, known_c
                    print("  Using known bounds for case (matched): {}".format(known_name))
                    return (bounds, center)
            
            if case_name in known_bounds:
                bounds, center = known_bounds[case_name]
                print("  Using known bounds for case: {}".format(case_name))
                return (bounds, center)
        except:
            pass
    
    return (None, None)


def calculate_adaptive_velocity_scale(velocity_max, domain_size, target_vector_length_ratio=0.03):
    """
    Calculate adaptive scale factor for velocity vectors.
    
    Args:
        velocity_max: Maximum velocity magnitude (m/s)
        domain_size: Characteristic domain size (m)
        target_vector_length_ratio: Desired vector length as fraction of domain (default: 3%)
    
    Returns:
        Scale factor to use for glyphs
    """
    if velocity_max is None or velocity_max <= 0:
        # Default for very small velocities
        return 1.0
    
    if domain_size is None or domain_size <= 0:
        # Default domain size assumption
        domain_size = 1.0
    
    # Target vector length (as fraction of domain)
    target_length = domain_size * target_vector_length_ratio
    
    # Calculate scale factor: scale_factor * velocity_max = target_length
    if velocity_max > 0:
        scale_factor = target_length / velocity_max
    else:
        scale_factor = 1.0
    
    # Clamp to reasonable range based on domain size
    # For large domains (100m+), use smaller scale factors
    # For small domains (<10m), use larger scale factors
    if domain_size > 100:
        # Large domain: scale factor should be relatively small
        scale_factor = max(0.1, min(scale_factor, 10.0))
    elif domain_size > 10:
        # Medium domain
        scale_factor = max(0.5, min(scale_factor, 50.0))
    else:
        # Small domain: can use larger scale factors
        scale_factor = max(1.0, min(scale_factor, 500.0))
    
    return scale_factor


def calculate_adaptive_stride(num_points, target_num_vectors=500):
    """
    Calculate adaptive stride based on mesh density.
    
    Args:
        num_points: Number of points in the slice
        target_num_vectors: Target number of vectors to display
    
    Returns:
        Stride value (show every Nth point)
    """
    if num_points is None or num_points <= 0:
        return 5  # Default
    
    stride = max(1, int(num_points / target_num_vectors))
    # Clamp stride to reasonable range
    stride = max(1, min(stride, 20))
    
    return stride


def get_data_range(source, array_name, use_points=True):
    """
    Get the data range for a given array from a source.
    
    Args:
        source: ParaView source object
        array_name: Name of the array
        use_points: If True, try POINTS data first, else try CELLS
    
    Returns:
        [min, max] or None if not found
    """
    try:
        source.UpdatePipeline()
        dataInfo = source.GetDataInformation()
        if dataInfo:
            # Try POINTS first if requested
            if use_points:
                pointData = dataInfo.GetPointDataInformation()
                if pointData:
                    for i in range(pointData.GetNumberOfArrays()):
                        arrayInfo = pointData.GetArrayInformation(i)
                        if arrayInfo and arrayInfo.GetName() == array_name:
                            try:
                                return [arrayInfo.GetComponentRange(0)[0], arrayInfo.GetComponentRange(0)[1]]
                            except:
                                try:
                                    # Alternative method
                                    comp_range = arrayInfo.GetComponentRange(0)
                                    if comp_range and len(comp_range) >= 2:
                                        return [comp_range[0], comp_range[1]]
                                except:
                                    pass
            
            # Try CELLS as fallback
            cellData = dataInfo.GetCellDataInformation()
            if cellData:
                for i in range(cellData.GetNumberOfArrays()):
                    arrayInfo = cellData.GetArrayInformation(i)
                    if arrayInfo and arrayInfo.GetName() == array_name:
                        try:
                            return [arrayInfo.GetComponentRange(0)[0], arrayInfo.GetComponentRange(0)[1]]
                        except:
                            try:
                                comp_range = arrayInfo.GetComponentRange(0)
                                if comp_range and len(comp_range) >= 2:
                                    return [comp_range[0], comp_range[1]]
                            except:
                                pass
    except:
        pass
    return None


def get_data_range_legacy(source, array_name):
    """Legacy function for backward compatibility."""
    return get_data_range(source, array_name, use_points=False)

def load_stl_geometry(case_path, renderView):
    """
    Helper function to load and display STL geometry.
    
    Args:
        case_path: Case directory path
        renderView: ParaView render view
    
    Returns:
        (stl_reader, stl_display, stl_bounds) or (None, None, None) if not found
    """
    stl_reader = None
    stl_display = None
    stl_bounds = None
    
    if not case_path:
        return (None, None, None)
    
    stl_path = os.path.join(case_path, 'constant', 'triSurface', 'vidigal.stl')
    if not os.path.exists(stl_path):
        # Try to find any STL file
        tri_surface_dir = os.path.join(case_path, 'constant', 'triSurface')
        if os.path.isdir(tri_surface_dir):
            for f in os.listdir(tri_surface_dir):
                if f.endswith('.stl'):
                    stl_path = os.path.join(tri_surface_dir, f)
                    break
    
    if os.path.exists(stl_path):
        try:
            stl_reader = pv.STLReader(FileNames=[stl_path])
            stl_reader.UpdatePipeline()
            
            # Get STL bounds
            stl_info = stl_reader.GetDataInformation()
            if stl_info:
                stl_bounds = stl_info.GetBounds()
            
            # Display STL as solid surface
            stl_display = pv.Show(stl_reader, renderView)
            stl_display.Representation = 'Surface'
            stl_display.Opacity = 1.0
            stl_display.DiffuseColor = [0.85, 0.80, 0.75]  # Light beige
            stl_display.AmbientColor = [0.3, 0.3, 0.3]
            stl_display.SpecularColor = [1.0, 1.0, 1.0]
            stl_display.SpecularPower = 30.0
            stl_display.Ambient = 0.3
            stl_display.Diffuse = 0.7
            stl_display.Specular = 0.2
            
            # Render STL on top
            try:
                stl_display.SetRenderOrder(1)
            except:
                pass
            
            return (stl_reader, stl_display, stl_bounds)
        except Exception as e:
            print("  [WARN] Could not load STL: {}".format(str(e)))
            return (None, None, None)
    
    return (None, None, None)

def add_bounding_box_wireframe(bounds, renderView):
    """
    Add a wireframe bounding box to show geometry or domain boundaries.
    
    Typically used to display STL geometry bounds, with fallback to domain bounds.
    
    Args:
        bounds: List of 6 values [x_min, x_max, y_min, y_max, z_min, z_max]
        renderView: ParaView render view
    
    Returns:
        box_source object or None if bounds invalid
    """
    if not bounds or len(bounds) < 6:
        return None
    
    try:
        x_min, x_max = bounds[0], bounds[1]
        y_min, y_max = bounds[2], bounds[3]
        z_min, z_max = bounds[4], bounds[5]
        
        # Create a box source for the bounding box
        box_source = pv.Box()
        box_source.XLength = abs(x_max - x_min)
        box_source.YLength = abs(y_max - y_min)
        box_source.ZLength = abs(z_max - z_min)
        box_source.Center = [
            (x_min + x_max) / 2.0,
            (y_min + y_max) / 2.0,
            (z_min + z_max) / 2.0
        ]
        box_source.UpdatePipeline()
        
        # Display as wireframe
        box_display = pv.Show(box_source, renderView)
        box_display.Representation = 'Wireframe'
        box_display.LineWidth = 1.5
        box_display.Opacity = 0.8
        box_display.Color = [0.5, 0.5, 0.5]  # Gray wireframe
        box_display.DiffuseColor = [0.5, 0.5, 0.5]
        
        # Render bounding box first (behind everything)
        try:
            box_display.SetRenderOrder(0)
        except:
            pass
        
        return box_source
    except Exception as e:
        print("  [WARN] Could not create bounding box: {}".format(str(e)))
        return None

def create_temperature_slice(reader, output_path, width=1200, height=800, case_path=None):
    """
    Create a temperature contour slice visualization.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Get domain bounds and center dynamically
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    if center is None:
        # Fallback to default (for backward compatibility)
        slice_origin = [0.5, 0.5, 0.005]
        print("  [WARN] Using default slice origin: {}".format(slice_origin))
    else:
        # Use center of domain, but place slice at mid-height (z_center)
        # For street canyon, we want a horizontal slice through the middle
        slice_origin = [center[0], center[1], center[2]]
        print("  Using slice origin: [{:.2f}, {:.2f}, {:.2f}]".format(*slice_origin))
    
    # Create slice filter
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = slice_origin
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]    # Z-normal for 2D horizontal view
    
    # Update pipeline to get data
    slice1.UpdatePipeline()
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background for better contrast
    
    # Load STL geometry as base (if available)
    stl_reader, stl_display, stl_bounds = load_stl_geometry(case_path, renderView)
    if stl_reader:
        print("  STL geometry loaded as base")
    
    # Add bounding box wireframe to show geometry boundaries (use STL bounds if available)
    bounding_box = None
    if stl_bounds and len(stl_bounds) >= 6:
        bounding_box = add_bounding_box_wireframe(stl_bounds, renderView)
        if bounding_box:
            print("  Geometry bounding box wireframe added")
    elif bounds and len(bounds) >= 6:
        # Fallback to domain bounds if STL not available
        bounding_box = add_bounding_box_wireframe(bounds, renderView)
        if bounding_box:
            print("  Domain bounding box wireframe added")
    
    # Display slice - make it translucent so STL shows through
    sliceDisplay = pv.Show(slice1, renderView)
    sliceDisplay.Representation = 'Surface'
    sliceDisplay.Opacity = 0.6  # Translucent to show STL geometry
    
    # T is a cell array in OpenFOAM, try CELLS first, then POINTS
    try:
        sliceDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        try:
            sliceDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            try:
                sliceDisplay.ColorArrayName = 'T'
            except:
                # Last resort: try without specifying
                pass
    
    # Update to get data range
    renderView.Update()
    pv.Render()
    
    # Set color map (Blue-Red for temperature)
    colorMap = pv.GetColorTransferFunction('T')
    
    # Ensure lookup table is set
    sliceDisplay.LookupTable = colorMap
    
    # Get temperature range adaptively
    dataRange = get_data_range(slice1, 'T', use_points=True)
    
    if dataRange and len(dataRange) >= 2 and dataRange[0] != dataRange[1]:
        minVal = dataRange[0]
        maxVal = dataRange[1]
        range_span = maxVal - minVal
        
        # If range is very wide (>10K), it likely includes boundary values
        # Try to focus on internal field variation
        if range_span > 10.0:
            print("  Detected wide range ({:.2f} K span), likely includes boundaries".format(range_span))
            # Use middle 80% of range to focus on internal field
            range_pad = range_span * 0.1
            minVal = dataRange[0] + range_pad
            maxVal = dataRange[1] - range_pad
            print("  Focusing on internal field: {:.2f} to {:.2f} K".format(minVal, maxVal))
        
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
        print("Temperature range: {:.2f} to {:.2f} K (span: {:.2f} K)".format(minVal, maxVal, maxVal - minVal))
    else:
        # Fallback: use reasonable default range
        minVal = 290.0
        maxVal = 320.0
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
        print("  [WARN] Could not determine temperature range, using default: {:.2f} to {:.2f} K".format(minVal, maxVal))
    
    # Add scalar bar
    scalarBar = pv.GetScalarBar(colorMap, renderView)
    scalarBar.Title = 'Temperature [K]'
    scalarBar.ComponentTitle = ''
    scalarBar.Visibility = 1
    
    # Reset camera and render
    renderView.ResetCamera()
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Temperature slice saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(slice1)
    if bounding_box:
        pv.Delete(bounding_box)
    if stl_reader:
        pv.Delete(stl_reader)
    pv.Delete(renderView)
    
    return output_path


def create_temperature_slice_vertical(reader, output_path, width=1200, height=800, case_path=None):
    """
    Create a vertical (side/elevation) temperature contour slice visualization.
    Shows temperature stratification and vertical flow patterns.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        case_path: Optional case directory path for bounds
    """
    # Get domain bounds and center dynamically
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    if center is None or bounds is None:
        # Fallback to default
        slice_origin = [0.5, 0.5, 0.005]
        print("  [WARN] Using default vertical slice origin: {}".format(slice_origin))
    else:
        # Create vertical slice through center: YZ plane (Normal = [1, 0, 0])
        # This shows side view looking along X-axis
        slice_origin = [center[0], center[1], center[2]]
        print("  Using vertical slice origin: [{:.2f}, {:.2f}, {:.2f}] (YZ plane)".format(*slice_origin))
    
    # Create slice filter - vertical slice (YZ plane)
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = slice_origin
    slice1.SliceType.Normal = [1.0, 0.0, 0.0]    # X-normal for YZ plane (side view)
    
    # Update pipeline to get data
    slice1.UpdatePipeline()
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    # Load STL geometry as base (if available)
    stl_reader, stl_display, stl_bounds = load_stl_geometry(case_path, renderView)
    if stl_reader:
        print("  STL geometry loaded as base")
    
    # Add bounding box wireframe to show geometry boundaries (use STL bounds if available)
    bounding_box = None
    if stl_bounds and len(stl_bounds) >= 6:
        bounding_box = add_bounding_box_wireframe(stl_bounds, renderView)
        if bounding_box:
            print("  Geometry bounding box wireframe added")
    elif bounds and len(bounds) >= 6:
        # Fallback to domain bounds if STL not available
        bounding_box = add_bounding_box_wireframe(bounds, renderView)
        if bounding_box:
            print("  Domain bounding box wireframe added")
    
    # Display slice - make it translucent so STL shows through
    sliceDisplay = pv.Show(slice1, renderView)
    sliceDisplay.Representation = 'Surface'
    sliceDisplay.Opacity = 0.6  # Translucent to show STL geometry
    
    # T is a cell array in OpenFOAM, try CELLS first, then POINTS
    try:
        sliceDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        try:
            sliceDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            try:
                sliceDisplay.ColorArrayName = 'T'
            except:
                pass
    
    # Update to get data range
    renderView.Update()
    pv.Render()
    
    # Set color map (Blue-Red for temperature)
    colorMap = pv.GetColorTransferFunction('T')
    sliceDisplay.LookupTable = colorMap
    
    # Get temperature range adaptively (T is typically a cell array)
    dataRange = get_data_range(slice1, 'T', use_points=False)  # Try cells first
    if not dataRange:
        dataRange = get_data_range(slice1, 'T', use_points=True)  # Fallback to points
    
    if dataRange and len(dataRange) >= 2 and dataRange[0] != dataRange[1]:
        minVal = dataRange[0]
        maxVal = dataRange[1]
        range_span = maxVal - minVal
        
        # If range is very wide (>10K), it likely includes boundary values
        if range_span > 10.0:
            print("  Detected wide range ({:.2f} K span), likely includes boundaries".format(range_span))
            range_pad = range_span * 0.1
            minVal = dataRange[0] + range_pad
            maxVal = dataRange[1] - range_pad
            print("  Focusing on internal field: {:.2f} to {:.2f} K".format(minVal, maxVal))
        
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
        print("Temperature range: {:.2f} to {:.2f} K (span: {:.2f} K)".format(minVal, maxVal, maxVal - minVal))
    else:
        # Fallback: use reasonable default range
        minVal = 290.0
        maxVal = 320.0
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
        print("  [WARN] Could not determine temperature range, using default: {:.2f} to {:.2f} K".format(minVal, maxVal))
    
    # Add scalar bar
    scalarBar = pv.GetScalarBar(colorMap, renderView)
    scalarBar.Title = 'Temperature [K]'
    scalarBar.ComponentTitle = ''
    scalarBar.Visibility = 1
    
    # Reset camera and render
    # For vertical slice, we want to look from the side (along X-axis)
    renderView.ResetCamera()
    
    # Adjust camera for better side view
    camera = renderView.GetActiveCamera()
    # For YZ plane slice, we want to look along X-axis (from the side)
    # Get current camera position and adjust
    current_pos = camera.GetPosition()
    current_focal = camera.GetFocalPoint()
    
    # Position camera to look at slice from side (along X-axis)
    # The slice is in YZ plane, so we want to look along X
    if bounds and len(bounds) >= 6:
        # Position camera to the side (along X-axis)
        # Place camera at a reasonable distance along X
        x_center = (bounds[0] + bounds[1]) / 2.0
        y_center = (bounds[2] + bounds[3]) / 2.0
        z_center = (bounds[4] + bounds[5]) / 2.0
        
        # Camera should be to the side, looking at the slice
        x_size = abs(bounds[1] - bounds[0])
        camera_distance = max(x_size * 1.5, 50.0)  # Distance from slice
        
        camera.SetPosition([x_center + camera_distance, y_center, z_center])
        camera.SetFocalPoint([x_center, y_center, z_center])
        camera.SetViewUp([0.0, 0.0, 1.0])  # Z is up for side view
        camera.OrthogonalizeViewUp()
    
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Temperature vertical slice saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(slice1)
    if bounding_box:
        pv.Delete(bounding_box)
    if stl_reader:
        pv.Delete(stl_reader)
    pv.Delete(renderView)
    
    return output_path


def create_isometric_3d_view(reader, output_path, width=1200, height=800, case_path=None):
    """
    Create an isometric 3D view showing the full domain with temperature contours.
    Uses volume rendering or surface representation to show 3D structure.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        case_path: Optional case directory path for bounds
    """
    # Get domain bounds and center
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    if center is None:
        center = [0.5, 0.5, 0.005]
        print("  [WARN] Using default center for isometric view")
    else:
        print("  Using domain center: [{:.2f}, {:.2f}, {:.2f}]".format(*center))
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    # Load STL geometry as base (if available)
    stl_reader, stl_display, stl_bounds = load_stl_geometry(case_path, renderView)
    if stl_reader:
        print("  STL geometry loaded as base")
    
    # Add bounding box wireframe to show geometry boundaries (use STL bounds if available)
    bounding_box = None
    if stl_bounds and len(stl_bounds) >= 6:
        bounding_box = add_bounding_box_wireframe(stl_bounds, renderView)
        if bounding_box:
            print("  Geometry bounding box wireframe added")
    elif bounds and len(bounds) >= 6:
        # Fallback to domain bounds if STL not available
        bounding_box = add_bounding_box_wireframe(bounds, renderView)
        if bounding_box:
            print("  Domain bounding box wireframe added")
    
    # Display the full mesh (or use a representative slice with transparency)
    # For better visualization, we'll use a slice with some transparency
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = center
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]  # Horizontal slice
    slice1.UpdatePipeline()
    
    # Display slice with transparency to show STL geometry
    sliceDisplay = pv.Show(slice1, renderView)
    sliceDisplay.Representation = 'Surface'
    sliceDisplay.Opacity = 0.6  # Translucent to show STL geometry
    
    # Color by temperature
    try:

        sliceDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        try:
            sliceDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            sliceDisplay.ColorArrayName = 'T'
    
    # Set color map
    colorMap = pv.GetColorTransferFunction('T')
    sliceDisplay.LookupTable = colorMap
    
    # Get temperature range
    dataRange = get_data_range(slice1, 'T', use_points=False)
    if not dataRange:
        dataRange = get_data_range(slice1, 'T', use_points=True)
    
    if dataRange and len(dataRange) >= 2 and dataRange[0] != dataRange[1]:
        minVal = dataRange[0]
        maxVal = dataRange[1]
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
        print("Temperature range: {:.2f} to {:.2f} K".format(minVal, maxVal))
    else:
        minVal = 290.0
        maxVal = 320.0
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,
            midVal, 1.0, 1.0, 1.0,
            maxVal, 1.0, 0.0, 0.0
        ]
        print("  [WARN] Using default temperature range")
    
    # Add scalar bar
    scalarBar = pv.GetScalarBar(colorMap, renderView)
    scalarBar.Title = 'Temperature [K]'
    scalarBar.Visibility = 1
    
    # Set up isometric camera view
    renderView.ResetCamera()
    camera = renderView.GetActiveCamera()
    
    if bounds and len(bounds) >= 6:
        # Calculate domain center and size
        x_center = (bounds[0] + bounds[1]) / 2.0
        y_center = (bounds[2] + bounds[3]) / 2.0
        z_center = (bounds[4] + bounds[5]) / 2.0
        
        x_size = abs(bounds[1] - bounds[0])
        y_size = abs(bounds[3] - bounds[2])
        z_size = abs(bounds[5] - bounds[4])
        max_size = max(x_size, y_size, z_size)
        
        # Position camera for isometric view (45 degrees elevation, 45 degrees azimuth)
        # Distance should be enough to see the whole domain
        distance = max_size * 2.5
        
        # Isometric view: equal angles (45, 45)
        import math
        elevation = 45.0  # degrees
        azimuth = 45.0    # degrees
        
        # Convert to radians
        elev_rad = math.radians(elevation)
        azim_rad = math.radians(azimuth)
        
        # Calculate camera position
        camera_x = x_center + distance * math.cos(elev_rad) * math.cos(azim_rad)
        camera_y = y_center + distance * math.cos(elev_rad) * math.sin(azim_rad)
        camera_z = z_center + distance * math.sin(elev_rad)
        
        camera.SetPosition([camera_x, camera_y, camera_z])
        camera.SetFocalPoint([x_center, y_center, z_center])
        camera.SetViewUp([0.0, 0.0, 1.0])  # Z is up
        camera.OrthogonalizeViewUp()
    
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Isometric 3D view saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(slice1)
    if bounding_box:
        pv.Delete(bounding_box)
    if stl_reader:
        pv.Delete(stl_reader)
    pv.Delete(renderView)
    
    return output_path


def create_geometry_3d_view(reader, output_path, width=1200, height=800, case_path=None):
    """
    Create a 3D geometry visualization showing walls/buildings with temperature,
    and velocity vectors in the volume.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        case_path: Optional case directory path for bounds
    """
    # Get domain bounds and center
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    if center is None:
        center = [0.5, 0.5, 0.005]
        print("  [WARN] Using default center for geometry view")
    else:
        print("  Using domain center: [{:.2f}, {:.2f}, {:.2f}]".format(*center))
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    # Step 1: Clip the volume first to exclude boundary regions, then extract surfaces
    # This approach preserves walls that are near boundaries but removes inlet/outlet/top
    # Domain bounds: X: 0-230, Y: 0-250, Z: 0-60
    # Strategy: Clip volume to keep interior region, then extract surfaces
    # Keep: Internal surfaces (walls/buildings) and ground (Z=0)
    
    # Get domain bounds
    if not bounds or len(bounds) < 6:
        # Try to get from case_path
        if case_path:
            case_name = os.path.basename(case_path)
            if 'Vidigal' in case_name or 'vidigal' in case_name:
                # Vidigal_CFD bounds
                x_min, x_max = -445.21, 1210.54
                y_min, y_max = -531.42, 524.92
                z_min, z_max = 133.11, 584.49
            else:
                # Fallback bounds for streetCanyon_CFD
                x_min, x_max = 0.0, 230.0
                y_min, y_max = 0.0, 250.0
                z_min, z_max = 0.0, 60.0
        else:
            # Fallback bounds for streetCanyon_CFD
            x_min, x_max = 0.0, 230.0
            y_min, y_max = 0.0, 250.0
            z_min, z_max = 0.0, 60.0
    else:
        x_min, x_max = bounds[0], bounds[1]
        y_min, y_max = bounds[2], bounds[3]
        z_min, z_max = bounds[4], bounds[5]
    
    # Calculate adaptive buffer based on domain size
    # For large domains (like Vidigal_CFD), use percentage-based buffer
    x_size = abs(x_max - x_min)
    y_size = abs(y_max - y_min)
    z_size = abs(z_max - z_min)
    max_size = max(x_size, y_size, z_size)
    
    # Adaptive buffer: 1% of domain size, but at least 0.5m and at most 50m
    buffer = max(0.5, min(max_size * 0.01, 50.0))
    print("  Using adaptive buffer: {:.2f} m (domain size: {:.2f} m)".format(buffer, max_size))
    
    # Method 1: Try patch-based extraction (more precise)
    # Extract only the "ground" patch explicitly
    try:
        # Enable patch selection in reader
        reader.EnablePatches = 1
        reader.UpdatePipeline()
        
        # Try to extract only ground patch using ExtractBlock
        # This is more precise than clipping
        extractBlock = pv.ExtractBlock(Input=reader)
        # We'll filter by patch name - but ParaView might need patch indices
        # For now, use clipping approach but with better buffer
        
        # Use clipping with adaptive buffer
        clip_volume = pv.Clip(Input=reader)
        clip_volume.ClipType = 'Box'
        clip_volume.ClipType.Bounds = [
            x_min + buffer, x_max - buffer,  # X: exclude boundaries
            y_min + buffer, y_max - buffer,  # Y: exclude side boundaries
            z_min, z_max - buffer             # Z: exclude top, keep ground
        ]
        clip_volume.Invert = 0  # Keep inside the box
        clip_volume.UpdatePipeline()
        
        # Extract surfaces from clipped volume
        extractSurface = pv.ExtractSurface(Input=clip_volume)
        extractSurface.UpdatePipeline()
        filteredSurface = extractSurface
        
    except:
        # Fallback: use clipping approach
        clip_volume = pv.Clip(Input=reader)
        clip_volume.ClipType = 'Box'
        clip_volume.ClipType.Bounds = [
            x_min + buffer, x_max - buffer,
            y_min + buffer, y_max - buffer,
            z_min, z_max - buffer
        ]
        clip_volume.Invert = 0
        clip_volume.UpdatePipeline()
        
        extractSurface = pv.ExtractSurface(Input=clip_volume)
        extractSurface.UpdatePipeline()
        filteredSurface = extractSurface
    
    # Display filtered surfaces - adjust opacity based on case
    # For large domains (Vidigal_CFD), use lower opacity to see through boundaries
    # For smaller domains, use higher opacity
    if max_size > 500:  # Large domain like Vidigal_CFD
        surface_opacity = 0.5  # More opaque for large domains
        edge_opacity = 0.8  # Stronger edges
    else:
        surface_opacity = 0.3  # More transparent for small domains
        edge_opacity = 1.0
    
    surfaceDisplay = pv.Show(filteredSurface, renderView)
    surfaceDisplay.Representation = 'Surface'
    surfaceDisplay.Opacity = surface_opacity
    # Use edge highlighting to maintain geometry visibility
    surfaceDisplay.EdgeColor = [0.0, 0.0, 0.0]  # Black edges for definition
    # Note: EdgeOpacity not available in ParaView, using edge color only
    
    # Color surfaces by temperature
    try:
        surfaceDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        try:
            surfaceDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            surfaceDisplay.ColorArrayName = 'T'
    
    # Set color map for temperature
    colorMap = pv.GetColorTransferFunction('T')
    surfaceDisplay.LookupTable = colorMap
    
    # Get temperature range from filtered surfaces
    # Try to get range from filtered surface first
    dataRange = get_data_range(filteredSurface, 'T', use_points=False)
    if not dataRange:
        dataRange = get_data_range(filteredSurface, 'T', use_points=True)
    
    # If still no range, try getting from original extractSurface (before clipping)
    if not dataRange:
        dataRange = get_data_range(extractSurface, 'T', use_points=False)
        if not dataRange:
            dataRange = get_data_range(extractSurface, 'T', use_points=True)
    
    if dataRange and len(dataRange) >= 2 and dataRange[0] != dataRange[1]:
        minVal = dataRange[0]
        maxVal = dataRange[1]
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
        print("  Temperature range on surfaces: {:.2f} to {:.2f} K".format(minVal, maxVal))
    else:
        minVal = 290.0
        maxVal = 320.0
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,
            midVal, 1.0, 1.0, 1.0,
            maxVal, 1.0, 0.0, 0.0
        ]
        print("  [WARN] Using default temperature range")
    
    # Step 3: Add streamlines to show flow (no volume rendering, no glyphs)
    # Streamlines show flow around and above the canyon
    # Use the clipped volume for streamlines to focus on canyon region
    
    # Create line source for seed points
    line1 = pv.Line()
    if bounds and len(bounds) >= 6:
        # Seed line: from inlet side, across domain, at mid-height
        # For Vidigal_CFD, seed from inlet (x_min) to interior
        if max_size > 500:  # Large domain
            # Multiple seed lines for better coverage
            line1.Point1 = [x_min + buffer * 2, y_min + buffer, center[2]]
            line1.Point2 = [x_min + buffer * 2, y_max - buffer, center[2]]
            line1.Resolution = 20  # More seed points for large domain
        else:
            line1.Point1 = [x_min + buffer, y_min, center[2]]
            line1.Point2 = [x_max - buffer, y_max, center[2]]
            line1.Resolution = 15
    else:
        line1.Point1 = [0.5, 0.0, center[2]]
        line1.Point2 = [229.5, 250.0, center[2]]
        line1.Resolution = 15
    
    # Create stream tracer
    streamTracer1 = pv.StreamTracer(Input=clip_volume, SeedType=line1)
    
    # Set velocity field
    try:
        streamTracer1.Vectors = ['CELLS', 'U']
    except:
        streamTracer1.Vectors = ['POINTS', 'U']
    
    # Adaptive streamline length based on domain size
    x_size, y_size, z_size, char_length = get_domain_size(clip_volume)
    if char_length and char_length > 0:
        if max_size > 500:  # Large domain like Vidigal_CFD
            max_length = max(char_length * 0.3, 50.0)  # 30% of length, min 50m
            max_length = min(max_length, 1000.0)  # Cap at 1000m for large domains
        else:
            max_length = max(char_length * 0.5, 10.0)  # 50% of length, min 10m
            max_length = min(max_length, 500.0)  # Cap at 500m
    else:
        if max_size > 500:
            max_length = 500.0
        else:
            max_length = 100.0
    
    streamTracer1.MaximumStreamlineLength = max_length
    streamTracer1.IntegrationDirection = 'BOTH'
    streamTracer1.UpdatePipeline()
    
    # Display streamlines - make them more visible through transparent surfaces
    # Render streamlines AFTER surfaces so they appear on top
    streamDisplay = pv.Show(streamTracer1, renderView)
    streamDisplay.Representation = 'Surface'
    streamDisplay.LineWidth = 4.0  # Thicker lines for better visibility through transparent surfaces
    streamDisplay.Opacity = 1.0  # Fully opaque streamlines - they should stand out
    # Make streamlines more prominent with tube representation if available
    try:
        streamDisplay.Representation = 'Surface With Edges'
    except:
        pass
    
    # Color streamlines by temperature (from the volume)
    try:
        streamDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        try:
            streamDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            streamDisplay.ColorArrayName = 'T'
    
    # Use same temperature color map for streamlines
    streamDisplay.LookupTable = colorMap
    
    # Add scalar bars
    tempScalarBar = pv.GetScalarBar(colorMap, renderView)
    tempScalarBar.Title = 'Temperature [K]'
    tempScalarBar.Visibility = 1
    tempScalarBar.WindowLocation = 'UpperLeftCorner'
    
    # Set up isometric camera view - zoomed to street canyon region (clipped volume)
    # First, reset camera to the filtered surface bounds (canyon region, not full domain)
    renderView.ResetCamera()
    camera = renderView.GetActiveCamera()
    
    # Get bounds of the filtered surface (canyon region, not full domain)
    surfaceInfo = filteredSurface.GetDataInformation()
    if surfaceInfo:
        surfaceBounds = surfaceInfo.GetBounds()
        if surfaceBounds and len(surfaceBounds) >= 6:
            # Use surface bounds for camera (canyon region)
            x_min_surf, x_max_surf = surfaceBounds[0], surfaceBounds[1]
            y_min_surf, y_max_surf = surfaceBounds[2], surfaceBounds[3]
            z_min_surf, z_max_surf = surfaceBounds[4], surfaceBounds[5]
            
            x_center = (x_min_surf + x_max_surf) / 2.0
            y_center = (y_min_surf + y_max_surf) / 2.0
            z_center = (z_min_surf + z_max_surf) / 2.0
            
            x_size = abs(x_max_surf - x_min_surf)
            y_size = abs(y_max_surf - y_min_surf)
            z_size = abs(z_max_surf - z_min_surf)
            max_size = max(x_size, y_size, z_size)
            
            # Set camera to focus on canyon region
            renderView.CameraFocalPoint = [x_center, y_center, z_center]
            renderView.CameraPosition = [x_center, y_center, z_center + max_size * 1.5]
            renderView.CameraViewUp = [0.0, 1.0, 0.0]
            
            # Isometric view: 45 degrees elevation, 45 degrees azimuth
            import math
            elevation = 45.0
            azimuth = 45.0
            
            elev_rad = math.radians(elevation)
            azim_rad = math.radians(azimuth)
            
            # Zoom in close to canyon - use smaller distance for tighter view
            distance = max_size * 1.2  # Closer camera for better canyon view
            
            camera_x = x_center + distance * math.cos(elev_rad) * math.cos(azim_rad)
            camera_y = y_center + distance * math.cos(elev_rad) * math.sin(azim_rad)
            camera_z = z_center + distance * math.sin(elev_rad)
            
            camera.SetPosition([camera_x, camera_y, camera_z])
            camera.SetFocalPoint([x_center, y_center, z_center])
            camera.SetViewUp([0.0, 0.0, 1.0])
            camera.OrthogonalizeViewUp()
            
            # Zoom to canyon region with tight bounds - focus on canyon, not full domain
            renderView.ResetCamera(surfaceBounds)
            # Additional zoom factor to get closer view
            camera.Zoom(1.5)  # Zoom in 50% more for tighter canyon view
        else:
            # Fallback to domain center
            if bounds and len(bounds) >= 6:
                x_center = (bounds[0] + bounds[1]) / 2.0
                y_center = (bounds[2] + bounds[3]) / 2.0
                z_center = (bounds[4] + bounds[5]) / 2.0
                
                x_size = abs(bounds[1] - bounds[0])
                y_size = abs(bounds[3] - bounds[2])
                z_size = abs(bounds[5] - bounds[4])
                max_size = max(x_size, y_size, z_size)
                
                import math
                elevation = 45.0
                azimuth = 45.0
                elev_rad = math.radians(elevation)
                azim_rad = math.radians(azimuth)
                distance = max_size * 2.0
                
                camera_x = x_center + distance * math.cos(elev_rad) * math.cos(azim_rad)
                camera_y = y_center + distance * math.cos(elev_rad) * math.sin(azim_rad)
                camera_z = z_center + distance * math.sin(elev_rad)
                
                camera.SetPosition([camera_x, camera_y, camera_z])
                camera.SetFocalPoint([x_center, y_center, z_center])
                camera.SetViewUp([0.0, 0.0, 1.0])
                camera.OrthogonalizeViewUp()
    
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Geometry 3D view saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(streamTracer1)
    pv.Delete(line1)
    pv.Delete(filteredSurface)
    if clip_volume:
        pv.Delete(clip_volume)
    pv.Delete(renderView)
    
    return output_path


def create_geometry_focused_view(reader, output_path, width=1200, height=800, case_path=None):
    """
    Create a geometry-focused visualization with STL as the primary element.
    The STL building geometry is displayed prominently with flow field around it.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        case_path: Optional case directory path for bounds and STL location
    """
    # Get domain bounds and center
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    if center is None:
        center = [0.5, 0.5, 0.005]
        print("  [WARN] Using default center for geometry view")
    else:
        print("  Using domain center: [{:.2f}, {:.2f}, {:.2f}]".format(*center))
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    # Step 1: Load STL geometry as the PRIMARY element
    stl_reader = None
    stl_display = None
    stl_bounds = None
    
    if case_path:
        stl_path = os.path.join(case_path, 'constant', 'triSurface', 'vidigal.stl')
        if not os.path.exists(stl_path):
            # Try to find any STL file
            tri_surface_dir = os.path.join(case_path, 'constant', 'triSurface')
            if os.path.isdir(tri_surface_dir):
                for f in os.listdir(tri_surface_dir):
                    if f.endswith('.stl'):
                        stl_path = os.path.join(tri_surface_dir, f)
                        break
        
        if os.path.exists(stl_path):
            try:
                print("  Loading STL geometry: {}".format(os.path.basename(stl_path)))
                stl_reader = pv.STLReader(FileNames=[stl_path])
                stl_reader.UpdatePipeline()
                
                # Get STL bounds for camera positioning
                stl_info = stl_reader.GetDataInformation()
                if stl_info:
                    stl_bounds = stl_info.GetBounds()
                    if stl_bounds:
                        print("  STL bounds: X[{:.1f}, {:.1f}] Y[{:.1f}, {:.1f}] Z[{:.1f}, {:.1f}]".format(
                            stl_bounds[0], stl_bounds[1], stl_bounds[2], stl_bounds[3],
                            stl_bounds[4], stl_bounds[5]))
                
                # Display STL as SOLID SURFACE with edges - this is the main geometry
                stl_display = pv.Show(stl_reader, renderView)
                
                # Use Surface representation (edges can be too cluttered with many vertices)
                # For high-resolution STL files, Surface alone is clearer
                stl_display.Representation = 'Surface'
                
                stl_display.Opacity = 1.0  # Fully opaque - this is what we want to see
                
                # Use a more visible color for buildings - light beige/tan
                stl_display.DiffuseColor = [0.85, 0.80, 0.75]  # Light beige for buildings
                stl_display.AmbientColor = [0.3, 0.3, 0.3]  # Ambient lighting
                stl_display.SpecularColor = [1.0, 1.0, 1.0]  # White specular highlights
                stl_display.SpecularPower = 30.0  # Shiny surface
                
                stl_display.EdgeColor = [0.1, 0.1, 0.1]  # Dark gray edges for definition
                try:
                    stl_display.LineWidth = 0.5  # Thin edges to avoid clutter with many vertices
                except:
                    pass
                
                # Enable lighting for better 3D appearance
                stl_display.Ambient = 0.3
                stl_display.Diffuse = 0.7
                stl_display.Specular = 0.2
                
                print("  [OK] STL geometry loaded and displayed as primary element (light beige with edges)")
            except Exception as e:
                print("  [WARN] Could not load STL geometry: {}".format(str(e)))
                stl_reader = None
        else:
            print("  [WARN] STL file not found, will use mesh surfaces only")
    
    # Step 2: Add flow field visualization around the geometry
    # Use the full volume (or clipped to exclude far boundaries) for streamlines
    if not bounds or len(bounds) < 6:
        if case_path:
            case_name = os.path.basename(case_path)
            if 'Vidigal' in case_name or 'vidigal' in case_name:
                x_min, x_max = -445.21, 1210.54
                y_min, y_max = -531.42, 524.92
                z_min, z_max = 133.11, 584.49
            else:
                x_min, x_max = 0.0, 230.0
                y_min, y_max = 0.0, 250.0
                z_min, z_max = 0.0, 60.0
        else:
            x_min, x_max = 0.0, 230.0
            y_min, y_max = 0.0, 250.0
            z_min, z_max = 0.0, 60.0
    else:
        x_min, x_max = bounds[0], bounds[1]
        y_min, y_max = bounds[2], bounds[3]
        z_min, z_max = bounds[4], bounds[5]
    
    # Calculate buffer for excluding far boundaries (but keep flow field around buildings)
    x_size = abs(x_max - x_min)
    y_size = abs(y_max - y_min)
    z_size = abs(z_max - z_min)
    max_size = max(x_size, y_size, z_size)
    
    # Use moderate buffer to exclude far boundaries but keep flow around buildings
    buffer = max(1.0, min(max_size * 0.05, 200.0))  # 5% buffer, max 200m
    print("  Using buffer: {:.2f} m to exclude far boundaries".format(buffer))
    
    # Clip volume to exclude far boundaries but keep flow around buildings
    clip_volume = pv.Clip(Input=reader)
    clip_volume.ClipType = 'Box'
    clip_volume.ClipType.Bounds = [
        x_min + buffer, x_max - buffer,
        y_min + buffer, y_max - buffer,
        z_min, z_max - buffer
    ]
    clip_volume.Invert = 0
    clip_volume.UpdatePipeline()
    
    # Step 3: Add streamlines to show flow around buildings
    line1 = pv.Line()
    if bounds and len(bounds) >= 6:
        if max_size > 500:
            # Seed streamlines upstream of buildings
            line1.Point1 = [x_min + buffer * 2, y_min + buffer, center[2]]
            line1.Point2 = [x_min + buffer * 2, y_max - buffer, center[2]]
            line1.Resolution = 30  # More seed points for better coverage
        else:
            line1.Point1 = [x_min + buffer, y_min, center[2]]
            line1.Point2 = [x_max - buffer, y_max, center[2]]
            line1.Resolution = 20
    else:
        line1.Point1 = [0.5, 0.0, center[2]]
        line1.Point2 = [229.5, 250.0, center[2]]
        line1.Resolution = 20
    
    streamTracer1 = pv.StreamTracer(Input=clip_volume, SeedType=line1)
    try:
        streamTracer1.Vectors = ['CELLS', 'U']
    except:
        streamTracer1.Vectors = ['POINTS', 'U']
    
    if max_size > 500:
        max_length = max(max_size * 0.4, 100.0)  # Longer streamlines for large domain
        max_length = min(max_length, 1500.0)
    else:
        max_length = max(max_size * 0.6, 20.0)
        max_length = min(max_length, 500.0)
    
    streamTracer1.MaximumStreamlineLength = max_length
    streamTracer1.IntegrationDirection = 'BOTH'
    streamTracer1.UpdatePipeline()
    
    # Display streamlines - these show flow around the STL geometry
    streamDisplay = pv.Show(streamTracer1, renderView)
    streamDisplay.Representation = 'Surface'
    streamDisplay.LineWidth = 3.5  # Thick lines for visibility
    streamDisplay.Opacity = 0.9  # Slightly transparent so STL shows through
    
    # Color streamlines by temperature
    try:
        streamDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        try:
            streamDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            streamDisplay.ColorArrayName = 'T'
    
    # Make streamlines render before STL so buildings are on top
    try:
        streamDisplay.SetRenderOrder(0)  # Render first
    except:
        pass
    
    # Get temperature range from streamlines
    tempRange = get_data_range(streamTracer1, 'T', use_points=True)
    if not tempRange:
        tempRange = get_data_range(clip_volume, 'T', use_points=True)
    
    # Set color map
    colorMap = pv.GetColorTransferFunction('T')
    streamDisplay.LookupTable = colorMap
    
    if tempRange and len(tempRange) >= 2 and tempRange[0] != tempRange[1]:
        minVal = tempRange[0]
        maxVal = tempRange[1]
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,
            midVal, 1.0, 1.0, 1.0,
            maxVal, 1.0, 0.0, 0.0
        ]
        print("  Temperature range: {:.2f} to {:.2f} K".format(minVal, maxVal))
    else:
        minVal = 290.0
        maxVal = 320.0
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,
            midVal, 1.0, 1.0, 1.0,
            maxVal, 1.0, 0.0, 0.0
        ]
    
    # Step 4: Optionally add a transparent slice BELOW buildings to show temperature field
    # This helps visualize the flow field around buildings without obscuring them
    slice1 = None
    if stl_bounds:
        # Create a horizontal slice below building height (ground level)
        slice_z = stl_bounds[4] + 5.0  # Just above ground, below buildings
        slice1 = pv.Slice(Input=clip_volume)
        slice1.SliceType = 'Plane'
        slice1.SliceType.Origin = [center[0], center[1], slice_z]
        slice1.SliceType.Normal = [0.0, 0.0, 1.0]
        slice1.UpdatePipeline()
        
        sliceDisplay = pv.Show(slice1, renderView)
        sliceDisplay.Representation = 'Surface'
        sliceDisplay.Opacity = 0.2  # Very transparent - just to show field, won't obscure STL
        try:
            sliceDisplay.ColorArrayName = ['CELLS', 'T']
        except:
            try:
                sliceDisplay.ColorArrayName = ['POINTS', 'T']
            except:
                sliceDisplay.ColorArrayName = 'T'
        sliceDisplay.LookupTable = colorMap
        
        # Make sure slice renders before STL (lower render order)
        try:
            sliceDisplay.SetRenderOrder(0)  # Render first, behind STL
        except:
            pass
    
    # Add scalar bar
    tempScalarBar = pv.GetScalarBar(colorMap, renderView)
    tempScalarBar.Title = 'Temperature [K]'
    tempScalarBar.Visibility = 1
    tempScalarBar.WindowLocation = 'UpperLeftCorner'
    
    # Step 5: Set up camera to focus on STL geometry
    renderView.ResetCamera()
    camera = renderView.GetActiveCamera()
    
    # Use STL bounds if available, otherwise use domain bounds
    if stl_bounds and len(stl_bounds) >= 6:
        x_center = (stl_bounds[0] + stl_bounds[1]) / 2.0
        y_center = (stl_bounds[2] + stl_bounds[3]) / 2.0
        z_center = (stl_bounds[4] + stl_bounds[5]) / 2.0
        
        x_size = abs(stl_bounds[1] - stl_bounds[0])
        y_size = abs(stl_bounds[3] - stl_bounds[2])
        z_size = abs(stl_bounds[5] - stl_bounds[4])
        max_size = max(x_size, y_size, z_size)
        
        print("  Focusing camera on STL geometry")
    elif bounds and len(bounds) >= 6:
        x_center = (bounds[0] + bounds[1]) / 2.0
        y_center = (bounds[2] + bounds[3]) / 2.0
        z_center = (bounds[4] + bounds[5]) / 2.0
        
        x_size = abs(bounds[1] - bounds[0])
        y_size = abs(bounds[3] - bounds[2])
        z_size = abs(bounds[5] - bounds[4])
        max_size = max(x_size, y_size, z_size)
    else:
        x_center, y_center, z_center = center[0], center[1], center[2]
        max_size = 100.0
    
    # Isometric view focused on geometry
    import math
    elevation = 45.0
    azimuth = 45.0
    elev_rad = math.radians(elevation)
    azim_rad = math.radians(azimuth)
    distance = max_size * 1.8  # Good distance to see geometry and flow
    
    camera_x = x_center + distance * math.cos(elev_rad) * math.cos(azim_rad)
    camera_y = y_center + distance * math.cos(elev_rad) * math.sin(azim_rad)
    camera_z = z_center + distance * math.sin(elev_rad)
    
    camera.SetPosition([camera_x, camera_y, camera_z])
    camera.SetFocalPoint([x_center, y_center, z_center])
    camera.SetViewUp([0.0, 0.0, 1.0])
    camera.OrthogonalizeViewUp()
    
    # Reset camera to STL bounds if available
    if stl_bounds:
        renderView.ResetCamera(stl_bounds)
        camera.Zoom(1.2)  # Slight zoom to focus on buildings
    elif bounds:
        renderView.ResetCamera(bounds)
    
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Geometry-focused view saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(streamTracer1)
    pv.Delete(line1)
    pv.Delete(clip_volume)
    if slice1:
        pv.Delete(slice1)
    if stl_reader:
        pv.Delete(stl_reader)
    pv.Delete(renderView)
    
    return output_path


def create_velocity_vectors(reader, output_path, width=1200, height=800, case_path=None):
    """
    Create a velocity vector visualization using glyphs.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Get domain bounds and center dynamically
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    
    # Create render view first to load STL and get geometry bounds
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    # Load STL geometry as base (if available) to get geometry bounds
    stl_reader, stl_display, stl_bounds = load_stl_geometry(case_path, renderView)
    if stl_reader:
        print("  STL geometry loaded as base")
    
    # Use STL bounds to position slice at geometry height, otherwise use domain center
    if stl_bounds and len(stl_bounds) >= 6:
        # Position slice at mid-height of geometry
        slice_z = (stl_bounds[4] + stl_bounds[5]) / 2.0
        slice_origin = [(stl_bounds[0] + stl_bounds[1]) / 2.0,
                        (stl_bounds[2] + stl_bounds[3]) / 2.0,
                        slice_z]
        print("  Using slice origin at geometry center: [{:.2f}, {:.2f}, {:.2f}]".format(*slice_origin))
    elif center is not None:
        slice_origin = [center[0], center[1], center[2]]
        print("  Using slice origin at domain center: [{:.2f}, {:.2f}, {:.2f}]".format(*slice_origin))
    else:
        slice_origin = [0.5, 0.5, 0.005]
        print("  [WARN] Using default slice origin: {}".format(slice_origin))
    
    # Create slice first
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = slice_origin
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
    
    # Add bounding box wireframe to show geometry boundaries (use STL bounds if available)
    bounding_box = None
    if stl_bounds and len(stl_bounds) >= 6:
        bounding_box = add_bounding_box_wireframe(stl_bounds, renderView)
        if bounding_box:
            print("  Geometry bounding box wireframe added")
    elif bounds and len(bounds) >= 6:
        # Fallback to domain bounds if STL not available
        bounding_box = add_bounding_box_wireframe(bounds, renderView)
        if bounding_box:
            print("  Domain bounding box wireframe added")
    
    # Compute velocity magnitude for coloring
    calculator1 = pv.Calculator(Input=slice1)
    calculator1.ResultArrayName = 'U_mag'
    calculator1.Function = 'mag(U)'
    calculator1.UpdatePipeline()
    
    # Create glyphs with velocity magnitude coloring
    # Use POINTS for better visualization (like we did for temperature)
    glyph2 = pv.Glyph(Input=calculator1, GlyphType='Arrow')
    
    # Try POINTS first, fallback to CELLS
    try:
        glyph2.OrientationArray = ['POINTS', 'U']
        glyph2.ScaleArray = ['POINTS', 'U']
    except:
        glyph2.OrientationArray = ['CELLS', 'U']
        glyph2.ScaleArray = ['CELLS', 'U']
    
    # Get slice info for adaptive stride calculation
    sliceInfo = slice1.GetDataInformation()
    num_points = sliceInfo.GetNumberOfPoints() if sliceInfo else None
    
    # Calculate adaptive stride - use fewer vectors for clearer visualization
    # Focus on geometry area: use STL bounds to estimate area if available
    if stl_bounds and len(stl_bounds) >= 6:
        # Calculate geometry area
        x_size = abs(stl_bounds[1] - stl_bounds[0])
        y_size = abs(stl_bounds[3] - stl_bounds[2])
        geometry_area = x_size * y_size
        # Target much fewer vectors for clearer visualization (80-120 vectors)
        # This provides better clarity without overwhelming the view
        target_num_vectors = max(80, min(120, int(geometry_area / 200.0)))
    else:
        # Default to fewer vectors
        target_num_vectors = 100
    
    # Calculate stride directly to match target number of vectors
    if num_points and num_points > 0:
        stride = max(1, int(num_points / target_num_vectors))
        # Ensure stride is reasonable (not too small, not too large)
        stride = max(10, min(stride, 1000))
    else:
        stride = calculate_adaptive_stride(num_points, target_num_vectors=target_num_vectors)
    
    print("  Slice has {} points, using stride: {} (target: {} vectors, actual: ~{} vectors)".format(
        num_points if num_points else "unknown", stride, target_num_vectors,
        int(num_points / stride) if num_points and stride > 0 else "unknown"))
    
    glyph2.GlyphMode = 'Every Nth Point'
    glyph2.Stride = stride
    
    # Scale factor will be calculated adaptively after we get velocity range (see below)
    
    # Ensure arrow glyph properties are set correctly
    try:
        glyph2.GlyphType.TipResolution = 6
        glyph2.GlyphType.ShaftResolution = 6
        glyph2.GlyphType.TipRadius = 0.1
        glyph2.GlyphType.ShaftRadius = 0.03
    except:
        pass
    glyph2.UpdatePipeline()
    
    # Verify glyphs were created
    try:
        glyphInfo = glyph2.GetDataInformation()
        numGlyphs = glyphInfo.GetNumberOfCells()
        numPoints = glyphInfo.GetNumberOfPoints()
        print("  Created {} glyph cells, {} points".format(numGlyphs, numPoints))
    except:
        print("  [WARN] Could not get glyph information")
    
    # Display glyphs
    glyphDisplay = pv.Show(glyph2, renderView)
    glyphDisplay.Representation = 'Surface'
    
    # Ensure glyphs are visible - set opacity and rendering properties
    glyphDisplay.Opacity = 1.0
    glyphDisplay.Representation = 'Surface'
    try:
        glyphDisplay.LineWidth = 3.0
        glyphDisplay.EdgeColor = [0.0, 0.0, 0.0]  # Black edges for contrast
    except:
        pass
    
    # Force update and render to ensure glyphs are displayed
    renderView.Update()
    pv.Render()
    time.sleep(0.3)  # Give time for rendering
    pv.Render()
    
    # Try POINTS first for coloring
    try:

        glyphDisplay.ColorArrayName = ['POINTS', 'U_mag']
    except:
        glyphDisplay.ColorArrayName = ['CELLS', 'U_mag']
    
    renderView.Update()
    pv.Render()
    
    colorMap = pv.GetColorTransferFunction('U_mag')
    
    # Get velocity magnitude range and domain size for adaptive scaling
    dataRange = get_data_range(calculator1, 'U_mag', use_points=True)
    
    # Get domain size from slice
    x_size, y_size, z_size, char_length = get_domain_size(slice1)
    
    # Calculate adaptive scale factor
    if dataRange and len(dataRange) >= 2 and dataRange[1] > 0:
        maxVal = dataRange[1]
        # Calculate scale factor: target vector length = 7% of domain (adjustable)
        scale_factor = calculate_adaptive_velocity_scale(maxVal, char_length, target_vector_length_ratio=0.07)
        print("  Velocity magnitude range: {:.6e} to {:.6e} m/s".format(dataRange[0], maxVal))
        print("  Domain size: {:.3f} m, calculated scale factor: {:.1f}".format(
            char_length if char_length else 1.0, scale_factor))
        
        # Update scale factor
        glyph2.ScaleFactor = scale_factor
        glyph2.UpdatePipeline()
        
        # Set color map range
        minVal = dataRange[0]
        colorMap.RGBPoints = [
            minVal, 0.267, 0.005, 0.329,  # Dark purple
            maxVal, 0.993, 0.906, 0.144   # Yellow
        ]
    else:
        # Fallback: use domain-size-based default
        if char_length and char_length > 0:
            # For large domains, use smaller scale
            if char_length > 100:
                glyph2.ScaleFactor = 1.0
            elif char_length > 10:
                glyph2.ScaleFactor = 5.0
            else:
                glyph2.ScaleFactor = 50.0
        else:
            glyph2.ScaleFactor = 1.0
        glyph2.UpdatePipeline()
        print("  [WARN] Could not determine velocity range, using default scale factor: {:.2f}".format(glyph2.ScaleFactor))
        try:
            colorMap.ApplyPreset('Viridis (matplotlib)', True)
        except:
            colorMap.RGBPoints = [0.0, 0.267, 0.005, 0.329, 0.0005, 0.993, 0.906, 0.144]
    try:
        colorMap.RescaleTransferFunctionToDataRange(True, False)
    except:
        try:
            pv.UpdateScalarBarRange(colorMap)
        except:
            pass
    
    # Add scalar bar
    scalarBar = pv.GetScalarBar(colorMap, renderView)
    scalarBar.Title = 'Velocity Magnitude [m/s]'
    scalarBar.Visibility = 1
    
    # Focus camera on geometry bounds (STL bounds) if available
    if stl_bounds and len(stl_bounds) >= 6:
        # Reset camera to geometry bounds
        renderView.ResetCamera(stl_bounds)
        camera = renderView.GetActiveCamera()
        # Zoom in slightly to focus on geometry
        camera.Zoom(1.2)
        print("  Camera focused on geometry bounds")
    else:
        # Fallback to domain bounds
        renderView.ResetCamera()
        if bounds and len(bounds) >= 6:
            renderView.ResetCamera(bounds)
    
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Velocity vectors saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(glyph2)
    pv.Delete(calculator1)
    pv.Delete(slice1)
    if bounding_box:
        pv.Delete(bounding_box)
    if stl_reader:
        pv.Delete(stl_reader)
    pv.Delete(renderView)
    
    return output_path


def create_streamlines(reader, output_path, width=1200, height=800, case_path=None):
    """
    Create a streamline visualization.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Get domain bounds and center dynamically
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    if bounds is None or center is None:
        # Fallback to default
        point1 = [0.0, 0.0, 0.005]
        point2 = [0.0, 1.0, 0.005]
        print("  [WARN] Using default seed line: {} to {}".format(point1, point2))
    else:
        # Create seed line along Y-axis at X=0, at mid-height (Z=center[2])
        # Adjust based on actual domain bounds
        point1 = [bounds[0], bounds[2], center[2]]  # Start at min X, min Y, center Z
        point2 = [bounds[0], bounds[3], center[2]]  # End at min X, max Y, center Z
        print("  Using seed line: [{:.2f}, {:.2f}, {:.2f}] to [{:.2f}, {:.2f}, {:.2f}]".format(
            point1[0], point1[1], point1[2], point2[0], point2[1], point2[2]))
    
    # Create line source for seed points
    line1 = pv.Line()
    line1.Point1 = point1
    line1.Point2 = point2
    line1.Resolution = 20
    
    # Create stream tracer
    streamTracer1 = pv.StreamTracer(Input=reader, SeedType=line1)
    streamTracer1.Vectors = ['CELLS', 'U']
    streamTracer1.MaximumStreamlineLength = 2.0
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    # Load STL geometry as base (if available)
    stl_reader, stl_display, stl_bounds = load_stl_geometry(case_path, renderView)
    if stl_reader:
        print("  STL geometry loaded as base")
    
    # Add bounding box wireframe to show geometry boundaries (use STL bounds if available)
    bounding_box = None
    if stl_bounds and len(stl_bounds) >= 6:
        bounding_box = add_bounding_box_wireframe(stl_bounds, renderView)
        if bounding_box:
            print("  Geometry bounding box wireframe added")
    elif bounds and len(bounds) >= 6:
        # Fallback to domain bounds if STL not available
        bounding_box = add_bounding_box_wireframe(bounds, renderView)
        if bounding_box:
            print("  Domain bounding box wireframe added")
    
    streamTracer1.UpdatePipeline()
    
    # Display streamlines colored by temperature - make translucent to show STL
    streamDisplay = pv.Show(streamTracer1, renderView)
    streamDisplay.Representation = 'Surface'
    streamDisplay.LineWidth = 3.0  # Make streamlines visible
    streamDisplay.Opacity = 0.8  # Translucent to show STL geometry
    
    # Try CELLS first (T is typically a cell array), then POINTS
    try:

        streamDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        try:
            streamDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            try:
                streamDisplay.ColorArrayName = 'T'
            except:
                pass
    
    # Check if streamlines were created
    try:
        streamInfo = streamTracer1.GetDataInformation()
        numLines = streamInfo.GetNumberOfCells()
        numPoints = streamInfo.GetNumberOfPoints()
        print("  Created {} streamline cells, {} points".format(numLines, numPoints))
        if numLines == 0:
            print("  [WARN] No streamlines created - check seed line position and velocity field")
    except:
        print("  [WARN] Could not get streamline information")
    
    renderView.Update()
    pv.Render()
    
    # Set color map
    colorMap = pv.GetColorTransferFunction('T')
    
    # Get data range from reader (streamlines use same T field)
    dataRange = get_data_range(reader, 'T')
    if dataRange and len(dataRange) >= 2:
        minVal = dataRange[0]
        maxVal = dataRange[1]
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
    else:
        colorMap.RGBPoints = [285.0, 0.0, 0.0, 1.0, 300.0, 1.0, 1.0, 1.0, 315.0, 1.0, 0.0, 0.0]
    
    # Add scalar bar
    scalarBar = pv.GetScalarBar(colorMap, renderView)
    scalarBar.Title = 'Temperature [K]'
    scalarBar.Visibility = 1
    
    # Reset camera and render
    renderView.ResetCamera()
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Streamlines saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(streamTracer1)
    pv.Delete(line1)
    if bounding_box:
        pv.Delete(bounding_box)
    if stl_reader:
        pv.Delete(stl_reader)
    pv.Delete(renderView)
    
    return output_path


def create_overview(reader, output_path, width=2400, height=1600, case_path=None, is_3d=False):
    """
    Create a combined visualization with temperature slice and velocity vectors overlaid.
    For 3D cases, can show both plan and elevation views side-by-side.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        case_path: Optional case directory path for bounds
        is_3d: If True, case is 3D and may benefit from multiple views
    """
    # Get domain bounds and center dynamically
    bounds, center = get_domain_bounds_and_center(reader, case_path)
    if center is None:
        slice_origin = [0.5, 0.5, 0.005]
        print("  [WARN] Using default slice origin: {}".format(slice_origin))
    else:
        slice_origin = [center[0], center[1], center[2]]
        print("  Using slice origin: [{:.2f}, {:.2f}, {:.2f}]".format(*slice_origin))
    
    # Create slice
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = slice_origin
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    # Load STL geometry as base (if available)
    stl_reader, stl_display, stl_bounds = load_stl_geometry(case_path, renderView)
    if stl_reader:
        print("  STL geometry loaded as base")
    
    # Add bounding box wireframe to show geometry boundaries (use STL bounds if available)
    bounding_box = None
    if stl_bounds and len(stl_bounds) >= 6:
        bounding_box = add_bounding_box_wireframe(stl_bounds, renderView)
        if bounding_box:
            print("  Geometry bounding box wireframe added")
    elif bounds and len(bounds) >= 6:
        # Fallback to domain bounds if STL not available
        bounding_box = add_bounding_box_wireframe(bounds, renderView)
        if bounding_box:
            print("  Domain bounding box wireframe added")
    
    slice1.UpdatePipeline()
    
    # Display temperature slice - make translucent to show STL and vectors
    sliceDisplay = pv.Show(slice1, renderView)
    sliceDisplay.Representation = 'Surface'
    # T is a cell array in OpenFOAM
    try:
        sliceDisplay.ColorArrayName = ['CELLS', 'T']
    except:
        sliceDisplay.ColorArrayName = ['POINTS', 'T']
    sliceDisplay.Opacity = 0.5  # More transparent to show STL geometry and vectors
    
    renderView.Update()
    pv.Render()
    
    colorMap = pv.GetColorTransferFunction('T')
    
    # Get temperature range adaptively (same logic as temperature slice)
    dataRange = get_data_range(slice1, 'T', use_points=False)  # Try cells first
    if not dataRange:
        dataRange = get_data_range(slice1, 'T', use_points=True)  # Fallback to points
    
    if dataRange and len(dataRange) >= 2 and dataRange[0] != dataRange[1]:
        minVal = dataRange[0]
        maxVal = dataRange[1]
        range_span = maxVal - minVal
        
        # If range is very wide, focus on internal field
        if range_span > 10.0:
            range_pad = range_span * 0.1
            minVal = dataRange[0] + range_pad
            maxVal = dataRange[1] - range_pad
        
        midVal = (minVal + maxVal) / 2.0
        colorMap.RGBPoints = [
            minVal, 0.0, 0.0, 1.0,      # Blue at min
            midVal, 1.0, 1.0, 1.0,      # White at mid
            maxVal, 1.0, 0.0, 0.0       # Red at max
        ]
    else:
        # Default range
        colorMap.RGBPoints = [290.0, 0.0, 0.0, 1.0, 305.0, 1.0, 1.0, 1.0, 320.0, 1.0, 0.0, 0.0]
    
    # Add velocity vectors
    calculator1 = pv.Calculator(Input=slice1)
    calculator1.ResultArrayName = 'U_mag'
    calculator1.Function = 'mag(U)'
    
    glyph1 = pv.Glyph(Input=calculator1, GlyphType='Arrow')
    # Try POINTS first
    try:
        glyph1.OrientationArray = ['POINTS', 'U']
        glyph1.ScaleArray = ['POINTS', 'U']
    except:
        glyph1.OrientationArray = ['CELLS', 'U']
        glyph1.ScaleArray = ['CELLS', 'U']
    # Get velocity range and domain size for adaptive scaling in overview
    calcInfo = calculator1.GetDataInformation()
    u_mag_range = get_data_range(calculator1, 'U_mag', use_points=True)
    x_size, y_size, z_size, char_length = get_domain_size(slice1)
    
    if u_mag_range and len(u_mag_range) >= 2 and u_mag_range[1] > 0:
        scale_factor = calculate_adaptive_velocity_scale(u_mag_range[1], char_length, target_vector_length_ratio=0.06)
        glyph1.ScaleFactor = scale_factor
    else:
        glyph1.ScaleFactor = 1000.0  # Default
    
    # Adaptive stride for overview (fewer vectors)
    sliceInfo = slice1.GetDataInformation()
    num_points = sliceInfo.GetNumberOfPoints() if sliceInfo else None
    stride = calculate_adaptive_stride(num_points, target_num_vectors=300)
    
    glyph1.GlyphMode = 'Every Nth Point'
    glyph1.Stride = stride
    
    glyphDisplay = pv.Show(glyph1, renderView)
    glyphDisplay.Representation = 'Surface'
    glyphDisplay.ColorArrayName = ['CELLS', 'U_mag']
    
    # Add scalar bar for temperature
    scalarBar = pv.GetScalarBar(colorMap, renderView)
    scalarBar.Title = 'Temperature [K]'
    scalarBar.Visibility = 1
    
    # Reset camera and render
    renderView.ResetCamera()
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Overview saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(glyph1)
    pv.Delete(calculator1)
    pv.Delete(slice1)
    if bounding_box:
        pv.Delete(bounding_box)
    if stl_reader:
        pv.Delete(stl_reader)
    pv.Delete(renderView)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate standard visualization images from OpenFOAM case',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('case_dir', help='Case directory path')
    parser.add_argument('time_dir', nargs='?', default=None,
                       help='Time directory (default: latest)')
    parser.add_argument('--output-dir', default='images',
                       help='Output directory for images (default: images/)')
    parser.add_argument('--width', type=int, default=1200,
                       help='Image width in pixels (default: 1200)')
    parser.add_argument('--height', type=int, default=800,
                       help='Image height in pixels (default: 800)')
    parser.add_argument('--no-overview', action='store_true',
                       help='Skip overview image generation')
    
    args = parser.parse_args()
    
    case_path = os.path.abspath(args.case_dir)
    if not os.path.isdir(case_path):
        print("Error: Case directory '{}' does not exist".format(case_path))
        sys.exit(1)
    
    case_name = os.path.basename(case_path)
    
    # Find latest time directory if not specified
    if args.time_dir is None:
        time_dirs = []
        for d in os.listdir(case_path):
            d_path = os.path.join(case_path, d)
            if os.path.isdir(d_path) and d.replace('.', '').replace('-', '').isdigit():
                time_dirs.append(d)
        if not time_dirs:
            print("Error: No time directories found in '{}'".format(case_path))
            sys.exit(1)
        time_dir = max(time_dirs, key=lambda x: float(x))
        print("Using latest time directory: {}".format(time_dir))
    else:
        time_dir = args.time_dir
    
    # Ensure .foam file exists
    foam_file = os.path.join(case_path, "{}.foam".format(case_name))
    if not os.path.exists(foam_file):
        open(foam_file, 'a').close()
        print("Created ParaView case file: {}".format(foam_file))
    
    # Create output directory
    output_dir = os.path.join(case_path, args.output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("\nGenerating images for {} at time {}".format(case_name, time_dir))
    print("Output directory: {}\n".format(output_dir))
    
    # Open OpenFOAM case
    try:
        reader = pv.OpenFOAMReader(FileName=str(foam_file))
        # Use Reconstructed Case (works better than Decomposed)
        reader.CaseType = 'Reconstructed Case'
        try:
            reader.EnablePatches = 1
        except AttributeError:
            pass
        
        # Detect if this is a multi-region case
        # Check for region directories in 0/
        zero_dir = os.path.join(case_path, "0")
        if os.path.isdir(zero_dir):
            regions = [d for d in os.listdir(zero_dir) if os.path.isdir(os.path.join(zero_dir, d)) and d not in ['include', 'polyMesh']]
            if regions:
                # Multi-region case - ParaView uses 'regionName/internalMesh' format
                region_name = regions[0]  # e.g., 'air'
                # First update pipeline to get available regions from ParaView
                reader.UpdatePipelineInformation()
                available_regions = reader.MeshRegions
                
                # Try to find the correct region format
                # ParaView may use 'air/internalMesh' or just 'air'
                region_to_use = None
                for reg in available_regions:
                    if region_name in reg or reg.endswith('/internalMesh'):
                        region_to_use = reg
                        break
                
                if region_to_use:
                    reader.MeshRegions = [region_to_use]
                    print("Detected multi-region case, using region: {}".format(region_to_use))
                else:
                    # Fallback: try the region name directly
                    reader.MeshRegions = [region_name]
                    print("Detected multi-region case, using region: {} (fallback)".format(region_name))
            else:
                # Single region case
                reader.MeshRegions = ['internalMesh']
        else:
            # Single region case
            reader.MeshRegions = ['internalMesh']
        
        # Set arrays - urbanMicroclimateFoam uses h (enthalpy) in addition to T
        reader.CellArrays = ['U', 'p', 'p_rgh', 'T', 'h']
        reader.PointArrays = []
        
        # Update pipeline information to get timesteps
        reader.UpdatePipelineInformation()
        timesteps = reader.TimestepValues
        
        # Set time step if specified
        if time_dir and timesteps:
            try:
                time_val = float(time_dir)
                # Find closest timestep and set as list
                closest = min(timesteps, key=lambda x: abs(x - time_val))
                reader.TimestepValues = [closest]
            except:
                pass
        
        # Update reader pipeline
        reader.UpdatePipeline()
        print("[OK] Case loaded successfully\n")
        
        # Detect if this is a 3D case (needs vertical slices)
        bounds, center = get_domain_bounds_and_center(reader, case_path)
        is_3d = is_3d_case(bounds, case_path)
        if is_3d:
            print("Detected 3D case - will generate vertical slice for complementary view\n")
        else:
            print("Detected 2D case - using plan view only\n")
    except Exception as e:
        print("Error loading case: {}".format(e))
        sys.exit(1)
    
    # Generate images
    images = []
    
    try:
        # Temperature slice (plan view - always generated)
        temp_path = os.path.join(output_dir, "temperature_{}.png".format(time_dir))
        create_temperature_slice(reader, temp_path, args.width, args.height, case_path)
        images.append(temp_path)
        
        # Temperature vertical slice, isometric view, and 3D geometry (only for 3D cases)
        if is_3d:
            temp_vertical_path = os.path.join(output_dir, "temperature_vertical_{}.png".format(time_dir))
            create_temperature_slice_vertical(reader, temp_vertical_path, args.width, args.height, case_path)
            images.append(temp_vertical_path)
            
            # Isometric 3D view (slice-based)
            isometric_path = os.path.join(output_dir, "temperature_isometric_{}.png".format(time_dir))
            create_isometric_3d_view(reader, isometric_path, args.width, args.height, case_path)
            images.append(isometric_path)
            
            # 3D geometry view (actual surfaces with temperature and velocity)
            geometry_path = os.path.join(output_dir, "geometry_3d_{}.png".format(time_dir))
            create_geometry_3d_view(reader, geometry_path, args.width, args.height, case_path)
            images.append(geometry_path)
            
            # Geometry-focused view with STL overlay and wireframe edges
            geometry_focused_path = os.path.join(output_dir, "geometry_focused_{}.png".format(time_dir))
            create_geometry_focused_view(reader, geometry_focused_path, args.width, args.height, case_path)
            images.append(geometry_focused_path)
        
        # Velocity vectors
        vel_path = os.path.join(output_dir, "velocity_{}.png".format(time_dir))
        create_velocity_vectors(reader, vel_path, args.width, args.height, case_path)
        images.append(vel_path)
        
        # Streamlines
        stream_path = os.path.join(output_dir, "streamlines_{}.png".format(time_dir))
        create_streamlines(reader, stream_path, args.width, args.height, case_path)
        images.append(stream_path)
        
        # Overview (optional)
        if not args.no_overview:
            overview_path = os.path.join(output_dir, "overview_{}.png".format(time_dir))
            create_overview(reader, overview_path, args.width * 2, args.height * 2, case_path, is_3d=is_3d)
            images.append(overview_path)
        
        print("\n[OK] Successfully generated {} images:".format(len(images)))
        for img in images:
            print("  - {}".format(img))
        
    except Exception as e:
        print("\nError generating images: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up reader
        pv.Delete(reader)


if __name__ == '__main__':
    main()

