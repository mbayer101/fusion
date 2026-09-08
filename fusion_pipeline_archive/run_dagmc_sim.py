import openmc

print("=== Setting up DAGMC OpenMC Simulation ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# 1. Define Materials
mat_fw = openmc.Material(name='First_Wall')
mat_fw.add_element('Fe', 0.89, percent_type='ao')
mat_fw.add_element('Cr', 0.10, percent_type='ao')
mat_fw.add_element('W', 0.01, percent_type='ao')
mat_fw.set_density('g/cm3', 7.8)

materials = openmc.Materials([mat_fw])
materials.cross_sections = '/root/cross_sections.xml'
materials.export_to_xml()

# 2. Load Geometry via DAGMC with an automatic vacuum bounding box
print("Loading and bounding DAGMC universe from fusion_reactor.h5m...")
bound_dag_univ = openmc.DAGMCUniverse('fusion_reactor.h5m').bounded_universe(padding_distance=20.0)
geometry = openmc.Geometry(root=bound_dag_univ)
geometry.export_to_xml()

# 3. Settings (Fixed 14.1 MeV Neutron Source)
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 20
settings.particles = 5000

source = openmc.IndependentSource()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(50.0, 100.0),
    phi=openmc.stats.Uniform(0.0, 2.0 * 3.1415926535),
    z=openmc.stats.Uniform(-40.0, 40.0),
    origin=(0.0, 0.0, 0.0)
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])

settings.source = source
settings.export_to_xml()

# 4. Tallies
tallies = openmc.Tallies()
material_filter = openmc.MaterialFilter([mat_fw])
tally = openmc.Tally(name='dagmc_first_wall_performance')
tally.filters = [material_filter]
tally.scores = ['heating']
tallies.append(tally)
tallies.export_to_xml()

print("=== Starting DAGMC OpenMC Simulation ===")
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')

print("\n=== Parsing Results (Direct NumPy Extraction) ===")
sp = openmc.StatePoint('statepoint.20.h5')
tally = sp.get_tally(name='dagmc_first_wall_performance')

# Extract mean and standard deviation directly from tally results array shape (bins, scores, statistics)
mean_val = tally.mean[0][0][0]
std_dev = tally.std_dev[0][0][0]

print("\n========================================")
print("     DAGMC CAD SIMULATION RESULTS       ")
print("========================================")
print(f"Score : Heating")
print(f"Mean  : {mean_val:.5e} eV/source particle")
print(f"StDev : {std_dev:.5e}")
print("========================================")
