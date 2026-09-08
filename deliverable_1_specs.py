# Deliverable 1: 3D Toroidal Reactor Parameter Specification
# Baseline established from 1D OpenMC model and project records.

REACTOR_PARAMS = {
    "configuration": "D-T Fusion Toroidal Blanket",
    "minor_radius_m": 2.0,
    "major_radius_m": None,  # To be defined for 3D model
    "fusion_power_mw": 500.0,
    "neutron_energy_mev": 14.1,
    
    "materials": {
        "first_wall": {"name": "Tungsten", "density_g_cm3": 19.3},
        "multiplier": {"name": "Lead", "density_g_cm3": 11.34},
        "breeder": {"name": "PbLi", "li6_enrichment": 0.50},
        "structure": {"name": "Fe-Cr", "fe_fraction": 0.88, "cr_fraction": 0.12}
    },
    
    "reference_results_1d": {
        "tbr": 1.0200,
        "tbr_uncertainty": 0.0006,
        "pbli_heating_mw": 161.91,
        "tungsten_heating_mw": 2.31,
        "lead_heating_mw": 2.17,
        "fe_cr_heating_mw": 0.59
    }
}

if __name__ == "__main__":
    print(f"Loaded baseline configuration for: {REACTOR_PARAMS['configuration']}")
    print(f"Plasma Minor Radius: {REACTOR_PARAMS['minor_radius_m']} m")
    print(f"Baseline Li-6 Enrichment: {REACTOR_PARAMS['materials']['breeder']['li6_enrichment']*100}%")
    print(f"Target Baseline TBR: {REACTOR_PARAMS['reference_results_1d']['tbr']} +/- {REACTOR_PARAMS['reference_results_1d']['tbr_uncertainty']}")
