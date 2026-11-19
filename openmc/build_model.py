import openmc
import numpy as np

print("Building production 3-stage F-F-F OpenMC model with 6.0 cm Beryllium front multiplier...")

# --- 1. Materials ---
tungsten = openmc.Material(name="Tungsten_First_Wall")
tungsten.add_element('W', 1.0, 'wo')
tungsten.set_density('g/cc', 19.3)

beryllium = openmc.Material(name="Beryllium_Multiplier")
beryllium.add_element('Be', 1.0, 'ao')
beryllium.set_density('g/cc', 1.85)

# Radially graded Stage 2 Uranium loading (7 / 14 / 24 wt%)
grade_specs = [(0.07, 10.31), (0.14, 10.47), (0.24, 10.70)]
lbe_zones = []
for idx, (u_tot, rho) in enumerate(grade_specs):
    u235_w = u_tot * (0.005 / 0.15)
    u238_w = u_tot - u235_w
    lbe_w  = 1.0 - u_tot
    mat = openmc.Material(name=f"Fission_LBE_Zone{idx+1}")
    mat.add_element('Pb', lbe_w * 0.447, 'wo')
    mat.add_element('Bi', lbe_w * 0.553, 'wo')
    mat.add_nuclide('U238', u238_w, 'wo')
    mat.add_nuclide('U235', u235_w, 'wo')
    mat.set_density('g/cc', rho)
    lbe_zones.append(mat)

flibe = openmc.Material(name="Enriched_FliBe")
flibe.add_element('Li', 2.0, 'ao', enrichment=90.0, enrichment_target='Li6')
flibe.add_element('Be', 1.0, 'ao')
flibe.add_element('F', 4.0, 'ao')
flibe.set_density('g/cc', 1.94)

graphite = openmc.Material(name="Graphite_Reflector")
graphite.add_element('C', 1.0, 'ao')
graphite.set_density('g/cc', 1.75)

materials = openmc.Materials([tungsten, beryllium] + lbe_zones + [flibe, graphite])
materials.export_to_xml()

# --- 2. Concentric Geometry with 6.0 cm Beryllium Front Multiplier (32 - 38 cm) ---
r_plasma = openmc.Sphere(r=30.0)
r_wall   = openmc.Sphere(r=32.0)
r_be     = openmc.Sphere(r=38.0)
r_z1     = openmc.Sphere(r=46.0)
r_z2     = openmc.Sphere(r=56.0)
r_fiss   = openmc.Sphere(r=71.0)
r_breed  = openmc.Sphere(r=101.0)
r_refl   = openmc.Sphere(r=126.0, boundary_type='vacuum')

c_plasma = openmc.Cell(name='Stage1_Plasma_Void', region=-r_plasma)
c_wall   = openmc.Cell(name='First_Wall_W', fill=tungsten, region=+r_plasma & -r_wall)
c_be     = openmc.Cell(name='Front_Be_Multiplier', fill=beryllium, region=+r_wall & -r_be)
c_z1     = openmc.Cell(name='Stage2_Zone1_Inner', fill=lbe_zones[0], region=+r_be & -r_z1)
c_z2     = openmc.Cell(name='Stage2_Zone2_Mid', fill=lbe_zones[1], region=+r_z1 & -r_z2)
c_z3     = openmc.Cell(name='Stage2_Zone3_Outer', fill=lbe_zones[2], region=+r_z2 & -r_fiss)
c_breed  = openmc.Cell(name='Stage3_Tritium_Breeding', fill=flibe, region=+r_fiss & -r_breed)
c_refl   = openmc.Cell(name='Outer_Graphite_Reflector', fill=graphite, region=+r_breed & -r_refl)

geometry = openmc.Geometry([c_plasma, c_wall, c_be, c_z1, c_z2, c_z3, c_breed, c_refl])
geometry.export_to_xml()

# --- 3. Source & MAGIC Variance Reduction ---
source = openmc.IndependentSource()
source.space = openmc.stats.Point((0.0, 0.0, 0.0))
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])

settings = openmc.Settings()
settings.source = source
settings.batches = 25
settings.particles = 10000
settings.run_mode = 'fixed source'

mesh = openmc.SphericalMesh(
    r_grid=[30.0, 32.0, 38.0, 46.0, 56.0, 71.0, 81.0, 91.0, 101.0, 126.0],
    theta_grid=[0.0, np.pi],
    phi_grid=[0.0, 2.0 * np.pi]
)

settings.weight_window_generators = openmc.WeightWindowGenerator(
    method='magic', mesh=mesh, max_realizations=settings.batches
)
settings.export_to_xml()

# --- 4. Tallies ---
heating_tally = openmc.Tally(name='volumetric_heating')
heating_tally.filters = [openmc.MeshFilter(mesh)]
heating_tally.scores = ['heating']

tbr_tally = openmc.Tally(name='tritium_breeding')
tbr_tally.filters = [openmc.CellFilter(c_breed)]
tbr_tally.scores = ['(n,Xt)']

tallies = openmc.Tallies([heating_tally, tbr_tally])
tallies.export_to_xml()
print("Exported 6.0 cm Be-multiplied F-F-F geometry and tallies!")
