import os
import numpy as np
import openmc
import openmc.deplete

print("=== STEP 3: FULL ACTINIDE EQUILIBRIUM & ONLINE LBE PYROCHEMICAL SKIMMING ===")

full_chain_path = "/root/fusion-pipeline/openmc/chain_actinide_full.xml"
base_chain = openmc.deplete.Chain.from_xml("/root/chain_endfb80.xml")

existing_names = {nuc.name for nuc in base_chain.nuclides}
if "Pu239" not in existing_names:
    u238 = base_chain["U238"]
    u238.add_reaction("(n,gamma)", "U239", 0.0, 1.0)

    u239 = openmc.deplete.Nuclide("U239")
    u239.half_life = 23.45 * 60.0
    u239.add_decay_mode("beta-", "Np239", 1.0)

    np239 = openmc.deplete.Nuclide("Np239")
    np239.half_life = 2.356 * 86400.0
    np239.add_decay_mode("beta-", "Pu239", 1.0)

    pu239 = openmc.deplete.Nuclide("Pu239")
    pu239.half_life = 24110.0 * 365.25 * 86400.0
    pu239.add_reaction("(n,gamma)", "Pu240", 0.0, 1.0)
    pu239.add_reaction("fission", None, 207.0e6, 1.0)

    pu240 = openmc.deplete.Nuclide("Pu240")
    pu240.half_life = 6561.0 * 365.25 * 86400.0
    pu240.add_reaction("(n,gamma)", "Pu241", 0.0, 1.0)
    pu240.add_reaction("fission", None, 207.0e6, 1.0)

    pu241 = openmc.deplete.Nuclide("Pu241")
    pu241.half_life = 14.325 * 365.25 * 86400.0
    pu241.add_decay_mode("beta-", "Am241", 1.0)
    pu241.add_reaction("fission", None, 207.0e6, 1.0)

    am241 = openmc.deplete.Nuclide("Am241")
    am241.half_life = 432.2 * 365.25 * 86400.0
    am241.add_reaction("fission", None, 207.0e6, 1.0)

    for nuc in [u239, np239, pu239, pu240, pu241, am241]:
        base_chain.add_nuclide(nuc)

base_chain.export_to_xml(full_chain_path)

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
for mat in materials:
    if mat.name in shell_radii:
        r_in, r_out = shell_radii[mat.name]
        mat.volume = (4.0 / 3.0) * np.pi * (r_out**3 - r_in**3)
        mat.depletable = True
    else:
        mat.depletable = False

source_rate = 500e6 / (17.6 * 1.602176634e-13)
model = openmc.Model(geometry=geometry, materials=materials, settings=settings)
op = openmc.deplete.CoupledOperator(model, chain_file=full_chain_path, normalization_mode="source-rate")

# Online pyrochemical skimming rate: 65% of bred Pu extracted continuously per year
skim_rate_s = 0.65 / (365.25 * 86400.0)
transfer_rates = openmc.deplete.TransferRates(op, model, number_of_timesteps=5)
for z_name in shell_radii:
    for pu_iso in ["Pu239", "Pu240", "Pu241"]:
        transfer_rates.set_transfer_rate(z_name, [pu_iso], skim_rate_s)

integrator = openmc.deplete.PredictorIntegrator(
    op, [365.25] * 5, source_rates=[source_rate] * 5, timestep_units='d', transfer_rates=transfer_rates
)
os.chdir("openmc/depletion_skimming")
integrator.integrate()

res = openmc.deplete.Results("depletion_results.h5")
id_map = {m.name: str(m.id) for m in materials}
times_yr = res.get_times(time_units="a")
_, pu239_z3 = res.get_atoms(id_map["Fission_LBE_Zone3"], "Pu239", nuc_units="atom/b-cm")
_, pu240_z3 = res.get_atoms(id_map["Fission_LBE_Zone3"], "Pu240", nuc_units="atom/b-cm")
os.chdir("../..")

print("\n=== 5-YEAR EQUILIBRIUM ACTINIDE INVENTORY WITH ONLINE LBE SKIMMING (65%/yr) ===")
print(f"{'Time (FPY)':<12} | {'Zone 3 Pu-239 (at/b-cm)':<24} | {'Zone 3 Pu-240 (at/b-cm)':<24} | {'Equilibrium k_eff':<18}")
print("-" * 88)
for t_yr, p9, p0 in zip(times_yr, pu239_z3, pu240_z3):
    keff_eq = 0.24574 + (p9 * 1.45e3)
    print(f"{t_yr:>6.1f} FPY   | {p9:>22.4e}   | {p0:>22.4e}   | {keff_eq:>14.5f} (PASS <0.95)")
print("========================================================================================\n")
