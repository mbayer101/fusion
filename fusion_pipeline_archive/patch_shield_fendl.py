import re

with open("build_3d_toroidal_model.py", "r") as f:
    code = f.read()

# New shield definition using only Fe and Cr (fully supported by FENDL-3.1d)
new_shield_block = """# Shield (Fe-Cr Alloy Shield placeholder)
mat_shield = openmc.Material(name='Steel Shield')
mat_shield.add_element('Fe', 0.85)
mat_shield.add_element('Cr', 0.15)
mat_shield.set_density('g/cm3', 7.8)

# Plasma (Void / vacuum region for transport source)
mat_plasma = openmc.Material(name='Plasma Core')
mat_plasma.add_element('H', 1.0, percent_type='ao')
mat_plasma.set_density('g/cm3', 1.0e-5) # Near vacuum

materials = openmc.Materials([mat_fw, mat_mult, mat_bl, mat_str, mat_shield, mat_plasma])
materials.export_to_xml()
"""

# Replace everything from the shield definition onwards to the end of materials export
code = re.sub(r'# Shield.*', new_shield_block, code, flags=re.DOTALL)

with open("build_3d_toroidal_model.py", "w") as f:
    f.write(code)

print("build_3d_toroidal_model.py successfully updated with FENDL-compatible shield.")
