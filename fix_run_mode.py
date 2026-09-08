import re

with open("build_settings_tallies.py", "r") as f:
    code = f.read()

# Insert run_mode = 'fixed source' right after settings instantiation
code = code.replace("settings = openmc.Settings()", "settings = openmc.Settings()\nsettings.run_mode = 'fixed source'")

with open("build_settings_tallies.py", "w") as f:
    f.write(code)

print("Updated settings to run-mode: fixed source")
