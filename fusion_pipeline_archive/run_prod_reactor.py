import openmc
import time

print("=== 1. Initializing Production Run: Materials & Cross Sections ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# First Wall Material
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

print("=== 3. Configuring High-Fidelity Settings & Source ===")
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 50          
settings.particles = 100000    # 5 Million total particle histories

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

vol_calc = openmc.VolumeCalculation(
    domains=[mat_fw, mat_bb, mat_div],
    samples=500_000,
    lower_left=(-200.0, -200.0, -150.0),
    upper_right=(200.0, 200.0, 150.0)
)
settings.volume_calculations = [vol_calc]
settings.export_to_xml()

print("=== 4. Setting up High-Resolution Tallies ===")
tallies = openmc.Tallies()

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

mesh = openmc.RegularMesh()
mesh.lower_left = (-150.0, -150.0, -120.0)
mesh.upper_right = (150.0, 150.0, 120.0)
mesh.dimension = (50, 50, 50)

mesh_filter = openmc.MeshFilter(mesh)
tally_mesh = openmc.Tally(name='spatial_heating_mesh')
tally_mesh.filters = [mesh_filter]
tally_mesh.scores = ['heating']
tallies.append(tally_mesh)

tallies.export_to_xml()

print("=== 5. Executing Production Simulation (5M Histories) ===")
start_time = time.time()
openmc.run(openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')
print(f"=== Simulation Completed in {(time.time() - start_time):.2f} seconds ===")

print("\n=== 6. Parsing Production Results & Exporting VTK ===")
sp = openmc.StatePoint('statepoint.50.h5')

fw_tally = sp.get_tally(name='first_wall_heating')
fw_mean = fw_tally.mean[0][0][0]
fw_std = fw_tally.std_dev[0][0][0]

tbr_tally = sp.get_tally(name='breeding_blanket_tbr')
tbr_mean = tbr_tally.mean[0][0][0]
tbr_std = tbr_tally.std_dev[0][0][0]

div_tally = sp.get_tally(name='divertor_heating')
div_mean = div_tally.mean[0][0][0]
div_std = div_tally.std_dev[0][0][0]

print("\n========================================")
print("     HIGH-FIDELITY PRODUCTION RESULTS   ")
print("========================================")
print(f"First Wall Heating : {fw_mean:.5e} +/- {fw_std:.5e} eV/src")
print(f"Tritium Breeding   : {tbr_mean:.5e} +/- {tbr_std:.5e} trit/src")
print(f"Divertor Heating   : {div_mean:.5e} +/- {div_std:.5e} eV/src")
print("========================================")

mesh_tally = sp.get_tally(name='spatial_heating_mesh')
mesh = mesh_tally.find_filter(openmc.MeshFilter).mesh
heating_data = mesh_tally.mean.ravel()
mesh.write_data_to_vtk('prod_spatial_heating.vtk', datasets={'heating': heating_data})
print("\n[+] High-fidelity 3D Mesh Tally exported to 'prod_spatial_heating.vtk'!")
