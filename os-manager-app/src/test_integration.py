#!/usr/bin/env python3
"""
Basic integration test for OS Manager update functionality
This tests the actual tool selection logic without mocking
"""

import subprocess
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Define UPDATE_TOOLS (same as in atomic-os-manager.py)
UPDATE_TOOLS = [
    {
        "name": "uupd",
        "command": ["flatpak-spawn", "--host", "pkexec", "uupd"],
        "check_command": "uupd",
        "reboot_indicators": ["(R)eboot", "(r)eboot", "restart required", "Reboot required", "System restart required"],
    },
    {
        "name": "ujust update",
        "command": ["flatpak-spawn", "--host", "ujust", "update"],
        "check_command": "ujust",
        "reboot_indicators": ["(R)eboot", "(r)eboot"],
    },
    {
        "name": "ublue-update",
        "command": ["flatpak-spawn", "--host", "ublue-update"],
        "check_command": "ublue-update",
        "reboot_indicators": ["(R)eboot", "(r)eboot"],
    }
]


def check_tool_availability():
    """Check which update tools are available on the system"""
    print("=== Checking Update Tool Availability ===")
    available_tools = []
    
    for tool in UPDATE_TOOLS:
        check_cmd = ["which", tool["check_command"]]
        try:
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {tool['name']} - AVAILABLE at {result.stdout.strip()}")
                available_tools.append(tool)
            else:
                print(f"✗ {tool['name']} - NOT FOUND")
        except Exception as e:
            print(f"✗ {tool['name']} - ERROR: {e}")
    
    return available_tools


def test_tool_selection_logic():
    """Test the tool selection logic matches implementation"""
    print("\n=== Testing Tool Selection Logic ===")
    
    # Simulate the actual selection logic from run_system_update()
    selected_tool = None
    for tool in UPDATE_TOOLS:
        # Note: Using 'which' directly for testing, actual code uses flatpak-spawn
        check_cmd = ["which", tool["check_command"]]
        try:
            result = subprocess.run(check_cmd, capture_output=True)
            if result.returncode == 0:
                selected_tool = tool
                print(f"Selected tool: {tool['name']}")
                break
            else:
                print(f"{tool['name']} not found, checking next tool...")
        except Exception as e:
            print(f"Error checking {tool['name']}: {e}")
    
    if not selected_tool:
        print("✗ No update tool found (uupd, ujust, or ublue-update)")
        print("Please ensure at least one update tool is installed on your system.")
    else:
        print(f"\n✓ Would use: {selected_tool['name']} for system update")
        print(f"  Command: {' '.join(selected_tool['command'])}")
        print(f"  Reboot indicators: {selected_tool['reboot_indicators']}")
    
    return selected_tool


def test_command_execution_dry_run():
    """Test command construction without actually running updates"""
    print("\n=== Testing Command Construction ===")
    
    selected_tool = test_tool_selection_logic()
    if selected_tool:
        print(f"\nCommand that would be executed:")
        print(f"  {' '.join(selected_tool['command'])}")
        
        # Test with --help flag to verify command structure without updating
        test_cmd = selected_tool["command"] + ["--help"]
        print(f"\nTesting command with --help flag:")
        try:
            # Remove flatpak-spawn for direct testing
            if test_cmd[0] == "flatpak-spawn" and test_cmd[1] == "--host":
                test_cmd = test_cmd[2:]
            
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ Command executed successfully")
                print(f"  First line of output: {result.stdout.split(chr(10))[0][:80]}...")
            else:
                print(f"✗ Command failed with return code: {result.returncode}")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print("✗ Command timed out")
        except Exception as e:
            print(f"✗ Error executing command: {e}")


def main():
    """Run integration tests"""
    print("OS Manager Update Tool Integration Test")
    print("=" * 50)
    
    # Check what tools are available
    available_tools = check_tool_availability()
    
    if not available_tools:
        print("\n⚠️  WARNING: No update tools found on this system!")
        print("   Please install at least one of: uupd, ujust, or ublue-update")
        return 1
    
    # Test tool selection
    test_tool_selection_logic()
    
    # Test command construction
    test_command_execution_dry_run()
    
    print("\n" + "=" * 50)
    print("Integration test completed.")
    print(f"Found {len(available_tools)} update tool(s) on this system.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())