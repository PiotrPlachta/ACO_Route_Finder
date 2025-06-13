import networkx as nx
import pants  # aco-pants package is imported as 'pants' module
import random
import time
import sys
from geopy.distance import geodesic

def display_progress(iteration, total, prefix='', suffix='', length=50, fill='█'):    
    percent = iteration / total
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write('\r%s |%s| %3d%% %s' % (prefix, bar, int(100 * percent), suffix))
    sys.stdout.flush()
    if iteration == total:
        print()


def solve_route_with_aco(graph, num_ants=10, num_iterations=100, alpha=1.0, beta=3.0, evaporation_rate=0.8, start_node_index=None, show_progress=True):
    """
    Finds a route visiting all nodes in the graph using Ant Colony Optimization (TSP variant).

    Args:
        graph (nx.MultiGraph): The road network graph. Nodes are (lat, lon) tuples.
                               Edges must have a 'weight' attribute (length).
        num_ants (int): Number of ants to use in each iteration.
        num_iterations (int): Number of iterations for the ACO algorithm (limit parameter).
        alpha (float): Pheromone influence factor (default=1.0).
        beta (float): Heuristic (distance) influence factor (default=3.0).
        evaporation_rate (float): Rate at which pheromone evaporates (rho parameter, default=0.8).
        start_node_index (int, optional): The index of the node to start the tour from. 
                                          If None, a random start node is chosen.

    Returns:
        A list of (lat, lon) coordinates representing the optimized tour, or None if failed.
    """
    if not graph or graph.number_of_nodes() < 2:
        print("Graph is too small or empty for ACO.")
        return None

    # pants works with integer-indexed nodes. Create a mapping.
    node_list = list(graph.nodes())
    node_to_int = {node: i for i, node in enumerate(node_list)}
    int_to_node = {i: node for i, node in enumerate(node_list)}
    
    num_nodes = len(node_list)

    # Define the distance callback for pants (lfunc parameter)
    memoized_distances = {}
    def distance_callback(start_int, end_int):
        if (start_int, end_int) in memoized_distances:
            return memoized_distances[(start_int, end_int)]
        if (end_int, start_int) in memoized_distances: # Distances are symmetric for undirected paths
            return memoized_distances[(end_int, start_int)]

        start_coord = int_to_node[start_int]
        end_coord = int_to_node[end_int]
        
        if start_coord == end_coord:
            return 0.0
        
        try:
            # Use NetworkX to find the shortest path length
            length = nx.shortest_path_length(graph, source=start_coord, target=end_coord, weight='weight')
            memoized_distances[(start_int, end_int)] = length
            return length
        except nx.NetworkXNoPath:
            print(f"Warning: No path between {start_coord} and {end_coord}. Using large distance.")
            return float('inf')
        except Exception as e:
            print(f"Error calculating distance between {start_coord} and {end_coord}: {e}")
            return float('inf')

    print(f"Starting ACO for {num_nodes} nodes with {num_ants} ants and {num_iterations} iterations.")

    # Create world with nodes and length function
    world = pants.World(list(range(num_nodes)), lfunc=distance_callback)
    
    if start_node_index is None:
        effective_start_node_idx = random.choice(list(range(num_nodes)))
    elif 0 <= start_node_index < num_nodes:
        effective_start_node_idx = start_node_index
    else:
        print(f"Warning: Invalid start_node_index {start_node_index}. Choosing randomly.")
        effective_start_node_idx = random.choice(list(range(num_nodes)))
    
    print(f"ACO starting node (integer index): {effective_start_node_idx} (corresponds to {int_to_node[effective_start_node_idx]}) ")

    # Create solver with our parameters
    solver = pants.Solver(
        alpha=alpha,
        beta=beta,
        rho=evaporation_rate,
        limit=num_iterations,
        ant_count=num_ants
    )
    
    try:
        # Instead of directly calling solver.solve(world), we'll handle iterations manually
        # to display progress
        if show_progress:
            print(f"\nStarting ACO iterations:")
            
            # Create a colony to work with
            colony = pants.Colony(world)
            
            # Configure ants
            for ant in colony.get_ants():
                ant.initialize(alpha=alpha, beta=beta)
                
            # Track the best solution
            best_tour_indices = None
            best_tour_distance = float('inf')
            last_improvement = 0
            
            # Run the iterations with progress display
            start_time = time.time()
            for i in range(num_iterations):
                # Update progress bar
                elapsed = time.time() - start_time
                eta = (elapsed / (i+1)) * (num_iterations - i - 1) if i > 0 else 0
                suffix = f"[ETA: {eta:.1f}s]" if eta > 0 else ""
                if i % 2 == 0:  # Update every other iteration to reduce flicker
                    display_progress(i+1, num_iterations, 
                                    prefix=f"Iteration {i+1}/{num_iterations}", 
                                    suffix=suffix)
                
                # Run a single iteration
                colony.make_tours()
                colony.pheromone_changes()
                colony.spread_pheromone(rho=evaporation_rate)
                
                # Check if we have a better solution
                for ant in colony.get_ants():
                    if ant.distance < best_tour_distance:
                        best_tour_distance = ant.distance
                        best_tour_indices = ant.tour
                        last_improvement = i
                        if show_progress:
                            print(f"\r\033[KFound better tour at iteration {i+1}: {best_tour_distance:.2f} meters")
                            # Redraw progress bar
                            display_progress(i+1, num_iterations, 
                                        prefix=f"Iteration {i+1}/{num_iterations}", 
                                        suffix=suffix)
                
                # Early stopping if no improvement for a while
                if i - last_improvement > num_iterations // 5 and i > num_iterations // 2:
                    print(f"\r\033[KStopping early at iteration {i+1}/{num_iterations} - No improvement for {i - last_improvement} iterations")
                    break
            
            # Ensure we show 100% at the end
            if show_progress:
                display_progress(num_iterations, num_iterations, 
                               prefix=f"Iteration {num_iterations}/{num_iterations}", 
                               suffix="[Complete]")
                print(f"\nFinal tour distance: {best_tour_distance:.2f} meters")
        else:
            # If not showing progress, just use the standard solve method
            solution = solver.solve(world)

            if hasattr(solution, 'tour'):
                best_tour_indices = solution.tour
            else:
                print("Solution doesn't have 'tour' attribute. Using solution directly.")
                best_tour_indices = solution

        if not best_tour_indices:
            print("ACO did not return a valid tour.")
            return None
            
        if best_tour_indices[0] != best_tour_indices[-1]:
             best_tour_indices.append(best_tour_indices[0])

        optimized_route_coords = [int_to_node[idx] for idx in best_tour_indices]
        
        total_distance = 0
        for i in range(len(best_tour_indices) - 1):
            total_distance += distance_callback(best_tour_indices[i], best_tour_indices[i+1])
        
        print(f"ACO finished. Best tour length: {total_distance:.2f} meters.")
        print(f"Tour path (node indices): {best_tour_indices}")
        return optimized_route_coords

    except Exception as e:
        print(f"An error occurred during ACO solving: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # Example usage:
    # Create a sample graph (e.g., from graph_utils.py's test data or a small manual one)
    
    # For testing, let's use the sample_segments_data to build a graph.
    # This requires importing from graph_utils. If running this file directly,
    # ensure Python can find graph_utils (e.g., by being in the project root and running `python -m src.solvers.aco_solver`)
    # For simplicity in direct execution of this file, let's redefine a tiny graph here.

    test_graph = nx.MultiGraph()
    # A simple connected graph with lat/lon coordinates as nodes
    test_nodes_coords = {
        0: (50.0, 19.0), 
        1: (50.01, 19.01), 
        2: (50.02, 19.02),
        3: (50.00, 19.02) # Another node to make it slightly more complex
    }
    
    test_graph.add_edge(test_nodes_coords[0], test_nodes_coords[1], weight=geodesic(test_nodes_coords[0], test_nodes_coords[1]).meters)
    test_graph.add_edge(test_nodes_coords[1], test_nodes_coords[2], weight=geodesic(test_nodes_coords[1], test_nodes_coords[2]).meters)
    test_graph.add_edge(test_nodes_coords[2], test_nodes_coords[0], weight=geodesic(test_nodes_coords[2], test_nodes_coords[0]).meters) # Makes a 3-cycle
    test_graph.add_edge(test_nodes_coords[0], test_nodes_coords[3], weight=geodesic(test_nodes_coords[0], test_nodes_coords[3]).meters)
    test_graph.add_edge(test_nodes_coords[3], test_nodes_coords[2], weight=geodesic(test_nodes_coords[3], test_nodes_coords[2]).meters)


    print("--- Testing ACO Solver ---")
    if test_graph.number_of_nodes() > 0:
        # Use the first node as starting point for consistency in testing
        graph_node_list_for_test = list(test_graph.nodes())
        start_node_index = 0  # Just use the first node in our indexed mapping
        
        # Solve with reasonable parameters for our small test graph
        optimized_route = solve_route_with_aco(
            test_graph, 
            num_ants=5, 
            num_iterations=20, 
            start_node_index=start_node_index
        )
        
        if optimized_route:
            print("\nOptimized route (sequence of coordinates):")
            for i, coord in enumerate(optimized_route):
                print(f" {i+1}. {coord}")
        else:
            print("ACO route finding failed.")
    else:
        print("Test graph is empty, skipping ACO test.")
