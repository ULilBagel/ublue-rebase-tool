#!/usr/bin/env python3
"""
Helper module to interact with rpm-ostree via flatpak-spawn
"""

import subprocess
import json
import os
import threading
import queue
from typing import List, Dict, Any, Optional, Callable


def run_rpm_ostree_command(args: List[str]) -> tuple[bool, str, str]:
    """
    Run rpm-ostree command via flatpak-spawn to access host system
    
    Returns: (success, stdout, stderr)
    """
    try:
        # Check if we're in flatpak
        if 'FLATPAK_ID' in os.environ:
            # Use flatpak-spawn to run on host
            cmd = ["flatpak-spawn", "--host", "rpm-ostree"] + args
        else:
            # Direct call when not in flatpak
            cmd = ["rpm-ostree"] + args
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def get_status_json() -> Optional[Dict[str, Any]]:
    """Get rpm-ostree status as JSON"""
    success, stdout, stderr = run_rpm_ostree_command(["status", "--json"])
    
    if success:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return None
    return None


def rebase(image_url: str) -> tuple[bool, str]:
    """Execute rebase to new image"""
    success, stdout, stderr = run_rpm_ostree_command(["rebase", image_url])
    
    if success:
        return True, stdout
    else:
        return False, stderr


def rebase_with_progress(image_url: str, progress_callback: Callable[[str], None]) -> tuple[bool, str]:
    """Execute rebase with real-time progress updates"""
    try:
        # Check if we're in flatpak
        if 'FLATPAK_ID' in os.environ:
            cmd = ["flatpak-spawn", "--host", "rpm-ostree", "rebase", image_url]
        else:
            cmd = ["rpm-ostree", "rebase", image_url]
        
        # Start process with unbuffered output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        output_lines = []
        
        # Read output line by line
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            line = line.rstrip()
            if line:  # Only process non-empty lines
                output_lines.append(line)
                try:
                    progress_callback(line)
                except Exception as e:
                    print(f"Error in progress callback: {e}")
        
        # Make sure process is fully complete
        process.stdout.close()
        return_code = process.wait()
        
        # Give a moment for any remaining I/O to complete
        import time
        time.sleep(0.1)
        
        if return_code == 0:
            return True, '\n'.join(output_lines)
        else:
            return False, '\n'.join(output_lines)
            
    except Exception as e:
        print(f"Exception in rebase_with_progress: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def rollback() -> tuple[bool, str]:
    """Execute rollback to previous deployment"""
    success, stdout, stderr = run_rpm_ostree_command(["rollback"])
    
    if success:
        return True, stdout
    else:
        return False, stderr


def rollback_with_progress(progress_callback: Callable[[str], None]) -> tuple[bool, str]:
    """Execute rollback with real-time progress updates"""
    try:
        # Check if we're in flatpak
        if 'FLATPAK_ID' in os.environ:
            cmd = ["flatpak-spawn", "--host", "rpm-ostree", "rollback"]
        else:
            cmd = ["rpm-ostree", "rollback"]
        
        # Start process with unbuffered output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        output_lines = []
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                output_lines.append(line)
                progress_callback(line)
        
        process.wait()
        
        if process.returncode == 0:
            return True, '\n'.join(output_lines)
        else:
            return False, '\n'.join(output_lines)
            
    except Exception as e:
        return False, str(e)