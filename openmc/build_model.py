import openmc
import numpy as np

print("Setting up OpenMC fusion blanket model with CSG geometry...")

# --- 1. Materials Definition ---
eurofer = openmc.Material(name="Eurofer-97")
eurofer.add_nuclide('Fe56', 0.88, 'wo')
eurofer.add_nuclide('Cr52', 0.09, 'wo')
eurofer.add_nuclide('W182', 0.01, 'wo')
eurofer.set_density('g/cc', 7.75)

lipb = openmc.Material(name="LiPb-Eutectic")
lipb.add_element('Li', 0.176, 'ao', enrichment=90.0, enrichment_target='Li6')
lipb.add_element('Pb', 0.824, 'ao')
lipb.set_density('g/cc', 9.4)

materials = openmc.Materials([eurofer, lipb])
materials.export_to_xml()

# --- 2. Geometry Setup (Simple CSG Bounding Box) ---
outer_surf = openmc.Sphere(r=100.0, boundary_type='vacuum')
blanket_cell = openmc.Cell(cell_id=1, name='Blanket Region')
blanket_cell.fill = lipb
blanket_cell.region = -outer_surf

geometry = openmc.Geometry([blanket_cell])
geometry.export_to_xml()

# --- 3. Source Definition (14.1 MeV D-T Fusion Neutrons) ---
source = openmc.IndependentSource()
source.space = openmc.stats.Point((0.0, 0.0, 0.0))
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])

settings = openmc.Settings()
settings.source = source
settings.batches = 20
settings.particles = 5000
settings.run_mode = 'fixed source'
settings.export_to_xml()

# --- 4. Tallies Definition (Volumetric Heating Mesh Tally) ---
mesh = openmc.RegularMesh()
mesh.lower_left = (-50.0, -50.0, -50.0)
mesh.upper_right = (50.0, 50.0, 50.0)
mesh.dimension = (50, 50, 50)  # Increased resolution

tally = openmc.Tally(name='volumetric_heating')
tally.mesh = mesh
tally.scores = ['heating']

tallies = openmc.Tallies([tally])
tallies.export_to_xml()

print("OpenMC CSG geometry, materials, source, and tallies exported successfully!")
