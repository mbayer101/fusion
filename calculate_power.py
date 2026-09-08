import openmc

# --- CONSTANTS ---
FUSION_POWER_MW = 500.0  # MW
TOTAL_ENERGY_PER_DT_EV = 17.6e6  # 17.6 MeV per D-T fusion in eV

# Calculate source neutron emission rate (neutrons/second)
# Fusion Power (eV/s) / Energy per fusion (eV)
fusion_power_ev_per_sec = FUSION_POWER_MW * 1e6 / 1.6022e-19
source_rate = fusion_power_ev_per_sec / TOTAL_ENERGY_PER_DT_EV

print(f"Target Fusion Power: {FUSION_POWER_MW} MW")
print(f"Required Source Rate: {source_rate:.4e} neutrons/second\n")

# --- READ STATEPOINT & EXTRACT HEATING ---
with openmc.StatePoint('statepoint.100.h5') as sp:
    tally = sp.get_tally(name='Component-Heating-Tally')
    df = tally.get_pandas_dataframe()

    print("--- Component Thermal Power Deposition ---")
    for index, row in df.iterrows():
        cell_id = row['cell']
        heating_per_source = row['mean']  # eV/source neutron
        
        # Calculate total power in Watts
        power_watts = heating_per_source * 1.6022e-19 * source_rate
        power_mw = power_watts / 1e6
        
        print(f"Cell {cell_id} ({row['score']}): {power_mw:.2f} MW")

