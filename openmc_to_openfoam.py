import openmc
import numpy as np
import os

print("=== STARTING OPENMC TO OPENFOAM DATA BRIDGE ===")

# 1. Load Statepoint & Tally
sp = openmc.StatePoint('statepoint.50.h5')
# Assuming our production mesh tally from previous runs
tally = sp.get_tally(name='reactor_production_tally')
heating_data = tally.get_slice(scores=['heating'])

# Extract mean heating values (eV / source particle / cm³)
mean_heating_eV_cm3 = heating_data.mean

# 2. Convert to Macroscopic Power Density (W/m³)
# Target fusion power: 500 MW = 500e6 Watts
# Each D-T fusion reaction releases ~17.6 MeV = 2.82e-12 Joules
# Source normalization factor (neutrons/second) based on power
total_fusion_power_watts = 500e6 
joules_per_MeV = 1.602176634e-13
MeV_per_DT_neutron = 14.1 + 3.5 # 14.1 MeV neutron + 3.5 MeV alpha
joules_per_neutron = MeV_per_DT_neutron * joules_per_MeV
total_source_rate = total_fusion_power_watts / joules_per_neutron # neutrons/sec

# Conversion factor: eV to Joules (1 eV = 1.60218e-19 J)
eV_to_J = 1.60218e-19
# Conversion factor: cm³ to m³ (1 cm³ = 1e-6 m³)
cm3_to_m3 = 1e6

# Power density q_dot (W/m³) = (eV / particle * cm³) * (particles / sec) * (J / eV) * (cm³ / m³)
power_density_W_m3 = mean_heating_eV_cm3 * total_source_rate * eV_to_J * cm3_to_m3

print(f"Total Source Rate: {total_source_rate:.3e} n/s")
print(f"Max Power Density: {np.max(power_density_W_m3):.3e} W/m³")

# 3. Export as an OpenFOAM-compatible field or lookup table
# For direct integration, we save the grid mapping to a CSV/dat file that OpenFOAM's 
# fvOptions or a custom boundary condition can read.
np.savetxt('openfoam_heat_source.dat', power_density_W_m3.flatten(), header='Volumetric Heat Source (W/m3)', comments='# ')
print("Successfully exported 'openfoam_heat_source.dat' for OpenFOAM ingestion.")
print("================================================================")

