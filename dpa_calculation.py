import os
import math
import openmc
import pandas as pd

# --- 0. CONFIGURE CROSS SECTIONS ---
os.environ['OPENMC_CROSS_SECTIONS'] = '/root/cross_sections.xml'
openmc.config['cross_sections'] = '/root/cross_sections.xml'

# Constants for power conversion (500 MW reactor scale)
FUSION_POWER_MW = 500.0
TOTAL_ENERGY_PER_DT_EV = 17.6e6
fusion_power_ev_sec = FUSION_POWER_MW * 1e6 / 1.6022e-19
source_rate = fusion_power_ev_sec / TOTAL_ENERGY_PER_DT_EV

print("Running Simulation with RAFM DPA Tally...")

# --- 1. DEFINE MATERIALS ---
dt_fuel = openmc.Material(name='DT-Plasma')
dt_fuel.add_nuclide('H2', 0.5, 'ao')
dt_fuel.add_nuclide('H3', 0.5, 'ao')
dt_fuel.set_density('g/cm3', 1.0e-4)

tungsten = openmc.Material(name='Tungsten-Wall')
tungsten.add_element('W', 1.0, 'ao')
tungsten.set_density('g/cm3', 19.3)

lead_multiplier = openmc.Material(name='Lead-Multiplier')
lead_multiplier.add_element('Pb', 1.0, 'ao')
lead_multiplier.set_density('g/cm3', 11.34)

pbli = openmc.Material(name='PbLi-Blanket')
pbli.add_element('Pb', 0.83, 'ao')
pbli.add_element('Li', 0.17, 'ao', enrichment=90.0, enrichment_target='Li6', enrichment_type='ao')
pbli.set_density('g/cm3', 9.5)

rafm = openmc.Material(name='RAFM-Structure')
rafm.add_element('Fe', 89.0, 'wo')
rafm.add_element('Cr', 9.0, 'wo')
rafm.add_element('W', 1.0, 'wo')
rafm.add_element('V', 0.25, 'wo')
rafm.add_element('Ta', 0.07, 'wo')
rafm.set_density('g/cm3', 7.8)

materials = openmc.Materials([dt_fuel, tungsten, lead_multiplier, pbli, rafm])
materials.export_to_xml()

# --- 2. DEFINE GEOMETRY ---
r_plasma = 0.5
r_wall = 0.55
r_multiplier = r_wall + 5.0      # 5.55 cm
r_blanket = r_multiplier + 45.0  # 50.55 cm
r_struct = r_blanket + 2.0       # 52.55 cm
r_outer = r_struct + 2.5         # 55.05 cm

c_plasma = openmc.Cylinder(r=r_plasma)
c_wall = openmc.Cylinder(r=r_wall)
c_multiplier = openmc.Cylinder(r=r_multiplier)
c_blanket = openmc.Cylinder(r=r_blanket)
c_struct = openmc.Cylinder(r=r_struct)
c_outer = openmc.Cylinder(r=r_outer, boundary_type='vacuum')

region_plasma = -c_plasma
region_wall = +c_plasma & -c_wall
region_multiplier = +c_wall & -c_multiplier
region_blanket = +c_multiplier & -c_blanket
region_struct = +c_blanket & -c_struct
region_outer = +c_struct & -c_outer

cell_plasma = openmc.Cell(fill=dt_fuel, region=region_plasma)
cell_wall = openmc.Cell(fill=tungsten, region=region_wall)
cell_multiplier = openmc.Cell(fill=lead_multiplier, region=region_multiplier)
cell_blanket = openmc.Cell(fill=pbli, region=region_blanket)
cell_struct = openmc.Cell(fill=rafm, region=region_struct)
cell_outer = openmc.Cell(region=region_outer)

geometry = openmc.Geometry([cell_plasma, cell_wall, cell_multiplier, cell_blanket, cell_struct, cell_outer])
geometry.export_to_xml()

# --- 3. SETTINGS & NEUTRON SOURCE ---
settings = openmc.Settings()
settings.batches = 50
settings.inactive = 10
settings.particles = 25000
settings.run_mode = 'fixed source'

source = openmc.IndependentSource()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(0.0, 0.45),
    phi=openmc.stats.Uniform(0.0, 6.28318),
    z=openmc.stats.Uniform(-1.0, 1.0)
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])
settings.source = source
settings.export_to_xml()

# --- 4. TALLIES ---
tallies = openmc.Tallies()

# DPA Tally on the structural wall
tally_dpa = openmc.Tally(name='RAFM-Damage-Tally')
tally_dpa.filters = [openmc.CellFilter([cell_struct])]
tally_dpa.scores = ['damage-energy']
tallies.append(tally_dpa)

tallies.export_to_xml()

# --- 5. RUN SIMULATION ---
sp_filename = 'statepoint.50.h5'
if os.path.exists(sp_filename):
    os.remove(sp_filename)

openmc.run(output=False)

# --- 6. EXTRACT RESULTS & CALCULATE DPA ---
with openmc.StatePoint(sp_filename) as sp:
    t_dpa = sp.get_tally(name='RAFM-Damage-Tally')
    df_dpa = t_dpa.get_pandas_dataframe()
    damage_energy_mean = df_dpa['mean'].values[0]  # eV per source particle

    # Physical constants for NRT-DPA calculation
    Ed_Fe = 40.0  # Threshold displacement energy for Iron/Steel (eV)
    
    # Structural Volume Calculation (2 cm height based on source Z-range)
    h_source = 2.0  
    vol_struct = math.pi * (r_struct**2 - r_blanket**2) * h_source
    
    # Atomic density for RAFM steel (~7.8 g/cm3)
    # Iron molar mass = ~55.85 g/mol, Avogadro = 6.022e23
    atoms_per_cm3 = (7.8 / 55.85) * 6.022e23
    total_atoms = vol_struct * atoms_per_cm3
    
    # Calculations
    total_damage_rate_ev = damage_energy_mean * source_rate  # eV / sec
    displacements_per_sec = total_damage_rate_ev / (2.0 * Ed_Fe)
    dpa_per_sec = displacements_per_sec / total_atoms
    
    # Convert to Full Power Year (FPY)
    seconds_per_year = 365.25 * 24 * 3600
    dpa_per_fpy = dpa_per_sec * seconds_per_year
    
    print('\n==================================================')
    print('      RAFM STRUCTURAL WALL DAMAGE (DPA)           ')
    print('==================================================')
    print(f"Total Damage Energy: {damage_energy_mean:.2e} eV/particle")
    print(f"Estimated DPA rate:  {dpa_per_fpy:.2f} DPA per Full Power Year")
    print('==================================================')

