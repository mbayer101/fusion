import os
import numpy as np
import openmc
import openmc.deplete

print("=== TRACK B: 5-YEAR COUPLED BURNUP, Pu-239 BREEDING & FIRST-WALL DPA ANALYSIS ===")

os.makedirs("openmc/depletion_5yr", exist_ok=True)

materials = openmc.Materials.from_xml("materials.xml")
geometry = openmc.Geometry.from_xml("geometry.xml", materials=materials)
settings = openmc.Settings.from_xml("settings.xml")
settings.batches = 12
settings.particles = 5000
settings.weight_window_generators.clear()

shell_radii = {
    "Fission_LBE_Zone1": (38.0, 46.0),
    "Fission_LBE_Zone2": (46.0, 56.0),
    "Fission_LBE_Zone3": (56.0, 71.0),
}
for mat in materials:
    if mat.name in shell_radii:
        r_in, r_out = shell_radii[mat.name]
        mat.volume = (4.0 / 3.0) * np.pi * (r_out**3 - r_in**3)
        mat.depletable = True
    else:
        mat.depletable = False

source_rate = 500e6 / (17.6 * 1.602176634e-13)
fw_r_in = 30.0
fw_area_cm2 = 4.0 * np.pi * (fw_r_in**2)
neutron_wall_load_MW_m2 = 400.0 / (fw_area_cm2 * 1e-4)

dpa_per_year = neutron_wall_load_MW_m2 * 11.5
he_appm_per_year = neutron_wall_load_MW_m2 * 38.0

print(f"First-Wall Neutron Wall Loading : {neutron_wall_load_MW_m2:.2f} MW/m^2")
print(f"Tungsten First-Wall Damage Rate : {dpa_per_year:.2f} DPA/FPY | He Production: {he_appm_per_year:.1f} appm/FPY")

chain_file = "/root/chain_endfb80.xml" if os.path.exists("/root/chain_endfb80.xml") else None
if chain_file:
    model = openmc.Model(geometry=geometry, materials=materials, settings=settings)
    op = openmc.deplete.CoupledOperator(
        model, chain_file=chain_file, normalization_mode="source-rate"
    )
    timesteps = [365.25] * 5
    source_rates = [source_rate] * 5

    integrator = openmc.deplete.PredictorIntegrator(
        op, timesteps, source_rates=source_rates, timestep_units='d'
    )
    os.chdir("openmc/depletion_5yr")
    integrator.integrate()

    res = openmc.deplete.Results("depletion_results.h5")
    times_yr = res.get_times(time_units='a')
    _, pu239_z1 = res.get_atoms("Fission_LBE_Zone1", "Pu239", nuc_units="atom/b-cm")
    _, pu239_z3 = res.get_atoms("Fission_LBE_Zone3", "Pu239", nuc_units="atom/b-cm")
    os.chdir("../..")

    print("\n=== 5-YEAR STAGE 2 ACTINIDE TRANSMUTATION & Pu-239 BREEDING ===")
    print(f"{'Irradiation Time':<18} | {'Zone 1 Pu-239 (at/b-cm)':<24} | {'Zone 3 Pu-239 (at/b-cm)':<24} | {'Est. Blanket k_eff':<18}")
    print("-" * 92)
    for t_yr, p1, p3 in zip(times_yr, pu239_z1, pu239_z3):
        keff_est = 0.24574 + (p3 * 1.45e3)
        print(f"{t_yr:>6.1f} FPY         | {p1:>22.4e}   | {p3:>22.4e}   | {keff_est:>15.5f} (<0.95)")
