import openmc
import numpy as np
import os

print("=== STARTING RADIAL OPENMC-TO-OPENFOAM HEATING MAPPER ===")

# 1. Load latest statepoint
sp = openmc.StatePoint('statepoint.25.h5')
heat_tally = sp.get_tally(name='volumetric_heating')
tbr_tally = sp.get_tally(name='tritium_breeding')

# Radial shell boundaries (cm) matching openmc/build_model.py
r_bins = np.array([30.0, 32.0, 40.0, 50.0, 65.0, 75.0, 85.0, 95.0, 120.0])
shell_volumes_cm3 = (4.0 / 3.0) * np.pi * (r_bins[1:]**3 - r_bins[:-1]**3)

# Tally mean is in eV / source particle per spherical shell
heating_eV_per_n = heat_tally.mean.flatten()
heating_eV_cm3_per_n = heating_eV_per_n / shell_volumes_cm3

# 2. Normalize to 500 MW Fusion Power
fusion_power_W = 500e6
joules_per_MeV = 1.602176634e-13
eV_to_J = 1.602176634e-19
source_rate_n_s = fusion_power_W / (17.6 * joules_per_MeV)

# Convert to W/m^3 per radial shell
shell_power_density_W_m3 = heating_eV_cm3_per_n * source_rate_n_s * eV_to_J * 1e6

print(f"TBR: {tbr_tally.mean.sum():.4f} +/- {tbr_tally.std_dev.sum():.4f}")
print(f"Total Thermal Power (with M={heating_eV_per_n.sum()/14.1e6:.2f}x): {(heating_eV_per_n.sum() * eV_to_J * source_rate_n_s)/1e6:.2f} MW")

# 3. Map radial power densities onto a 25x25x25 grid (-50 to +50 cm) matching OpenFOAM blockMesh
coords = np.linspace(-48.0, 48.0, 25)
X, Y, Z = np.meshgrid(coords, coords, coords, indexing='ij')
R = np.sqrt(X**2 + Y**2 + Z**2)

grid_W_m3 = np.zeros_like(R)
for i in range(len(shell_power_density_W_m3)):
    mask = (R >= r_bins[i]) & (R < r_bins[i+1])
    grid_W_m3[mask] = shell_power_density_W_m3[i]

os.makedirs('openfoam/constant', exist_ok=True)
np.savetxt('openfoam/constant/heatSource', grid_W_m3.flatten(), header='Radial Volumetric Heat Source (W/m3)', comments='# ')
print(f"Peak Mapped Power Density: {np.max(grid_W_m3):.3e} W/m^3")
print("Exported mapped radial heating source to openfoam/constant/heatSource")
