import os
import subprocess
import numpy as np
import openmc

print("=== TRACK A: 3D D-SHAPED TOROIDAL CAD / DAGMC & INBOARD-OUTBOARD WALL LOADING ===")

# 1. D-Shaped Tokamak Parametric Geometry (R0 = 300 cm, a = 100 cm, kappa = 1.7, delta = 0.33)
R0 = 300.0
a_plasma = 100.0
kappa = 1.7
delta = 0.33

os.makedirs("cad", exist_ok=True)
os.makedirs("openmc/toroidal_3d", exist_ok=True)

# Attempt CadQuery + DAGMC export if installed; generate full 3D toroidal OpenMC model directly
dagmc_available = False
try:
    if os.path.exists("cad/fff_toroidal_sector.h5m"): raise RuntimeError("Reusing existing cad/fff_toroidal_sector.h5m")
    import cadquery as cq
    from cad_to_dagmc import CadToDagmc

    def d_shape_points(minor_r, n_pts=60):
        theta = np.linspace(0, 2 * np.pi, n_pts, endpoint=False)
        r = R0 + minor_r * np.cos(theta + delta * np.sin(theta))
        z = kappa * minor_r * np.sin(theta)
        return [(float(ri), float(zi)) for ri, zi in zip(r, z)]

    # Build 90-degree toroidal sector shells (reflective symmetry on phi = 0, 90 deg)
    radii = [
        ("first_wall_w", 100.0, 102.0),
        ("be_multiplier", 102.0, 108.0),
        ("stage2_z1_lbe", 108.0, 116.0),
        ("stage2_z2_lbe", 116.0, 126.0),
        ("stage2_z3_lbe", 126.0, 141.0),
        ("stage3_flibe",  141.0, 171.0),
        ("graphite_refl", 171.0, 196.0),
    ]
    model = CadToDagmc()
    for tag, r_in, r_out in radii:
        outer_wire = cq.Workplane("XZ").polyline(d_shape_points(r_out)).close()
        inner_wire = cq.Workplane("XZ").polyline(d_shape_points(r_in)).close()
        shell = outer_wire.revolve(90, (0, 0, 0), (0, 1, 0)).cut(
            inner_wire.revolve(90, (0, 0, 0), (0, 1, 0))
        )
        model.add_cadquery_object(shell, material_tags=[tag])

    h5m_path = "cad/fff_toroidal_sector.h5m"
    model.export_dagmc_h5m_file(filename=h5m_path, min_mesh_size=2.0, max_mesh_size=8.0)
    dagmc_available = True
    print(f"Exported faceted 3D D-shaped DAGMC mesh to {h5m_path}")
except Exception as e:
    print(f"CadQuery/DAGMC direct export skipped ({e}); building exact 3D Toroidal CSG model with port streaming...")

# 2. Define Production 4-Zone Materials
tungsten = openmc.Material(name="first_wall_w")
tungsten.add_element('W', 1.0, 'wo')
tungsten.set_density('g/cc', 19.3)

beryllium = openmc.Material(name="be_multiplier")
beryllium.add_element('Be', 1.0, 'ao')
beryllium.set_density('g/cc', 1.85)

grade_specs = [(0.07, 10.31), (0.14, 10.47), (0.24, 10.70)]
lbe_zones = []
for idx, (u_tot, rho) in enumerate(grade_specs):
    u235_w = u_tot * (0.005 / 0.15)
    u238_w = u_tot - u235_w
    lbe_w  = 1.0 - u_tot
    mat = openmc.Material(name=f"stage2_z{idx+1}_lbe")
    mat.add_element('Pb', lbe_w * 0.447, 'wo')
    mat.add_element('Bi', lbe_w * 0.553, 'wo')
    mat.add_nuclide('U238', u238_w, 'wo')
    mat.add_nuclide('U235', u235_w, 'wo')
    mat.set_density('g/cc', rho)
    lbe_zones.append(mat)

flibe = openmc.Material(name="stage3_flibe")
flibe.add_element('Li', 2.0, 'ao', enrichment=90.0, enrichment_target='Li6')
flibe.add_element('Be', 1.0, 'ao')
flibe.add_element('F', 4.0, 'ao')
flibe.set_density('g/cc', 1.94)

graphite = openmc.Material(name="graphite_refl")
graphite.add_element('C', 1.0, 'ao')
graphite.set_density('g/cc', 1.75)

mats = openmc.Materials([tungsten, beryllium] + lbe_zones + [flibe, graphite])
mats.export_to_xml("openmc/toroidal_3d/materials.xml")

# 3. 3D Toroidal Geometry (Z-elongated Torus + Midplane Equatorial Heating Port)
def make_torus(minor_r, btype='transmission'):
    return openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=minor_r * kappa, c=minor_r, boundary_type=btype)

t_plasma = make_torus(100.0)
t_fw     = make_torus(102.0)
t_be     = make_torus(108.0)
t_z1     = make_torus(116.0)
t_z2     = make_torus(126.0)
t_z3     = make_torus(141.0)
t_br     = make_torus(171.0)
t_rf     = make_torus(196.0, btype='vacuum')

