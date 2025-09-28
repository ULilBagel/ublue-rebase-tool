#!/usr/bin/env python3
"""Test script to capture uupd output and analyze progress patterns"""

import subprocess
import sys
import re

def test_uupd_output():
    """Run uupd in dry-run mode and capture output"""
    print("Testing uupd output patterns...")
    print("=" * 50)
    
    # Test 1: Default uupd output
    print("\n1. Default uupd output (dry-run):")
    try:
        result = subprocess.run(
            ["flatpak-spawn", "--host", "uupd", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print("STDOUT:")
        for i, line in enumerate(result.stdout.splitlines()[:20]):
            print(f"  {i+1}: {line}")
        if result.stderr:
            print("STDERR:")
            for i, line in enumerate(result.stderr.splitlines()[:20]):
                print(f"  {i+1}: {line}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 2: With verbose flag
    print("\n2. With --verbose flag:")
    try:
        result = subprocess.run(
            ["flatpak-spawn", "--host", "uupd", "--verbose", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print("STDOUT:")
        for i, line in enumerate(result.stdout.splitlines()[:20]):
            print(f"  {i+1}: {line}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 3: Check for progress patterns
    print("\n3. Checking for progress patterns:")
    patterns = [
        r'\d+%',  # Any percentage
        r'\[\d+/\d+\]',  # [current/total] format
        r'progress',  # Word "progress"
        r'downloading',  # Downloading indicator
        r'updating',  # Updating indicator
    ]
    
    print("Looking for patterns:", patterns)

if __name__ == "__main__":
    test_uupd_output()