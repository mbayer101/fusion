import cadquery as cq
from cad_to_dagmc import CadToDagmc

print("=== Initializing CAD-to-DAGMC Converter ===")
model = CadToDagmc()

# Load your STEP file. 
# Ensure the order of material_tags matches the order of volumes inside your STEP file, 
# OR use material_tags='assembly_names' if your parts are named inside FreeCAD.
step_file = 'full_reactor.step'
model.add_stp_file(
    step_file, 
    material_tags=['First_Wall', 'Breeding_Blanket']
)

print("=== Generating High-Resolution DAGMC Mesh ===")
model.export_dagmc_h5m_file(
    filename='full_reactor.h5m',
    meshing_backend='gmsh',
    min_mesh_size=0.5,
    max_mesh_size=5.0,
    tolerance=1e-3
)

print("=== Success: full_reactor.h5m is ready! ===")
