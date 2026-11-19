import openmc
import numpy as np

print("Setting up upgraded 3-stage F-F-F OpenMC model with SphericalMesh & MAGIC Weight Windows...")

# --- 1. Materials Definition ---
tungsten = openmc.Material(name="Tungsten_First_Wall")
tungsten.add_element('W', 1.0, 'wo')
tungsten.set_density('g/cc', 19.3)

eurofer = openmc.Material(name="Eurofer-97")
eurofer.add_nuclide('Fe56', 0.88, 'wo')
eurofer.add_nuclide('Cr52', 0.09, 'wo')
eurofer.add_nuclide('W182', 0.01, 'wo')
eurofer.set_density('g/cc', 7.75)

# Stage 2: Subcritical Fission Blanket (Fertile U-238 suspended in LBE)
fission_lbe = openmc.Material(name="Fission_LBE_U238")
fission_lbe.add_element('Pb', 0.38, 'wo')
fission_lbe.add_element('Bi', 0.47, 'wo')
fission_lbe.add_nuclide('U238', 0.145, 'wo')
fission_lbe.add_nuclide('U235', 0.005, 'wo')
fission_lbe.set_density('g/cc', 10.5)

# Stage 3: Tritium Breeding Blanket (Enriched Li-6 FliBe)
flibe = openmc.Material(name="Enriched_FliBe")
flibe.add_element('Li', 2.0, 'ao', enrichment=90.0, enrichment_target='Li6')
flibe.add_element('Be', 1.0, 'ao')
flibe.add_element('F', 4.0, 'ao')
flibe.set_density('g/cc', 1.94)

# Outer Reflector: Graphite to reduce neutron leakage
graphite = openmc.Material(name="Graphite_Reflector")
graphite.add_element('C', 1.0, 'ao')
graphite.set_density('g/cc', 1.75)

materials = openmc.Materials([tungsten, eurofer, fission_lbe, flibe, graphite])
materials.export_to_xml()

# --- 2. Concentric 3-Stage F-F-F Geometry ---
r_plasma = openmc.Sphere(r=30.0)
r_wall   = openmc.Sphere(r=32.0)
r_fiss   = openmc.Sphere(r=65.0)
r_breed  = openmc.Sphere(r=95.0)
r_refl   = openmc.Sphere(r=120.0, boundary_type='vacuum')

cell_plasma = openmc.Cell(name='Stage1_Plasma_Void', region=-r_plasma)
cell_wall   = openmc.Cell(name='First_Wall_W', fill=tungsten, region=+r_plasma & -r_wall)
cell_fiss   = openmc.Cell(name='Stage2_Subcritical_Fission', fill=fission_lbe, region=+r_wall & -r_fiss)
cell_breed  = openmc.Cell(name='Stage3_Tritium_Breeding', fill=flibe, region=+r_fiss & -r_breed)
cell_refl   = openmc.Cell(name='Outer_Graphite_Reflector', fill=graphite, region=+r_breed & -r_refl)

geometry = openmc.Geometry([cell_plasma, cell_wall, cell_fiss, cell_breed, cell_refl])
geometry.export_to_xml()

# --- 3. Source & Variance Reduction Settings ---
source = openmc.IndependentSource()
source.space = openmc.stats.Point((0.0, 0.0, 0.0))
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])

settings = openmc.Settings()
settings.source = source
settings.batches = 25
settings.particles = 10000
settings.run_mode = 'fixed source'

# --- 4. Spherical Mesh & MAGIC Weight Windows ---
mesh = openmc.SphericalMesh()
mesh.r_grid = [30.0, 32.0, 40.0, 50.0, 65.0, 75.0, 85.0, 95.0, 120.0]
mesh.theta_grid = [0.0, np.pi]
mesh.phi_grid = [0.0, 2.0 * np.pi]

wwg = openmc.WeightWindowGenerator(
    method='magic',
    mesh=mesh,
    max_realizations=settings.batches
)
settings.weight_window_generators = wwg
settings.export_to_xml()

# --- 5. Tallies (Volumetric Heating + Tritium Breeding Ratio) ---
mesh_filter = openmc.MeshFilter(mesh)

heating_tally = openmc.Tally(name='volumetric_heating')
heating_tally.filters = [mesh_filter]
heating_tally.scores = ['heating']

tbr_tally = openmc.Tally(name='tritium_breeding')
tbr_tally.filters = [openmc.CellFilter(cell_breed)]
tbr_tally.scores = ['(n,Xt)']

tallies = openmc.Tallies([heating_tally, tbr_tally])
tallies.export_to_xml()

print("Exported upgraded 3-stage F-F-F geometry, SphericalMesh, and MAGIC weight windows!")
