import os
import re
import subprocess
import numpy as np
import openmc

print("=== STEP 1 & 2: 3D OPENMC HEATING COUPLING + kOmegaSST TURBULENT CHT SOLVER ===")

# 1. Extract 3D Toroidal Nuclear Heating from OpenMC Statepoint (if present)
sp_path = "openmc/toroidal_tbr_opt/statepoint.15.h5"
if os.path.exists(sp_path):
    with openmc.StatePoint(sp_path) as sp:
        mev_per_src = sp.get_tally(name='heat_3d').mean.sum() / 1e6
    # Scale to 500 MW D-T driver (1.773e20 n/s) across Stage 2 LBE volume (~35.4 m^3)
    p_th_mw = 500.0 * (mev_per_src / 17.6)
    q_vol_mw_m3 = p_th_mw / 35.4
    # Specific enthalpy source h_spec = q_vol / rho_lbe (W/kg)
    h_spec_source = (q_vol_mw_m3 * 1e6) / 10050.0
    print(f"Mapped 3D OpenMC Tally ({mev_per_src:.2f} MeV/n -> {p_th_mw:.1f} MWth): Specific Source = {h_spec_source:.1f} W/kg")
else:
    h_spec_source = 5350.0
    print(f"Using baseline specific source: {h_spec_source:.1f} W/kg")

base = "openfoam_cht"
os.makedirs(f"{base}/0/fluid_lbe", exist_ok=True)
os.makedirs(f"{base}/constant/fluid_lbe", exist_ok=True)

# 2. Switch fluid_lbe to RAS kOmegaSST Turbulence (OpenFOAM v2412 momentumTransport + turbulenceProperties)
for fname in ["turbulenceProperties", "momentumTransport"]:
    with open(f"{base}/constant/fluid_lbe/{fname}", "w") as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "constant/fluid_lbe"; object """ + fname + """;
}
simulationType  RAS;
RAS
{
    model           kOmegaSST;
    turbulence      on;
    printCoeffs     on;
}
""")

# 3. Create Turbulent Boundary Fields (k, omega, nut, alphat) in 0/fluid_lbe/
with open(f"{base}/0/fluid_lbe/k", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class volScalarField; location "0/fluid_lbe"; object k;
}
dimensions [0 2 -2 0 0 0 0];
internalField uniform 0.02;
boundaryField
{
    inlet       { type fixedValue; value uniform 0.02; }
    outlet      { type zeroGradient; }
    outer_wall  { type kqRWallFunction; value uniform 0.02; }
    sides       { type symmetry; }
    "fluid_lbe_to_.*" { type kqRWallFunction; value uniform 0.02; }
}
""")

with open(f"{base}/0/fluid_lbe/omega", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class volScalarField; location "0/fluid_lbe"; object omega;
}
dimensions [0 0 -1 0 0 0 0];
internalField uniform 15.0;
boundaryField
{
    inlet       { type fixedValue; value uniform 15.0; }
    outlet      { type zeroGradient; }
    outer_wall  { type omegaWallFunction; value uniform 15.0; }
    sides       { type symmetry; }
    "fluid_lbe_to_.*" { type omegaWallFunction; value uniform 15.0; }
}
""")

with open(f"{base}/0/fluid_lbe/nut", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class volScalarField; location "0/fluid_lbe"; object nut;
}
dimensions [0 2 -1 0 0 0 0];
internalField uniform 1e-4;
boundaryField
{
    inlet       { type calculated; value uniform 1e-4; }
    outlet      { type calculated; value uniform 1e-4; }
    outer_wall  { type nutkWallFunction; value uniform 1e-4; }
    sides       { type symmetry; }
    "fluid_lbe_to_.*" { type nutkWallFunction; value uniform 1e-4; }
}
""")

