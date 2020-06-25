TEST_NUMBER_CHOICES = [("01", "first-layer track height vs first-layer printing speed"),
                       ("02", "first-layer track width"),
                       ("03", "Extrusion temperature test"),
                       ("04", "extrusion temperature vs printing speed"),
                       ("05", "track width"),
                       ("06", "extrusion multiplier vs printing speed"),
                       ("07", "printing speed"),
                       ("08", "extrusion temperature vs retraction distance"),
                       ("09", "retraction distance vs printing speed"),
                       ("10", "retraction distance"),
                       ("11", "retraction distance vs retraction speed"),
                       ("12", "bridging extrusion multiplier vs bridging printing speed")]
SLICER_CHOICES = [("Prusa", "Slic3r PE"), ("Simplify3D", "Simplify3D"), ("Cura", "Cura")]
TARGET_CHOICES = [("mechanical_strength", "Mechanical Strength"), ("aesthetics", "Visual Quality"), ("fast_printing", "Short Printing Time")]
MODE_CHOICES = [("core", "Core"), ("advanced", "Advanced"), ("guided", "Guided")]
WIZARD_MODES = [("guided", "Guided"), ("normal", "Normal")]
TOOL_CHOICES = [("T0", "T0"), ("T1", "T1"), ("T2", "T2")]
FORM_CHOICES = [("elliptic", "Delta"), ("cartesian", "Cartesian")]
UNITS = [("mm", "mm"), ("mm/s", "mm/s"), ("degC", "degC")]
