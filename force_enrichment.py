import openmc

# Re-initialize materials with Enriched Li-6 and valid FENDL nuclides/elements
mat_plasma = openmc.Material(name='Plasma D-T')
mat_plasma.add_nuclide('H2', 0.5, percent_type='ao')
mat_plasma.add_nuclide('H3', 0.5, percent_type='ao')
mat_plasma.set_density('g/cm3', 1e-4)

mat_fw = openmc.Material(name='First Wall (Eurofer)')
mat_fw.add_element('Fe', 0.89, percent_type='ao')
mat_fw.add_element('Cr', 0.10, percent_type='ao')
mat_fw.add_element('W', 0.01, percent_type='ao')
mat_fw.set_density('g/cm3', 7.8)

mat_mult = openmc.Material(name='Neutron Multiplier (Lead)')
mat_mult.add_element('Pb', 1.0, percent_type='ao')
mat_mult.set_density('g/cm3', 11.34)

# ENRICHED BREEDING BLANKET (90% Li-6, 10% Li-7 + Pb)
mat_bl = openmc.Material(name='Breeding Blanket')
mat_bl.add_nuclide('Li6', 0.18, percent_type='ao')
mat_bl.add_nuclide('Li7', 0.02, percent_type='ao')
mat_bl.add_element('Pb', 0.8, percent_type='ao')
mat_bl.set_density('g/cm3', 9.5)

mat_struct = openmc.Material(name='Structure (Tungsten)')
mat_struct.add_element('W', 1.0, percent_type='ao')
mat_struct.set_density('g/cm3', 19.3)

# SHIELD (Steel + Tungsten composite, using available elements)
mat_shield = openmc.Material(name='Shield (Steel-Tungsten)')
mat_shield.add_element('Fe', 0.70, percent_type='ao')
mat_shield.add_element('Cr', 0.10, percent_type='ao')
mat_shield.add_element('W', 0.20, percent_type='ao')
mat_shield.set_density('g/cm3', 10.5)

# Export materials.xml
materials = openmc.Materials([mat_plasma, mat_fw, mat_mult, mat_bl, mat_struct, mat_shield])
materials.export_to_xml()

print("Materials successfully re-exported with enriched Li-6 blanket and valid shield composition!")
