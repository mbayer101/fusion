import pyvista as pv
import matplotlib.pyplot as plt
import numpy as np

# Load the final time step internal volume VTK file
vtk_file = "openfoam/VTK/openfoam_100/internal.vtu"
print(f"Loading VTK dataset from {vtk_file}...")
mesh = pv.read(vtk_file)

# Determine domain bounds to find the center coordinates
bounds = mesh.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
x_min, x_max = bounds[0], bounds[1]
y_center = (bounds[2] + bounds[3]) / 2.0
z_center = (bounds[4] + bounds[5]) / 2.0

# Define line probe from one side to the other through the center
pointa = (x_min, y_center, z_center)
pointb = (x_max, y_center, z_center)

print(f"Sampling line profile along X-axis from {pointa} to {pointb}...")
profile = mesh.sample_over_line(pointa, pointb, resolution=200)

# Extract distance along the line and temperature 'T'
distance = profile.points[:, 0] - x_min
temperature = profile.point_data["T"]

# Generate plot
plt.figure(figsize=(8, 5))
plt.plot(distance, temperature, color="crimson", linewidth=2.5, label="T (K)")
plt.title("1D Temperature Profile Across Fusion Blanket Center", fontsize=12, fontweight="bold")
plt.xlabel("Distance along X-axis (cm)", fontsize=10)
plt.ylabel("Temperature (K)", fontsize=10)
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()
plt.tight_layout()

output_image = "temperature_profile.png"
plt.savefig(output_image, dpi=300)
print(f"Successfully generated and saved line profile plot to {output_image}")
