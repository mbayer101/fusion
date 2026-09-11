import openmc
import numpy as np
import os

print("Starting OpenMC-to-OpenFOAM heating data mapper...")

statepoint_files = [f for f in os.listdir('.') if f.startswith('statepoint.') and f.endswith('.h5')]
if not statepoint_files:
    print("No statepoint file found. Run OpenMC simulation first to generate tally data.")
    exit(1)

latest_sp = max(statepoint_files, key=os.path.getmtime)
print(f"Reading latest statepoint: {latest_sp}")

with openmc.StatePoint(latest_sp) as sp:
    tally = sp.get_tally(name='volumetric_heating')
    heating_data = tally.get_values(scores=['heating'])
    
    # Unit conversion from eV/source-particle to W/cm^3 (assuming 1 MW fusion power scaling)
    fusion_power_watts = 1e6 
    joules_per_ev = 1.60218e-19
    heating_watts_per_cm3 = heating_data * joules_per_ev * (fusion_power_watts / 14.1e6)
    
    # Reshape to match the 50x50x50 grid dimensions
    grid_shape = (50, 50, 50)
    if heating_watts_per_cm3.size == np.prod(grid_shape):
        heating_3d = heating_watts_per_cm3.reshape(grid_shape)
    else:
        heating_3d = heating_watts_per_cm3.squeeze()
        
    print(f"Reshaped heating data grid shape: {heating_3d.shape}")
    
    # Ensure OpenFOAM constant directory exists and export
    os.makedirs('openfoam/constant', exist_ok=True)
    output_path = 'openfoam/constant/heatSource'
    np.savetxt(output_path, heating_3d.flatten(), header="// OpenFOAM 50x50x50 volumetric heat source (W/cm^3)", comments="")
    print(f"Exported heating source term to {output_path}")

