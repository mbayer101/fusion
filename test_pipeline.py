import cadquery as cq
from cad_to_dagmc import CadToDagmc

print("=== Generating Test CAD Geometry (Hollow Cylinder) ===")
result = (
    cq.Workplane("XY")
    .cylinder(height=200, radius=110)
    .faces(">Z or <Z or (not %CYLINDER)")
    .shell(-10.0)
)

step_filename = 'first_wall.step'
result.val().exportStep(step_filename)
print(f"=== Exported {step_filename} successfully ===")

print("=== Initializing CadToDagmc Converter ===")
model = CadToDagmc()
model.add_stp_file(step_filename, material_tags=['First_Wall'])

print("=== Exporting to DAGMC h5m format (using Gmsh backend) ===")
model.export_dagmc_h5m_file(
    filename='fusion_reactor.h5m',
    meshing_backend='gmsh',
    min_mesh_size=1.0,
    max_mesh_size=10.0
)

print("=== Conversion Complete: fusion_reactor.h5m created ===")
