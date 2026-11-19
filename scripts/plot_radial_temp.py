import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("=== GENERATING 1D RADIAL TEMPERATURE PROFILE PLOT (6.0 CM BE MULTIPLIER) ===")

coords = np.linspace(-48.0, 48.0, 25)
X, Y, Z = np.meshgrid(coords, coords, coords, indexing='ij')
R = np.sqrt(X**2 + Y**2 + Z**2)

q_3d = np.loadtxt('openfoam/constant/heatSource').reshape((25, 25, 25))
q_mw_m3 = q_3d / 1e6

# Solve 3D steady-state conduction + LBE convective cooling at ~1,955 MWth
k_eff = 14.5
T_cool = 450.0
h_vol = 1.38e7  # Scaled convective LBE flow rate for M=4.64x thermal load
dx = 0.04

T = np.full((25, 25, 25), T_cool, dtype=float)
alpha = k_eff / (dx**2)
denom = 6.0 * alpha + h_vol

for _ in range(400):
    T_pad = np.pad(T, 1, mode='edge')
    lap_neighbors = (
        T_pad[2:, 1:-1, 1:-1] + T_pad[:-2, 1:-1, 1:-1] +
        T_pad[1:-1, 2:, 1:-1] + T_pad[1:-1, :-2, 1:-1] +
        T_pad[1:-1, 1:-1, 2:] + T_pad[1:-1, 1:-1, :-2]
    )
    T = (alpha * lap_neighbors + q_3d + h_vol * T_cool) / denom

R_flat = R.flatten()
T_flat = T.flatten()
q_flat = q_mw_m3.flatten()

r_edges = np.linspace(0.0, 50.0, 26)
r_centers = 0.5 * (r_edges[:-1] + r_edges[1:])
T_mean, T_min, T_max, q_mean = [], [], [], []

for i in range(len(r_centers)):
    mask = (R_flat >= r_edges[i]) & (R_flat < r_edges[i+1])
    if np.any(mask):
        T_mean.append(np.mean(T_flat[mask]))
        T_min.append(np.min(T_flat[mask]))
        T_max.append(np.max(T_flat[mask]))
        q_mean.append(np.mean(q_flat[mask]))
    else:
        T_mean.append(np.nan)
        T_min.append(np.nan)
        T_max.append(np.nan)
        q_mean.append(np.nan)

T_mean, T_min, T_max, q_mean = map(np.array, (T_mean, T_min, T_max, q_mean))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 7.5), sharex=True, gridspec_kw={'height_ratios': [2.2, 1]})

ax1.axvspan(0, 30, color='#e0f2fe', alpha=0.45, label='Stage 1: Plasma Void (0–30 cm)')
ax1.axvspan(30, 32, color='#94a3b8', alpha=0.55, label='Tungsten First Wall (30–32 cm)')
ax1.axvspan(32, 38, color='#bbf7d0', alpha=0.60, label='Beryllium (n,2n) Multiplier (32–38 cm)')
ax1.axvspan(38, 46, color='#fef3c7', alpha=0.55, label='Stage 2 Zone 1: 7 wt% U-LBE (38–46 cm)')
ax1.axvspan(46, 50, color='#fde68a', alpha=0.65, label='Stage 2 Zone 2: 14 wt% U-LBE (46–50 cm)')

for span_a, span_b, col in [(0, 30, '#e0f2fe'), (30, 32, '#94a3b8'), (32, 38, '#bbf7d0'), (38, 46, '#fef3c7'), (46, 50, '#fde68a')]:
    ax2.axvspan(span_a, span_b, color=col, alpha=0.55)

ax1.plot(r_centers, T_mean, color='#dc2626', linewidth=2.5, marker='o', markersize=5, label='Shell Mean Temperature (°C)')
ax1.fill_between(r_centers, T_min, T_max, color='#dc2626', alpha=0.15, label='Min–Max Shell Envelope')

ax1.axhline(650.0, color='#7f1d1d', linestyle='--', linewidth=1.8, label='Eurofer97 Creep Limit (650 °C)')
ax1.axhline(450.0, color='#0369a1', linestyle=':', linewidth=1.8, label='LBE Coolant Inlet (450 °C)')

ax1.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold')
ax1.set_title('F-F-F Hybrid Blanket (6.0 cm Be Multiplier, M=4.64x): 1D Radial Temperature & Heating Profile', fontsize=12, fontweight='bold', pad=12)
ax1.set_ylim(420, 685)
ax1.grid(True, linestyle='--', alpha=0.4)
ax1.legend(loc='upper left', fontsize=8.2, ncol=2, framealpha=0.92)

ax2.step(r_centers, q_mean, where='mid', color='#d97706', linewidth=2.3, label='Nuclear Heating Density (MW/m³)')
ax2.fill_between(r_centers, 0, q_mean, step='mid', color='#f59e0b', alpha=0.25)
ax2.set_xlabel('Radial Distance from Plasma Centerline, r (cm)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Power Density\n(MW/m³)', fontsize=10.5, fontweight='bold')
ax2.set_xlim(0, 50)
ax2.grid(True, linestyle='--', alpha=0.4)
ax2.legend(loc='upper left', fontsize=8.5)

plt.tight_layout()
out_file = 'results/radial_temp_profile.png'
plt.savefig(out_file, dpi=300)
print(f"Saved updated 1D radial temperature profile plot to {out_file}")
print(f"Min Blanket Temp : {np.min(T_flat):.2f} C")
print(f"Mean Blanket Temp: {np.mean(T_flat):.2f} C")
print(f"Peak Blanket Temp: {np.max(T_flat):.2f} C (Margin below 650 C Eurofer97 limit: {650.0 - np.max(T_flat):.2f} C)")
