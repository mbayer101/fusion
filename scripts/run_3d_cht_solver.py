import os
import re
import subprocess
import numpy as np

print("=== STEP 1: 3D MULTI-REGION OPENFOAM CHT (chtMultiRegionSimpleFoam) EXECUTION ===")

base = "openfoam_cht"
subprocess.run(["rm", "-rf", base], check=True)

dirs = [
    f"{base}/system",
    f"{base}/system/solid_fw",
    f"{base}/system/fluid_lbe",
    f"{base}/constant",
    f"{base}/constant/solid_fw",
    f"{base}/constant/fluid_lbe",
    f"{base}/0/solid_fw",
    f"{base}/0/fluid_lbe",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# 1. regionProperties & controlDict
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
endTime         60;
deltaT          1;
writeControl    timeStep;
writeInterval   60;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable false;
""")

# Global fvSchemes & fvSolution (required by splitMeshRegions & solver)
for region in ["", "solid_fw/", "fluid_lbe/"]:
    with open(f"{base}/system/{region}fvSchemes", "w") as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "system"; object fvSchemes;
}
ddtSchemes      { default steadyState; }
gradSchemes     { default Gauss linear; }
divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss upwind;
    div(phi,h)      bounded Gauss upwind;
    div(phi,K)      bounded Gauss upwind;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear orthogonal; }
interpolationSchemes { default linear; }
snGradSchemes   { default orthogonal; }
""")
    with open(f"{base}/system/{region}fvSolution", "w") as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "system"; object fvSolution;
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
    "(U|h|T)"
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
    equations   { U 0.7; h 0.5; T 0.8; }
}
""")

# 2. blockMeshDict (3D Poloidal Channel Segment: X = 0..0.41m [0.02m W + 0.39m LBE], Y = 0..0.40m, Z = 0..4.0m)
with open(f"{base}/system/blockMeshDict", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "system"; object blockMeshDict;
}
scale 1.0;
vertices
(
    (0.00 0.00 0.0) (0.02 0.00 0.0) (0.41 0.00 0.0)
    (0.00 0.40 0.0) (0.02 0.40 0.0) (0.41 0.40 0.0)
    (0.00 0.00 4.0) (0.02 0.00 4.0) (0.41 0.00 4.0)
    (0.00 0.40 4.0) (0.02 0.40 4.0) (0.41 0.40 4.0)
);
blocks
(
    hex (0 1 4 3 6 7 10 9) solid_fw  (4 10 25) simpleGrading (1 1 1)
    hex (1 2 5 4 7 8 11 10) fluid_lbe (12 10 25) simpleGrading (1 1 1)
);
boundary
(
    plasma_wall
    {
        type wall;
        faces ((0 3 9 6));
    }
    outer_wall
    {
        type wall;
        faces ((2 8 11 5));
    }
    inlet
    {
        type patch;
        faces ((0 1 4 3) (1 2 5 4));
    }
    outlet
    {
        type patch;
        faces ((6 9 10 7) (7 10 11 8));
    }
    sides
    {
        type symmetry;
        faces ((0 6 7 1) (1 7 8 2) (3 4 10 9) (4 5 11 10));
    }
);
""")

# 3. Thermophysical Properties (Tungsten Solid + Liquid LBE Fluid) & Gravity
with open(f"{base}/constant/solid_fw/thermophysicalProperties", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "constant/solid_fw"; object thermophysicalProperties;
}
thermoType
{
    type            heSolidThermo;
    mixture         pureMixture;
    transport       constIso;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}
mixture
{
    specie      { molWeight 183.84; }
    transport   { kappa 115.0; }
    thermo      { Hf 0; Cp 134.0; }
    equationOfState { rho 19300.0; }
}
""")

with open(f"{base}/constant/fluid_lbe/thermophysicalProperties", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "constant/fluid_lbe"; object thermophysicalProperties;
}
thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}
mixture
{
    specie          { molWeight 208.0; }
    transport       { mu 1.35e-3; Pr 0.022; }
    thermodynamics  { Hf 0; Cp 146.0; }
    equationOfState { rho 10050.0; }
}
""")

for reg in ["", "fluid_lbe/"]:
    with open(f"{base}/constant/{reg}g", "w") as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class uniformDimensionedVectorField; location "constant"; object g;
}
dimensions [0 1 -2 0 0 0 0];
value (0 0 -9.81);
""")

with open(f"{base}/constant/fluid_lbe/turbulenceProperties", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "constant/fluid_lbe"; object turbulenceProperties;
}
simulationType laminar;
""")

