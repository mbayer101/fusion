import openmc
import numpy as np
import subprocess
import os

print("=== STARTING STAGE 2 RADIAL ACTINIDE GRADING SWEEP ===")

sweep_cases = [
    ("Case_1_Uniform_15wt",       [0.15, 0.15, 0.15]),
    ("Case_2_Mild_Outward_Grade", [0.10, 0.15, 0.20]),
    ("Case_3_Steep_Outward_Grade",[0.07, 0.14, 0.24]),
    ("Case_4_Extreme_Outward",    [0.05, 0.12, 0.28]),
]

r_bins = np.array([30.0, 32.0, 40.0, 50.0, 65.0, 75.0, 85.0, 95.0, 120.0])
shell_vols = (4.0 / 3.0) * np.pi * (r_bins[1:]**3 - r_bins[:-1]**3)
stage2_vols = shell_vols[1:4]  # Sub-shells: 32-40, 40-50, 50-65 cm

results = []

for label, u_fracs in sweep_cases:
    print(f"Running {label} (U wt% by radial zone: {u_fracs})...")
    
    tungsten = openmc.Material(name="Tungsten_FW")
    tungsten.add_element('W', 1.0, 'wo')
    tungsten.set_density('g/cc', 19.3)

    lbe_zones = []
    for idx, u_tot in enumerate(u_fracs):
        u235_w = u_tot * (0.005 / 0.15)
        u238_w = u_tot - u235_w
        lbe_w  = 1.0 - u_tot
        
        mat = openmc.Material(name=f"LBE_Zone_{idx+1}")
        mat.add_element('Pb', lbe_w * 0.447, 'wo')
        mat.add_element('Bi', lbe_w * 0.553, 'wo')
        mat.add_nuclide('U238', u238_w, 'wo')
        mat.add_nuclide('U235', u235_w, 'wo')
        mat.set_density('g/cc', 10.15 + (u_tot * 2.3))
        lbe_zones.append(mat)

    flibe = openmc.Material(name="Enriched_FliBe")
    flibe.add_element('Li', 2.0, 'ao', enrichment=90.0, enrichment_target='Li6')
    flibe.add_element('Be', 1.0, 'ao')
    flibe.add_element('F', 4.0, 'ao')
    flibe.set_density('g/cc', 1.94)

    graphite = openmc.Material(name="Graphite_Reflector")
    graphite.add_element('C', 1.0, 'ao')
    graphite.set_density('g/cc', 1.75)

    materials = openmc.Materials([tungsten] + lbe_zones + [flibe, graphite])
    materials.export_to_xml()

    r_plasma = openmc.Sphere(r=30.0)
    r_wall   = openmc.Sphere(r=32.0)
    r_z1     = openmc.Sphere(r=40.0)
    r_z2     = openmc.Sphere(r=50.0)
    r_fiss   = openmc.Sphere(r=65.0)
    r_breed  = openmc.Sphere(r=95.0)
    r_refl   = openmc.Sphere(r=120.0, boundary_type='vacuum')

    c_plasma = openmc.Cell(region=-r_plasma)
    c_wall   = openmc.Cell(fill=tungsten, region=+r_plasma & -r_wall)
    c_z1     = openmc.Cell(fill=lbe_zones[0], region=+r_wall & -r_z1)
    c_z2     = openmc.Cell(fill=lbe_zones[1], region=+r_z1 & -r_z2)
    c_z3     = openmc.Cell(fill=lbe_zones[2], region=+r_z2 & -r_fiss)
    c_breed  = openmc.Cell(fill=flibe, region=+r_fiss & -r_breed)
    c_refl   = openmc.Cell(fill=graphite, region=+r_breed & -r_refl)

    geometry = openmc.Geometry([c_plasma, c_wall, c_z1, c_z2, c_z3, c_breed, c_refl])
    geometry.export_to_xml()

    source = openmc.IndependentSource()
    source.space = openmc.stats.Point((0.0, 0.0, 0.0))
    source.angle = openmc.stats.Isotropic()
    source.energy = openmc.stats.Discrete([14.1e6], [1.0])

    settings = openmc.Settings()
    settings.source = source
    settings.batches = 15
    settings.particles = 8000
    settings.run_mode = 'fixed source'
    settings.output = {'tallies': False}
    settings.export_to_xml()

    mesh = openmc.SphericalMesh(
        r_grid=list(r_bins),
        theta_grid=[0.0, np.pi],
        phi_grid=[0.0, 2.0 * np.pi]
    )
    heating_tally = openmc.Tally(name='volumetric_heating')
    heating_tally.filters = [openmc.MeshFilter(mesh)]
    heating_tally.scores = ['heating']

    tbr_tally = openmc.Tally(name='tritium_breeding')
    tbr_tally.filters = [openmc.CellFilter(c_breed)]
    tbr_tally.scores = ['(n,Xt)']

    tallies = openmc.Tallies([heating_tally, tbr_tally])
    tallies.export_to_xml()

    if os.path.exists('statepoint.15.h5'):
        os.remove('statepoint.15.h5')
    subprocess.run(
        ["mpirun", "--allow-run-as-root", "-n", "4", "/root/miniforge3/envs/openmc_dagmc_env/bin/openmc", "-s", "10"],
        stdout=subprocess.DEVNULL, check=True
    )

    with openmc.StatePoint('statepoint.15.h5') as sp:
        tbr_val = sp.get_tally(name='tritium_breeding').mean.sum()
        heat_mev = sp.get_tally(name='volumetric_heating').mean.flatten() / 1e6
        total_mev = heat_mev.sum()
        mult_M = total_mev / 14.1

        s2_mev = heat_mev[1:4]
        s2_q_dens = s2_mev / stage2_vols
        q_avg = s2_mev.sum() / stage2_vols.sum()
        ppf = np.max(s2_q_dens) / q_avg

        results.append((label, u_fracs, mult_M, tbr_val, ppf))

print("\n=========================================================================================")
print(f"{'Sweep Configuration':<28} | {'U wt% (Z1/Z2/Z3)':<18} | {'Mult (M)':<8} | {'TBR':<7} | {'Radial PPF':<10}")
print("-----------------------------------------------------------------------------------------")
for label, u_f, mult_M, tbr_val, ppf in results:
    u_str = f"{int(u_f[0]*100)}/{int(u_f[1]*100)}/{int(u_f[2]*100)}%"
    print(f"{label:<28} | {u_str:<18} | {mult_M:<7.2f}x | {tbr_val:<7.4f} | {ppf:<10.2f}")
print("=========================================================================================")
