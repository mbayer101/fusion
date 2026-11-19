import openmc
import subprocess
import os

print("=== RUNNING STAGE 2 SUBCRITICALITY (k_eff) EIGENVALUE VERIFICATION ===")

# Load existing production materials.xml and geometry.xml (6.0 cm Be + graded 7/14/24 wt% U Stage 2)
# Override settings.xml temporarily for a k-eigenvalue criticality check
settings = openmc.Settings()
settings.run_mode = 'eigenvalue'
settings.batches = 40
settings.inactive = 10
settings.particles = 10000

# Initialize fission source uniformly across the Stage 2 fissile/fertile LBE annulus (r = 38 to 71 cm)
r_dist = openmc.stats.Uniform(38.0, 71.0)
cos_theta = openmc.stats.Uniform(-1.0, 1.0)
phi = openmc.stats.Uniform(0.0, 2.0 * 3.141592653589793)
settings.source = openmc.IndependentSource(
    space=openmc.stats.SphericalIndependent(r_dist, cos_theta, phi)
)
settings.output = {'tallies': False}
settings.export_to_xml()

# Remove tallies.xml during eigenvalue check so OpenMC runs fast and clean
if os.path.exists('tallies.xml'):
    os.rename('tallies.xml', 'tallies.xml.bak')

try:
    if os.path.exists('statepoint.40.h5'):
        os.remove('statepoint.40.h5')
    subprocess.run(
        ["mpirun", "--allow-run-as-root", "-n", "4", "/root/miniforge3/envs/openmc_dagmc_env/bin/openmc", "-s", "10"],
        stdout=subprocess.DEVNULL, check=True
    )

    with openmc.StatePoint('statepoint.40.h5') as sp:
        keff = sp.keff
        print(f"\n==================================================================")
        print(f"Verified Blanket Eigenvalue (k_eff) : {keff.nominal_value:.5f} +/- {keff.std_dev:.5f}")
        print(f"Subcritical Safety Margin (to 0.95) : {0.95 - keff.nominal_value:+.5f}")
        status = "PASS (Strictly Subcritical)" if keff.nominal_value < 0.95 else "WARNING (Exceeds 0.95 limit)"
        print(f"Regulatory Safety Status            : {status}")
        print(f"==================================================================\n")
finally:
    # Restore production fixed-source settings.xml and tallies.xml cleanly
    if os.path.exists('tallies.xml.bak'):
        os.rename('tallies.xml.bak', 'tallies.xml')
    subprocess.run(["/root/miniforge3/envs/openmc_dagmc_env/bin/python", "openmc/build_model.py"], stdout=subprocess.DEVNULL, check=True)
