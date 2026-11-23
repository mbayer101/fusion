import os
import subprocess
import numpy as np
import openmc

print("=== STEP 2: 3D TOROIDAL TBR RECOVERY SWEEP (PORT COLLAR + STAGE 2/3 RE-BALANCING) ===")

R0 = 300.0
kappa = 1.7
os.makedirs("openmc/toroidal_tbr_opt", exist_ok=True)

configs = [
    ("3D_Baseline_33cm_LBE",   [8.0, 10.0, 15.0], 30.0, False),
    ("3D_Opt_27cm_LBE_Collar", [7.0, 9.0, 11.0],  40.0, True),
    ("3D_Opt_22cm_LBE_Collar", [6.0, 7.0, 9.0],   45.0, True),
]

summary = []

for name, z_thicks, flibe_thick, use_port_collar in configs:
    tungsten = openmc.Material(name="fw_w")
    tungsten.add_element('W', 1.0, 'wo')
    tungsten.set_density('g/cc', 19.3)

    beryllium = openmc.Material(name="be_mult")
    beryllium.add_element('Be', 1.0, 'ao')
    beryllium.set_density('g/cc', 1.85)

    grade_specs = [(0.07, 10.31), (0.14, 10.47), (0.24, 10.70)]
    lbe_zones = []
    for idx, (u_tot, rho) in enumerate(grade_specs):
        u235_w = u_tot * (0.005 / 0.15)
        u238_w = u_tot - u235_w
        lbe_w  = 1.0 - u_tot
        mat = openmc.Material(name=f"lbe_z{idx+1}")
        mat.add_element('Pb', lbe_w * 0.447, 'wo')
        mat.add_element('Bi', lbe_w * 0.553, 'wo')
        mat.add_nuclide('U238', u238_w, 'wo')
        mat.add_nuclide('U235', u235_w, 'wo')
        mat.set_density('g/cc', rho)
        lbe_zones.append(mat)

    flibe = openmc.Material(name="flibe_3d")
    flibe.add_element('Li', 2.0, 'ao', enrichment=90.0, enrichment_target='Li6')
    flibe.add_element('Be', 1.0, 'ao')
    flibe.add_element('F', 4.0, 'ao')
    flibe.set_density('g/cc', 1.94)

    graphite = openmc.Material(name="graphite_3d")
    graphite.add_element('C', 1.0, 'ao')
    graphite.set_density('g/cc', 1.75)

    openmc.Materials([tungsten, beryllium] + lbe_zones + [flibe, graphite]).export_to_xml("openmc/toroidal_tbr_opt/materials.xml")

    def make_torus(minor_r, btype='transmission'):
        return openmc.ZTorus(x0=0.0, y0=0.0, z0=0.0, a=R0, b=minor_r * kappa, c=minor_r, boundary_type=btype)

    r_fw = 102.0
    r_be = 108.0
    r_z1 = r_be + z_thicks[0]
    r_z2 = r_z1 + z_thicks[1]
    r_z3 = r_z2 + z_thicks[2]
    r_br = r_z3 + flibe_thick
    r_rf = r_br + 25.0

    t_plasma = make_torus(100.0)
    t_fw     = make_torus(r_fw)
    t_be     = make_torus(r_be)
    t_z1     = make_torus(r_z1)
    t_z2     = make_torus(r_z2)
    t_z3     = make_torus(r_z3)
    t_br     = make_torus(r_br)
    t_rf     = make_torus(r_rf, btype='vacuum')

    port_cyl = openmc.XCylinder(y0=0.0, z0=0.0, r=22.0)
    collar_cyl = openmc.XCylinder(y0=0.0, z0=0.0, r=36.0)
    x_outboard = openmc.XPlane(x0=R0)
    port_void = -port_cyl & +x_outboard & +t_plasma & -t_rf

    c_plasma = openmc.Cell(region=-t_plasma)
    c_port   = openmc.Cell(region=port_void)
    c_fw     = openmc.Cell(fill=tungsten, region=+t_plasma & -t_fw & ~port_void)
    c_be     = openmc.Cell(fill=beryllium, region=+t_fw & -t_be & ~port_void)

    if use_port_collar:
        collar_reg = +port_cyl & -collar_cyl & +x_outboard & +t_be & -t_rf
        exclude = port_void | collar_reg
        breed_reg = ((+t_z3 & -t_br) | collar_reg) & ~port_void
    else:
        exclude = port_void
        breed_reg = (+t_z3 & -t_br) & ~port_void

    c_z1     = openmc.Cell(fill=lbe_zones[0], region=+t_be & -t_z1 & ~exclude)
    c_z2     = openmc.Cell(fill=lbe_zones[1], region=+t_z1 & -t_z2 & ~exclude)
    c_z3     = openmc.Cell(fill=lbe_zones[2], region=+t_z2 & -t_z3 & ~exclude)
    c_breed  = openmc.Cell(fill=flibe, region=breed_reg)
    c_refl   = openmc.Cell(fill=graphite, region=+t_br & -t_rf & ~exclude)

    openmc.Geometry([c_plasma, c_port, c_fw, c_be, c_z1, c_z2, c_z3, c_breed, c_refl]).export_to_xml("openmc/toroidal_tbr_opt/geometry.xml")

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
    settings.batches = 15
    settings.particles = 8000
    settings.run_mode = 'fixed source'
    settings.export_to_xml("openmc/toroidal_tbr_opt/settings.xml")

    t_tbr = openmc.Tally(name='tbr_3d')
    t_tbr.filters = [openmc.CellFilter(c_breed)]
    t_tbr.scores = ['(n,Xt)']

    t_heat = openmc.Tally(name='heat_3d')
    t_heat.filters = [openmc.CellFilter([c_fw, c_be, c_z1, c_z2, c_z3, c_breed, c_refl])]
    t_heat.scores = ['heating']

    openmc.Tallies([t_tbr, t_heat]).export_to_xml("openmc/toroidal_tbr_opt/tallies.xml")

    sp_path = "openmc/toroidal_tbr_opt/statepoint.15.h5"
    if os.path.exists(sp_path):
        os.remove(sp_path)
    subprocess.run(
        ["mpirun", "--allow-run-as-root", "-n", "4", "/root/miniforge3/envs/openmc_dagmc_env/bin/openmc", "-s", "10"],
        cwd="openmc/toroidal_tbr_opt", stdout=subprocess.DEVNULL, check=True
    )

    with openmc.StatePoint(sp_path) as sp:
        tbr_val = sp.get_tally(name='tbr_3d').mean.sum()
        mev_val = sp.get_tally(name='heat_3d').mean.sum() / 1e6
        mult_val = mev_val / 14.1
        summary.append((name, sum(z_thicks), flibe_thick, mult_val, tbr_val))

print("\n======================================================================================")
print(f"{'3D Toroidal Configuration':<26} | {'Stage 2 LBE':<12} | {'Stage 3 FliBe':<14} | {'Mult (M)':<9} | {'3D TBR':<10}")
print("--------------------------------------------------------------------------------------")
for name, lbe_t, flibe_t, m_val, tbr_v in summary:
    status = "PASS (>1.10)" if tbr_v >= 1.10 else "LOW"
    print(f"{name:<26} | {lbe_t:>8.1f} cm  | {flibe_t:>10.1f} cm  | {m_val:>7.2f}x  | {tbr_v:>7.4f} ({status})")
print("======================================================================================\n")
