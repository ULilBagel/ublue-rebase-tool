#!/usr/bin/env python3
"""
Import bridge for ublue-image-manager.py

This module exists to bridge the gap between Python's import naming requirements
(which don't allow hyphens) and the Universal Blue convention of using hyphenated
filenames. 

Tests expect to import from 'ublue_image_manager' (with underscores), but the 
actual application file is named 'ublue-image-manager.py' (with hyphens).

This bridge module dynamically loads the hyphenated module and re-exports all
necessary classes, allowing tests to use standard Python import syntax:
    from ublue_image_manager import UBlueImageAPI, UBlueImageWindow

To add new exports:
1. Import the class/function from the loaded module
2. Add it to the __all__ list

Reference: .claude/specs/fix-import-errors/
"""

import importlib.util
import sys
from pathlib import Path

try:
    # Get the path to the hyphenated module
    module_path = Path(__file__).parent / "ublue-image-manager.py"
    
    if not module_path.exists():
        raise ImportError(
            f"Cannot find ublue-image-manager.py at {module_path}. "
            "This bridge module requires the hyphenated file to exist."
        )
    
    # Create a module spec from the file location
    spec = importlib.util.spec_from_file_location("ublue_image_manager_impl", module_path)
    
    if spec is None or spec.loader is None:
        raise ImportError(
            "Failed to create module spec for ublue-image-manager.py. "
            "This may indicate a problem with the Python environment."
        )
    
    # Create the module from the spec
    module = importlib.util.module_from_spec(spec)
    
    # Register the module in sys.modules to prevent re-loading
    sys.modules["ublue_image_manager_impl"] = module
    
    # Execute the module to load its contents
    spec.loader.exec_module(module)
    
    # Re-export all necessary classes
    # These are the classes that tests expect to import
    try:
        UBlueImageAPI = module.UBlueImageAPI
        UBlueImageWindow = module.UBlueImageWindow
        UBlueImageApplication = module.UBlueImageApplication
    except AttributeError as e:
        # Provide helpful error if expected classes are missing
        available = [name for name in dir(module) if not name.startswith('_')]
        raise ImportError(
            f"Failed to import expected class from ublue-image-manager.py: {e}\n"
            f"Available attributes in module: {', '.join(available)}"
        )
    
    # Define what should be available when using 'from ublue_image_manager import *'
    __all__ = ["UBlueImageAPI", "UBlueImageWindow", "UBlueImageApplication"]
    
except Exception as e:
    # Re-raise with additional context while preserving the original traceback
    raise ImportError(
        f"Failed to load ublue-image-manager.py through import bridge: {e}"
    ) from e