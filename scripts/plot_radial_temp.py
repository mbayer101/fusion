import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("=== GENERATING 1D RADIAL TEMPERATURE PROFILE PLOT ===")

# 1. Reconstruct 25x25x25 OpenFOAM blockMesh cell centers (-48 to +48 cm)
coords = np.linspace(-48.0, 48.0, 25)
X, Y, Z = np.meshgrid(coords, coords, coords, indexing='ij')
R = np.sqrt(X**2 + Y**2 + Z**2)

# 2. Load exact 3D spatially mapped nuclear heating from OpenMC (W/m^3)
q_3d = np.loadtxt('openfoam/constant/heatSource').reshape((25, 25, 25))
q_mw_m3 = q_3d / 1e6

# 3. Solve 3D steady-state conduction + LBE convective cooling:
#    k_eff * nabla^2(T) + q'''(r) - h_vol * (T - T_cool) = 0
#    LBE effective conductivity k_eff = 14.5 W/(m*K), T_coolant = 450.0 C
#    Volumetric convective heat removal coefficient h_vol = 6.85e6 W/(m^3*K)
k_eff = 14.5
T_cool = 450.0
h_vol = 6.85e6
dx = 0.04  # 4 cm cell spacing in meters

# Jacobi/SOR relaxation to exact steady-state thermal equilibrium
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

# 4. Bin cells radially from r = 0 to 50 cm
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

T_mean = np.array(T_mean)
T_min = np.array(T_min)
T_max = np.array(T_max)
q_mean = np.array(q_mean)

# 5. Create 2-panel engineering plot (Temperature Profile + Flattened Power Density)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, gridspec_kw={'height_ratios': [2.2, 1]})

ax1.axvspan(0, 30, color='#e0f2fe', alpha=0.45, label='Stage 1: Plasma Void (0–30 cm)')
ax1.axvspan(30, 32, color='#94a3b8', alpha=0.55, label='Tungsten First Wall (30–32 cm)')
ax1.axvspan(32, 40, color='#fef3c7', alpha=0.55, label='Stage 2 Zone 1: 7 wt% U-LBE (32–40 cm)')
ax1.axvspan(40, 50, color='#fde68a', alpha=0.65, label='Stage 2 Zone 2: 14 wt% U-LBE (40–50 cm)')

ax2.axvspan(0, 30, color='#e0f2fe', alpha=0.45)
ax2.axvspan(30, 32, color='#94a3b8', alpha=0.55)
ax2.axvspan(32, 40, color='#fef3c7', alpha=0.55)
ax2.axvspan(40, 50, color='#fde68a', alpha=0.65)

ax1.plot(r_centers, T_mean, color='#dc2626', linewidth=2.5, marker='o', markersize=5, label='Shell Mean Temperature (°C)')
ax1.fill_between(r_centers, T_min, T_max, color='#dc2626', alpha=0.15, label='Min–Max Shell Envelope')

ax1.axhline(650.0, color='#7f1d1d', linestyle='--', linewidth=1.8, label='Eurofer97 Creep Limit (650 °C)')
ax1.axhline(450.0, color='#0369a1', linestyle=':', linewidth=1.8, label='LBE Coolant Inlet (450 °C)')

ax1.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold')
ax1.set_title('F-F-F Hybrid Blanket: 1D Radial Temperature & Flattened Heating Profile (500 MW Fusion)', fontsize=12.5, fontweight='bold', pad=12)
ax1.set_ylim(420, 685)
ax1.grid(True, linestyle='--', alpha=0.4)
ax1.legend(loc='upper left', fontsize=8.5, ncol=2, framealpha=0.92)

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
print(f"Saved 1D radial temperature profile plot to {out_file}")
print(f"Min Blanket Temp : {np.min(T_flat):.2f} C")
print(f"Mean Blanket Temp: {np.mean(T_flat):.2f} C")
print(f"Peak Blanket Temp: {np.max(T_flat):.2f} C (Margin below 650 C Eurofer97 limit: {650.0 - np.max(T_flat):.2f} C)")
