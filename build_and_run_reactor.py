import openmc
import numpy as np
import time
import os

print("=== INITIALIZING MASTER REACTOR BUILD & TRANSPORT PIPELINE ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Clean up previous state files
for f in ['summary.h5', 'statepoint.50.h5', 'geometry.xml', 'materials.xml', 'settings.xml', 'tallies.xml']:
    if os.path.exists(f):
        os.remove(f)

# --- 1. MATERIAL DEFINITIONS (BOM) ---
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

mat_shield = openmc.Material(name='Bio_Shield', material_id=4)
mat_shield.add_element('Fe', 0.60, percent_type='ao')
mat_shield.add_element('W', 0.15, percent_type='ao')
mat_shield.add_element('Pb', 0.25, percent_type='ao')
mat_shield.set_density('g/cm3', 11.3)

materials = openmc.Materials([mat_fw, mat_bb, mat_div, mat_shield])
materials.cross_sections = '/root/cross_sections.xml'
materials.export_to_xml()

# --- 2. CAD / DAGMC GEOMETRY SETUP ---
print("Loading DAGMC reactor topology (`full_reactor.h5m`)...")
bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

# --- 3. PHYSICS & SOURCE CONFIGURATION ---
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 50
settings.particles = 50000
settings.output = {'summary': False}

# 14.1 MeV Fusion Neutron Ring Source
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

# Weight Window Generator for Deep Shield Penetration
ww_mesh = openmc.CylindricalMesh(
    r_grid=np.linspace(30.0, 200.0, 25),
    phi_grid=np.linspace(0.0, 2.0 * np.pi, 8),
    z_grid=np.linspace(-80.0, 80.0, 25)
)

ww_gen = openmc.WeightWindowGenerator(
    mesh=ww_mesh,
    particle_type='neutron',
    method='magic',
    max_realizations=4,
    update_interval=2,
    on_the_fly=True
)
settings.weight_windows = ww_gen
settings.export_to_xml()

# --- 4. TALLIES & FIELD MAPPING ---
tallies = openmc.Tallies()
mesh_filter = openmc.MeshFilter(ww_mesh)

production_tally = openmc.Tally(name='reactor_production_tally')
production_tally.filters = [mesh_filter]
production_tally.scores = ['flux', 'heating', 'damage-energy']
tallies.append(production_tally)
tallies.export_to_xml()

# --- 5. EXECUTION ---
print("Executing production transport simulation...")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"Simulation completed in {(time.time() - start_time):.2f} seconds.")

# --- 6. RESULTS EXTRACTION ---
sp = openmc.StatePoint('statepoint.50.h5')
tally = sp.get_tally(name='reactor_production_tally')
flux_data = tally.get_slice(scores=['flux']).mean
heating_data = tally.get_slice(scores=['heating']).mean

print("\n=== BUILD & TRANSPORT VALIDATION SUMMARY ===")
print(f" - Spatial Mesh Bins Processed: {flux_data.shape[0]}")
print(f" - Peak Spatial Heating:        {np.max(heating_data):.4e} eV/source particle")
print(f" - Peak Neutron Flux:           {np.max(flux_data):.4e} n/cm²-s")
print("=======================================================")


