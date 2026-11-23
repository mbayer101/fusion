# End-to-End Fusion-Fission-Fusion (F-F-F) Hybrid Reactor Simulation Pipeline

An integrated multi-physics simulation framework coupling **OpenMC** (3D Monte Carlo neutron transport with MAGIC variance reduction) and **OpenFOAM** (Conjugate Heat Transfer & convective thermal-hydraulics) for a low-$Q$ D-T Tokamak driven subcritical fission and tritium breeding blanket.

---

## 4-Zone Concentric Reactor Architecture

1. **Stage 1 — Driven D-T Fusion Driver (`0–30 cm`):** 500 MW (14.1 MeV) isotropic neutron core confined by REBCO high-temperature superconducting magnets behind a 2 cm polycrystalline Tungsten (W) first wall (`30–32 cm`).
2. **Front Neutron Multiplier (`32–38 cm`):** 6.0 cm Beryllium (Be) front multiplier zone triggering `(n, 2n)` reactions from 14.1 MeV fusion neutrons to boost blanket multiplication to **M = 4.64x**.
3. **Stage 2 — Radially Graded Subcritical Fission Blanket (`38–71 cm`):** Liquid Lead-Bismuth Eutectic (LBE) carrying radially graded depleted/low-enriched uranium (`7 wt% -> 14 wt% -> 24 wt%`) across three concentric zones (`38–46`, `46–56`, `56–71 cm`) to flatten volumetric power peaking while remaining strictly subcritical ($k_{eff} < 0.95$).
4. **Stage 3 — Tritium Breeding Blanket & Graphite Reflector (`71–126 cm`):** 90%-enriched Li-6 FliBe molten salt loop (`71–101 cm`) backed by a 25 cm Graphite neutron reflector (`101–126 cm`).

---

## Verified Neutronics, Thermal-Hydraulics & Power-Cycle Results

| Performance Metric | Baseline (Uniform CSG) | Graded F-F-F (`0 cm Be`) | Production (`6.0 cm Be` Multiplier) |
| :--- | :--- | :--- | :--- |
| **Neutron Leakage Fraction** | `26.64%` | `1.79%` | **`< 1.80%`** |
| **Blanket Energy Multiplication ($M$)** | `1.00x` | `3.17x` (`44.69 MeV/n`) | **`4.64x`** (`65.45 MeV/n`) |
| **Total Thermal Power (500 MW Fusion)** | `500.0 MWth` | `1,367.30 MWth` | **`1,959.25 MWth`** |
| **Tritium Breeding Ratio (TBR)** | `1.05` | `1.5685` | **`1.1785`** (`>1.10` self-sufficient) |
| **Net Grid Output ($Q_{plasma} = 2.0$, sCO2)** | Net Negative | `152.63 MWe` | **`432.68 MWe`** |
| **Peak Blanket Temperature (Cooled LBE)** | `3,772.06 C` (Uncooled) | `631.62 C` | **`< 650.00 C`** (Eurofer97 compliant) |

---

## 1D Radial Temperature & Flattened Heating Profile

![1D Radial Temperature Profile](results/radial_temp_profile.png)

---

## Power-Cycle Operating Envelope ($Q_{plasma}$ vs. Blanket Multiplication $M$)

![Q vs M Operating Envelope](results/q_vs_m_operating_envelope.png)

---

## Quick Execution

    export OPENMC_CROSS_SECTIONS=/root/openmc_data/endf-b-vii.1/cross_sections.xml
    python3 openmc/build_model.py
    mpirun --allow-run-as-root -n 4 openmc -s 10
    python3 scripts/map_heating.py
    (cd openfoam && laplacianFoam && foamToVTK)
    python3 scripts/plot_radial_temp.py
    python3 scripts/brayton_cycle.py

---

## Subcriticality Safety Verification ($k_{eff}$ Eigenvalue Check)

* **Verified Blanket $k_{eff}$ (Plasma Driver Off):** **`0.24574 +/- 0.00076`** (strictly below the `k_eff < 0.95` regulatory subcriticality limit; failsafe passive shutdown upon plasma termination).

---

## v3 Engineering Roadmap Results (3D Toroidal, 5-Year Depletion & Multi-Region CHT)

- **Track A — 3D Toroidal Geometry & NBI Port Streaming (`R0 = 3.0 m, a = 1.0 m, kappa = 1.7`):**
  - **3D Blanket Multiplication ($M$):** **`5.52x`** (`77.90 MeV/n`) with **`0.38%`** total leakage (`1.87x` outboard/inboard Shafranov-shift wall-loading asymmetry).
- **Track B — 5-Year Coupled Depletion & First-Wall Radiation Damage (`500 MW` D-T Driver):**
  - **First-Wall Damage (3D Toroidal `2.60 MW/m^2` NWL):** **`29.9 DPA/FPY`** (`98.8 appm He/FPY`), supporting a 5-year Tungsten monoblock replacement cycle (`~150 DPA`).
  - **Actinide Transmutation & Subcriticality Control:** `15.9%` of Zone 3 $^{238}\text{U}$ transmutes over 5 FPY; closed-batch operation remains strictly subcritical up to **2.0 FPY ($k_{eff} = 0.906 < 0.95$)**, requiring annual/continuous online LBE actinide skimming to hold $k_{eff} \in [0.25, 0.65]$ over the full 5-year cycle.
- **Track C — Multi-Region CHT Fluid Loop & $\text{SiC}_f/\text{SiC}$ Flow Channel Inserts (`12 T` Field):**
  - **MHD Pressure Drop Reduction:** **`97.1%`** (`67.86 MPa` bare Eurofer97 $\rightarrow$ **`2.00 MPa`** with $\text{SiC}_f/\text{SiC}$ inserts; **`22.95 MWe`** total pumping power at `9.20 m^3/s`).
  - **Coupled Thermal Limits:** LBE outlet **`595.14 C`**, Eurofer97/LBE interface **`646.92 C`** (`< 650 C` creep limit), Tungsten plasma-facing surface **`899.10 C`** (`< 1,200 C` recrystallization limit).
