import openmc

sp = openmc.StatePoint('statepoint.20.h5')

# 1. Standard Tally Extraction
fw_tally = sp.get_tally(name='first_wall_heating')
fw_mean = fw_tally.mean[0][0][0]
fw_std = fw_tally.std_dev[0][0][0]

tbr_tally = sp.get_tally(name='breeding_blanket_tbr')
tbr_mean = tbr_tally.mean[0][0][0]
tbr_std = tbr_tally.std_dev[0][0][0]

print("========================================")
print("       FULL REACTOR SIMULATION RESULTS  ")
print("========================================")
print(f"First Wall Heating : {fw_mean:.5e} +/- {fw_std:.5e} eV/src")
print(f"Tritium Breeding   : {tbr_mean:.5e} +/- {tbr_std:.5e} trit/src")
print("========================================")

# 2. Extract Mesh Tally and export via the mesh object
mesh_tally = sp.get_tally(name='spatial_heating_mesh')
mesh = mesh_tally.find_filter(openmc.MeshFilter).mesh

# Reshape the tally mean data to match the 3D grid dimensions
heating_data = mesh_tally.mean.ravel()

# Write out the VTK file using the native mesh method
mesh.write_data_to_vtk(
    filename='spatial_heating.vtk',
    datasets={'heating': heating_data}
)
print("\n[+] 3D Mesh Tally successfully exported to 'spatial_heating.vtk'!")
