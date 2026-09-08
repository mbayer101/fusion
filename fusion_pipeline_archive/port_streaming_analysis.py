import openmc
import numpy as np

# Load existing materials and geometry configuration
openmc.config['cross_sections'] = '/root/cross_sections.xml'
geometry = openmc.Geometry.from_xml()
materials = openmc.Materials.from_xml()

tallies = openmc.Tallies()

# 1. High-Resolution Cylindrical Mesh Focused on Port Exit / Magnet Region
# Extending radially and axially where the port penetrates the outer shield
port_streaming_mesh = openmc.CylindricalMesh(
    r_grid=np.linspace(100.0, 200.0, 50),     # Fine grid across the port radius
    phi_grid=np.linspace(0.0, 2.0 * np.pi, 20), # Azimuthal coverage around the port angle
    z_grid=np.linspace(-60.0, 60.0, 40)        # Axial profile along the duct exit
)

port_mesh_filter = openmc.MeshFilter(port_streaming_mesh)

# 2. Port Streaming Tally (Flux and Heating to evaluate magnet degradation)
streaming_tally = openmc.Tally(name='port_streaming_flux_heating')
streaming_tally.filters = [port_mesh_filter]
streaming_tally.scores = ['flux', 'heating', '(n,g)'] # Captures neutron flux, energy deposition, and capture gammas
tallies.append(streaming_tally)

tallies.export_to_xml()
print("Port streaming tallies successfully configured and exported.")

