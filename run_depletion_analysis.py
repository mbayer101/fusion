import openmc
import openmc.deplete
import os
import numpy as np

print("=== STEP 1: INITIALIZING ENVIRONMENT & MATERIALS ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

mat_fw = openmc.Material(name='First_Wall', material_id=1)
mat_fw.add_element('Fe', 0.89, percent_type='ao')
mat_fw.add_element('Cr', 0.10, percent_type='ao')
mat_fw.add_element('W', 0.01, percent_type='ao')
mat_fw.set_density('g/cm3', 7.8)
mat_fw.depletable = True
mat_fw.volume = 50000.0  # cm^3

mat_bb = openmc.Material(name='Breeding_Blanket', material_id=2)
mat_bb.add_element('Li', 0.5, percent_type='ao', enrichment=90.0, enrichment_target='Li6')
mat_bb.add_element('Pb', 0.5, percent_type='ao')
mat_bb.set_density('g/cm3', 9.5)
mat_bb.depletable = True
mat_bb.volume = 250000.0  # cm^3

mat_div = openmc.Material(name='Divertor', material_id=3)
mat_div.add_element('W', 1.0, percent_type='ao')
mat_div.set_density('g/cm3', 19.3)
mat_div.depletable = True
mat_div.volume = 30000.0  # cm^3

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
settings.batches = 40
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
settings.export_to_xml()

print("=== STEP 4: INITIALIZING FIXED-SOURCE COUPLED DEPLETION OPERATOR ===")
chain_path = '/root/chain_endfb80.xml'

if not os.path.exists(chain_path):
    print(f"Error: Inventory chain file not found at {chain_path}.")
else:
    # For fixed-source (fusion) calculations, we specify source rates instead of total thermal power
    source_rates = [1.0e19, 1.0e19, 1.0e19] # Source neutrons/sec for each timestep
    time_steps = [30.0, 30.0, 30.0] # Days
    
    model = openmc.Model(geometry=geometry, materials=materials, settings=settings)
    
    # Use 'source-rate' normalization mode since this is a fixed-source fusion problem
    operator = openmc.deplete.CoupledOperator(
        model=model,
        chain_file=chain_path,
        normalization_mode='source-rate'
    )
    
    integrator = openmc.deplete.CECMIntegrator(operator, time_steps, source_rates=source_rates)
    
    print("Depletion operator and CECM integrator initialized successfully.")
    print("Starting time-step transmutation loop...")
    
    integrator.integrate()
    
    print("\n=======================================================")
    print("         DEPLETION & ACTIVATION RUN COMPLETE           ")
    print("=======================================================")