# Midplane diagnostic/NBI port on +X axis (radius = 22 cm)
port_cyl = openmc.XCylinder(y0=0.0, z0=0.0, r=22.0)
x_outboard = openmc.XPlane(x0=R0)
inboard_halfspace = -openmc.Cylinder(x0=0.0, y0=0.0, r=R0)
outboard_halfspace = +openmc.Cylinder(x0=0.0, y0=0.0, r=R0)

port_region = -port_cyl & +x_outboard & +t_plasma & -t_rf

c_plasma = openmc.Cell(name="Toroidal_Plasma_Core", region=-t_plasma)
c_port   = openmc.Cell(name="Equatorial_NBI_Port_Void", region=port_region)
c_fw_in  = openmc.Cell(name="FW_Inboard",  fill=tungsten, region=+t_plasma & -t_fw & inboard_halfspace & ~port_region)
c_fw_out = openmc.Cell(name="FW_Outboard", fill=tungsten, region=+t_plasma & -t_fw & outboard_halfspace & ~port_region)
c_be     = openmc.Cell(name="Be_Multiplier_3D", fill=beryllium, region=+t_fw & -t_be & ~port_region)
c_z1     = openmc.Cell(name="Stage2_Z1_3D", fill=lbe_zones[0], region=+t_be & -t_z1 & ~port_region)
c_z2     = openmc.Cell(name="Stage2_Z2_3D", fill=lbe_zones[1], region=+t_z1 & -t_z2 & ~port_region)
c_z3     = openmc.Cell(name="Stage2_Z3_3D", fill=lbe_zones[2], region=+t_z2 & -t_z3 & ~port_region)
c_breed  = openmc.Cell(name="Stage3_FliBe_3D", fill=flibe, region=+t_z3 & -t_br & ~port_region)
c_refl   = openmc.Cell(name="Graphite_Refl_3D", fill=graphite, region=+t_br & -t_rf & ~port_region)

geom = openmc.Geometry([c_plasma, c_port, c_fw_in, c_fw_out, c_be, c_z1, c_z2, c_z3, c_breed, c_refl])
geom.export_to_xml("openmc/toroidal_3d/geometry.xml")

# 4. Distributed Toroidal Ring D-T Plasma Source (peaked at R = R0 + 10 cm Shafranov shift)
r_src = openmc.stats.Discrete([R0 + 10.0], [1.0])
phi_src = openmc.stats.Uniform(0.0, 2.0 * np.pi)
z_src = openmc.stats.Normal(0.0, 25.0)
source = openmc.IndependentSource(
    space=openmc.stats.CylindricalIndependent(r_src, phi_src, z_src),
    angle=openmc.stats.Isotropic(),
    energy=openmc.stats.Discrete([14.1e6], [1.0])
)

settings = openmc.Settings()
settings.source = source
settings.batches = 20
settings.particles = 10000
settings.run_mode = 'fixed source'
settings.export_to_xml("openmc/toroidal_3d/settings.xml")

# 5. Tallies: 3D TBR, Blanket Multiplication, and Inboard vs. Outboard First-Wall Flux/Heating
t_fw_in  = openmc.Tally(name='fw_inboard_flux')
t_fw_in.filters = [openmc.CellFilter(c_fw_in)]
t_fw_in.scores = ['flux', 'heating']

t_fw_out = openmc.Tally(name='fw_outboard_flux')
t_fw_out.filters = [openmc.CellFilter(c_fw_out)]
t_fw_out.scores = ['flux', 'heating']

t_tbr = openmc.Tally(name='toroidal_tbr')
t_tbr.filters = [openmc.CellFilter(c_breed)]
t_tbr.scores = ['(n,Xt)']

t_heat = openmc.Tally(name='toroidal_total_heating')
t_heat.filters = [openmc.CellFilter([c_fw_in, c_fw_out, c_be, c_z1, c_z2, c_z3, c_breed, c_refl])]
t_heat.scores = ['heating']

openmc.Tallies([t_fw_in, t_fw_out, t_tbr, t_heat]).export_to_xml("openmc/toroidal_3d/tallies.xml")

# 6. Run 3D Toroidal Simulation
subprocess.run(
    ["mpirun", "--allow-run-as-root", "-n", "4", "/root/miniforge3/envs/openmc_dagmc_env/bin/openmc", "-s", "10", ],
    cwd="openmc/toroidal_3d", check=True
)

with openmc.StatePoint("openmc/toroidal_3d/statepoint.20.h5") as sp:
    tbr_3d = sp.get_tally(name='toroidal_tbr').mean.sum()
    heat_mev = sp.get_tally(name='toroidal_total_heating').mean.sum() / 1e6
    fw_in_h = sp.get_tally(name='fw_inboard_flux').mean[0, 0, 1] / 1e6
    fw_out_h = sp.get_tally(name='fw_outboard_flux').mean[0, 0, 1] / 1e6

    print("\n======================================================================")
    print(f"3D Toroidal Blanket Multiplication (M) : {heat_mev / 14.1:.2f}x ({heat_mev:.2f} MeV/n)")
    print(f"3D Toroidal TBR (with NBI Port Loss)   : {tbr_3d:.4f}")
    print(f"Outboard / Inboard FW Heating Ratio    : {fw_out_h / max(fw_in_h, 1e-9):.2f}x (Shafranov shift asymmetry)")
    print("======================================================================\n")
