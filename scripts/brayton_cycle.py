import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("=== F-F-F HYBRID REACTOR: sCO2 BRAYTON CYCLE & (Q_plasma vs. M) OPERATING ENVELOPE ===")

# 1. Baseline Design Point (from OpenMC + OpenFOAM runs)
P_fusion_MW = 500.0          # Stage 1 D-T Tokamak fusion power
Q_base = 2.0                 # Low-Q driven tokamak plasma gain
M_base = 3.17                # Current graded Stage 2+3 blanket multiplication (44.69 / 14.1 MeV)
T_lbe_out_C = 631.62         # Peak cooled blanket temp (18.38 C margin below 650 C Eurofer97 limit)
T_sink_C = 32.0              # CO2 compressor inlet temp

# Recompression sCO2 Brayton Cycle Thermodynamics
T_turb_in_K = (T_lbe_out_C - 15.0) + 273.15
T_comp_in_K = T_sink_C + 273.15
eta_carnot = 1.0 - (T_comp_in_K / T_turb_in_K)
eta_thermal_gross = 0.72 * eta_carnot  # ~47.31%

def evaluate_plant(Q_val, M_val):
    # Total thermal power: 80% of D-T fusion (400 MW neutron power) is multiplied by M, plus 20% alpha heating (100 MW)
    P_th = (0.80 * P_fusion_MW * M_val) + (0.20 * P_fusion_MW)
    P_gross_e = P_th * eta_thermal_gross

    # Parasitic loads (MWe)
    P_aux_heat = (P_fusion_MW / Q_val) / 0.55   # RF/NBI wall-plug efficiency = 55%
    P_fixed_parasitic = 12.0 + 8.5 + 4.2 + 15.0 # REBCO cryo + LBE/FliBe EM pumps + BOP = 39.7 MWe
    P_parasitic = P_aux_heat + P_fixed_parasitic

    P_net_e = P_gross_e - P_parasitic
    eta_net = (P_net_e / P_th) * 100.0
    Q_eng = P_gross_e / P_parasitic
    return P_th, P_gross_e, P_net_e, eta_net, Q_eng

# Print baseline point
p_th0, p_g0, p_n0, eta0, qeng0 = evaluate_plant(Q_base, M_base)
print(f"Baseline Point (Q={Q_base:.1f}, M={M_base:.2f}x): Thermal={p_th0:.2f} MWth | Gross={p_g0:.2f} MWe | Net={p_n0:.2f} MWe | Q_eng={qeng0:.2f}x\n")

# 2. Parametric Matrix Table: Q_plasma vs. Blanket Multiplication M
Q_list = [1.5, 2.0, 3.0, 4.0, 5.0]
M_list = [2.5, 3.17, 4.5, 6.0, 8.0]

header = f"{'Q_plasma \\ M':<12} | " + " | ".join([f"M = {m:<5.2f}x" for m in M_list])
print("=== NET PLANT ELECTRICAL OUTPUT (MWe) MATRIX [500 MW Fusion Driver] ===")
print(header)
print("-" * len(header))
for q in Q_list:
    row_vals = []
    for m in M_list:
        _, _, p_net, _, _ = evaluate_plant(q, m)
        tag = "*" if (abs(q - Q_base) < 1e-3 and abs(m - M_base) < 1e-2) else " "
        row_vals.append(f"{p_net:>7.1f}{tag}")
    print(f"Q = {q:<8.1f} | " + " | ".join(row_vals))
print("(* = Current graded F-F-F simulation baseline; target >= 300 MWe commercial grid output)\n")

# 3. Generate 2D Contour Plot of Net Electrical Output (MWe)
Q_grid = np.linspace(1.2, 6.0, 120)
M_grid = np.linspace(2.0, 9.0, 120)
QQ, MM = np.meshgrid(Q_grid, M_grid)
_, _, PP_net, _, _ = evaluate_plant(QQ, MM)

fig, ax = plt.subplots(figsize=(9.5, 6.5))
levels = np.arange(-100, 1401, 100)
cf = ax.contourf(QQ, MM, PP_net, levels=levels, cmap='RdYlGn', extend='both')
cbar = plt.colorbar(cf, ax=ax)
cbar.set_label('Net Grid Electrical Output (MWe)', fontsize=11, fontweight='bold')

# Key operational threshold contours
cs_zero = ax.contour(QQ, MM, PP_net, levels=[0.0], colors='black', linestyles='--', linewidths=1.8)
ax.clabel(cs_zero, fmt='Break-Even (0 MWe)', fontsize=9.5)

cs_300 = ax.contour(QQ, MM, PP_net, levels=[300.0], colors='#1d4ed8', linestyles='-', linewidths=2.3)
ax.clabel(cs_300, fmt='Commercial Target (300 MWe)', fontsize=10)

cs_600 = ax.contour(QQ, MM, PP_net, levels=[600.0], colors='#065f46', linestyles='-.', linewidths=1.8)
ax.clabel(cs_600, fmt='600 MWe', fontsize=9.5)

# Plot current baseline design point & recommended upgrade target
ax.scatter([Q_base], [M_base], color='#dc2626', edgecolor='black', s=120, zorder=5, label=f'Current Baseline (Q=2.0, M=3.17x -> {p_n0:.1f} MWe)')
_, _, p_opt, _, _ = evaluate_plant(3.5, 4.5)
ax.scatter([3.5], [4.5], color='#2563eb', edgecolor='white', marker='*', s=220, zorder=6, label=f'Target Upgrade (Q=3.5, M=4.50x -> {p_opt:.1f} MWe)')

ax.set_title('F-F-F Hybrid Plant Operating Envelope: Plasma Gain (Q) vs. Blanket Multiplication (M)', fontsize=12, fontweight='bold', pad=12)
ax.set_xlabel('Stage 1 Tokamak Plasma Gain, Q_plasma (P_fusion / P_aux)', fontsize=11, fontweight='bold')
ax.set_ylabel('Stage 2 Blanket Energy Multiplication Factor, M', fontsize=11, fontweight='bold')
ax.grid(True, linestyle=':', alpha=0.45)
ax.legend(loc='upper right', fontsize=9.5, framealpha=0.92)

plt.tight_layout()
out_png = 'results/q_vs_m_operating_envelope.png'
plt.savefig(out_png, dpi=300)
print(f"Saved Q vs. M operating envelope contour plot to {out_png}")
