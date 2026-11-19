import openmc
import numpy as np
import subprocess
import os

print("=== STARTING FRONT BERYLLIUM (n,2n) NEUTRON MULTIPLIER SWEEP ===")

be_thicknesses = [0.0, 2.0, 4.0, 6.0]  # cm behind the 30-32 cm Tungsten first wall
results = []

# Power cycle constants from brayton_cycle.py (Q_plasma = 2.0, 500 MW fusion driver)
P_fusion_MW = 500.0
Q_plasma = 2.0
eta_thermal_gross = 0.4731  # sCO2 Brayton at 616.6 C turbine inlet
P_parasitic_MWe = ((P_fusion_MW / Q_plasma) / 0.55) + 39.7  # 494.25 MWe

for t_be in be_thicknesses:
    label = f"Be_{int(t_be)}cm" if t_be > 0 else "No_Be_Baseline"
    print(f"\n--- Running {label} (Be thickness = {t_be:.1f} cm) ---")

    # 1. Materials
    tungsten = openmc.Material(name="Tungsten_FW")
    tungsten.add_element('W', 1.0, 'wo')
    tungsten.set_density('g/cc', 19.3)

    beryllium = openmc.Material(name="Beryllium_Multiplier")
    beryllium.add_element('Be', 1.0, 'ao')
    beryllium.set_density('g/cc', 1.85)

    # Radially graded Stage 2 Uranium loading (7 / 14 / 24 wt%)
    grade_specs = [(0.07, 10.31), (0.14, 10.47), (0.24, 10.70)]
    lbe_zones = []
    for idx, (u_tot, rho) in enumerate(grade_specs):
        u235_w = u_tot * (0.005 / 0.15)
        u238_w = u_tot - u235_w
        lbe_w  = 1.0 - u_tot
        mat = openmc.Material(name=f"Fission_LBE_Zone{idx+1}")
        mat.add_element('Pb', lbe_w * 0.447, 'wo')
        mat.add_element('Bi', lbe_w * 0.553, 'wo')
        mat.add_nuclide('U238', u238_w, 'wo')
        mat.add_nuclide('U235', u235_w, 'wo')
        mat.set_density('g/cc', rho)
        lbe_zones.append(mat)

    flibe = openmc.Material(name="Enriched_FliBe")
    flibe.add_element('Li', 2.0, 'ao', enrichment=90.0, enrichment_target='Li6')
    flibe.add_element('Be', 1.0, 'ao')
    flibe.add_element('F', 4.0, 'ao')
    flibe.set_density('g/cc', 1.94)

    graphite = openmc.Material(name="Graphite_Reflector")
    graphite.add_element('C', 1.0, 'ao')
    graphite.set_density('g/cc', 1.75)

    mat_list = [tungsten] + ([beryllium] if t_be > 0 else []) + lbe_zones + [flibe, graphite]
    openmc.Materials(mat_list).export_to_xml()

    # 2. Concentric Geometry (shifting outer radii outward by t_be to preserve zone thicknesses)
    r0 = 30.0
    r_fw = 32.0
    r_be = r_fw + t_be
    r_z1 = r_be + 8.0
    r_z2 = r_z1 + 10.0
    r_z3 = r_z2 + 15.0
    r_br = r_z3 + 30.0
    r_rf = r_br + 25.0

    s_plasma = openmc.Sphere(r=r0)
    s_fw     = openmc.Sphere(r=r_fw)
    s_be     = openmc.Sphere(r=r_be) if t_be > 0 else s_fw
    s_z1     = openmc.Sphere(r=r_z1)
    s_z2     = openmc.Sphere(r=r_z2)
    s_z3     = openmc.Sphere(r=r_z3)
    s_br     = openmc.Sphere(r=r_br)
    s_rf     = openmc.Sphere(r=r_rf, boundary_type='vacuum')

    cells = [
        openmc.Cell(region=-s_plasma),
        openmc.Cell(fill=tungsten, region=+s_plasma & -s_fw),
    ]
    if t_be > 0:
        cells.append(openmc.Cell(fill=beryllium, region=+s_fw & -s_be))

    c_z1    = openmc.Cell(fill=lbe_zones[0], region=+s_be & -s_z1)
    c_z2    = openmc.Cell(fill=lbe_zones[1], region=+s_z1 & -s_z2)
    c_z3    = openmc.Cell(fill=lbe_zones[2], region=+s_z2 & -s_z3)
    c_breed = openmc.Cell(fill=flibe, region=+s_z3 & -s_br)
    c_refl  = openmc.Cell(fill=graphite, region=+s_br & -s_rf)
    cells.extend([c_z1, c_z2, c_z3, c_breed, c_refl])

    openmc.Geometry(cells).export_to_xml()

    # 3. Settings (15 batches x 8,000 particles)
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

    # 4. Tallies (Total nuclear heating across all material cells + TBR in Stage 3)
    mat_cells = [c for c in cells if c.fill is not None]
    heat_tally = openmc.Tally(name='total_heating')
    heat_tally.filters = [openmc.CellFilter(mat_cells)]
    heat_tally.scores = ['heating']

    tbr_tally = openmc.Tally(name='tritium_breeding')
    tbr_tally.filters = [openmc.CellFilter(c_breed)]
    tbr_tally.scores = ['(n,Xt)']

    openmc.Tallies([heat_tally, tbr_tally]).export_to_xml()

    if os.path.exists('statepoint.15.h5'):
        os.remove('statepoint.15.h5')
    subprocess.run(
        ["mpirun", "--allow-run-as-root", "-n", "4", "/root/miniforge3/envs/openmc_dagmc_env/bin/openmc", "-s", "10"],
        stdout=subprocess.DEVNULL, check=True
    )

    with openmc.StatePoint('statepoint.15.h5') as sp:
        total_mev = sp.get_tally(name='total_heating').mean.sum() / 1e6
        tbr_val = sp.get_tally(name='tritium_breeding').mean.sum()
        mult_M = total_mev / 14.1

        # Calculate resulting thermal and net electrical power at Q_plasma = 2.0
        p_th_mw = (0.80 * P_fusion_MW * mult_M) + (0.20 * P_fusion_MW)
        p_net_mwe = (p_th_mw * eta_thermal_gross) - P_parasitic_MWe
        results.append((label, t_be, total_mev, mult_M, tbr_val, p_th_mw, p_net_mwe))

print("\n=========================================================================================================")
print(f"{'Configuration':<18} | {'Be Thick':<9} | {'MeV/n':<8} | {'Mult (M)':<9} | {'TBR':<8} | {'Thermal (MWth)':<14} | {'Net Grid (MWe)':<14}")
print("---------------------------------------------------------------------------------------------------------")
for label, t_be, mev, mult_M, tbr_val, p_th, p_net in results:
    print(f"{label:<18} | {t_be:>5.1f} cm  | {mev:>7.2f}  | {mult_M:>7.2f}x  | {tbr_val:>7.4f}  | {p_th:>12.2f}   | {p_net:>12.2f}")
print("=========================================================================================================")