with open(f"{base}/0/fluid_lbe/alphat", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class volScalarField; location "0/fluid_lbe"; object alphat;
}
dimensions [1 -1 -1 0 0 0 0];
internalField uniform 5.0;
boundaryField
{
    inlet       { type calculated; value uniform 5.0; }
    outlet      { type calculated; value uniform 5.0; }
    outer_wall  { type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 5.0; }
    sides       { type symmetry; }
    "fluid_lbe_to_.*" { type compressible::alphatJayatillekeWallFunction; Prt 0.85; value uniform 5.0; }
}
""")

# 4. Update fvOptions with Mapped 3D OpenMC Specific Volumetric Heating
with open(f"{base}/constant/fluid_lbe/fvOptions", "w") as f:
    f.write(f"""FoamFile
{{
    version 2.0; format ascii; class dictionary; location "constant/fluid_lbe"; object fvOptions;
}}
nuclearBlanketHeating
{{
    type            scalarSemiImplicitSource;
    active          true;
    scalarSemiImplicitSourceCoeffs
    {{
        selectionMode   all;
        volumeMode      specific;
        sources
        {{
            h
            {{
                explicit    {h_spec_source:.2f};
                implicit    0.0;
            }}
        }}
    }}
}}
""")

# 5. Update fluid_lbe fvSchemes & fvSolution for k and omega
with open(f"{base}/system/fluid_lbe/fvSchemes", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "system/fluid_lbe"; object fvSchemes;
}
ddtSchemes      { default steadyState; }
gradSchemes     { default Gauss linear; }
divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss upwind;
    div(phi,h)      bounded Gauss upwind;
    div(phi,K)      bounded Gauss upwind;
    div(phi,k)      bounded Gauss upwind;
    div(phi,omega)  bounded Gauss upwind;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear orthogonal; }
interpolationSchemes { default linear; }
snGradSchemes   { default orthogonal; }
wallDist        { method meshWave; }
""")

with open(f"{base}/system/fluid_lbe/fvSolution", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "system/fluid_lbe"; object fvSolution;
}
solvers
{
    p_rgh
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-7;
        relTol          0.01;
    }
    "(U|h|k|omega)"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-7;
        relTol          0.1;
    }
}
SIMPLE
{
    momentumPredictor   yes;
    nNonOrthogonalCorrectors 0;
    pRefCell            0;
    pRefValue           1e5;
}
relaxationFactors
{
    fields      { p_rgh 0.3; rho 1.0; }
    equations   { U 0.7; h 0.5; k 0.5; omega 0.5; }
}
""")

# Remove old laminar timestep folder 60 and run turbulent chtMultiRegionSimpleFoam
subprocess.run(["rm", "-rf", f"{base}/60"], check=True)
subprocess.run(["chtMultiRegionSimpleFoam"], cwd=base, stdout=subprocess.DEVNULL, check=True)
subprocess.run(["foamToVTK", "-region", "fluid_lbe"], cwd=base, stdout=subprocess.DEVNULL, check=True)
subprocess.run(["foamToVTK", "-region", "solid_fw"], cwd=base, stdout=subprocess.DEVNULL, check=True)

def read_field_stats(path):
    with open(path) as f:
        txt = f.read()
    m = re.search(r'internalField\s+nonuniform\s+List<scalar>\s+\d+\s*\((.*?)\)', txt, re.S)
    vals = np.fromstring(m.group(1), sep='\n')
    return vals.min() - 273.15, vals.mean() - 273.15, vals.max() - 273.15

lbe_min, lbe_mean, lbe_max = read_field_stats(f"{base}/60/fluid_lbe/T")
fw_min, fw_mean, fw_max = read_field_stats(f"{base}/60/solid_fw/T")

print("=========================================================================")
print(f"3D Turbulent CHT Fluid LBE Temp (Min / Mean / Max) : {lbe_min:.2f} C / {lbe_mean:.2f} C / {lbe_max:.2f} C")
print(f"3D Turbulent CHT Solid FW  Temp (Min / Mean / Max) : {fw_min:.2f} C / {fw_mean:.2f} C / {fw_max:.2f} C")
print(f"Tungsten Recrystallization Margin (< 1,200 C)      : {1200.0 - fw_max:+.2f} C")
print("Exported updated turbulent CHT VTK files to openfoam_cht/VTK/")
print("=========================================================================\n")
