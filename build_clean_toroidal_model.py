import openmc

print("Building Clean 3D Toroidal Fusion Model with Enriched Blanket...")

# 1. Materials
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

# Enriched Breeding Blanket (90% Li-6, 10% Li-7 + Pb)
mat_bl = openmc.Material(name='Breeding Blanket')
mat_bl.add_nuclide('Li6', 0.18, percent_type='ao')
mat_bl.add_nuclide('Li7', 0.02, percent_type='ao')
mat_bl.add_element('Pb', 0.8, percent_type='ao')
mat_bl.set_density('g/cm3', 9.5)

mat_struct = openmc.Material(name='Structure (Tungsten)')
mat_struct.add_element('W', 1.0, percent_type='ao')
mat_struct.set_density('g/cm3', 19.3)

mat_shield = openmc.Material(name='Shield (Steel-Tungsten)')
mat_shield.add_element('Fe', 0.70, percent_type='ao')
mat_shield.add_element('Cr', 0.10, percent_type='ao')
mat_shield.add_element('W', 0.20, percent_type='ao')
mat_shield.set_density('g/cm3', 10.5)

materials = openmc.Materials([mat_plasma, mat_fw, mat_mult, mat_bl, mat_struct, mat_shield])
materials.export_to_xml()

# 2. Geometry (Concentric Toroidal Shells, Major Radius R0 = 600 cm)
R0 = 600.0

surf_plasma = openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=200.0, c=200.0)
surf_plasma.id = 1

surf_fw = openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=210.0, c=210.0)
surf_fw.id = 2

surf_mult = openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=220.0, c=220.0)
surf_mult.id = 3

surf_bl = openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=280.0, c=280.0)
surf_bl.id = 4

surf_struct = openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=290.0, c=290.0)
surf_struct.id = 5

surf_shield = openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=350.0, c=350.0)
surf_shield.id = 6

# Regions
reg_plasma = -surf_plasma
reg_fw     = +surf_plasma & -surf_fw
reg_mult   = +surf_fw & -surf_mult
reg_bl     = +surf_mult & -surf_bl
reg_struct = +surf_bl & -surf_struct
reg_shield = +surf_struct & -surf_shield

# Cells
cell_plasma = openmc.Cell(cell_id=1, name='Plasma', fill=mat_plasma, region=reg_plasma)
cell_fw     = openmc.Cell(cell_id=2, name='First Wall', fill=mat_fw, region=reg_fw)
cell_mult   = openmc.Cell(cell_id=3, name='Multiplier', fill=mat_mult, region=reg_mult)
cell_bl     = openmc.Cell(cell_id=4, name='Breeding Blanket', fill=mat_bl, region=reg_bl)
cell_struct = openmc.Cell(cell_id=5, name='Structure', fill=mat_struct, region=reg_struct)
cell_shield = openmc.Cell(cell_id=6, name='Shield', fill=mat_shield, region=reg_shield)

root_universe = openmc.Universe(cells=[cell_plasma, cell_fw, cell_mult, cell_bl, cell_struct, cell_shield])
geometry = openmc.Geometry(root_universe)
geometry.export_to_xml()

# 3. Settings (Fixed Source Mode)
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 50
settings.inactive = 10
settings.particles = 10000
settings.source_rejection_fraction = 0.5

source = openmc.IndependentSource()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(400.0, 800.0),
    phi=openmc.stats.Uniform(0.0, 2.0 * 3.1415926535),
    z=openmc.stats.Uniform(-200.0, 200.0),
    origin=(0.0, 0.0, 0.0)
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])

settings.source = source
settings.export_to_xml()

# 4. Tallies (Cell 4: Breeding Blanket)
tallies = openmc.Tallies()
cell_filter = openmc.CellFilter([4])
tally_blanket = openmc.Tally(name='blanket_performance')
tally_blanket.filters = [cell_filter]
tally_blanket.scores = ['heating', '(n,t)']
tallies.append(tally_blanket)
tallies.export_to_xml()

print("Clean toroidal model built and exported successfully!")
