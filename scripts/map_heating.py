import openmc
import numpy as np
import os

print("=== STARTING RADIAL OPENMC-TO-OPENFOAM HEATING MAPPER (6.0 CM BE MULTIPLIER) ===")

sp = openmc.StatePoint('statepoint.25.h5')
heat_tally = sp.get_tally(name='volumetric_heating')
tbr_tally = sp.get_tally(name='tritium_breeding')

r_bins = np.array([30.0, 32.0, 38.0, 46.0, 56.0, 71.0, 81.0, 91.0, 101.0, 126.0])
shell_volumes_cm3 = (4.0 / 3.0) * np.pi * (r_bins[1:]**3 - r_bins[:-1]**3)

heating_eV_per_n = heat_tally.mean.flatten()
heating_eV_cm3_per_n = heating_eV_per_n / shell_volumes_cm3

fusion_power_W = 500e6
joules_per_MeV = 1.602176634e-13
eV_to_J = 1.602176634e-19
source_rate_n_s = fusion_power_W / (17.6 * joules_per_MeV)

shell_power_density_W_m3 = heating_eV_cm3_per_n * source_rate_n_s * eV_to_J * 1e6

mult_M = heating_eV_per_n.sum() / 14.1e6
total_th_MW = ((heating_eV_per_n.sum() * eV_to_J * source_rate_n_s) / 1e6) + 100.0  # +100 MW alpha heating

print(f"TBR: {tbr_tally.mean.sum():.4f} +/- {tbr_tally.std_dev.sum():.4f}")
print(f"Blanket Energy Multiplication M: {mult_M:.2f}x ({heating_eV_per_n.sum()/1e6:.2f} MeV/n)")
print(f"Total Plant Thermal Power (Neutron + Alpha): {total_th_MW:.2f} MWth")

coords = np.linspace(-48.0, 48.0, 25)
X, Y, Z = np.meshgrid(coords, coords, coords, indexing='ij')
R = np.sqrt(X**2 + Y**2 + Z**2)

grid_W_m3 = np.zeros_like(R)
for i in range(len(shell_power_density_W_m3)):
    mask = (R >= r_bins[i]) & (R < r_bins[i+1])
    grid_W_m3[mask] = shell_power_density_W_m3[i]

os.makedirs('openfoam/constant', exist_ok=True)
np.savetxt('openfoam/constant/heatSource', grid_W_m3.flatten(), header='Radial Volumetric Heat Source with 6cm Be Multiplier (W/m3)', comments='# ')
print(f"Peak Mapped Power Density: {np.max(grid_W_m3):.3e} W/m^3")
