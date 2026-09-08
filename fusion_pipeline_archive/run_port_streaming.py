import openmc
import time
import numpy as np

print("=== STEP 1: INITIALIZING ENVIRONMENT & MATERIALS ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Load existing core materials
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

print("=== STEP 2: LOADING DAGMC REACTOR GEOMETRY ===")
bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

print("=== STEP 3: CONFIGURE FIXED SOURCE & SIMULATION SETTINGS ===")
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 50
settings.particles = 50000

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
settings.export_to_xml()

print("=== STEP 4: SETTING UP SEPARATE PORT STREAMING TALLIES ===")
tallies = openmc.Tallies()

port_streaming_mesh = openmc.CylindricalMesh(
    r_grid=np.linspace(100.0, 200.0, 30),
    phi_grid=np.linspace(0.0, 2.0 * np.pi, 12),
    z_grid=np.linspace(-60.0, 60.0, 30)
)
port_mesh_filter = openmc.MeshFilter(port_streaming_mesh)

# Dedicated Flux Tally (guaranteed 3D array)
flux_tally = openmc.Tally(name='port_flux_tally')
flux_tally.filters = [port_mesh_filter]
flux_tally.scores = ['flux']
tallies.append(flux_tally)

# Dedicated Heating Tally (guaranteed 3D array)
heating_tally = openmc.Tally(name='port_heating_tally')
heating_tally.filters = [port_mesh_filter]
heating_tally.scores = ['heating']
tallies.append(heating_tally)

tallies.export_to_xml()

print("=== STEP 5: EXECUTING TRANSPORT SIMULATION ===")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"Simulation completed in {(time.time() - start_time):.2f} seconds.")

print("\n=== STEP 6: EXPORTING STREAMING MESH TO VTK (PARA-VIEW) ===")
sp = openmc.StatePoint('statepoint.50.h5')

flux_result = sp.get_tally(name='port_flux_tally')
heating_result = sp.get_tally(name='port_heating_tally')

vtk_filename = "port_streaming_analysis.vtk"
port_streaming_mesh.write_data_to_vtk(
    vtk_filename, 
    datasets={
        'Neutron Flux (n/cm2-src)': flux_result.mean,
        'Heating (eV/src)': heating_result.mean
    }
)
print(f"Successfully exported port streaming analysis to {vtk_filename}")

print("\n=======================================================")
print("      PORT STREAMING PIPELINE EXECUTION COMPLETE       ")
print("=======================================================")
