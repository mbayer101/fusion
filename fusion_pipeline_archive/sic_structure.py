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

print("Running Simulation with Silicon Carbide (SiC) Structure and 50% Li-6...")

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

# Using optimized 50% Li-6 enrichment
pbli = openmc.Material(name='PbLi-Blanket')
pbli.add_element('Pb', 0.83, 'ao')
pbli.add_element('Li', 0.17, 'ao', enrichment=50.0, enrichment_target='Li6', enrichment_type='ao')
pbli.set_density('g/cm3', 9.5)

# New Silicon Carbide (SiC) Structure using explicit isotopes
sic_struct = openmc.Material(name='SiC-Structure')
# Silicon isotopes (92.23% Si28, 4.67% Si29, 3.10% Si30)
sic_struct.add_nuclide('Si28', 0.9223, 'ao')
sic_struct.add_nuclide('Si29', 0.0467, 'ao')
sic_struct.add_nuclide('Si30', 0.0310, 'ao')
# Carbon isotopes (98.93% C12, 1.07% C13)
sic_struct.add_nuclide('C12', 0.9893, 'ao')
sic_struct.add_nuclide('C13', 0.0107, 'ao')
sic_struct.set_density('g/cm3', 3.21)

materials = openmc.Materials([dt_fuel, tungsten, lead_multiplier, pbli, sic_struct])
materials.export_to_xml()

# --- 2. DEFINE REALISTIC GEOMETRY ---
r_plasma = 200.0
r_wall = r_plasma + 2.0
r_multiplier = r_wall + 5.0
r_blanket = r_multiplier + 45.0
r_struct = r_blanket + 5.0
r_outer = r_struct + 100.0

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
cell_struct = openmc.Cell(fill=sic_struct, region=region_struct)
cell_outer = openmc.Cell(region=region_outer)

geometry = openmc.Geometry([cell_plasma, cell_wall, cell_multiplier, cell_blanket, cell_struct, cell_outer])
geometry.export_to_xml()

# --- 3. SETTINGS & SOURCE ---
settings = openmc.Settings()
settings.batches = 40
settings.inactive = 10
settings.particles = 40000
settings.run_mode = 'fixed source'

source = openmc.IndependentSource()
source.space = openmc.stats.CylindricalIndependent(
    r=openmc.stats.Uniform(0.0, 190.0),
    phi=openmc.stats.Uniform(0.0, 6.28318),
    z=openmc.stats.Uniform(-300.0, 300.0)
)
source.angle = openmc.stats.Isotropic()
source.energy = openmc.stats.Discrete([14.1e6], [1.0])
settings.source = source
settings.export_to_xml()

# --- 4. TALLIES ---
tallies = openmc.Tallies()

tally_tbr = openmc.Tally(name='Tritium-Br-Tally')
tally_tbr.filters = [openmc.CellFilter([cell_blanket])]
tally_tbr.scores = ['205']
tallies.append(tally_tbr)

heating_filter = openmc.CellFilter([cell_wall, cell_multiplier, cell_blanket, cell_struct])
tally_heating = openmc.Tally(name='Component-Heating-Tally')
tally_heating.filters = [heating_filter]
tally_heating.scores = ['heating']
tallies.append(tally_heating)

tallies.export_to_xml()

# --- 5. RUN ---
sp_filename = 'statepoint.40.h5'
if os.path.exists(sp_filename):
    os.remove(sp_filename)

openmc.run(output=False)

# --- 6. EXTRACT RESULTS ---
with openmc.StatePoint(sp_filename) as sp:
    t_tbr = sp.get_tally(name='Tritium-Br-Tally')
    df_tbr = t_tbr.get_pandas_dataframe()
    tbr_mean = df_tbr['mean'].values[0]
    tbr_std = df_tbr['std. dev.'].values[0]

    t_heat = sp.get_tally(name='Component-Heating-Tally')
    df_heat = t_heat.get_pandas_dataframe()

    print('\n==================================================')
    print('       SIC STRUCTURE + 50% ENRICHMENT RESULTS     ')
    print('==================================================')
    print(f"Tritium Breeding Ratio (TBR): {tbr_mean:.4f} +/- {tbr_std:.4f}")
    print('--------------------------------------------------')
    print('Thermal Power Deposition:')

    cell_names = {
        cell_wall.id: "Tungsten First Wall",
        cell_multiplier.id: "Lead Multiplier",
        cell_blanket.id: "PbLi Blanket",
        cell_struct.id: "SiC Structure"
    }

    for _, row in df_heat.iterrows():
        c_id = row['cell']
        if c_id in cell_names:
            power_mw = (row['mean'] * 1.6022e-19 * source_rate) / 1e6
            print(f"  - {cell_names[c_id]}: {power_mw:.2f} MW")
            
    print('==================================================')

