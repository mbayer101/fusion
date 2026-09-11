import openmc
import numpy as np
import os

print("Starting OpenMC-to-OpenFOAM heating data mapper...")

statepoint_files = [f for f in os.listdir('.') if f.startswith('statepoint.') and f.endswith('.h5')]

if not statepoint_files:
    print("No statepoint file found. Run OpenMC simulation first to generate tally data.")
else:
    # Sort by file modification time (newest first)
    latest_sp = max(statepoint_files, key=os.path.getmtime)
    print(f"Reading latest statepoint: {latest_sp}")
    
    with openmc.StatePoint(latest_sp) as sp:
        tally = sp.get_tally(name='volumetric_heating')
        heating_data = tally.get_values(scores=['heating'])
        
        print(f"Extracted heating mesh tally shape: {heating_data.shape}")
        print("Heating data extraction successful! Ready for OpenFOAM fvOptions export.")

