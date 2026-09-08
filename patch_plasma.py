import re

with open("build_3d_toroidal_model.py", "r") as f:
    code = f.read()

# Replace plasma definition to use Tungsten at near-vacuum density instead of Hydrogen
old_plasma = """# Plasma (Void / vacuum region for transport source)
mat_plasma = openmc.Material(name='Plasma Core')
mat_plasma.add_element('H', 1.0, percent_type='ao')
mat_plasma.set_density('g/cm3', 1.0e-5) # Near vacuum"""

new_plasma = """# Plasma (Near-vacuum placeholder using FENDL-compatible Tungsten)
mat_plasma = openmc.Material(name='Plasma Core')
mat_plasma.add_element('W', 1.0, percent_type='ao')
mat_plasma.set_density('g/cm3', 1.0e-7) # Ultra-low density near-vacuum"""

code = code.replace(old_plasma, new_plasma)

with open("build_3d_toroidal_model.py", "w") as f:
    f.write(code)

print("Updated plasma core material to use FENDL-compatible W at near-vacuum density.")
