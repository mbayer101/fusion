import os
import openmc

# --- 0. CONFIGURE CROSS SECTIONS ---
os.environ['OPENMC_CROSS_SECTIONS'] = '/root/cross_sections.xml'
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# --- 1. DEFINE MATERIALS ---
dt_fuel = openmc.Material(name='DT-Plasma')
dt_fuel.add_nuclide('H2', 0.5, 'ao')
dt_fuel.add_nuclide('H3', 0.5, 'ao')
dt_fuel.set_density('g/cm3', 1.0e-4)

tungsten = openmc.Material(name='Tungsten-Wall')
tungsten.add_element('W', 1.0, 'ao')
tungsten.set_density('g/cm3', 19.3)

pbli = openmc.Material(name='PbLi-Blanket')
pbli.add_element('Pb', 0.83, 'ao')
pbli.add_element(
    'Li',
    0.17,
    'ao',
    enrichment=90.0,
    enrichment_target='Li6',
    enrichment_type='ao',
)
pbli.set_density('g/cm3', 9.5)

rafm = openmc.Material(name='RAFM-Structure')
rafm.add_element('Fe', 89.0, 'wo')
rafm.add_element('Cr', 9.0, 'wo')
rafm.add_element('W', 1.0, 'wo')
rafm.add_element('V', 0.25, 'wo')
rafm.add_element('Ta', 0.07, 'wo')
rafm.set_density('g/cm3', 7.8)

materials = openmc.Materials([dt_fuel, tungsten, pbli, rafm])
materials.export_to_xml()

# --- 2. DEFINE GEOMETRY ---
c_plasma = openmc.Cylinder(r=0.5)
c_wall = openmc.Cylinder(r=0.55)
# THICKENED BLANKET: 50 cm thick (0.55 cm to 50.55 cm)
c_blanket = openmc.Cylinder(r=50.55)
# MOVED STRUCT AND OUTER BOUNDARY OUTWARD TO FIT THE BLANKET
c_struct = openmc.Cylinder(r=52.55)
c_outer = openmc.Cylinder(r=55.00, boundary_type='vacuum')

region_plasma = -c_plasma
region_wall = +c_plasma & -c_wall
region_blanket = +c_wall & -c_blanket
region_struct = +c_blanket & -c_struct
region_outer = +c_struct & -c_outer

cell_plasma = openmc.Cell(fill=dt_fuel, region=region_plasma)
cell_wall = openmc.Cell(fill=tungsten, region=region_wall)
cell_blanket = openmc.Cell(fill=pbli, region=region_blanket)
cell_struct = openmc.Cell(fill=rafm, region=region_struct)
cell_outer = openmc.Cell(region=region_outer)

geometry = openmc.Geometry(
    [cell_plasma, cell_wall, cell_blanket, cell_struct, cell_outer]
)
geometry.export_to_xml()

# --- 3. SETTINGS & NEUTRON SOURCE ---
settings = openmc.Settings()
settings.batches = 100
settings.inactive = 20
settings.particles = 50000
settings.run_mode = 'fixed source'

source = openmc.IndependentSource()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(0.0, 0.45),
    phi=openmc.stats.Uniform(0.0, 6.28318),
    z=openmc.stats.Uniform(-1.0, 1.0),
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])
settings.source = source
settings.export_to_xml()

# --- 4. TALLIES ---
tallies = openmc.Tallies()

# Tritium Breeding Ratio (TBR) Tally
tally_tbr = openmc.Tally(name='Tritium-Br-Tally')
tally_tbr.filters = [openmc.CellFilter([cell_blanket])]
tally_tbr.scores = ['205']
tallies.append(tally_tbr)

# Component Heating Tally covering Wall and Blanket
heating_filter = openmc.CellFilter([cell_wall, cell_blanket])
tally_heating = openmc.Tally(name='Component-Heating-Tally')
tally_heating.filters = [heating_filter]
tally_heating.scores = ['heating']
tallies.append(tally_heating)

tallies.export_to_xml()

# --- 5. GENERATE SLICE PLOT ---
plot = openmc.SlicePlot.from_geometry(geometry)
plot.basis = 'xy'
# UPDATED PLOT WIDTH: Expanded to 115x115 cm to capture the new 55 cm radius
plot.width = (115.0, 115.0) 
plot.pixels = (400, 400)
plot.color_by = 'material'

plot.colors = {
    dt_fuel: 'pink',
    tungsten: 'gray',
    pbli: 'blue',
    rafm: 'orange',
}

# Export through XML collection workflow for the modern plot generator
plots = openmc.Plots([plot])
plots.export_to_xml()

print('Model configuration, tallies, and plot definitions completed successfully.')
