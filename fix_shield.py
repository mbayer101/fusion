with open("build_3d_toroidal_model.py", "r") as f:
    code = f.read()

# Replace the borated steel shield with standard Stainless Steel 316
old_shield = """# Shield (Borated Steel representation / placeholder)
mat_shield = openmc.Material(name='Borated Steel Shield')
mat_shield.add_element('Fe', 0.70)
mat_shield.add_element('Cr', 0.20)
mat_shield.add_element('B', 0.10)
mat_shield.set_density('g/cm3', 7.7)"""

new_shield = """# Shield (Stainless Steel 316 placeholder)
mat_shield = openmc.Material(name='SS316 Shield')
mat_shield.add_element('Fe', 0.65)
mat_shield.add_element('Cr', 0.18)
mat_shield.add_element('Ni', 0.12)
mat_shield.add_element('Mo', 0.05)
mat_shield.set_density('g/cm3', 7.98)"""

if old_shield in code:
    code = code.replace(old_shield, new_shield)
    with open("build_3d_toroidal_model.py", "w") as f:
        f.write(code)
    print("Successfully patched build_3d_toroidal_model.py with SS316 shield.")
else:
    print("Could not find exact text match; updating shield block manually.")
    # Fallback rewrite of materials section
    import re
    code = re.sub(r'mat_shield\s*=.*?(?=mat_plasma)', '', code, flags=re.DOTALL)
    # Append correct shield and plasma
    shield_code = """
# Shield (Stainless Steel 316 placeholder)
mat_shield = openmc.Material(name='SS316 Shield')
mat_shield.add_element('Fe', 0.65)
mat_shield.add_element('Cr', 0.18)
mat_shield.add_element('Ni', 0.12)
mat_shield.add_element('Mo', 0.05)
mat_shield.set_density('g/cm3', 7.98)

# Plasma (Void / vacuum region for transport source)
mat_plasma = openmc.Material(name='Plasma Core')
mat_plasma.add_element('H', 1.0, percent_type='ao')
mat_plasma.set_density('g/cm3', 1.0e-5) # Near vacuum

materials = openmc.Materials([mat_fw, mat_mult, mat_bl, mat_str, mat_shield, mat_plasma])
materials.export_to_xml()
"""
    # Replace from mat_fw definition onwards
    code = re.sub(r'# Tungsten First Wall.*', shield_code, code, flags=re.DOTALL)
    with open("build_3d_toroidal_model.py", "w") as f:
        f.write(code)
    print("Fallback patch applied successfully.")
