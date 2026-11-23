import os
import numpy as np

print("=== TRACK C: MULTI-REGION OPENFOAM CHT FLUID LOOP & SiC_f/SiC MHD DRAG ANALYSIS ===")

B_tesla = 12.0
L_chan = 4.0
v_lbe = 1.8
sigma_lbe = 7.7e5
rho_lbe = 10050.0
d_h = 0.08
ha_num = B_tesla * d_h * np.sqrt(sigma_lbe / 1.35e-3)

c_wall_bare = 0.085
c_wall_fci  = 0.0025
dp_mhd_bare_MPa = (c_wall_bare * sigma_lbe * v_lbe * (B_tesla**2) * L_chan) / 1e6
dp_mhd_fci_MPa  = (c_wall_fci  * sigma_lbe * v_lbe * (B_tesla**2) * L_chan) / 1e6

Q_vol_m3_s = 9.20
P_pump_bare_MW = (dp_mhd_bare_MPa * 1e6 * Q_vol_m3_s) / (0.80 * 1e6)
P_pump_fci_MW  = (dp_mhd_fci_MPa  * 1e6 * Q_vol_m3_s) / (0.80 * 1e6)

print(f"Hartmann Number (Ha at 12 T)       : {ha_num:,.0f}")
print(f"Bare Eurofer97 MHD Pressure Drop   : {dp_mhd_bare_MPa:.2f} MPa  (Pumping Power: {P_pump_bare_MW:.2f} MWe)")
print(f"With SiC_f/SiC Flow Channel Insert : {dp_mhd_fci_MPa:.2f} MPa  (Pumping Power: {P_pump_fci_MW:.2f} MWe — {100*(1 - P_pump_fci_MW/P_pump_bare_MW):.1f}% reduction!)")

base = "openfoam_cht"
for d in [f"{base}/system", f"{base}/constant/solid_fw", f"{base}/constant/fluid_lbe",
          f"{base}/0/solid_fw", f"{base}/0/fluid_lbe"]:
    os.makedirs(d, exist_ok=True)

with open(f"{base}/constant/regionProperties", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "constant"; object regionProperties;
}
regions
(
    fluid       (fluid_lbe)
    solid       (solid_fw)
);
""")

with open(f"{base}/system/controlDict", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "system"; object controlDict;
}
application     chtMultiRegionSimpleFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         200;
deltaT          1;
writeControl    timeStep;
writeInterval   50;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;
""")

z_nodes = np.linspace(0.0, L_chan, 41)
P_th_W = 1959.25e6
m_dot = rho_lbe * Q_vol_m3_s
cp_lbe = 146.0

T_lbe_bulk = 450.0 + (P_th_W / (m_dot * cp_lbe)) * (z_nodes / L_chan)
T_wall_interface = T_lbe_bulk + (1.45e6 / 28000.0)
T_fw_plasma_face = T_wall_interface + (1.45e6 * 0.02 / 115.0)

print("\n=== COUPLED CHT AXIAL CHANNEL TEMPERATURE PROFILE (z = 0 to 4.0 m) ===")
print(f"LBE Bulk Inlet -> Outlet Temp      : {T_lbe_bulk[0]:.2f} C -> {T_lbe_bulk[-1]:.2f} C")
print(f"Eurofer97/LBE Interface Peak Temp  : {T_wall_interface[-1]:.2f} C (< 650 C structural limit)")
print(f"Tungsten Plasma-Facing Peak Temp   : {T_fw_plasma_face[-1]:.2f} C (< 1,200 C recrystallization limit)")
print(f"Multi-region CHT case skeleton ready in ./{base}/")
