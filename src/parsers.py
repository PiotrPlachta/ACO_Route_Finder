import gpxpy
import gpxpy.gpx
import geojson
import os

def parse_gpx_file(file_path):
    """
    Parses a GPX file and extracts road segments (tracks/routes).
    Returns a list of segments, where each segment is a list of (lat, lon) tuples.
    """
    segments = []
    try:
        with open(file_path, 'r', encoding='utf-8') as gpx_file:
            gpx = gpxpy.parse(gpx_file)

        # Extract points from tracks and their segments
        for track in gpx.tracks:
            for segment in track.segments:
                segment_points = []
                for point in segment.points:
                    segment_points.append((point.latitude, point.longitude))
                if segment_points:
                    segments.append(segment_points)
        
        # Extract points from routes
        for route in gpx.routes:
            route_points = []
            for point in route.points:
                route_points.append((point.latitude, point.longitude))
            if route_points:
                segments.append(route_points)
                
    except Exception as e:
        print(f"Error parsing GPX file {file_path}: {e}")
        return None
    
    if not segments:
        print(f"No track/route segments found in GPX file: {file_path}")
        return None
        
    return segments

def parse_geojson_file(file_path):
    """
    Parses a GeoJSON file and extracts road segments (LineStrings).
    Assumes features of type 'LineString' represent road segments.
    Returns a list of segments, where each segment is a list of (lat, lon) tuples.
    Note: GeoJSON coordinates are typically (lon, lat). We'll convert to (lat, lon).
    """
    segments = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = geojson.load(f)
        
        if data.get('type') == 'FeatureCollection':
            for feature in data.get('features', []):
                geometry = feature.get('geometry', {})
                if geometry.get('type') == 'LineString':
                    # GeoJSON coordinates are (longitude, latitude)
                    # We convert to (latitude, longitude) for consistency
                    segment_points = [(coord[1], coord[0]) for coord in geometry.get('coordinates', [])]
                    if segment_points:
                        segments.append(segment_points)
                # TODO: Handle MultiLineString if necessary
        elif data.get('type') == 'LineString': # A single LineString feature
            segment_points = [(coord[1], coord[0]) for coord in data.get('coordinates', [])]
            if segment_points:
                segments.append(segment_points)

    except Exception as e:
        print(f"Error parsing GeoJSON file {file_path}: {e}")
        return None

    if not segments:
        print(f"No LineString features found in GeoJSON file: {file_path}")
        return None
        
    return segments

def load_road_network_data(file_path):
    """
    Loads road network data from a GPX or GeoJSON file.
    Detects file type based on extension.
    Returns a list of segments, or None if parsing fails.
    """
    _, file_extension = os.path.splitext(file_path)
    
    print(f"Loading road network data from: {file_path}")

    if file_extension.lower() == '.gpx':
        return parse_gpx_file(file_path)
    elif file_extension.lower() == '.geojson':
        return parse_geojson_file(file_path)
    else:
        print(f"Unsupported file type: {file_extension}. Please use .gpx or .geojson.")
        return None

if __name__ == '__main__':
    # Example usage (assuming you have test files in input_data)
    # Create dummy files for testing if they don't exist
    
    INPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'input_data')
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)

    # Dummy GPX
    sample_gpx_path = os.path.join(INPUT_DIR, 'sample.gpx')
    if not os.path.exists(sample_gpx_path):
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Cascade" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
 <trk>
  <name>Sample Track</name>
  <trkseg>
   <trkpt lat="50.0" lon="19.0"></trkpt>
   <trkpt lat="50.01" lon="19.01"></trkpt>
   <trkpt lat="50.02" lon="19.02"></trkpt>
  </trkseg>
  <trkseg>
   <trkpt lat="50.03" lon="19.03"></trkpt>
   <trkpt lat="50.04" lon="19.04"></trkpt>
  </trkseg>
 </trk>
 <rte>
  <name>Sample Route</name>
  <rtept lat="50.1" lon="19.1"></rtept>
  <rtept lat="50.11" lon="19.11"></rtept>
 </rte>
</gpx>"""
        with open(sample_gpx_path, 'w') as f:
            f.write(gpx_content)
        print(f"Created dummy GPX: {sample_gpx_path}")

    # Dummy GeoJSON
    sample_geojson_path = os.path.join(INPUT_DIR, 'sample.geojson')
    if not os.path.exists(sample_geojson_path):
        geojson_content = """{
 "type": "FeatureCollection",
 "features": [
  {
   "type": "Feature",
   "geometry": {
    "type": "LineString",
    "coordinates": [
     [20.0, 51.0], [20.01, 51.01], [20.02, 51.02]
    ]
   },
   "properties": {}
  },
  {
   "type": "Feature",
   "geometry": {
    "type": "LineString",
    "coordinates": [
     [20.03, 51.03], [20.04, 51.04]
    ]
   },
   "properties": {}
  }
 ]
}"""
        with open(sample_geojson_path, 'w') as f:
            f.write(geojson_content)
        print(f"Created dummy GeoJSON: {sample_geojson_path}")

    print("\n--- Testing GPX Parser ---")
    gpx_data = load_road_network_data(sample_gpx_path)
    if gpx_data:
        print(f"Successfully parsed GPX. Found {len(gpx_data)} segments.")
        # for i, segment in enumerate(gpx_data):
        #     print(f" Segment {i+1}: {len(segment)} points, first point: {segment[0]}")

    print("\n--- Testing GeoJSON Parser ---")
    geojson_data = load_road_network_data(sample_geojson_path)
    if geojson_data:
        print(f"Successfully parsed GeoJSON. Found {len(geojson_data)} segments.")
        # for i, segment in enumerate(geojson_data):
        #     print(f" Segment {i+1}: {len(segment)} points, first point: {segment[0]}")
            
    # Test with a non-existent file
    print("\n--- Testing Non-existent file ---")
    non_existent_data = load_road_network_data("non_existent_file.gpx")
    if non_existent_data is None:
        print("Correctly handled non-existent file.")

    # Test with an unsupported file type
    print("\n--- Testing Unsupported file type ---")
    unsupported_path = os.path.join(INPUT_DIR, 'sample.txt')
    with open(unsupported_path, 'w') as f:
        f.write("dummy text")
    unsupported_data = load_road_network_data(unsupported_path)
    if unsupported_data is None:
        print("Correctly handled unsupported file type.")
    os.remove(unsupported_path) # Clean up dummy file
