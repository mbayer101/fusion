import openmc
import time

print("=== 1. Initializing Materials & FENDL Cross Sections ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# First Wall Material (Structural Steel with Tungsten trace)
mat_fw = openmc.Material(name='First_Wall')
mat_fw.add_element('Fe', 0.89, percent_type='ao')
mat_fw.add_element('Cr', 0.10, percent_type='ao')
mat_fw.add_element('W', 0.01, percent_type='ao')
mat_fw.set_density('g/cm3', 7.8)

# Breeding Blanket Material
mat_bb = openmc.Material(name='Breeding_Blanket')
mat_bb.add_element('Li', 0.5, percent_type='ao', enrichment=90.0, enrichment_target='Li6')
mat_bb.add_element('Pb', 0.5, percent_type='ao')
mat_bb.set_density('g/cm3', 9.5)

# Divertor Material (Pure Tungsten)
mat_div = openmc.Material(name='Divertor')
mat_div.add_element('W', 1.0, percent_type='ao')
mat_div.set_density('g/cm3', 19.3)

materials = openmc.Materials([mat_fw, mat_bb, mat_div])
materials.cross_sections = '/root/cross_sections.xml'
materials.export_to_xml()

print("=== 2. Loading DAGMC Geometry ===")
bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

print("=== 3. Configuring Settings & 14.1 MeV Fusion Source ===")
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 30          
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

print("=== 4. Setting up Advanced Tallies (Heating, TBR, & DPA) ===")
tallies = openmc.Tallies()

# Standard Thermal & Breeding Tallies
tally_fw = openmc.Tally(name='first_wall_heating')
tally_fw.filters = [openmc.MaterialFilter([mat_fw])]
tally_fw.scores = ['heating']
tallies.append(tally_fw)

tally_tbr = openmc.Tally(name='breeding_blanket_tbr')
tally_tbr.filters = [openmc.MaterialFilter([mat_bb])]
tally_tbr.scores = ['(n,t)']
tallies.append(tally_tbr)

tally_div = openmc.Tally(name='divertor_heating')
tally_div.filters = [openmc.MaterialFilter([mat_div])]
tally_div.scores = ['heating']
tallies.append(tally_div)

# --- MATERIAL DAMAGE TALLIES ---
dpa_fw = openmc.Tally(name='first_wall_damage_energy')
dpa_fw.filters = [openmc.MaterialFilter([mat_fw])]
dpa_fw.scores = ['damage-energy']
tallies.append(dpa_fw)

dpa_div = openmc.Tally(name='divertor_damage_energy')
dpa_div.filters = [openmc.MaterialFilter([mat_div])]
dpa_div.scores = ['damage-energy']
tallies.append(dpa_div)

tallies.export_to_xml()

print("=== 5. Executing Damage & Simulation ===")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"=== Simulation Completed in {(time.time() - start_time):.2f} seconds ===")

print("\n=== 6. Parsing Damage and Thermal Results ===")
sp = openmc.StatePoint('statepoint.30.h5')

fw_heat = sp.get_tally(name='first_wall_heating')
tbr = sp.get_tally(name='breeding_blanket_tbr')
div_heat = sp.get_tally(name='divertor_heating')
dpa_fw_tally = sp.get_tally(name='first_wall_damage_energy')
dpa_div_tally = sp.get_tally(name='divertor_damage_energy')

print("\n=======================================================")
print("     REACTOR INTEGRITY & MATERIALS DAMAGE REPORT       ")
print("=======================================================")
print(f"First Wall Heating    : {fw_heat.mean[0][0][0]:.5e} +/- {fw_heat.std_dev[0][0][0]:.5e} eV/src")
print(f"Divertor Heating      : {div_heat.mean[0][0][0]:.5e} +/- {div_heat.std_dev[0][0][0]:.5e} eV/src")
print(f"Tritium Breeding (TBR): {tbr.mean[0][0][0]:.5e} +/- {tbr.std_dev[0][0][0]:.5e} trit/src")
print(f"FW Damage Energy      : {dpa_fw_tally.mean[0][0][0]:.5e} +/- {dpa_fw_tally.std_dev[0][0][0]:.5e} eV/src")
print(f"Divertor Damage Energy: {dpa_div_tally.mean[0][0][0]:.5e} +/- {dpa_div_tally.std_dev[0][0][0]:.5e} eV/src")
print("=======================================================")
