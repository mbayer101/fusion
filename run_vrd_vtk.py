import openmc
import numpy as np
import os

print("=== STEP 1: SETTING UP SPATIAL MESH TALLY FOR VTK EXPORT ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Re-load geometry and materials
mat_fw = openmc.Material(name='First_Wall', material_id=1)
mat_fw.add_element('Fe', 0.89, percent_type='ao')
mat_fw.add_element('Cr', 0.10, percent_type='ao')
mat_fw.add_element('W', 0.01, percent_type='ao')
mat_fw.set_density('g/cm3', 7.8)

mat_bb = openmc.Material(name='Breeding_Blanket', material_id=2)
mat_bb.add_element('Li', 0.5, percent_type='ao', enrichment=90.0, enrichment_target='Li6')
mat_bb.add_element('Pb', 0.5, percent_type='ao')
mat_bb.set_density('g/cm3', 9.5)

mat_div = openmc.Material(name='Divertor', material_id=3)
mat_div.add_element('W', 1.0, percent_type='ao')
mat_div.set_density('g/cm3', 19.3)

materials = openmc.Materials([mat_fw, mat_bb, mat_div])
materials.cross_sections = '/root/cross_sections.xml'
materials.export_to_xml()

bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 20
settings.particles = 20000

source = openmc.IndependentSource()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(40.0, 90.0),
    phi=openmc.stats.Uniform(0.0, 2.0 * np.pi),
    z=openmc.stats.Uniform(-30.0, 30.0),
    origin=(0.0, 0.0, 0.0)
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])
settings.source = source

print("=== STEP 2: CONFIGURE WEIGHT WINDOW GENERATOR (MAGIC METHOD) ===")
# Define a cylindrical mesh covering the core and shielding for variance reduction
ww_mesh = openmc.CylindricalMesh(
    r_grid=np.linspace(30.0, 150.0, 20),
    phi_grid=np.linspace(0.0, 2.0 * np.pi, 8),
    z_grid=np.linspace(-60.0, 60.0, 20)
)

# Attach Weight Window Generator to settings for automated variance reduction optimization
ww_gen = openmc.WeightWindowGenerator(
    mesh=ww_mesh,
    particle_type='neutron',
    method='magic',
    max_realizations=5,
    update_interval=2,
    on_the_fly=True
)
settings.weight_windows = ww_gen
settings.export_to_xml()

print("=== STEP 3: ADDING SPATIAL MESH TALLY FOR VTK VISUALIZATION ===")
tallies = openmc.Tallies()
mesh_filter = openmc.MeshFilter(ww_mesh)

spatial_tally = openmc.Tally(name='spatial_heating_tally')
spatial_tally.filters = [mesh_filter]
spatial_tally.scores = ['heating', 'flux']
tallies.append(spatial_tally)
tallies.export_to_xml()

print("=== STEP 4: EXECUTING OPTIMIZED TRANSPORT RUN ===")
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')

print("\n=== STEP 5: EXPORTING RESULTS TO VTK FORMAT ===")
sp = openmc.StatePoint('statepoint.20.h5')
tally = sp.get_tally(name='spatial_heating_tally')

# Write mesh tally data directly to a legacy VTK file for ParaView inspection
vtk_filename = 'reactor_heating_flux.vtk'
tally.write_to_vtk(vtk_filename)

print(f"VTK export successful: '{vtk_filename}' generated.")
print("You can download and open this file in ParaView to analyze 3D spatial distributions.")
print("=======================================================")
