"""
Simple test script to verify pants module functionality
"""
print("Starting ACO test...")

try:
    import pants
    print(f"Successfully imported pants module")
    
    # Create simple test objects
    try:
        world = pants.World(nodes=list(range(3)), distance_fn=lambda a, b: 1.0)
        print("Successfully created pants.World")
        
        colony = pants.Colony(alpha=1.0, beta=2.0, world=world)
        print("Successfully created pants.Colony")
        
        ant = pants.Ant(world=world, start_node=0)
        print("Successfully created pants.Ant")
        
        solver = pants.Solver(colony=colony, world=world, ants=5, iterations=10, evaporation=0.5)
        print("Successfully created pants.Solver")
        print("All pants objects created successfully!")
    except Exception as e:
        print(f"Error creating pants objects: {e}")
        
except ImportError as e:
    print(f"Failed to import pants: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

print("Test completed.")
