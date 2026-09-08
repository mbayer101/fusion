import os

print("=== SETTING UP OPENFOAM REGION & fvOptions CASE STRUCTURE ===")

# Define case directories for a Conjugate Heat Transfer (CHT) setup
case_dir = "fusion_blanket_cht_case"
constant_dir = os.path.join(case_dir, "constant")
system_dir = os.path.join(case_dir, "system")
solid_system_dir = os.path.join(case_dir, "system", "solid")

os.makedirs(constant_dir, exist_ok=True)
os.makedirs(solid_system_dir, exist_ok=True)

# 1. Write constant/regionProperties
region_props_content = """/*----------------*- C++ -*------------------*=\
| =========                 |                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox |
|  \\    /   O peration     | Website:  openfoam.org          |
|   \\  /    A nd           | Version:  v2312 / custom        |
|    \\/     M anipulation  |                 |
\\*------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      regionProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

regions
(
    fluid (coolant_loop)
    solid (breeding_blanket first_wall)
);
"""

with open(os.path.join(constant_dir, "regionProperties"), "w") as f:
    f.write(region_props_content)

# 2. Write system/solid/fvOptions (Nuclear Heating Source Term)
fv_options_content = """/*----------------*- C++ -*------------------*=\
| =========                 |                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox |
|  \\    /   O peration     | Website:  openfoam.org          |
|   \\  /    A nd           | Version:  v2312 / custom        |
|    \\/     M anipulation  |                 |
\\*------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system/solid";
    object      fvOptions;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

nuclearHeating
{
    type            scalarTransport;
    active          true;
    
    scalarTransportCoeffs
    {
        field           h; // Enthalpy field in solid structural regions
        explicitSource  table;
        
        // Direct ingestion of OpenMC converted power density mapping
        table
        (
#include "openfoam_heat_source.dat"
        );
    }
}
"""

with open(os.path.join(solid_system_dir, "fvOptions"), "w") as f:
    f.write(fv_options_content)

# Copy the generated heat source data into the solid system directory for OpenFOAM visibility
if os.path.exists("openfoam_heat_source.dat"):
    import shutil
    shutil.copy("openfoam_heat_source.dat", os.path.join(solid_system_dir, "openfoam_heat_source.dat"))

print(f"Successfully generated OpenFOAM directory structure under: ./{case_dir}/")
print(" - constant/regionProperties configured for multi-region CHT.")
print(" - system/solid/fvOptions configured with nuclear heating table.")
print("==============================================================")

