import openmc
import numpy as np
import os

print("Starting OpenMC-to-OpenFOAM heating data mapper...")

# Find the latest statepoint file in the current working directory or openmc dir
statepoint_files = [f for f in os.listdir('.') if f.startswith('statepoint.') and f.endswith('.h5')]

if not statepoint_files:
    print("No statepoint file found. Run OpenMC simulation first to generate tally data.")
else:
    latest_sp = sorted(statepoint_files)[-1]
    print(f"Reading statepoint: {latest_sp}")
    
    with openmc.StatePoint(latest_sp) as sp:
        tally = sp.get_tally(name='volumetric_heating')
        # Extract mean values for the heating score
        heating_data = tally.get_values(scores=['heating'])
        
        print(f"Extracted heating mesh tally shape: {heating_data.shape}")
        # TODO: Interpolate / map grid onto OpenFOAM finite-volume mesh coordinates
        print("Ready for OpenFOAM fvOptions / source-term export.")

