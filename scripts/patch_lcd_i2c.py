Import("env")

import os
import re

project_dir = env.subst("$PROJECT_DIR")
environment = env.subst("$PIOENV")

source = os.path.join(
    project_dir,
    ".pio",
    "libdeps",
    environment,
    "LiquidCrystal_I2C",
    "LiquidCrystal_I2C.cpp",
)

if os.path.isfile(source):
    with open(source, "r") as file:
        content = file.read()

    patched = re.sub(r"(?<!I2C_)BUFFER_LENGTH\b",
                     "I2C_BUFFER_LENGTH", content)

    if patched != content:
        with open(source, "w") as file:
            file.write(patched)
        print("Patched LiquidCrystal_I2C.cpp: BUFFER_LENGTH -> I2C_BUFFER_LENGTH")
    else:
        print("LiquidCrystal_I2C.cpp already patched or no matching identifier found")
else:
    print("WARNING: LiquidCrystal_I2C.cpp not found; LCD patch skipped")
