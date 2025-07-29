#!/usr/bin/env python3
import os
import subprocess
from gi.repository import Gio

print("=== Testing Universal Blue Detection ===")

# Test 1: Check os-release
print("\n1. Checking os-release files:")
os_release_paths = ['/run/host/etc/os-release', '/etc/os-release']
for path in os_release_paths:
    print(f"\nChecking {path}:")
    if os.path.exists(path):
        with open(path, 'r') as f:
            content = f.read()
            print(f"File exists: YES")
            print(f"First few lines:")
            for line in content.split('\n')[:5]:
                print(f"  {line}")
            if 'bazzite' in content.lower():
                print("✓ Found 'bazzite' in os-release")
    else:
        print(f"✗ {path} not found")

# Test 2: Try rpm-ostree subprocess
print("\n2. Testing rpm-ostree subprocess:")
try:
    result = subprocess.run(['rpm-ostree', '--version'], 
                          capture_output=True, text=True)
    print(f"Return code: {result.returncode}")
    print(f"Output: {result.stdout[:100] if result.stdout else 'No output'}")
    print(f"Error: {result.stderr[:100] if result.stderr else 'No error'}")
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 3: Try D-Bus connection
print("\n3. Testing D-Bus connection:")
try:
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        "org.projectatomic.rpmostree1",
        "/org/projectatomic/rpmostree1/Sysroot",
        "org.projectatomic.rpmostree1.Sysroot",
        None
    )
    print("✓ D-Bus connection successful")
    
    # Try to get booted deployment
    booted = proxy.get_cached_property("Booted")
    if booted:
        print(f"Booted deployment path: {booted}")
except Exception as e:
    print(f"✗ D-Bus error: {e}")

# Test 4: Check host filesystem access
print("\n4. Checking filesystem access:")
paths = ['/etc/os-release', '/usr/bin/rpm-ostree', '/proc/cmdline']
for path in paths:
    exists = os.path.exists(path)
    print(f"{path}: {'EXISTS' if exists else 'NOT FOUND'}")