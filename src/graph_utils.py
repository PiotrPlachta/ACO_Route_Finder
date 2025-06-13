import networkx as nx
from geopy.distance import geodesic
import time
from collections import defaultdict

def create_road_network_graph(segments):
    """
    Creates a road network graph from a list of road segments.

    Args:
        segments: A list of segments, where each segment is a list of 
                  (latitude, longitude) coordinate tuples.

    Returns:
        A networkx.MultiGraph representing the road network.
        Nodes are coordinate tuples (lat, lon).
        Edges have a 'weight' attribute representing the length in meters.
    """
    if not segments:
        print("No segments provided to create graph.")
        return None

    graph = nx.MultiGraph()
    
    # Helper to add an edge with its calculated weight (length)
    def add_edge_with_weight(u_coord, v_coord):
        if u_coord == v_coord: # Skip zero-length segments if any point duplicates
            return
        length = geodesic(u_coord, v_coord).meters
        graph.add_edge(u_coord, v_coord, weight=length)

    print(f"Building graph from {len(segments)} segments...")
    processed_segments = 0

    for segment_points in segments:
        if len(segment_points) < 2:
            # A segment needs at least two points to form an edge
            continue
        
        # Add edges for each pair of consecutive points in the segment
        for i in range(len(segment_points) - 1):
            u_node = segment_points[i]
            v_node = segment_points[i+1]
            
            # Ensure nodes exist in the graph (NetworkX adds them automatically if not)
            # graph.add_node(u_node, pos=u_node) # Optional: store position for plotting
            # graph.add_node(v_node, pos=v_node)
            
            add_edge_with_weight(u_node, v_node)
        
        processed_segments += 1
        if processed_segments % 100 == 0:
            print(f"Processed {processed_segments}/{len(segments)} segments...")

    print(f"Finished building graph. Processed {processed_segments} segments.")
    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
    
    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        print("Warning: The created graph is empty or has no edges.")
        return None
        
    return graph

def simplify_graph(graph, junction_degree_threshold=3, max_nodes=500, verbose=True):
    """
    Simplifies a road network graph by:
    1. Keeping important junction nodes (with degree >= junction_degree_threshold)
    2. Removing pass-through nodes (nodes with exactly 2 connections)
    3. Ensuring the simplified graph preserves the network topology
    4. Optionally limiting the total number of nodes

    Args:
        graph: A networkx.MultiGraph representing the road network
        junction_degree_threshold: Minimum degree to consider a node as junction (default=3)
        max_nodes: Maximum number of nodes to keep in the simplified graph (default=500)
        verbose: Whether to print progress information

    Returns:
        A simplified networkx.MultiGraph
    """
    if graph is None:
        print("Cannot simplify a None graph")
        return None
    
    if graph.number_of_nodes() <= max_nodes:
        if verbose:
            print(f"Graph already has {graph.number_of_nodes()} nodes, which is under the maximum of {max_nodes}. No simplification needed.")
        return graph.copy()
    
    start_time = time.time()
    if verbose:
        print(f"Simplifying graph from {graph.number_of_nodes()} nodes...")
    
    # Create a copy to work with
    simplified = graph.copy()
    
    # Step 1: Identify key junction nodes (with many connections)
    junction_nodes = [node for node, degree in simplified.degree() if degree >= junction_degree_threshold]
    if verbose:
        print(f"Found {len(junction_nodes)} junction nodes with degree >= {junction_degree_threshold}")
    
    # Step 2: Identify pass-through nodes (degree exactly 2)
    passthrough_nodes = [node for node, degree in simplified.degree() if degree == 2]
    if verbose:
        print(f"Found {len(passthrough_nodes)} pass-through nodes with degree = 2")
    
    # Step 3: Remove pass-through nodes (contract edges)
    # Start with nodes that have the lowest impact (simplest to remove)
    nodes_removed = 0
    
    for i, node in enumerate(passthrough_nodes):
        # Check if we've reached our target
        if simplified.number_of_nodes() <= max_nodes:
            break
            
        # Skip if the node was already removed in previous iterations
        if node not in simplified:
            continue
            
        # Get the neighbors before removing the node
        neighbors = list(simplified.neighbors(node))
        if len(neighbors) != 2:  # Skip if degree is no longer 2
            continue
            
        # Calculate the combined weight of the edges we're replacing
        # Correct way to get edge data from a MultiGraph
        n1_weight = min(d.get('weight', 1.0) for u, v, d in simplified.edges(node, neighbors[0], data=True))
        n2_weight = min(d.get('weight', 1.0) for u, v, d in simplified.edges(node, neighbors[1], data=True))
        combined_weight = n1_weight + n2_weight
        
        # Remove the node and add a direct edge between its neighbors
        simplified.add_edge(neighbors[0], neighbors[1], weight=combined_weight)
        simplified.remove_node(node)
        nodes_removed += 1
        
        # Show progress periodically
        if verbose and (i+1) % 100 == 0:
            print(f"Processed {i+1}/{len(passthrough_nodes)} pass-through nodes. Graph now has {simplified.number_of_nodes()} nodes.")
    
    # Step 4: If we still have too many nodes, remove low-importance nodes
    if simplified.number_of_nodes() > max_nodes:
        # Sort nodes by degree (ascending - remove lowest-degree nodes first)
        nodes_by_importance = sorted(simplified.degree(), key=lambda x: x[1])
        
        # Calculate how many more nodes to remove
        nodes_to_remove = simplified.number_of_nodes() - max_nodes
        
        if verbose:
            print(f"Still need to remove {nodes_to_remove} more nodes to reach target size of {max_nodes}")
        
        # Remove nodes until we reach our target
        for i, (node, _) in enumerate(nodes_by_importance):
            if i >= nodes_to_remove:
                break
            simplified.remove_node(node)
    
    # Final check - ensure we don't have any isolated nodes
    isolated_nodes = list(nx.isolates(simplified))
    if isolated_nodes:
        if verbose:
            print(f"Removing {len(isolated_nodes)} isolated nodes")
        simplified.remove_nodes_from(isolated_nodes)
    
    if verbose:
        print(f"Graph simplification complete: {graph.number_of_nodes()} nodes → {simplified.number_of_nodes()} nodes")
        print(f"Simplification took {time.time() - start_time:.2f} seconds")
    
    return simplified


