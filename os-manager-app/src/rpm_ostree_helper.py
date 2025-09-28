#!/usr/bin/env python3
"""
Helper module to interact with rpm-ostree and bootc via flatpak-spawn
Provides fallback support for different atomic/image-based system tools
"""

import subprocess
import json
import os
import threading
import queue
from typing import List, Dict, Any, Optional, Callable, Tuple


def check_command_exists(command: str) -> bool:
    """Check if a command exists on the host system"""
    try:
        if 'FLATPAK_ID' in os.environ:
            cmd = ["flatpak-spawn", "--host", "which", command]
        else:
            cmd = ["which", command]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except:
        return False


def get_available_tools() -> Dict[str, bool]:
    """Check which atomic/image tools are available"""
    tools = {
        "rpm-ostree": check_command_exists("rpm-ostree"),
        "bootc": check_command_exists("bootc"),
        "ostree": check_command_exists("ostree"),
    }
    return tools


def run_command(command: List[str]) -> Tuple[bool, str, str]:
    """Run command via flatpak-spawn if needed"""
    try:
        if 'FLATPAK_ID' in os.environ:
            cmd = ["flatpak-spawn", "--host"] + command
        else:
            cmd = command
            
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
    """Get system status as JSON, with fallback support"""
    tools = get_available_tools()
    
    # Try rpm-ostree first
    if tools.get("rpm-ostree"):
        success, stdout, stderr = run_rpm_ostree_command(["status", "--json"])
        if success:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                pass
    
    # Try bootc if available
    if tools.get("bootc"):
        success, stdout, stderr = run_command(["bootc", "status", "--json"])
        if success:
            try:
                # Convert bootc status to rpm-ostree-like format
                bootc_data = json.loads(stdout)
                # Note: This is a simplified conversion, may need adjustment
                return {
                    "deployments": [{
                        "booted": True,
                        "container-image-reference": bootc_data.get("spec", {}).get("image", {}).get("image", ""),
                    }]
                }
            except json.JSONDecodeError:
                pass
    
    return None


def rebase(image_url: str) -> tuple[bool, str]:
    """Execute rebase to new image with fallback support"""
    tools = get_available_tools()
    
    # Try rpm-ostree first
    if tools.get("rpm-ostree"):
        # First, try to cleanup any pending deployments
        run_rpm_ostree_command(["cleanup", "-p"])
        
        # Now proceed with rebase
        success, stdout, stderr = run_rpm_ostree_command(["rebase", image_url])
        
        if success:
            return True, stdout
        elif "rpm-ostree" not in stderr.lower():
            # If it failed for reasons other than rpm-ostree not being available
            return False, stderr
    
    # Try bootc if available
    if tools.get("bootc"):
        # bootc uses 'switch' instead of 'rebase'
        # Convert ostree-image-signed format to OCI format if needed
        bootc_image = image_url
        if image_url.startswith("ostree-image-signed:docker://"):
            bootc_image = image_url.replace("ostree-image-signed:docker://", "")
        
        success, stdout, stderr = run_command(["bootc", "switch", bootc_image])
        
        if success:
            return True, stdout
        else:
            return False, stderr
    
    # No tools available
    return False, "No atomic/image management tool available (rpm-ostree or bootc)"


def rebase_with_progress(image_url: str, progress_callback: Callable[[str], None]) -> tuple[bool, str]:
    """Execute rebase with real-time progress updates and fallback support"""
    tools = get_available_tools()
    
    try:
        # Determine which tool to use
        if tools.get("rpm-ostree"):
            # First, try to cleanup any pending deployments
            if 'FLATPAK_ID' in os.environ:
                cleanup_cmd = ["flatpak-spawn", "--host", "rpm-ostree", "cleanup", "-p"]
            else:
                cleanup_cmd = ["rpm-ostree", "cleanup", "-p"]
            
            # Run cleanup silently
            subprocess.run(cleanup_cmd, capture_output=True, text=True)
            
            # Now proceed with rebase
            if 'FLATPAK_ID' in os.environ:
                cmd = ["flatpak-spawn", "--host", "rpm-ostree", "rebase", image_url]
            else:
                cmd = ["rpm-ostree", "rebase", image_url]
                
        elif tools.get("bootc"):
            # bootc uses 'switch' instead of 'rebase'
            bootc_image = image_url
            if image_url.startswith("ostree-image-signed:docker://"):
                bootc_image = image_url.replace("ostree-image-signed:docker://", "")
            
            if 'FLATPAK_ID' in os.environ:
                cmd = ["flatpak-spawn", "--host", "bootc", "switch", bootc_image]
            else:
                cmd = ["bootc", "switch", bootc_image]
        else:
            return False, "No atomic/image management tool available (rpm-ostree or bootc)"
        
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