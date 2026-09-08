import openmc
import openmc.deplete
import time
import os

print("=== 1. Initializing Materials & FENDL Cross Sections ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# First Wall Material (Structural Steel with Tungsten trace)
mat_fw = openmc.Material(name='First_Wall', material_id=1)
mat_fw.add_element('Fe', 0.89, percent_type='ao')
mat_fw.add_element('Cr', 0.10, percent_type='ao')
mat_fw.add_element('W', 0.01, percent_type='ao')
mat_fw.set_density('g/cm3', 7.8)

# Breeding Blanket Material
mat_bb = openmc.Material(name='Breeding_Blanket', material_id=2)
mat_bb.add_element('Li', 0.5, percent_type='ao', enrichment=90.0, enrichment_target='Li6')
mat_bb.add_element('Pb', 0.5, percent_type='ao')
mat_bb.set_density('g/cm3', 9.5)

# Divertor Material (Pure Tungsten)
mat_div = openmc.Material(name='Divertor', material_id=3)
mat_div.add_element('W', 1.0, percent_type='ao')
mat_div.set_density('g/cm3', 19.3)

materials = openmc.Materials([mat_fw, mat_bb, mat_div])
materials.cross_sections = '/root/cross_sections.xml'
materials.export_to_xml()

print("=== 2. Loading DAGMC Geometry ===")
bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

print("=== 3. Configuring High-Statistics Settings & Source ===")
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 100          # Enhancement 1: Increased batches
settings.particles = 100000     # Enhancement 1: Increased particle count

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

print("=== 4. Setting up Advanced Tallies & 3D Spatial Mesh Tallies ===")
tallies = openmc.Tallies()

# Global Material Tallies
tally_fw = openmc.Tally(name='first_wall_heating')
tally_fw.filters = [openmc.MaterialFilter([mat_fw])]
tally_fw.scores = ['heating', 'damage-energy']
tallies.append(tally_fw)

tally_tbr = openmc.Tally(name='breeding_blanket_tbr')
tally_tbr.filters = [openmc.MaterialFilter([mat_bb])]
tally_tbr.scores = ['(n,t)']
tallies.append(tally_tbr)

# Enhancement 2: 3D Cylindrical Mesh Tally for Spatial Heating/Damage mapping
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

print("=== 5. Executing High-Fidelity Simulation ===")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"=== Simulation Completed in {(time.time() - start_time):.2f} seconds ===")

print("\n=== 6. Setting up Depletion & Burnup Module ===")
# Enhancement 3: Configuring a depletion chain
chain_path = '/root/chain_endfb80.xml' 
if os.path.exists(chain_path):
    print(f"Initializing depletion operator with chain: {chain_path}")
    operator = openmc.deplete.CoupledOperator(geometry, settings, chain_file=chain_path)
    print("Depletion operator successfully initialized and ready for time-step integration.")
else:
    print(f"Depletion chain file not found at {chain_path}. Skipping active depletion integration step.")

print("\n=======================================================")
print("     ADVANCED REACTOR ANALYSIS REPORT COMPLETED        ")
print("=======================================================")
