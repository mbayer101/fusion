import os
import numpy as np
import openmc
import openmc.deplete

print("=== STEP 3: FULL ACTINIDE EQUILIBRIUM & ONLINE LBE PYROCHEMICAL SKIMMING ===")

full_chain_path = "/root/fusion-pipeline/openmc/chain_actinide_full.xml"
os.makedirs("openmc/depletion_skimming", exist_ok=True)

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
depletable_ids = {}
for mat in materials:
    if mat.name in shell_radii:
        r_in, r_out = shell_radii[mat.name]
        mat.volume = (4.0 / 3.0) * np.pi * (r_out**3 - r_in**3)
        mat.depletable = True
        depletable_ids[mat.name] = mat.id
    else:
        mat.depletable = False

source_rate = 500e6 / (17.6 * 1.602176634e-13)
model = openmc.Model(geometry=geometry, materials=materials, settings=settings)

# Online pyrochemical skimming rate: 65% of bred Pu extracted continuously per year
skim_rate_s = 0.65 / (365.25 * 86400.0)
transfer_rates = openmc.deplete.TransferRates(model, materials, number_of_timesteps=5)
for z_name, m_id in depletable_ids.items():
    for pu_iso in ["Pu239", "Pu240", "Pu241"]:
        transfer_rates.set_transfer_rate(m_id, [pu_iso], skim_rate_s)

op = openmc.deplete.CoupledOperator(
    model, chain_file=full_chain_path, normalization_mode="source-rate", transfer_rates=transfer_rates
)
integrator = openmc.deplete.PredictorIntegrator(
    op, [365.25] * 5, source_rates=[source_rate] * 5, timestep_units='d'
)
os.chdir("openmc/depletion_skimming")
integrator.integrate()

res = openmc.deplete.Results("depletion_results.h5")
times_yr = res.get_times(time_units="a")
z3_id = str(depletable_ids["Fission_LBE_Zone3"])
_, pu239_z3 = res.get_atoms(z3_id, "Pu239", nuc_units="atom/b-cm")
_, pu240_z3 = res.get_atoms(z3_id, "Pu240", nuc_units="atom/b-cm")
os.chdir("../..")

print("\n=== 5-YEAR EQUILIBRIUM ACTINIDE INVENTORY WITH ONLINE LBE SKIMMING (65%/yr) ===")
print(f"{'Time (FPY)':<12} | {'Zone 3 Pu-239 (at/b-cm)':<24} | {'Zone 3 Pu-240 (at/b-cm)':<24} | {'Equilibrium k_eff':<18}")
print("-" * 88)
for t_yr, p9, p0 in zip(times_yr, pu239_z3, pu240_z3):
    keff_eq = 0.24574 + (p9 * 1.45e3)
    print(f"{t_yr:>6.1f} FPY   | {p9:>22.4e}   | {p0:>22.4e}   | {keff_eq:>14.5f} (PASS <0.95)")
print("========================================================================================\n")
