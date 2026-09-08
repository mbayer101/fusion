import openmc

print("Building OpenMC 3D Axisymmetric Toroidal Geometry...")

# 1. Geometry Parameters (Converted to cm for OpenMC native units)
R0_cm = 600.0  # Major radius (6.0 m -> 600.0 cm)
a_minor_cm = 200.0  # Plasma minor radius (2.0 m -> 200.0 cm)

t_fw_cm = 2.0       # 2 cm Tungsten
t_mult_cm = 5.0     # 5 cm Lead multiplier
t_bl_cm = 40.0      # 40 cm PbLi breeding blanket
t_str_cm = 3.0      # 3 cm Fe-Cr structure
t_shield_cm = 30.0  # 30 cm Shield

# Calculate cumulative minor radii (perpendicular 'c' and parallel 'b')
r1 = a_minor_cm
r2 = r1 + t_fw_cm
r3 = r2 + t_mult_cm
r4 = r3 + t_bl_cm
r5 = r4 + t_str_cm
r6 = r5 + t_shield_cm

# 2. Define OpenMC ZTorus surfaces
# ZTorus signature: ZTorus(x0, y0, z0, a=Major_Radius, b=Parallel_Minor_Radius, c=Perpendicular_Minor_Radius)
s_plasma = openmc.ZTorus(a=R0_cm, b=r1, c=r1, boundary_type='vacuum')
s_fw = openmc.ZTorus(a=R0_cm, b=r2, c=r2)
s_mult = openmc.ZTorus(a=R0_cm, b=r3, c=r3)
s_bl = openmc.ZTorus(a=R0_cm, b=r4, c=r4)
s_str = openmc.ZTorus(a=R0_cm, b=r5, c=r5)
s_shield = openmc.ZTorus(a=R0_cm, b=r6, c=r6, boundary_type='vacuum')

print("ZTorus surfaces generated successfully:")
print(f" - Plasma Surface ID: {s_plasma.id}")
print(f" - First Wall Surface ID: {s_fw.id}")
print(f" - Multiplier Surface ID: {s_mult.id}")
print(f" - Breeding Blanket Surface ID: {s_bl.id}")
print(f" - Structure Surface ID: {s_str.id}")
print(f" - Shield Boundary Surface ID: {s_shield.id}")


# 3. Define Regions using ZTorus Half-Spaces
# Inside/outside half-spaces are represented using + and - operators on surfaces
reg_plasma = -s_plasma
reg_fw = +s_plasma & -s_fw
reg_mult = +s_fw & -s_mult
reg_bl = +s_mult & -s_bl
reg_str = +s_bl & -s_str
reg_shield = +s_str & -s_shield

print("3D Toroidal regions defined successfully:")
print(" - Region stack: Plasma -> First Wall -> Multiplier -> Blanket -> Structure -> Shield")

# 4. Define Materials (Using FENDL-3.1d data paths)
# Tungsten First Wall
mat_fw = openmc.Material(name='Tungsten First Wall')
mat_fw.add_element('W', 1.0)
mat_fw.set_density('g/cm3', 19.3)

# Lead Multiplier
mat_mult = openmc.Material(name='Lead Multiplier')
mat_mult.add_element('Pb', 1.0)
mat_mult.set_density('g/cm3', 11.34)

# PbLi Breeding Blanket (50% Li-6 Enrichment)
mat_bl = openmc.Material(name='PbLi Breeder')
mat_bl.add_element('Pb', 0.83)
mat_bl.add_nuclide('Li6', 0.50 * 0.17) # 50% enrichment scaling
mat_bl.add_nuclide('Li7', 0.50 * 0.17)
mat_bl.set_density('g/cm3', 9.5) # Typical density approximation

# Fe-Cr Structural Shell (88% Fe / 12% Cr)
mat_str = openmc.Material(name='Fe-Cr Structure')
mat_str.add_element('Fe', 0.88)
mat_str.add_element('Cr', 0.12)
mat_str.set_density('g/cm3', 7.8)

# Shield (Fe-Cr Alloy Shield placeholder)
mat_shield = openmc.Material(name='Steel Shield')
mat_shield.add_element('Fe', 0.85)
mat_shield.add_element('Cr', 0.15)
mat_shield.set_density('g/cm3', 7.8)

# Plasma (Near-vacuum placeholder using FENDL-compatible Tungsten)
mat_plasma = openmc.Material(name='Plasma Core')
mat_plasma.add_element('W', 1.0, percent_type='ao')
mat_plasma.set_density('g/cm3', 1.0e-7) # Ultra-low density near-vacuum

materials = openmc.Materials([mat_fw, mat_mult, mat_bl, mat_str, mat_shield, mat_plasma])
materials.export_to_xml()

# --- 2D Geometry Plot ---
plot = openmc.Plot()
plot.filename = 'torus_xz_slice'
plot.basis = 'xz'
plot.origin = (600.0, 0.0, 0.0) # Center of the torus major radius
plot.width = [1000.0, 1000.0]
plot.pixels = [800, 800]
plot.color_by = 'material'

plots = openmc.Plots([plot])
plots.export_to_xml()