if __name__ == '__main__':
    # Example Usage:
    # Assuming parsers.py is in the same directory or PYTHONPATH is set up
    # For direct testing, we might need to adjust import paths or run from project root
    
    # A simple list of segments for testing
    sample_segments_data = [
        [(50.0, 19.0), (50.01, 19.01), (50.02, 19.02)], # Segment 1
        [(50.02, 19.02), (50.03, 19.03)],             # Segment 2 (connects to seg 1)
        [(50.1, 19.1), (50.11, 19.11)]                # Segment 3 (disconnected)
    ]

    print("--- Testing Graph Creation with sample_segments_data ---")
    road_graph = create_road_network_graph(sample_segments_data)

    if road_graph:
        print(f"Sample graph created successfully.")
        print(f"Nodes: {list(road_graph.nodes(data=True))}") # data=True to see attributes like pos
        print(f"Edges: {list(road_graph.edges(data=True))}") # data=True to see attributes like weight
        
        # Example: Check connectivity (for more complex graphs)
        # if nx.is_connected(road_graph.to_undirected()): # Ensure graph is treated as undirected for this check
        #     print("The graph is connected.")
        # else:
        #     print(f"The graph is not connected. Number of connected components: {nx.number_connected_components(road_graph.to_undirected())}")
        
        # Verify total length of edges (approx)
        total_length = sum(d['weight'] for u,v,d in road_graph.edges(data=True))
        print(f"Approximate total length of roads in graph: {total_length:.2f} meters")

    print("\n--- Testing with empty segments list ---")
    empty_graph = create_road_network_graph([])
    if empty_graph is None:
        print("Correctly handled empty segments list.")

    print("\n--- Testing with segments having less than 2 points ---")
    short_segments_data = [
        [(50.0, 19.0)], 
        []
    ]
    short_segment_graph = create_road_network_graph(short_segments_data)
    if short_segment_graph is None: # Expecting an empty graph or None
         print("Correctly handled segments with insufficient points (resulted in None or empty graph).")
    elif short_segment_graph.number_of_edges() == 0:
        print("Correctly handled segments with insufficient points (resulted in an empty graph).")
