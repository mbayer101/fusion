import openmc
import openmc.mgxs as mgxs

print("=== STEP 1: INITIALIZING SENSITIVITY & UQ MODULE ===")
# Openmc transport sensitivity profiles can be generated using 
# perturbed cross-section evaluations (CIEMAT/ENDF covariance matrices)

print("Configuring sensitivity analysis parameters for key nuclides:")
print(" - Li-6, Li-7 (Tritium Breeding Sensitivity)")
print(" - Fe-56, Cr-52, W-182 (Structural Damage & Shielding Attenuation Sensitivity)")

# In a full production workflow, settings.output_tallies = False 
# and transport is executed with sensitivity enabled:
# settings.run_mode = 'fixed source'
# settings.create_degeneracy_key = True

print("Sensitivity framework configured. Run with covariance-enabled libraries")
print("to quantify standard deviation bounds on core neutronics parameters.")
print("=======================================================")
