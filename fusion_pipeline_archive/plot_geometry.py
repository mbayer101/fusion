import os
import openmc

# --- 0. CONFIGURE CROSS SECTIONS ---
os.environ['OPENMC_CROSS_SECTIONS'] = '/root/cross_sections.xml'
openmc.config['cross_sections'] = '/root/cross_sections.xml'

print("Generating reactor geometry plot...")

# --- 1. DEFINE MATERIALS (Same as your final 45cm model) ---
dt_fuel = openmc.Material(name='DT-Plasma')
dt_fuel.add_nuclide('H2', 0.5, 'ao')
dt_fuel.add_nuclide('H3', 0.5, 'ao')
dt_fuel.set_density('g/cm3', 1.0e-4)

tungsten = openmc.Material(name='Tungsten-Wall')
tungsten.add_element('W', 1.0, 'ao')
tungsten.set_density('g/cm3', 19.3)

lead_multiplier = openmc.Material(name='Lead-Multiplier')
lead_multiplier.add_element('Pb', 1.0, 'ao')
lead_multiplier.set_density('g/cm3', 11.34)

pbli = openmc.Material(name='PbLi-Blanket')
pbli.add_element('Pb', 0.83, 'ao')
pbli.add_element('Li', 0.17, 'ao', enrichment=90.0, enrichment_target='Li6', enrichment_type='ao')
pbli.set_density('g/cm3', 9.5)

rafm = openmc.Material(name='RAFM-Structure')
rafm.add_element('Fe', 89.0, 'wo')
rafm.add_element('Cr', 9.0, 'wo')
rafm.add_element('W', 1.0, 'wo')
rafm.add_element('V', 0.25, 'wo')
rafm.add_element('Ta', 0.07, 'wo')
rafm.set_density('g/cm3', 7.8)

materials = openmc.Materials([dt_fuel, tungsten, lead_multiplier, pbli, rafm])

# --- 2. DEFINE GEOMETRY ---
r_plasma = 0.5
r_wall = 0.55
r_multiplier = r_wall + 5.0      # 5 cm Lead multiplier layer
r_blanket = r_multiplier + 45.0  # 45 cm PbLi blanket
r_struct = r_blanket + 2.0       # 2 cm RAFM structure
r_outer = r_struct + 2.5         # Vacuum boundary

c_plasma = openmc.Cylinder(r=r_plasma)
c_wall = openmc.Cylinder(r=r_wall)
c_multiplier = openmc.Cylinder(r=r_multiplier)
c_blanket = openmc.Cylinder(r=r_blanket)
c_struct = openmc.Cylinder(r=r_struct)
c_outer = openmc.Cylinder(r=r_outer, boundary_type='vacuum')

region_plasma = -c_plasma
region_wall = +c_plasma & -c_wall
region_multiplier = +c_wall & -c_multiplier
region_blanket = +c_multiplier & -c_blanket
region_struct = +c_blanket & -c_struct
region_outer = +c_struct & -c_outer

cell_plasma = openmc.Cell(fill=dt_fuel, region=region_plasma)
cell_wall = openmc.Cell(fill=tungsten, region=region_wall)
cell_multiplier = openmc.Cell(fill=lead_multiplier, region=region_multiplier)
cell_blanket = openmc.Cell(fill=pbli, region=region_blanket)
cell_struct = openmc.Cell(fill=rafm, region=region_struct)
cell_outer = openmc.Cell(region=region_outer)

geometry = openmc.Geometry([cell_plasma, cell_wall, cell_multiplier, cell_blanket, cell_struct, cell_outer])

# --- 3. CONFIGURE PLOT ---
plot = openmc.Plot()
plot.filename = 'reactor_xy_cross_section'
plot.basis = 'xy'  # Slice across X-Y plane
plot.origin = (0.0, 0.0, 0.0)  # Center of the plot
plot.width = (110.0, 110.0)    # View window width and height in cm (covers up to outer boundary)
plot.pixels = (800, 800)       # Resolution (800x800 pixels)

# Assign distinct RGB colors to each material for clear visual differentiation
plot.color_by = 'material'
plot.colors = {
    dt_fuel: [255, 100, 100],        # Soft Red (Plasma)
    tungsten: [150, 150, 150],       # Gray (Tungsten First Wall)
    lead_multiplier: [70, 130, 180], # Steel Blue (Lead Multiplier)
    pbli: [34, 139, 34],             # Forest Green (PbLi Breeding Blanket)
    rafm: [218, 165, 32]             # Goldenrod (RAFM Structural Shell)
}

plots = openmc.Plots([plot])
plots.export_to_xml()

# --- 4. GENERATE PLOT ---
# This invokes OpenMC's plotting module to write out the image file
openmc.plot_geometry()

print("Success! Plot saved as 'reactor_xy_cross_section.png'.")

