import os
import sys
import argparse
import time
from datetime import datetime

# Import project modules
from src.parsers import parse_gpx_file, parse_geojson_file
from src.graph_utils import create_road_network_graph, simplify_graph
from src.solvers.aco_solver import solve_route_with_aco
from src.gpx_generator import convert_route_to_mapy_cz_compatible_gpx


def run(input_file, output_file=None, start_lat=None, start_lon=None, 
        num_ants=10, num_iterations=100, resample_interval=50, max_nodes=500, verbose=False):
    """Main function to orchestrate the route finding process."""
    start_time = time.time()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ACO Route Finder - Starting...")
    
    # Set default output file if not provided
    if output_file is None:
        input_basename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join('output', f'{input_basename}_optimized.gpx')
    
    # 1. Parse input file
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Parsing input file: {input_file}")
    file_extension = os.path.splitext(input_file)[1].lower()
    road_segments = []
    
    if file_extension == '.gpx':
        road_segments = parse_gpx_file(input_file)
    elif file_extension == '.geojson':
        road_segments = parse_geojson_file(input_file)
    else:
        print(f"Error: Unsupported file format {file_extension}. Please provide .gpx or .geojson")
        return
    
    if not road_segments:
        print("Error: No road segments found in the input file.")
        return
        
    print(f"Successfully parsed {len(road_segments)} road segments from input file.")
    
    # 2. Build graph
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Building road network graph...")
    graph = create_road_network_graph(road_segments)
    print(f"Road network graph created with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
    
    # 2a. Simplify the graph if it's too large
    if graph.number_of_nodes() > max_nodes:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Graph is too large ({graph.number_of_nodes()} nodes). Simplifying to approximately {max_nodes} nodes...")
        graph = simplify_graph(graph, max_nodes=max_nodes)
        print(f"Simplified graph now has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
    
    # Find starting node if coordinates are provided
    start_node_index = None
    if start_lat is not None and start_lon is not None:
        print(f"Finding closest node to starting coordinates: ({start_lat}, {start_lon})")
        start_point = (start_lat, start_lon)
        
        # Import here to avoid circular dependencies
        from geopy.distance import geodesic
        
        # Find the closest node in the graph to the given coordinates
        min_distance = float('inf')
        closest_node = None
        
        for node in graph.nodes():
            distance = geodesic(start_point, node).meters
            if distance < min_distance:
                min_distance = distance
                closest_node = node
        
        # Need to get the index of this node in a sorted list (for the ACO solver)
        if closest_node is not None:
            node_list = sorted(list(graph.nodes()))
            try:
                start_node_index = node_list.index(closest_node)
                print(f"Found closest node {closest_node} at index {start_node_index} (distance: {min_distance:.2f}m)")
            except ValueError:
                print(f"Warning: Could not find index of closest node {closest_node}. Using random start.")
    
    # 3. Run ACO solver
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running ACO solver with {num_ants} ants and {num_iterations} iterations...")
    optimized_route = solve_route_with_aco(
        graph, 
        num_ants=num_ants, 
        num_iterations=num_iterations, 
        start_node_index=start_node_index
    )
    
    if not optimized_route:
        print("Error: ACO solver failed to find a route.")
        return
        
    print(f"ACO solver found optimized route with {len(optimized_route)} points.")
    
    # 4. Generate output GPX
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating output GPX file...")
    
    route_name = f"Optimized route for {os.path.basename(input_file)}"
    route_description = f"Route optimized using Ant Colony Optimization with {num_ants} ants and {num_iterations} iterations."
    
    output_stats = convert_route_to_mapy_cz_compatible_gpx(
        optimized_route, 
        output_file, 
        route_name, 
        route_description,
        resample_interval=resample_interval
    )
    
    # Print results
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n--- Route Optimization Completed ---")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_stats['output_file']}")
    print(f"Route length: {output_stats['total_distance_km']:.2f} km")
    print(f"Original points: {output_stats['original_point_count']}")
    print(f"Output points: {output_stats['output_point_count']}")
    print(f"Processing time: {total_time:.2f} seconds")
    print(f"\nYou can open the output file in Mapy.cz or other GPX-compatible navigation apps.")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='ACO Route Finder - Optimize routes using Ant Colony Optimization')
    
    parser.add_argument('input_file', help='Path to input GPX or GeoJSON file with road network data')
    parser.add_argument('-o', '--output', dest='output_file', help='Path to output GPX file (default: ./output/input_name_optimized.gpx)')
    parser.add_argument('--start-lat', type=float, help='Starting point latitude')
    parser.add_argument('--start-lon', type=float, help='Starting point longitude')
    parser.add_argument('--ants', type=int, default=10, help='Number of ants to use in ACO (default: 10)')
    parser.add_argument('--iterations', type=int, default=100, help='Number of iterations for ACO (default: 100)')
    parser.add_argument('--resample', type=int, default=50, help='Resample interval in meters (default: 50, 0 to disable)')
    parser.add_argument('--max-nodes', type=int, default=500, help='Maximum number of nodes in simplified graph (default: 500)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    run(
        input_file=args.input_file,
        output_file=args.output_file,
        start_lat=args.start_lat,
        start_lon=args.start_lon,
        num_ants=args.ants,
        num_iterations=args.iterations,
        resample_interval=args.resample,
        max_nodes=args.max_nodes,
        verbose=args.verbose
    )
