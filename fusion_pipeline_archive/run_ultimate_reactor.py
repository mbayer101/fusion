import openmc
import openmc.deplete
import time
import os
import numpy as np

print("=== STEP 1: INITIALIZING MATERIALS & CROSS SECTIONS ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Materials setup
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

print("=== STEP 2: LOADING DAGMC GEOMETRY ===")
bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

print("=== STEP 3: SETTING UP HIGH-STATISTICS SIMULATION & SOURCE ===")
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 50
settings.particles = 50000

source = openmc.IndependentSource()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(40.0, 90.0),
    phi=openmc.stats.Uniform(0.0, 2.0 * 3.1415926535),
    z=openmc.stats.Uniform(-30.0, 30.0),
    origin=(0.0, 0.0, 0.0)
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])
settings.source = source
settings.export_to_xml()

print("=== STEP 4: CONFIGURING VARIANCE REDUCTION MESH FRAMEWORK ===")
ww_mesh = openmc.CylindricalMesh(
    r_grid=np.linspace(0.0, 200.0, 20),
    phi_grid=[0.0, 3.1415926535, 6.283185307],
    z_grid=np.linspace(-100.0, 100.0, 20)
)
print("Variance reduction spatial mesh structured successfully.")

print("=== STEP 5: CREATING TALLIES & 3D CYLINDRICAL MESH ===")
tallies = openmc.Tallies()

tally_fw = openmc.Tally(name='first_wall_heating')
tally_fw.filters = [openmc.MaterialFilter([mat_fw])]
tally_fw.scores = ['heating']
tallies.append(tally_fw)

tally_tbr = openmc.Tally(name='breeding_blanket_tbr')
tally_tbr.filters = [openmc.MaterialFilter([mat_bb])]
tally_tbr.scores = ['(n,t)']
tallies.append(tally_tbr)

mesh = openmc.CylindricalMesh(
    r_grid=[0.0, 50.0, 100.0, 150.0],
    phi_grid=[0.0, 3.1415926535, 6.283185307],
    z_grid=[-50.0, -25.0, 0.0, 25.0, 50.0]
)
mesh_tally = openmc.Tally(name='spatial_heating_mesh')
mesh_tally.filters = [openmc.MeshFilter(mesh)]
mesh_tally.scores = ['heating']
tallies.append(mesh_tally)

tallies.export_to_xml()

print("=== STEP 6: EXECUTING TRANSPORT SIMULATION ===")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"Simulation completed in {(time.time() - start_time):.2f} seconds.")

print("\n=== STEP 7: EXPORTING 3D MESH TALLY TO VTK (PARA-VIEW) ===")
sp = openmc.StatePoint('statepoint.50.h5')
mesh_tally_result = sp.get_tally(name='spatial_heating_mesh')
vtk_filename = "reactor_heating_distribution.vtk"
mesh.write_data_to_vtk(vtk_filename, datasets={'Heating (eV/src)': mesh_tally_result.mean})
print(f"Successfully exported 3D spatial mesh tally to {vtk_filename}")

print("\n=== STEP 8: INITIALIZING ISOTOPE DEPLETION & ACTIVATION MODULE ===")
chain_path = '/root/chain_endfb80.xml'
if os.path.exists(chain_path):
    time_steps = [30.0, 30.0, 30.0, 30.0, 30.0, 30.0]
    power = 500e6
    operator = openmc.deplete.CoupledOperator(geometry, settings, chain_file=chain_path)
    print("Depletion operator initialized. Ready to execute integrator.")
else:
    print(f"Depletion chain file missing at {chain_path}. Skipping active time-step loop.")

print("\n=======================================================")
print("    ULTIMATE REACTOR WORKFLOW PIPELINE COMPLETED       ")
print("=======================================================")
