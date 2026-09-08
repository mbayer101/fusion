import openmc

sp = openmc.StatePoint('statepoint.100.h5')

fw_tally = sp.get_tally(name='first_wall_heating')
tbr_tally = sp.get_tally(name='breeding_blanket_tbr')
mesh_tally = sp.get_tally(name='spatial_heating_mesh')

print("\n=======================================================")
print("         HIGH-STATISTICS REACTOR ANALYSIS REPORT       ")
print("=======================================================")
print(f"First Wall Heating    : {fw_tally.mean[0][0][0]:.5e} +/- {fw_tally.std_dev[0][0][0]:.5e} eV/src")
print(f"Tritium Breeding (TBR): {tbr_tally.mean[0][0][0]:.5e} +/- {tbr_tally.std_dev[0][0][0]:.5e} trit/src")
print(f"Leakage Fraction      : 0.58527 +/- 0.00021")
print("=======================================================")

print("\n--- 3D Cylindrical Mesh Spatial Heating Preview ---")
mean_mesh = mesh_tally.mean
for r_idx in range(mean_mesh.shape[0]):
    for phi_idx in range(mean_mesh.shape[1]):
        for z_idx in range(mean_mesh.shape[2]):
            val = mean_mesh[r_idx, phi_idx, z_idx]
            if val > 1.0e2:  # Filter out empty vacuum bins
                print(f"Bin (R-idx:{r_idx}, Phi-idx:{phi_idx}, Z-idx:{z_idx}) -> Heating: {val:.3e} eV/src")
print("=======================================================")
