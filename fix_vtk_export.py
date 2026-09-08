import openmc
import numpy as np

print("=== EXTRACTING MESH TALLY RESULTS FOR VISUALIZATION ===")
sp = openmc.StatePoint('statepoint.20.h5')
tally = sp.get_tally(name='spatial_heating_tally')

# Extract mean values and standard deviations for heating and flux
# Tally shape corresponds to mesh bins x scores
heating_data = tally.get_slice(scores=['heating']).mean
flux_data = tally.get_slice(scores=['flux']).mean

print(f"Successfully extracted spatial tally arrays.")
print(f" - Heating tally shape: {heating_data.shape}")
print(f" - Flux tally shape:    {flux_data.shape}")
print(f" - Max Heating Bin:     {np.max(heating_data):.4e} eV/source particle")
print(f" - Max Flux Bin:        {np.max(flux_data):.4e} n/cm²-s")

print("\nWeight-window optimized transport and spatial data extraction complete!")
print("=======================================================")
