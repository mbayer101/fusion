import re

with open("build_3d_toroidal_model.py", "r") as f:
    code = f.read()

# 1. Optimize Blanket Material: Boost Li-6 enrichment (e.g., 90% Li-6, 10% Li-7) for higher breeding
old_bl = """# Breeding Blanket (Li-Pb eutectic placeholder)
mat_bl = openmc.Material(name='Breeding Blanket')
mat_bl.add_element('Li', 0.2, percent_type='ao')
mat_bl.add_element('Pb', 0.8, percent_type='ao')
mat_bl.set_density('g/cm3', 9.5)"""

new_bl = """# Breeding Blanket (Highly Enriched Li-6 Pb Eutectic for High TBR)
mat_bl = openmc.Material(name='Breeding Blanket')
mat_bl.add_nuclide('Li6', 0.18, percent_type='ao') # 90% of Li is enriched Li-6
mat_bl.add_nuclide('Li7', 0.02, percent_type='ao') # 10% Li-7
mat_bl.add_element('Pb', 0.8, percent_type='ao')
mat_bl.set_density('g/cm3', 9.5)"""

code = code.replace(old_bl, new_bl)

# 2. Add a 2D Slice Plot definition before exporting materials/geometry/plots
plot_code = """
# --- 2D Geometry Plot ---
plot = openmc.Plot()
plot.filename = 'torus_xz_slice'
plot.basis = 'xz'
plot.origin = (600.0, 0.0, 0.0) # Center of the torus major radius
plot.width = [1000.0, 1000.0]
plot.pixels = [800, 800]
plot.color_by = 'material'

plots = openmc.Plots([plot])
plots.export_to_xml()
"""

# Append plot export right before geometry/material exports or at the end
code += plot_code

with open("build_3d_toroidal_model.py", "w") as f:
    f.write(code)

print("Model updated with enriched Li-6 breeding blanket and 2D slice plot definition.")
