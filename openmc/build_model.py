import openmc
import numpy as np

print("Setting up OpenMC fusion blanket model...")

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

# --- 2. Source Definition (14.1 MeV D-T Fusion Neutrons) ---
source = openmc.IndependentSource()
# 14.1 MeV monoenergetic neutron source
source.space = openmc.stats.Point((0.0, 0.0, 0.0))
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])

settings = openmc.Settings()
settings.source = source
settings.batches = 50
settings.particles = 10000
settings.run_mode = 'fixed source'
settings.export_to_xml()

# --- 3. Tallies Definition (Volumetric Heating Mesh Tally) ---
# Create a regular rectangular mesh over the blanket region
mesh = openmc.RegularMesh()
mesh.lower_left = (-50.0, -50.0, -50.0)
mesh.upper_right = (50.0, 50.0, 50.0)
mesh.dimension = (50, 50, 50)

# Define heating tally on the mesh
tally = openmc.Tally(name='volumetric_heating')
tally.mesh = mesh
tally.scores = ['heating'] # Nuclear heating score (eV/g or eV/cm^3 depending on settings)

tallies = openmc.Tallies([tally])
tallies.export_to_xml()

print("OpenMC physics, source, and mesh tally configurations exported successfully!")
