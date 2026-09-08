# Pure Python parameter configuration without external module dependencies

TOROIDAL_PARAMS = {
    "minor_radius_m": 2.0,
    "major_radius_m": 6.0,  # Aspect ratio A = 3.0
    "thicknesses": {
        "first_wall_w_m": 0.02,     # 2 cm Tungsten
        "multiplier_pb_m": 0.05,    # 5 cm Lead multiplier
        "blanket_pbli_m": 0.40,     # 40 cm PbLi breeding blanket
        "structure_fecr_m": 0.03,   # 3 cm Fe-Cr structure
        "shield_m": 0.30            # 30 cm Shield
    }
}

print("Toroidal baseline parameters configured:")
print(f"Major Radius (R0): {TOROIDAL_PARAMS['major_radius_m']} m")
print(f"Minor Radius (a): {TOROIDAL_PARAMS['minor_radius_m']} m")
for layer, thick in TOROIDAL_PARAMS['thicknesses'].items():
    print(f" - {layer}: {thick} m")
