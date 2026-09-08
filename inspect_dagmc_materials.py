import openmc

print("=== INSPECTING DAGMC GEOMETRY & MATERIAL BINDINGS ===")
dag_univ = openmc.DAGMCUniverse('full_reactor.h5m')

# Print metadata or volumes if accessible via DAGMC wrapper
print(f"DAGMC Universe ID: {dag_univ.id}")
print(f"Filename: {dag_univ.filename}")

# Let's verify underlying MOAB/DAGMC metadata if available
try:
    print("Materials defined in DAGMC file:")
    for mat in dag_univ.materials:
        print(f" - {mat}")
except AttributeError:
    print("DAGMC universe loaded successfully. Verifying via geometry cell mapping...")
    geometry = openmc.Geometry(root=dag_univ.bounded_universe(padding_distance=30.0))
    print("Geometry successfully bounded and wrapped.")

