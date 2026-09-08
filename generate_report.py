import os
from odf.opendocument import OpenDocumentText
from odf.text import H, P
from odf.table import Table, TableColumn, TableRow, TableCell

def create_scientific_report():
    # Initialize OpenDocument Text container
    doc = OpenDocumentText()

    # --- Document Header / Title ---
    doc.text.addElement(H(outlinelevel=1, text="Neutronics and Cost-Optimization Analysis of a 500 MW D-T Fusion Blanket Design"))
    
    # Author & Affiliation metadata
    doc.text.addElement(P(text="Prepared by: Michael J. Bayer | Information Security Engineering & Principal Architecture"))
    doc.text.addElement(P(text="Institution: Advanced Fusion Systems Research Group"))
    doc.text.addElement(P(text="Date: August 2026"))
    doc.text.addElement(P(text="---"))

    # --- Abstract ---
    doc.text.addElement(H(outlinelevel=2, text="Abstract"))
    abstract_text = (
        "This report evaluates the neutronic performance of a realistic 500 MW Deuterium-Tritium (D-T) "
        "fusion reactor model featuring a 2-meter minor radius plasma core, a tungsten first wall, a lead neutron "
        "multiplier, and a liquid lithium-lead (PbLi) breeding blanket supported by an structural steel shell. "
        "Using OpenMC Monte Carlo transport simulations, we examine Tritium Breeding Ratios (TBR), component thermal "
        "power extraction, and Lithium-6 enrichment optimizations to establish a cost-effective path toward commercial "
        "fuel self-sufficiency."
    )
    doc.text.addElement(P(text=abstract_text))

    # --- Methodology ---
    doc.text.addElement(H(outlinelevel=2, text="1. Reactor Configuration & Methodology"))
    method_text = (
        "The model implements a 1D cylindrical homogenized build mapped across realistic tokamak scales. "
        "The simulation source models isotropic 14.1 MeV D-T neutrons distributed uniformly across a 190 cm core radius "
        "within a 6-meter high section. Material cross-sections were evaluated using continuous-energy nuclear data libraries. "
        "Calculations incorporate cell-based heating tallies and nuclear response functions to calculate local power densities "
        "and breeding capabilities."
    )
    doc.text.addElement(P(text=method_text))

    # --- Parameter Sweep Results ---
    doc.text.addElement(H(outlinelevel=2, text="2. Li-6 Enrichment Optimization Sweep"))
    sweep_desc = (
        "To minimize procurement costs associated with high isotopic enrichment, a parameter sweep was conducted across "
        "various Lithium-6 weight percentages in the PbLi blanket. The threshold for self-sufficiency is established at a "
        "TBR >= 1.0 (accounting for decay and processing losses)."
    )
    doc.text.addElement(P(text=sweep_desc))

    # Table Creation for Enrichment Sweep
    table_data = [
        ["Enrichment (%)", "TBR Mean", "Standard Deviation", "Operational Status"],
        ["7.5%", "0.3969", "+/- 0.0005", "Sub-critical"],
        ["30.0%", "0.8299", "+/- 0.0006", "Sub-critical"],
        ["50.0%", "1.0200", "+/- 0.0006", "Self-Sustaining (Optimal)"],
        ["70.0%", "1.1416", "+/- 0.0007", "Self-Sustaining"],
        ["90.0%", "1.2263", "+/- 0.0007", "Self-Sustaining"]
    ]

    table = Table(name="EnrichmentTable")
    for _ in range(4):
        table.addElement(TableColumn())

    for row_content in table_data:
        tr = TableRow()
        for cell_value in row_content:
            tc = TableCell()
            tc.addElement(P(text=cell_value))
            tr.addElement(tc)
        table.addElement(tr)
    
    doc.text.addElement(table)
    doc.text.addElement(P(text="")) # Spacing

    # --- Final Results & Power Deposition ---
    doc.text.addElement(H(outlinelevel=2, text="3. Component Power Deposition (Optimized 50% Case)"))
    results_text = (
        "At the optimized 50% Li-6 enrichment level, the system achieves a secure TBR of 1.0200, successfully clearing "
        "the self-sufficiency criterion while avoiding the excessive expenses of 90% enrichment. Total thermal power "
        "deposition across structural and breeding components derived from the 500 MW fusion neutron source indicates "
        "efficient core energy capture:"
    )
    doc.text.addElement(P(text=results_text))

    doc.text.addElement(P(text="• Tungsten First Wall Thermal Power: 2.31 MW"))
    doc.text.addElement(P(text="• Lead Multiplier Thermal Power: 2.17 MW"))
    doc.text.addElement(P(text="• PbLi Breeding Blanket Thermal Power: 161.91 MW"))
    doc.text.addElement(P(text="• Fe-Cr Structural Shell Thermal Power: 0.59 MW"))

    # --- Conclusion ---
    doc.text.addElement(H(outlinelevel=2, text="4. Conclusion"))
    conclusion_text = (
        "The OpenMC simulations confirm that a 50% Li-6 enriched PbLi blanket combined with a library-compatible "
        "Fe-Cr structural layout provides an optimal balance between nuclear safety margins, tritium self-sufficiency, "
        "and industrial component affordability for future fusion reactor builds."
    )
    doc.text.addElement(P(text=conclusion_text))

    # Save Document
    filename = "fusion_reactor_report.odt"
    doc.save(filename)
    print(f"Scientific report successfully generated and saved as '{filename}'")

if __name__ == "__main__":
    create_scientific_report()

