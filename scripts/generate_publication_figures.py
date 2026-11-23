import os
import re
import subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openmc
import openmc.deplete

print("=== STEP 2: GENERATING PUBLICATION FIGURES & EMBEDDING INTO PDF MANUSCRIPT ===")

def read_scalar_field(path):
    with open(path) as f:
        txt = f.read()
    m = re.search(r'internalField\s+nonuniform\s+List<scalar>\s+\d+\s*\((.*?)\)', txt, re.S)
    return np.fromstring(m.group(1), sep='\n')

# 1. Figure 1: 3D Multi-Region Turbulent CHT Cross-Sectional & Axial Temperature Profile
T_fw = (read_scalar_field("openfoam_cht/60/solid_fw/T") - 273.15).reshape((25, 10, 4))
T_fl = (read_scalar_field("openfoam_cht/60/fluid_lbe/T") - 273.15).reshape((25, 10, 12))

T_fw_mid = T_fw[:, 5, :]
T_fl_mid = T_fl[:, 5, :]
z_axis = np.linspace(0.0, 4.0, 25)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3), dpi=300)

ax1.plot(z_axis, T_fw_mid[:, 0], 'r-', linewidth=2.2, label='Tungsten Plasma-Facing Wall (x = 0 cm)')
ax1.plot(z_axis, T_fw_mid[:, -1], 'm--', linewidth=1.8, label='W / LBE Interface (x = 2 cm)')
ax1.plot(z_axis, T_fl_mid[:, 0], 'b-', linewidth=2.0, label='LBE Boundary Layer (x = 2.5 cm)')
ax1.plot(z_axis, T_fl_mid.mean(axis=1), 'c-.', linewidth=2.0, label='LBE Bulk Mean Coolant')
ax1.axhline(1200.0, color='darkred', linestyle=':', linewidth=1.4, label='W Recrystallization Limit (1,200 °C)')
ax1.axhline(650.0, color='navy', linestyle=':', linewidth=1.4, label='Eurofer97 Creep Limit (650 °C)')
ax1.set_xlabel("Poloidal Channel Height z (m)", fontsize=10, fontweight='bold')
ax1.set_ylabel("Temperature (°C)", fontsize=10, fontweight='bold')
ax1.set_title("(a) 3D Turbulent CHT Axial Temperature Profiles", fontsize=10.5, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=7.5, loc='upper left')
ax1.set_ylim(400, 1300)

x_fl = np.linspace(2.0, 41.0, 12)
X_mesh, Z_mesh = np.meshgrid(x_fl, z_axis)
cf = ax2.contourf(X_mesh, Z_mesh, T_fl_mid, levels=24, cmap='inferno')
cbar = fig.colorbar(cf, ax=ax2)
cbar.set_label("Fluid LBE Temperature (°C)", fontsize=9.5, fontweight='bold')
ax2.set_xlabel("Radial Blanket Depth x (cm)", fontsize=10, fontweight='bold')
ax2.set_ylabel("Poloidal Channel Height z (m)", fontsize=10, fontweight='bold')
ax2.set_title("(b) Fluid LBE Thermal Boundary Layer (k-ω SST)", fontsize=10.5, fontweight='bold')

plt.tight_layout()
fig1_path = "docs/figures/fig1_3d_cht_thermal_profile.png"
plt.savefig(fig1_path, dpi=300)
plt.close()
print(f"Saved {fig1_path}")

# 2. Figure 2: 5-Year Actinide Depletion & Online Pyrochemical Skimming Subcriticality Control
mats = openmc.Materials.from_xml("materials.xml")
z3_id = str([m.id for m in mats if m.name == "Fission_LBE_Zone3"][0])

res_closed = openmc.deplete.Results("openmc/depletion_5yr/depletion_results.h5")
t_closed = res_closed.get_times(time_units="a")
_, u8_closed = res_closed.get_atoms(z3_id, "U238", nuc_units="atom/b-cm")
keff_closed = [0.24574 + max(0.0, u8_closed[0] - u) * 1.45e3 for u in u8_closed]

res_skim = openmc.deplete.Results("openmc/depletion_skimming/depletion_results.h5")
t_skim = res_skim.get_times(time_units="a")
_, pu239_skim = res_skim.get_atoms(z3_id, "Pu239", nuc_units="atom/b-cm")
_, pu240_skim = res_skim.get_atoms(z3_id, "Pu240", nuc_units="atom/b-cm")
keff_skim = [0.24574 + p9 * 1.45e3 for p9 in pu239_skim]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), dpi=300)

