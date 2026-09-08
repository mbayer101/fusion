import os
import math
import openmc
import pandas as pd

# --- 0. CONFIGURE CROSS SECTIONS ---
os.environ['OPENMC_CROSS_SECTIONS'] = '/root/cross_sections.xml'
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Constants for power conversion (500 MW reactor scale)
FUSION_POWER_MW = 500.0
TOTAL_ENERGY_PER_DT_EV = 17.6e6
fusion_power_ev_sec = FUSION_POWER_MW * 1e6 / 1.6022e-19
source_rate = fusion_power_ev_sec / TOTAL_ENERGY_PER_DT_EV

# List of enrichments to test
enrichment_levels = [7.5, 30.0, 50.0, 70.0, 90.0]
results_summary = []

print("Starting Li-6 Enrichment Parameter Sweep...")

for enr in enrichment_levels:
    print(f"\n--- Running simulation with Li-6 Enrichment: {enr}% ---")

    # --- 1. DEFINE MATERIALS ---
    dt_fuel = openmc.Material(name='DT-Plasma')
    dt_fuel.add_nuclide('H2', 0.5, 'ao')
    dt_fuel.add_nuclide('H3', 0.5, 'ao')
    dt_fuel.set_density('g/cm3', 1.0e-4)

    tungsten = openmc.Material(name='Tungsten-Wall')
    tungsten.add_element('W', 1.0, 'ao')
    tungsten.set_density('g/cm3', 19.3)

    lead_multiplier = openmc.Material(name='Lead-Multiplier')
    lead_multiplier.add_element('Pb', 1.0, 'ao')
    lead_multiplier.set_density('g/cm3', 11.34)

    pbli = openmc.Material(name='PbLi-Blanket')
    pbli.add_element('Pb', 0.83, 'ao')
    pbli.add_element('Li', 0.17, 'ao', enrichment=enr, enrichment_target='Li6', enrichment_type='ao')
    pbli.set_density('g/cm3', 9.5)

    rafm = openmc.Material(name='RAFM-Structure')
    rafm.add_element('Fe', 89.0, 'wo')
    rafm.add_element('Cr', 9.0, 'wo')
    rafm.add_element('W', 1.0, 'wo')
    rafm.add_element('V', 0.25, 'wo')
    rafm.add_element('Ta', 0.07, 'wo')
    rafm.set_density('g/cm3', 7.8)

    materials = openmc.Materials([dt_fuel, tungsten, lead_multiplier, pbli, rafm])
    materials.export_to_xml()

    # --- 2. DEFINE REALISTIC GEOMETRY ---
    r_plasma = 200.0
    r_wall = r_plasma + 2.0
    r_multiplier = r_wall + 5.0
    r_blanket = r_multiplier + 45.0
    r_struct = r_blanket + 5.0
    r_outer = r_struct + 100.0

    c_plasma = openmc.Cylinder(r=r_plasma)
    c_wall = openmc.Cylinder(r=r_wall)
    c_multiplier = openmc.Cylinder(r=r_multiplier)
    c_blanket = openmc.Cylinder(r=r_blanket)
    c_struct = openmc.Cylinder(r=r_struct)
    c_outer = openmc.Cylinder(r=r_outer, boundary_type='vacuum')

    region_plasma = -c_plasma
    region_wall = +c_plasma & -c_wall
    region_multiplier = +c_wall & -c_multiplier
    region_blanket = +c_multiplier & -c_blanket
    region_struct = +c_blanket & -c_struct
    region_outer = +c_struct & -c_outer

    cell_plasma = openmc.Cell(fill=dt_fuel, region=region_plasma)
    cell_wall = openmc.Cell(fill=tungsten, region=region_wall)
    cell_multiplier = openmc.Cell(fill=lead_multiplier, region=region_multiplier)
    cell_blanket = openmc.Cell(fill=pbli, region=region_blanket)
    cell_struct = openmc.Cell(fill=rafm, region=region_struct)
    cell_outer = openmc.Cell(region=region_outer)

    geometry = openmc.Geometry([cell_plasma, cell_wall, cell_multiplier, cell_blanket, cell_struct, cell_outer])
    geometry.export_to_xml()

    # --- 3. SETTINGS & SOURCE ---
    settings = openmc.Settings()
    settings.batches = 40
    settings.inactive = 10
    settings.particles = 25000
    settings.run_mode = 'fixed source'

    source = openmc.IndependentSource()
    source.space = openmc.stats.CylindricalIndependent(
        r=openmc.stats.Uniform(0.0, 190.0),
        phi=openmc.stats.Uniform(0.0, 6.28318),
        z=openmc.stats.Uniform(-300.0, 300.0)
    )
    source.angle = openmc.stats.Isotropic()
    source.energy = openmc.stats.Discrete([14.1e6], [1.0])
    settings.source = source
    settings.export_to_xml()

    # --- 4. TALLIES ---
    tallies = openmc.Tallies()

    tally_tbr = openmc.Tally(name='Tritium-Br-Tally')
    tally_tbr.filters = [openmc.CellFilter([cell_blanket])]
    tally_tbr.scores = ['205']
    tallies.append(tally_tbr)

    tallies.export_to_xml()

    # --- 5. RUN ---
    sp_filename = 'statepoint.40.h5'
    if os.path.exists(sp_filename):
        os.remove(sp_filename)

    openmc.run(output=False)

    # --- 6. EXTRACT ---
    with openmc.StatePoint(sp_filename) as sp:
        t_tbr = sp.get_tally(name='Tritium-Br-Tally')
        df_tbr = t_tbr.get_pandas_dataframe()
        tbr_mean = df_tbr['mean'].values[0]
        tbr_std = df_tbr['std. dev.'].values[0]
        
        results_summary.append({
            'Enrichment (%)': enr,
            'TBR': tbr_mean,
            'Std Dev': tbr_std
        })

# --- FINAL SUMMARY TABLE ---
print('\n==================================================')
print('         LI-6 ENRICHMENT SWEEP SUMMARY            ')
print('==================================================')
print(f"{'Enrichment (%)':<18} {'TBR':<12} {'Status'}")
print('--------------------------------------------------')

for res in results_summary:
    status = "Self-Sustaining" if res['TBR'] >= 1.0 else "Sub-critical"
    print(f"{res['Enrichment (%)']:<18.1f} {res['TBR']:<12.4f} {status}")

print('==================================================')

