"""
GPX output generator module for creating Mapy.cz compatible GPX files.
"""
import gpxpy
import gpxpy.gpx
from datetime import datetime
from geopy.distance import geodesic
import os

def create_gpx_route(coordinates, route_name="Optimized Route", route_description=None):
    """
    Create a GPX route from a sequence of (latitude, longitude) coordinates.
    
    Args:
        coordinates: List of (latitude, longitude) tuples representing the optimized route
        route_name: Name for the GPX route
        route_description: Optional description for the route
        
    Returns:
        A gpxpy.gpx.GPX object containing the route
    """
    gpx = gpxpy.gpx.GPX()
    
    # Create first track in our GPX
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = route_name
    if route_description:
        gpx_track.description = route_description
    gpx.tracks.append(gpx_track)
    
    # Create segment in our track
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    # Add points to our segment
    for lat, lon in coordinates:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
    
    # Add route metadata to make it more compatible with mapping services
    gpx.author_name = "ACO Route Optimizer"
    gpx.creator = "ACO Route Optimizer"
    gpx.time = datetime.utcnow()
    gpx.description = f"Optimized route with {len(coordinates)} points, created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return gpx

def resample_route(coordinates, interval=50):
    """
    Resample a route to have points approximately every 'interval' meters.
    This can make the route smoother and reduce file size for very dense tracks.
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        interval: Distance in meters between resampled points
        
    Returns:
        A new list of (latitude, longitude) tuples
    """
    if not coordinates or len(coordinates) < 2:
        return coordinates
        
    resampled = [coordinates[0]]  # Start with the first point
    distance_accumulator = 0
    
    for i in range(1, len(coordinates)):
        prev_point = coordinates[i-1]
        curr_point = coordinates[i]
        
        segment_distance = geodesic(prev_point, curr_point).meters
        
        # If very close points, just skip to avoid unnecessary density
        if segment_distance < 1.0:
            continue
            
        distance_accumulator += segment_distance
        
        # If we've accumulated enough distance, add this point
        if distance_accumulator >= interval:
            resampled.append(curr_point)
            distance_accumulator = 0
            
    # Always include the last point
    if coordinates[-1] != resampled[-1]:
        resampled.append(coordinates[-1])
        
    return resampled

def calculate_route_statistics(coordinates):
    """
    Calculate statistics for a route.
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        
    Returns:
        Dictionary with route statistics
    """
    if not coordinates or len(coordinates) < 2:
        return {
            "total_distance_km": 0,
            "num_points": len(coordinates) if coordinates else 0
        }
    
    total_distance = 0
    
    for i in range(1, len(coordinates)):
        prev_point = coordinates[i-1]
        curr_point = coordinates[i]
        segment_distance = geodesic(prev_point, curr_point).meters
        total_distance += segment_distance
        
    return {
        "total_distance_km": total_distance / 1000.0,
        "num_points": len(coordinates)
    }

def save_gpx_file(gpx_object, output_file_path):
    """
    Save a GPX object to a file.
    
    Args:
        gpx_object: A gpxpy.gpx.GPX object
        output_file_path: Path where the GPX file should be saved
        
    Returns:
        The path to the saved file
    """
    # Make sure the output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)
    
    # Write the GPX data to file
    with open(output_file_path, 'w') as f:
        f.write(gpx_object.to_xml())
        
    return output_file_path

def convert_route_to_mapy_cz_compatible_gpx(route_coordinates, output_file_path, 
                                          route_name="Optimized Route", 
                                          route_description=None,
                                          resample_interval=50):
    """
    Convert a list of coordinates to a Mapy.cz compatible GPX file.
    
    Args:
        route_coordinates: List of (latitude, longitude) tuples
        output_file_path: Path where the GPX file should be saved
        route_name: Name for the GPX route
        route_description: Optional description for the route
        resample_interval: Interval in meters for resampling points (0 to disable)
        
    Returns:
        Dictionary with statistics and the path to the saved file
    """
    # Optionally resample the route
    processed_route = route_coordinates
    if resample_interval > 0:
        processed_route = resample_route(route_coordinates, resample_interval)
    
    # Create GPX object
    gpx = create_gpx_route(processed_route, route_name, route_description)
    
    # Save to file
    save_path = save_gpx_file(gpx, output_file_path)
    
    # Calculate statistics
    stats = calculate_route_statistics(processed_route)
    stats["original_point_count"] = len(route_coordinates)
    stats["output_point_count"] = len(processed_route)
    stats["output_file"] = save_path
    
    return stats


if __name__ == "__main__":
    # Example usage:
    example_route = [
        (50.0, 19.0),
        (50.01, 19.01),
        (50.02, 19.02),
        (50.0, 19.02)
    ]
    
    output_file = "../output/example_route.gpx"
    
    stats = convert_route_to_mapy_cz_compatible_gpx(
        example_route, 
        output_file,
        "Example Route", 
        "This is a test route created by the GPX generator."
    )
    
    print(f"Route statistics: {stats}")
    print(f"GPX file saved to {stats['output_file']}")
