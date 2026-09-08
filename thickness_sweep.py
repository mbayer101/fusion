import os
import openmc
import pandas as pd

# --- 0. CONFIGURE CROSS SECTIONS ---
os.environ['OPENMC_CROSS_SECTIONS'] = '/root/cross_sections.xml'
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Define blanket thicknesses to test (in cm)
blanket_thicknesses = [30.0, 40.0, 50.0]
results = []

# Constants for power conversion (500 MW reactor scale)
FUSION_POWER_MW = 500.0
TOTAL_ENERGY_PER_DT_EV = 17.6e6
fusion_power_ev_sec = FUSION_POWER_MW * 1e6 / 1.6022e-19
source_rate = fusion_power_ev_sec / TOTAL_ENERGY_PER_DT_EV

print("Starting Blanket Thickness Parameter Sweep...")

for thickness in blanket_thicknesses:
    print(f"\n--- Running simulation with Blanket Thickness: {thickness} cm ---")

    # --- 1. DEFINE MATERIALS (Using 90% Li-6 Enriched PbLi) ---
    dt_fuel = openmc.Material(name='DT-Plasma')
    dt_fuel.add_nuclide('H2', 0.5, 'ao')
    dt_fuel.add_nuclide('H3', 0.5, 'ao')
    dt_fuel.set_density('g/cm3', 1.0e-4)

    tungsten = openmc.Material(name='Tungsten-Wall')
    tungsten.add_element('W', 1.0, 'ao')
    tungsten.set_density('g/cm3', 19.3)

    pbli = openmc.Material(name='PbLi-Blanket')
    pbli.add_element('Pb', 0.83, 'ao')
    pbli.add_element('Li', 0.17, 'ao', enrichment=90.0, enrichment_target='Li6', enrichment_type='ao')
    pbli.set_density('g/cm3', 9.5)

    rafm = openmc.Material(name='RAFM-Structure')
    rafm.add_element('Fe', 89.0, 'wo')
    rafm.add_element('Cr', 9.0, 'wo')
    rafm.add_element('W', 1.0, 'wo')
    rafm.add_element('V', 0.25, 'wo')
    rafm.add_element('Ta', 0.07, 'wo')
    rafm.set_density('g/cm3', 7.8)

    materials = openmc.Materials([dt_fuel, tungsten, pbli, rafm])
    materials.export_to_xml()

    # --- 2. DEFINE GEOMETRY WITH DYNAMIC RADIUS ---
    r_inner_wall = 0.55
    r_outer_blanket = r_inner_wall + thickness
    r_struct = r_outer_blanket + 2.0      # 2 cm structure thickness
    r_outer = r_struct + 2.5              # Vacuum boundary offset

    c_plasma = openmc.Cylinder(r=0.5)
    c_wall = openmc.Cylinder(r=r_inner_wall)
    c_blanket = openmc.Cylinder(r=r_outer_blanket)
    c_struct = openmc.Cylinder(r=r_struct)
    c_outer = openmc.Cylinder(r=r_outer, boundary_type='vacuum')

    region_plasma = -c_plasma
    region_wall = +c_plasma & -c_wall
    region_blanket = +c_wall & -c_blanket
    region_struct = +c_blanket & -c_struct
    region_outer = +c_struct & -c_outer

    cell_plasma = openmc.Cell(fill=dt_fuel, region=region_plasma)
    cell_wall = openmc.Cell(fill=tungsten, region=region_wall)
    cell_blanket = openmc.Cell(fill=pbli, region=region_blanket)
    cell_struct = openmc.Cell(fill=rafm, region=region_struct)
    cell_outer = openmc.Cell(region=region_outer)

    geometry = openmc.Geometry([cell_plasma, cell_wall, cell_blanket, cell_struct, cell_outer])
    geometry.export_to_xml()

    # --- 3. SETTINGS & NEUTRON SOURCE ---
    settings = openmc.Settings()
    settings.batches = 50
    settings.inactive = 10
    settings.particles = 25000
    settings.run_mode = 'fixed source'

    source = openmc.IndependentSource()
    source.space = openmc.stats.CylindricalIndependent(
        r=openmc.stats.Uniform(0.0, 0.45),
        phi=openmc.stats.Uniform(0.0, 6.28318),
        z=openmc.stats.Uniform(-1.0, 1.0)
    )
    source.angle = openmc.stats.Isotropic()
    source.energy = openmc.stats.Discrete([14.1e6], [1.0])
    settings.source = source
    settings.export_to_xml()

    # --- 4. TALLIES ---
    tallies = openmc.Tallies()

    # TBR Tally
    tally_tbr = openmc.Tally(name='Tritium-Br-Tally')
    tally_tbr.filters = [openmc.CellFilter([cell_blanket])]
    tally_tbr.scores = ['205']
    tallies.append(tally_tbr)

    # Heating Tally
    heating_filter = openmc.CellFilter([cell_wall, cell_blanket])
    tally_heating = openmc.Tally(name='Component-Heating-Tally')
    tally_heating.filters = [heating_filter]
    tally_heating.scores = ['heating']
    tallies.append(tally_heating)

    tallies.export_to_xml()

    # --- 5. RUN SIMULATION ---
    sp_filename = 'statepoint.50.h5'
    if os.path.exists(sp_filename):
        os.remove(sp_filename)

    openmc.run(output=False)

    # --- 6. EXTRACT RESULTS ---
    with openmc.StatePoint(sp_filename) as sp:
        # Get TBR
        t_tbr = sp.get_tally(name='Tritium-Br-Tally')
        df_tbr = t_tbr.get_pandas_dataframe()
        tbr_mean = df_tbr['mean'].values[0]

        # Get Blanket Heating Power
        t_heat = sp.get_tally(name='Component-Heating-Tally')
        df_heat = t_heat.get_pandas_dataframe()
        blanket_row = df_heat[df_heat['cell'] == cell_blanket.id]
        heating_per_source = blanket_row['mean'].values[0]
        
        blanket_power_mw = (heating_per_source * 1.6022e-19 * source_rate) / 1e6

    results.append({
        'Thickness (cm)': thickness,
        'TBR': tbr_mean,
        'Blanket Power (MW)': blanket_power_mw
    })

# --- SUMMARY REPORT ---
summary_df = pd.DataFrame(results)
print('\n==================================================')
print('        BLANKET THICKNESS SWEEP SUMMARY           ')
print('==================================================')
print(summary_df.to_string(index=False))
print('==================================================')

