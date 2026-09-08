import openmc
import numpy as np

sp = openmc.StatePoint('statepoint.50.h5')
tally_result = sp.get_tally(name='port_streaming_analysis')

port_streaming_mesh = openmc.CylindricalMesh(
    r_grid=np.linspace(100.0, 200.0, 30),
    phi_grid=np.linspace(0.0, 2.0 * np.pi, 12),
    z_grid=np.linspace(-60.0, 60.0, 30)
)

flux_data = tally_result.mean[:, :, :, 0]
heating_data = tally_result.mean[:, :, :, 1]

vtk_filename = "port_streaming_analysis.vtk"
port_streaming_mesh.write_data_to_vtk(
    vtk_filename, 
    datasets={
        'Neutron Flux (n/cm2-src)': flux_data,
        'Heating (eV/src)': heating_data
    }
)
print(f"Successfully exported port streaming analysis to {vtk_filename}")
