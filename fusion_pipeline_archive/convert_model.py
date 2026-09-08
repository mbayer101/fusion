from cad_to_dagmc import CadToDagmc

print("=== Initializing CadToDagmc Converter ===")
model = CadToDagmc()

# If your CAD model is in a single STEP file containing multiple volumes/assemblies:
# model.add_stp_file('reactor.step', material_tags='assembly_names')

# Or if you are loading individual STEP components separately:
model.add_stp_file('first_wall.step', material_tags=['First_Wall'])
# model.add_stp_file('blanket.step', material_tags=['Breeding_Blanket'])
# model.add_stp_file('shield.step', material_tags=['Shield'])

print("=== Exporting to DAGMC h5m format ===")
model.export_dagmc_h5m_file(
    filename='fusion_reactor.h5m',
    min_mesh_size=0.5,
    max_mesh_size=5.0,
    facet_tolerance=1e-3
)

print("=== Conversion Complete: fusion_reactor.h5m created ===")
