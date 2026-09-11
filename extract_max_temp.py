import pyvista as pv
import numpy as np

# Path to the final time step internal volume VTK file
vtk_file = "openfoam/VTK/openfoam_100/internal.vtu"

print(f"Loading VTK dataset from {vtk_file}...")
mesh = pv.read(vtk_file)

# Check available field data arrays
print("Available arrays:", list(mesh.point_data.keys()))

# Extract temperature ('T') field
if "T" in mesh.point_data:
    temps = mesh.point_data["T"]
    points = mesh.points
elif "T" in mesh.cell_data:
    mesh_cells = mesh.cell_data_to_point_data()
    temps = mesh_cells.point_data["T"]
    points = mesh.points
else:
    raise ValueError("Temperature field 'T' not found in dataset!")

# Find maximum temperature and its index
max_temp = np.max(temps)
max_idx = np.argmax(temps)
max_coords = points[max_idx]

print("\n" + "="*40)
print(" MAXIMUM TEMPERATURE RESULTS")
print("="*40)
print(f"Maximum Temperature : {max_temp:.2f} K")
print(f"X Coordinate        : {max_coords[0]:.3f} cm")
print(f"Y Coordinate        : {max_coords[1]:.3f} cm")
print(f"Z Coordinate        : {max_coords[2]:.3f} cm")
print("="*40)
