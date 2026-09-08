import cadquery as cq

print("=== Generating Multi-Component Reactor Assembly ===")
# Component 1: First Wall (Inner Shell)
fw = (
    cq.Workplane("XY")
    .cylinder(height=200, radius=100)
    .faces(">Z or <Z or (not %CYLINDER)")
    .shell(-5.0) # 5cm thickness
)

# Component 2: Breeding Blanket (Outer Shell wrapping the First Wall)
bb = (
    cq.Workplane("XY")
    .cylinder(height=200, radius=130)
    .faces(">Z or <Z or (not %CYLINDER)")
    .shell(-30.0) # 30cm thickness
)

# Combine them into an assembly and export as a single STEP file
assembly = cq.Assembly()
assembly.add(fw, name='First_Wall')
assembly.add(bb, name='Breeding_Blanket')
assembly.save('full_reactor.step')

print("=== Exported full_reactor.step successfully ===")
