import openmc
import numpy as np
import time

print("=== STEP 1: INITIALIZING SHIELDING & STREAMING ENVIRONMENT ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Re-load core materials
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

# Bio-Shield material using FENDL-native heavy elements (Fe, W, Pb)
mat_shield = openmc.Material(name='Bio_Shield', material_id=4)
mat_shield.add_element('Fe', 0.60, percent_type='ao')
mat_shield.add_element('W', 0.15, percent_type='ao')
mat_shield.add_element('Pb', 0.25, percent_type='ao')
mat_shield.set_density('g/cm3', 11.3)

materials = openmc.Materials([mat_fw, mat_bb, mat_div, mat_shield])
materials.cross_sections = '/root/cross_sections.xml'
materials.export_to_xml()

print("=== STEP 2: LOADING DAGMC GEOMETRY ===")
bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

print("=== STEP 3: CONFIGURE HIGH-STATISTICS SETTINGS & WEIGHT WINDOWS ===")
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 100
settings.particles = 100000

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

# Weight Window Generator setup for deep shielding attenuation
ww_mesh = openmc.CylindricalMesh(
    r_grid=np.linspace(30.0, 200.0, 30),
    phi_grid=np.linspace(0.0, 2.0 * np.pi, 12),
    z_grid=np.linspace(-80.0, 80.0, 30)
)

ww_gen = openmc.WeightWindowGenerator(
    mesh=ww_mesh,
    particle_type='neutron',
    method='magic',
    max_realizations=8,
    update_interval=2,
    on_the_fly=True
)
settings.weight_windows = ww_gen
settings.export_to_xml()

print("=== STEP 4: ESTABLISHING SHIELD PENETRATION & STREAMING TALLIES ===")
tallies = openmc.Tallies()
shield_filter = openmc.MeshFilter(ww_mesh)

streaming_tally = openmc.Tally(name='deep_shield_streaming_tally')
streaming_tally.filters = [shield_filter]
streaming_tally.scores = ['flux', 'damage-energy', 'heating']
tallies.append(streaming_tally)
tallies.export_to_xml()

print("=== STEP 5: EXECUTING PRODUCTION DEEP-PENETRATION SIMULATION ===")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"Deep-penetration simulation completed in {(time.time() - start_time):.2f} seconds.")

print("\n=== STEP 6: EXTRACTING ATTENUATION & STREAMING METRICS ===")
sp = openmc.StatePoint(f'statepoint.{settings.batches}.h5')
tally = sp.get_tally(name='deep_shield_streaming_tally')

flux_attenuation = tally.get_slice(scores=['flux']).mean
print(f"Shield attenuation map generated successfully.")
print(f" - Outer Shield/Streaming Mesh Bins: {flux_attenuation.shape[0]}")
print(f" - Peak Attenuated Flux Bin:         {np.max(flux_attenuation):.4e} n/cm²-s")
print(f" - Minimum Attenuated Flux Bin:      {np.min(flux_attenuation):.4e} n/cm²-s")
print("=======================================================")
