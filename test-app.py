#!/usr/bin/env python3
import sys
sys.path.insert(0, '/var/home/joem/code/ublue-rebase-tool/src')

print("Starting test...")

try:
    from ublue_image_manager import main
    print("Import successful, running main...")
    main()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()