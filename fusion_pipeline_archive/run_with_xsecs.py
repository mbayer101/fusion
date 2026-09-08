import os
import glob
import openmc

# Search common paths for cross_sections.xml
search_paths = [
    "/root/fendl*/cross_sections.xml",
    "/root/**/cross_sections.xml",
    "/usr/local/**/cross_sections.xml",
    "/opt/**/cross_sections.xml",
    "/*/cross_sections.xml"
]

found_path = None
for pattern in search_paths:
    matches = glob.glob(pattern, recursive=True)
    if matches:
        found_path = matches[0]
        break

if found_path:
    print(f"Found cross_sections.xml at: {found_path}")
    os.environ["OPENMC_CROSS_SECTIONS"] = found_path
    # Also register it globally in openmc config
    openmc.config['cross_sections'] = found_path
else:
    print("Warning: Could not automatically locate cross_sections.xml. Please check your FENDL installation path.")

print("Starting OpenMC simulation run...")
openmc.run()
