# End-to-End Fusion-Fission-Fusion (F-F-F) Hybrid Reactor Technical Design Report

**Repository:** `https://github.com/mbayer101/fusion` | **Release:** `v4.0.0`  
**Simulation Stack:** OpenMC 0.15.3 (ENDF/B-VII.1 & ENDF/B-VIII.0 Depletion) + OpenFOAM v2412 (`chtMultiRegionSimpleFoam` / `laplacianFoam`) + CadQuery/DAGMC + $\text{sCO}_2$ Brayton Thermodynamic Cycle

---

## 1. Executive Summary

This report documents the multi-physics design, neutronic optimization, thermal-hydraulic verification, and fuel-cycle safety analysis of a **500 MW D-T Fusion-Driven Subcritical Fission-Fusion Hybrid (F-F-F) Reactor**. By coupling a driven low-$Q$ ($Q_{plasma} = 2.0$) tokamak neutron source with a Beryllium $(n,2n)$ front neutron multiplier, a radially graded liquid Lead-Bismuth Eutectic (LBE) uranium blanket, and an enriched $^{6}\text{Li}$ FliBe tritium breeding loop, the plant achieves commercial net electrical output while remaining deeply subcritical ($k_{eff} < 0.95$) and tritium self-sufficient ($\text{TBR} > 1.10$).

| Key System Parameter | 1D Production Baseline (`v2.1.0`) | 3D Toroidal Hybrid (`v3.1.0 / v4.0.0`) | Engineering Design Limit |
| :--- | :---: | :---: | :---: |
| **Fusion Driver Power ($P_{fus}$)** | `500.0 MW` ($14.1\text{ MeV}$ D-T) | `500.0 MW` ($R_0=3.0\text{ m}, a=1.0\text{ m}, \kappa=1.7$) | Driven $Q_{plasma} = 2.0$ |
| **Blanket Energy Multiplication ($M$)** | **`4.64x`** (`65.45 MeV/n`) | **`3.20x – 5.52x`** (`45.19 – 77.90 MeV/n`) | Multiplies fusion thermal power |
| **Total Thermal Power ($P_{th}$)** | **`1,959.25 MWth`** | **`1,283.7 – 2,313.2 MWth`** | Primary IHX thermal duty |
| **Tritium Breeding Ratio (TBR)** | **`1.1785 ± 0.0026`** | **`1.1009`** (with equatorial NBI port) | **`> 1.10`** self-sufficiency |
| **Net Grid Electrical Output ($Q=2.0$)** | **`432.68 MWe`** (`47.31%` $\text{sCO}_2$) | **`> 300 MWe`** commercial class | Exceeds `300 MWe` target |
| **Initial Blanket Eigenvalue ($k_{eff}$)** | **`0.24574 ± 0.00076`** | **`0.24574`** (subcritical margin `+0.704`) | **`< 0.95`** regulatory limit |
| **Equilibrium $k_{eff}$ (`65%/yr` Pu Skim)** | **`0.29248`** at `5.0 FPY` | **`0.65165` max** (at `2.0 FPY`) | Passive shutdown on plasma off |
| **MHD Pressure Drop (`12 T` Field)** | `2.00 MPa` ($\text{SiC}_f/\text{SiC}$ FCI) | **`2.00 MPa`** (**`97.1%` reduction**) | `22.95 MWe` pumping power |
| **3D CHT Fluid LBE Temp (Mean / Max)** | `538.99 C` / `631.36 C` | **`452.15 C` / `488.38 C`** | **`< 650.0 C`** Eurofer97 creep |
| **3D CHT Tungsten FW Peak Temp** | `899.10 C` (1D turbulent) | **`891.81 C`** (`kOmegaSST` 3D CHT) | **`< 1,200.0 C`** recrystallization |

---

## 2. Four-Zone Concentric & 3D Toroidal Reactor Architecture

