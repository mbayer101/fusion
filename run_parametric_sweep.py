import openmc
import numpy as np
import os

print("=== STARTING PARAMETRIC DESIGN SWEEP ===")
openmc.config['cross_sections'] = '/root/cross_sections.xml'

enrichment_sweep = [60.0, 75.0, 90.0]
results_summary = []

for idx, enrichment in enumerate(enrichment_sweep):
    print(f"\n--- Running Iteration {idx+1}: Li-6 Enrichment = {enrichment}% ---")
    
    # Clean up previous state files if they exist
    for filename in ['summary.h5', 'statepoint.10.h5']:
        if os.path.exists(filename):
            os.remove(filename)

    # 1. Setup All Core Materials
    mat_fw = openmc.Material(name='First_Wall', material_id=1)
    mat_fw.add_element('Fe', 0.89, percent_type='ao')
    mat_fw.add_element('Cr', 0.10, percent_type='ao')
    mat_fw.add_element('W', 0.01, percent_type='ao')
    mat_fw.set_density('g/cm3', 7.8)

    mat_bb = openmc.Material(name='Breeding_Blanket', material_id=2)
    mat_bb.add_element('Li', 0.5, percent_type='ao', enrichment=enrichment, enrichment_target='Li6')
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

    # 2. Geometry & Settings
    bound_dag_univ = openmc.DAGMCUniverse('full_reactor.h5m').bounded_universe(padding_distance=30.0)
    geometry = openmc.Geometry(root=bound_dag_univ)
    geometry.export_to_xml()

    settings = openmc.Settings()
    settings.run_mode = 'fixed source'
    settings.batches = 10
    settings.particles = 10000
    # Disable summary output generation to prevent HDF5 lock conflicts
    settings.output = {'summary': False}

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

    # 3. Tally setup
    tallies = openmc.Tallies()
    bb_filter = openmc.MaterialFilter([mat_bb])
    bb_tally = openmc.Tally(name=f'sweep_bb_tally_{idx}')
    bb_tally.filters = [bb_filter]
    bb_tally.scores = ['heating', 'flux']
    tallies.append(bb_tally)
    tallies.export_to_xml()

    # 4. Execute transport run
    openmc.run(output=False, openmc_exec='/root/miniforge3/envs/openmc_dagmc_env/bin/openmc')

    # 5. Extract and store results
    sp = openmc.StatePoint('statepoint.10.h5')
    tally = sp.get_tally(name=f'sweep_bb_tally_{idx}')
    mean_heating = tally.get_slice(scores=['heating']).mean.sum()
    
    results_summary.append({
        'enrichment': enrichment,
        'heating_total': mean_heating
    })

print("\n=== PARAMETRIC SWEEP RESULTS SUMMARY ===")
print(f"{'Li-6 Enrichment (%)':<20} | {'Total Blanket Heating (eV)':<30}")
print("-" * 55)
for res in results_summary:
    print(f"{res['enrichment']:<20} | {res['heating_total']:<30.4e}")
print("========================================")
