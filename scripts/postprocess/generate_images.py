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
    python scripts/postprocess/generate_images.py cases/heatedCavity 200
    python scripts/postprocess/generate_images.py cases/heatedCavity 200 --output-dir results/images
"""

import sys
import os
import argparse
import time

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


def calculate_adaptive_velocity_scale(velocity_max, domain_size, target_vector_length_ratio=0.05):
    """
    Calculate adaptive scale factor for velocity vectors.
    
    Args:
        velocity_max: Maximum velocity magnitude (m/s)
        domain_size: Characteristic domain size (m)
        target_vector_length_ratio: Desired vector length as fraction of domain (default: 8%)
    
    Returns:
        Scale factor to use for glyphs
    """
    if velocity_max is None or velocity_max <= 0:
        # Default for very small velocities
        return 1000.0
    
    if domain_size is None or domain_size <= 0:
        # Default domain size assumption
        domain_size = 1.0
    
    # Target vector length
    target_length = domain_size * target_vector_length_ratio
    
    # Calculate scale factor: scale_factor * velocity_max = target_length
    if velocity_max > 0:
        scale_factor = target_length / velocity_max
    else:
        scale_factor = 1000.0
    
    # Clamp to reasonable range (avoid too small or too large)
    scale_factor = max(100.0, min(scale_factor, 10000.0))
    
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

def create_temperature_slice(reader, output_path, width=1200, height=800):
    """
    Create a temperature contour slice visualization.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Create slice filter
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = [0.5, 0.5, 0.005]  # Center of domain
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]    # Z-normal for 2D view
    
    # Update pipeline to get data
    slice1.UpdatePipeline()
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background for better contrast
    
    # Display slice
    sliceDisplay = pv.Show(slice1, renderView)
    sliceDisplay.Representation = 'Surface'
    
    # Try both CELLS and POINTS to see which works
    try:
        sliceDisplay.ColorArrayName = ['POINTS', 'T']
    except:
        try:
            sliceDisplay.ColorArrayName = ['POINTS', 'T']
        except:
            sliceDisplay.ColorArrayName = 'T'
    
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
    pv.Delete(renderView)
    
    return output_path


def create_velocity_vectors(reader, output_path, width=1200, height=800):
    """
    Create a velocity vector visualization using glyphs.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Create slice first
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = [0.5, 0.5, 0.005]
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
    
    # Create glyphs for velocity vectors
    glyph1 = pv.Glyph(Input=slice1, GlyphType='Arrow')
    glyph1.OrientationArray = ['CELLS', 'U']
    glyph1.ScaleArray = ['CELLS', 'U']
    glyph1.ScaleFactor = 0.1
    glyph1.GlyphMode = 'Every Nth Point'
    glyph1.Stride = 5  # Show every 5th point to avoid clutter
    glyph1.GlyphTransform = 'Transform2'
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
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
    
    # Calculate adaptive stride based on mesh density
    stride = calculate_adaptive_stride(num_points, target_num_vectors=400)
    print("  Slice has {} points, using stride: {}".format(num_points if num_points else "unknown", stride))
    
    glyph2.GlyphMode = 'Every Nth Point'
    glyph2.Stride = stride
    
    # Scale factor will be set adaptively after we get velocity range
    # Temporary default (will be updated)
    glyph2.ScaleFactor = 1000.0
    
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
        # Fallback: use default scale factor
        glyph2.ScaleFactor = 1000.0
        glyph2.UpdatePipeline()
        print("  [WARN] Could not determine velocity range, using default scale factor")
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
    
    # Reset camera and render
    renderView.ResetCamera()
    renderView.Update()
    pv.Render()
    
    # Save image
    pv.SaveScreenshot(output_path, renderView, ImageResolution=[width, height])
    print("[OK] Velocity vectors saved: {}".format(output_path))
    
    # Clean up
    pv.Delete(glyph2)
    pv.Delete(calculator1)
    pv.Delete(slice1)
    pv.Delete(renderView)
    
    return output_path


def create_streamlines(reader, output_path, width=1200, height=800):
    """
    Create a streamline visualization.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Create line source for seed points (along hot wall)
    line1 = pv.Line()
    line1.Point1 = [0.0, 0.0, 0.005]
    line1.Point2 = [0.0, 1.0, 0.005]
    line1.Resolution = 20
    
    # Create stream tracer
    streamTracer1 = pv.StreamTracer(Input=reader, SeedType=line1)
    streamTracer1.Vectors = ['CELLS', 'U']
    streamTracer1.MaximumStreamlineLength = 2.0
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    streamTracer1.UpdatePipeline()
    
    # Display streamlines colored by temperature
    streamDisplay = pv.Show(streamTracer1, renderView)
    streamDisplay.Representation = 'Surface'
    # Try POINTS first, fallback to CELLS
    try:
        streamDisplay.ColorArrayName = ['POINTS', 'T']
    except:
        streamDisplay.ColorArrayName = ['POINTS', 'T']
    
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
    pv.Delete(renderView)
    
    return output_path


def create_overview(reader, output_path, width=2400, height=1600):
    """
    Create a combined visualization with temperature slice and velocity vectors overlaid.
    
    Args:
        reader: ParaView OpenFOAM reader object
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Create slice
    slice1 = pv.Slice(Input=reader)
    slice1.SliceType = 'Plane'
    slice1.SliceType.Origin = [0.5, 0.5, 0.005]
    slice1.SliceType.Normal = [0.0, 0.0, 1.0]
    
    # Create render view
    renderView = pv.CreateView('RenderView')
    renderView.ViewSize = [width, height]
    renderView.Background = [0.32, 0.34, 0.43]  # Dark gray background
    
    slice1.UpdatePipeline()
    
    # Display temperature slice
    sliceDisplay = pv.Show(slice1, renderView)
    sliceDisplay.Representation = 'Surface'
    sliceDisplay.ColorArrayName = ['POINTS', 'T']
    sliceDisplay.Opacity = 0.7  # Semi-transparent to show vectors
    
    renderView.Update()
    pv.Render()
    
    colorMap = pv.GetColorTransferFunction('T')
    
    # Get temperature range adaptively (same logic as temperature slice)
    dataRange = get_data_range(slice1, 'T', use_points=True)
    
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
        reader.MeshRegions = ['internalMesh']
        reader.CellArrays = ['U', 'p', 'T']
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
    except Exception as e:
        print("Error loading case: {}".format(e))
        sys.exit(1)
    
    # Generate images
    images = []
    
    try:
        # Temperature slice
        temp_path = os.path.join(output_dir, "temperature_{}.png".format(time_dir))
        create_temperature_slice(reader, temp_path, args.width, args.height)
        images.append(temp_path)
        
        # Velocity vectors
        vel_path = os.path.join(output_dir, "velocity_{}.png".format(time_dir))
        create_velocity_vectors(reader, vel_path, args.width, args.height)
        images.append(vel_path)
        
        # Streamlines
        stream_path = os.path.join(output_dir, "streamlines_{}.png".format(time_dir))
        create_streamlines(reader, stream_path, args.width, args.height)
        images.append(stream_path)
        
        # Overview (optional)
        if not args.no_overview:
            overview_path = os.path.join(output_dir, "overview_{}.png".format(time_dir))
            create_overview(reader, overview_path, args.width * 2, args.height * 2)
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