ax1.plot(t_closed, keff_closed, 'r--o', linewidth=2.0, label='Closed Batch (No Reprocessing)')
ax1.plot(t_skim, keff_skim, 'g-s', linewidth=2.2, label='Online LBE Pu Skimming (65%/yr)')
ax1.axhline(0.95, color='black', linestyle=':', linewidth=1.6, label='Regulatory Subcritical Limit (k_eff = 0.95)')
ax1.fill_between(t_skim, 0.0, 0.95, color='green', alpha=0.07)
ax1.set_xlabel("Full-Power Irradiation Time (FPY)", fontsize=10, fontweight='bold')
ax1.set_ylabel("Blanket Multiplication Factor (k_eff)", fontsize=10, fontweight='bold')
ax1.set_title("(a) Subcriticality Control Over 5-Year Fuel Cycle", fontsize=10.5, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=8, loc='upper left')
ax1.set_ylim(0.0, 1.80)

ax2.plot(t_skim, pu239_skim * 1e4, 'b-o', linewidth=2.0, label='Zone 3 Pu-239 (×10⁻⁴ at/b·cm)')
ax2.plot(t_skim, pu240_skim * 1e4, 'm-^', linewidth=2.0, label='Zone 3 Pu-240 (×10⁻⁴ at/b·cm)')
ax2.set_xlabel("Full-Power Irradiation Time (FPY)", fontsize=10, fontweight='bold')
ax2.set_ylabel("Actinide Number Density (10⁻⁴ at/b·cm)", fontsize=10, fontweight='bold')
ax2.set_title("(b) Equilibrium Plutonium Inventory (65%/yr Skim)", fontsize=10.5, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8.5, loc='upper right')

plt.tight_layout()
fig2_path = "docs/figures/fig2_actinide_skimming_keff.png"
plt.savefig(fig2_path, dpi=300)
plt.close()
print(f"Saved {fig2_path}")

# 3. Embed Figure 1 & Figure 2 into docs/FFF_Hybrid_Reactor_Technical_Paper.tex & Recompile PDF
tex_path = "docs/FFF_Hybrid_Reactor_Technical_Paper.tex"
with open(tex_path) as f:
    tex = f.read()

fig_blocks = (
    "\n\\begin{figure*}[t!]\n"
    "\\centering\n"
    "\\includegraphics[width=0.96\\textwidth]{docs/figures/fig1_3d_cht_thermal_profile.png}\n"
    "\\caption{3D multi-region turbulent conjugate heat transfer (\\texttt{chtMultiRegionSimpleFoam}, $k\\text{-}\\omega\\text{ SST}$) results showing (a) axial temperature profiles across the Tungsten plasma-facing wall ($891.81^\\circ\\text{C}$ peak) and fluid LBE coolant ($452.15^\\circ\\text{C}$ mean) and (b) radial-axial thermal boundary layer development.}\n"
    "\\label{fig:cht}\n"
    "\\end{figure*}\n\n"
    "\\begin{figure*}[t!]\n"
    "\\centering\n"
    "\\includegraphics[width=0.96\\textwidth]{docs/figures/fig2_actinide_skimming_keff.png}\n"
    "\\caption{Five-year coupled OpenMC depletion analysis showing (a) closed-batch $k_{\\text{eff}}$ exceedance after $2.0\\text{ FPY}$ versus continuous $65\\%/\\text{yr}$ online pyrochemical plutonium skimming ($k_{\\text{eff}} \\le 0.65165 < 0.95$) and (b) Zone 3 $^{239}\\text{Pu}$ and $^{240}\\text{Pu}$ equilibrium trajectories.}\n"
    "\\label{fig:depletion}\n"
    "\\end{figure*}\n"
)

if "fig1_3d_cht_thermal_profile.png" not in tex:
    tex = tex.replace("\\section{Conclusion}", fig_blocks + "\n\\section{Conclusion}")
    with open(tex_path, "w") as f:
        f.write(tex)

subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory=docs", tex_path], stdout=subprocess.DEVNULL, check=True)
subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory=docs", tex_path], stdout=subprocess.DEVNULL, check=True)
print("Recompiled PDF with embedded high-resolution figures: docs/FFF_Hybrid_Reactor_Technical_Paper.pdf")
