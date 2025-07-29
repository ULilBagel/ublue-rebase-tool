#!/usr/bin/env python3
"""
Test Python imports for Flatpak structure without GTK dependencies
"""

import sys
import os

# Add the staging directory to Python path
staging_dir = "flatpak-staging/lib/python3.11/site-packages"
sys.path.insert(0, staging_dir)

print("Testing Python module imports...")
print("=" * 50)

# Test basic imports that don't require GTK
modules_to_test = [
    "command_executor",
    "deployment_manager", 
    "progress_tracker",
    "history_manager"
]

all_good = True

for module in modules_to_test:
    try:
        # Check if file exists
        module_file = os.path.join(staging_dir, f"{module}.py")
        if os.path.exists(module_file):
            print(f"✓ {module}.py exists")
        else:
            print(f"✗ {module}.py missing")
            all_good = False
    except Exception as e:
        print(f"✗ Error checking {module}: {e}")
        all_good = False

# Check UI module
ui_dir = os.path.join(staging_dir, "ui")
if os.path.exists(ui_dir) and os.path.exists(os.path.join(ui_dir, "__init__.py")):
    print("✓ ui module directory exists with __init__.py")
    if os.path.exists(os.path.join(ui_dir, "confirmation_dialog.py")):
        print("✓ ui.confirmation_dialog.py exists")
    else:
        print("✗ ui.confirmation_dialog.py missing")
        all_good = False
else:
    print("✗ ui module directory missing or incomplete")
    all_good = False

# Check main module files
if os.path.exists(os.path.join(staging_dir, "ublue_image_manager.py")):
    print("✓ ublue_image_manager.py (import bridge) exists")
else:
    print("✗ ublue_image_manager.py (import bridge) missing")
    all_good = False

if os.path.exists(os.path.join(staging_dir, "ublue-image-manager.py")):
    print("✓ ublue-image-manager.py (main module) exists")
else:
    print("✗ ublue-image-manager.py (main module) missing")
    all_good = False

print("\n" + "=" * 50)
if all_good:
    print("All module files are present!")
    print("\nNote: Actual import testing requires GTK dependencies.")
    print("The Flatpak runtime will provide these dependencies.")
else:
    print("Some module files are missing!")
    sys.exit(1)