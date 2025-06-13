"""
Script to inspect the pants API
"""
import pants
import inspect

print("="*50)
print("PANTS MODULE INSPECTION")
print("="*50)

# Print module attributes
print("\nModule-level attributes:")
module_attrs = [attr for attr in dir(pants) if not attr.startswith('_')]
print(module_attrs)

# Check for classes
if hasattr(pants, 'World'):
    print("\nWorld class signature:")
    print(inspect.signature(pants.World.__init__))
    
    print("\nWorld class docstring:")
    print(pants.World.__doc__)

if hasattr(pants, 'Ant'):
    print("\nAnt class signature:")
    print(inspect.signature(pants.Ant.__init__))
    
    print("\nAnt class docstring:")
    print(pants.Ant.__doc__)
    
if hasattr(pants, 'Solver'):
    print("\nSolver class signature:")
    print(inspect.signature(pants.Solver.__init__))
    
    print("\nSolver class docstring:")
    print(pants.Solver.__doc__)

# Try a simple example with proper parameters
print("\n\nTrying a simple example based on the API...")
try:
    # Define a simple length function
    def length(a, b):
        return abs(a - b)
    
    # Create basic World, Ant, and Solver instances
    world = pants.World([0, 1, 2], lfunc=length)
    print("Created World successfully")
    
    ant = pants.Ant(0, world)
    print("Created Ant successfully")
    
    # Try generating a simple tour
    tour = ant.tour()
    print(f"Generated tour: {tour}")
    
    # Try solving
    solver = pants.Solver(world)
    print("Created Solver successfully")
    solution = solver.solve()
    print(f"Solution: {solution}")
    
except Exception as e:
    print(f"Error in example: {e}")
