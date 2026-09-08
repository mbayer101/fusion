import openmc

print("Configuring OpenMC Settings and Tallies for 3D Toroidal Model...")

# 1. Settings (Source, Batches, Particles)
settings = openmc.Settings()
settings.run_mode = 'fixed source'
settings.batches = 50
settings.inactive = 10
settings.particles = 10000
settings.source_rejection_fraction = 0.5  # Allow rejection for toroidal cross-section bounds

# Define isotropic 14.1 MeV D-T neutron source inside the plasma torus (R0 = 600 cm, minor radius = 200 cm)
source = openmc.Source()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(400.0, 800.0),   # Major radius span: R0 - a to R0 + a
    phi=openmc.stats.Uniform(0.0, 2.0 * 3.1415926535),
    z=openmc.stats.Uniform(-200.0, 200.0),  # Z span: -a to +a
    origin=(0.0, 0.0, 0.0)
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0]) # 14.1 MeV D-T neutrons

settings.source = source
settings.export_to_xml()

# 2. Tallies (TBR and Volumetric Heating)
tallies = openmc.Tallies()

# Cell-based tally for heating and tritium production across the blanket (Cell 4)
cell_filter = openmc.CellFilter([4]) 
tally_blanket = openmc.Tally(name='blanket_performance')
tally_blanket.filters = [cell_filter]
tally_blanket.scores = ['heating', '(n,t)'] # Captures thermal load and tritium production

tallies.append(tally_blanket)
tallies.export_to_xml()

print("Settings and Tallies XML files successfully regenerated with correct toroidal source bounds!")