# Volumetric Nuclear Heating inside LBE Blanket (fvOptions for fluid_lbe)
with open(f"{base}/constant/fluid_lbe/fvOptions", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; location "constant/fluid_lbe"; object fvOptions;
}
nuclearBlanketHeating
{
    type            scalarSemiImplicitSource;
    active          true;
    scalarSemiImplicitSourceCoeffs
    {
        selectionMode   all;
        volumeMode      specific;
        sources
        {
            h
            {
                // Equivalent to ~54 MW/m^3 volumetric nuclear heating -> dT ~ 145 C across 4m channel at 2.4 m/s
                explicit    5350.0;
                implicit    0.0;
            }
        }
    }
}
""")

# 4. Initial Fields (0/solid_fw and 0/fluid_lbe)
with open(f"{base}/0/solid_fw/T", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class volScalarField; location "0/solid_fw"; object T;
}
dimensions [0 0 0 1 0 0 0];
internalField uniform 723.15;
boundaryField
{
    plasma_wall
    {
        type            externalWallHeatFluxTemperature;
        mode            flux;
        q               uniform 1.45e6;
        kappaMethod     solidThermo;
        value           uniform 723.15;
    }
    inlet       { type zeroGradient; }
    outlet      { type zeroGradient; }
    sides       { type symmetry; }
    "solid_fw_to_.*"
    {
        type            compressible::turbulentTemperatureCoupledBaffleMixed;
        Tnbr            T;
        kappaMethod     solidThermo;
        value           uniform 723.15;
    }
}
""")

with open(f"{base}/0/fluid_lbe/T", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class volScalarField; location "0/fluid_lbe"; object T;
}
dimensions [0 0 0 1 0 0 0];
internalField uniform 723.15;
boundaryField
{
    inlet       { type fixedValue; value uniform 723.15; }
    outlet      { type zeroGradient; }
    outer_wall  { type zeroGradient; }
    sides       { type symmetry; }
    "fluid_lbe_to_.*"
    {
        type            compressible::turbulentTemperatureCoupledBaffleMixed;
        Tnbr            T;
        kappaMethod     fluidThermo;
        value           uniform 723.15;
    }
}
""")

with open(f"{base}/0/fluid_lbe/U", "w") as f:
    f.write("""FoamFile
{
    version 2.0; format ascii; class volVectorField; location "0/fluid_lbe"; object U;
}
dimensions [0 1 -1 0 0 0 0];
internalField uniform (0 0 2.4);
boundaryField
{
    inlet       { type fixedValue; value uniform (0 0 2.4); }
    outlet      { type zeroGradient; }
    outer_wall  { type noSlip; }
    sides       { type symmetry; }
    "fluid_lbe_to_.*" { type noSlip; }
}
""")

for p_name in ["p_rgh", "p"]:
    with open(f"{base}/0/fluid_lbe/{p_name}", "w") as f:
        f.write(f"""FoamFile
{{
    version 2.0; format ascii; class volScalarField; location "0/fluid_lbe"; object {p_name};
}}
dimensions [1 -1 -2 0 0 0 0];
internalField uniform 2.0e6;
boundaryField
{{
    inlet       {{ type zeroGradient; }}
    outlet      {{ type fixedValue; value uniform 2.0e6; }}
    outer_wall  {{ type zeroGradient; }}
    sides       {{ type symmetry; }}
    "fluid_lbe_to_.*" {{ type zeroGradient; }}
}}
""")

# 5. Execute blockMesh -> splitMeshRegions -> chtMultiRegionSimpleFoam -> foamToVTK
subprocess.run(["blockMesh"], cwd=base, stdout=subprocess.DEVNULL, check=True)
subprocess.run(["splitMeshRegions", "-cellZones", "-overwrite"], cwd=base, stdout=subprocess.DEVNULL, check=True)
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
print(f"3D CHT Fluid LBE Temp (Min / Mean / Max) : {lbe_min:.2f} C / {lbe_mean:.2f} C / {lbe_max:.2f} C")
print(f"3D CHT Solid FW  Temp (Min / Mean / Max) : {fw_min:.2f} C / {fw_mean:.2f} C / {fw_max:.2f} C")
print("Exported multi-region CHT VTK files to openfoam_cht/VTK/")
print("=========================================================================\n")
