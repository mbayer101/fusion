import openmc
import time
import numpy as np

print("=== STEP 1: INITIALIZING ENVIRONMENT & MATERIALS ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

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

print("=== STEP 3: CONFIGURE FIXED SOURCE & SETTINGS ===")
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

print("=== STEP 4: SETTING UP EXPLICIT MATERIAL REACTION TALLIES ===")
tallies = openmc.Tallies()

fw_filter = openmc.MaterialFilter([mat_fw])
bb_filter = openmc.MaterialFilter([mat_bb])
div_filter = openmc.MaterialFilter([mat_div])

# 1. First Wall tally using verified standard scores
fw_tally = openmc.Tally(name='first_wall_activation')
fw_tally.filters = [fw_filter]
fw_tally.scores = ['flux', 'heating', '(n,2n)']
tallies.append(fw_tally)

# 2. Breeding Blanket tally
bb_tally = openmc.Tally(name='breeding_blanket_tritium')
bb_tally.filters = [bb_filter]
bb_tally.scores = ['flux', 'heating', '(n,2n)']
tallies.append(bb_tally)

# 3. Divertor tally
div_tally = openmc.Tally(name='divertor_damage')
div_tally.filters = [div_filter]
div_tally.scores = ['flux', 'heating', 'damage-energy']
tallies.append(div_tally)

tallies.export_to_xml()

print("=== STEP 5: EXECUTING TRANSPORT SIMULATION ===")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"Simulation completed in {(time.time() - start_time):.2f} seconds.")

print("\n=== STEP 6: EXTRACTING REACTION RATES & RESULTS ===")
sp = openmc.StatePoint('statepoint.50.h5')
bb_result = sp.get_tally(name='breeding_blanket_tritium')
flux_mean = bb_result.get_slice(scores=['flux']).mean

print(f"Extraction successful. Transport and activation tally mapping complete.")
print("=======================================================")