1. **Stage 1 — Driven D-T Fusion Driver (`r = 0–30 cm` 1D / `a = 100 cm` 3D):** $500\text{ MW}$ ($1.773 \times 10^{20}\text{ n/s}$) isotropic $14.1\text{ MeV}$ D-T plasma confined by $12\text{ T}$ REBCO superconducting magnets behind a $2.0\text{ cm}$ polycrystalline Tungsten (W) first wall.
2. **Front Neutron Multiplier (`6.0 cm` Beryllium):** Triggers $^9\text{Be}(n,2n)2\alpha$ reactions on $14.1\text{ MeV}$ source neutrons, amplifying the soft/fast neutron population entering Stage 2.
3. **Stage 2 — Radially Graded Subcritical Fission Blanket:** Flowing liquid Lead-Bismuth Eutectic (LBE, $\text{Pb}_{44.7}\text{Bi}_{55.3}$) carrying radially graded uranium (`7 wt% -> 14 wt% -> 24 wt%` in 1D; `12 wt% -> 22 wt% -> 34 wt%` in 3D outboard) to flatten volumetric power peaking while maintaining deep subcriticality.
4. **Stage 3 — Tritium Breeding Blanket & Graphite Reflector:** $90\%$-enriched $^6\text{Li}$ FliBe ($\text{Li}_2\text{BeF}_4$) molten salt loop (including an inboard breeding zone and NBI port collar in 3D geometry) backed by a $25\text{ cm}$ nuclear-grade Graphite reflector (`< 1.8%` leakage).

---

## 3. Neutronics, Subcriticality & 5-Year Fuel Cycle Verification

* **Passive Failsafe Subcriticality:** Eigenvalue criticality analysis (`scripts/check_subcriticality.py`) yields **$k_{eff} = 0.24574 \pm 0.00076$**, providing a `+0.70426` safety margin below the `0.95` regulatory ceiling. Terminating the fusion plasma shuts down blanket fission power passively.
* **First-Wall Radiation Damage (3D Toroidal):** At $2.60\text{ MW/m}^2$ outboard-peaked neutron wall loading (`1.87x` Shafranov shift asymmetry), the Tungsten first wall accumulates **`29.9 DPA/FPY`** (`98.8 appm He/FPY`), supporting a 5-year monoblock replacement schedule (`~150 DPA`).
* **Online Pyrochemical Actinide Skimming:** Coupled 5-year depletion (`scripts/full_actinide_skimming.py`) demonstrates that continuous pyrochemical extraction of `65%/yr` of bred plutonium from the liquid LBE loop caps peak $k_{eff}$ at **`0.65165`** (`2.0 FPY`) and stabilizes at **`0.29248`** (`5.0 FPY`).

---

## 4. Magnetohydrodynamic (MHD) & 3D Conjugate Heat Transfer (CHT) Performance

* **$\text{SiC}_f/\text{SiC}$ Flow Channel Inserts (FCIs):** Inside a $12\text{ T}$ toroidal magnetic field ($\text{Ha} = 22,927$), electrically insulating $\text{SiC}_f/\text{SiC}$ inserts reduce LBE MHD pressure drop by **`97.1%`**—from `67.86 MPa` (`780.37 MWe` pumping penalty) down to **`2.00 MPa`** (`22.95 MWe` pumping power at $9.20\text{ m}^3/\text{s}$ total loop flow).
* **3D Multi-Region Turbulent CHT (`openfoam_cht/`):** Solving coupled solid-fluid heat transfer with `chtMultiRegionSimpleFoam` (`kOmegaSST` turbulence + `alphatJayatillekeWallFunction`) yields a bulk LBE temperature of **`452.15 C`** (max **`488.38 C`**) and a peak Tungsten first-wall temperature of **`891.81 C`**.

---

## 5. Reproducibility & Repository Execution Map

* `openmc/build_model.py` — 1D production 4-zone OpenMC CSG + MAGIC weight-window generator
* `scripts/check_subcriticality.py` — $k_{eff}$ eigenvalue safety verification
* `scripts/build_toroidal_dagmc.py` & `scripts/toroidal_tbr_recovery.py` — 3D D-shaped CAD/DAGMC & toroidal TBR optimization
* `scripts/run_burnup_and_dpa.py` & `scripts/full_actinide_skimming.py` — 5-year coupled depletion, DPA, and online Pu skimming
* `scripts/run_3d_turbulent_cht.py` — 3D OpenMC-to-OpenFOAM `chtMultiRegionSimpleFoam` solver & VTK exporter
* `scripts/brayton_cycle.py` — Supercritical $\text{CO}_2$ Brayton power-cycle & $Q_{plasma}$ operating envelope solver
