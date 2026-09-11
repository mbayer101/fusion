import openmc
import numpy as np
import os

print("Starting OpenMC-to-OpenFOAM heating data mapper...")

statepoint_files = [f for f in os.listdir('.') if f.startswith('statepoint.') and f.endswith('.h5')]
latest_sp = max(statepoint_files, key=os.path.getmtime)
print(f"Reading latest statepoint: {latest_sp}")

with openmc.StatePoint(latest_sp) as sp:
    tally = sp.get_tally(name='volumetric_heating')
    heating_data = tally.get_values(scores=['heating'])
    
    # Convert eV/source-particle to W/m^3 (assuming a fusion power scaling factor)
    # 1 eV = 1.60218e-19 Joules. 
    # Example scaling for 1 MW fusion power (approx 3.5e16 neutrons/sec for 14.1 MeV)
    fusion_power_watts = 1e6 
    joules_per_ev = 1.60218e-19
    
    # Simple volumetric conversion placeholder
    heating_watts_per_cm3 = heating_data * joules_per_ev * (fusion_power_watts / 14.1e6)
    
    print(f"Processed heating data shape: {heating_watts_per_cm3.shape}")
    
    # Ensure openfoam output directory exists
    os.makedirs('openfoam/constant', exist_ok=True)
    
    # Export placeholder source term file
    output_path = 'openfoam/constant/heatSource'
    np.savetxt(output_path, heating_watts_per_cm3.flatten(), header="// OpenFOAM volumetric heat source (W/cm^3)", comments="")
    print(f"Exported heating source term to {output_path}")

