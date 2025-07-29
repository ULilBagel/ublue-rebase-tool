#!/usr/bin/env python3
"""
Registry Manager for querying container image registries
Implements functionality similar to bazzite-rollback-helper list
"""

import subprocess
import json
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RegistryImage:
    """Represents an image tag from a registry"""
    name: str           # Full image name (e.g., "bazzite")
    tag: str            # Tag (e.g., "stable", "testing", "40-stable-20240722")
    registry: str       # Registry URL
    date: Optional[datetime] = None  # Parsed date from tag if available
    
    @property
    def full_ref(self):
        """Get full image reference"""
        return f"{self.registry}/{self.name}:{self.tag}"
    
    @property
    def age_days(self):
        """Get age in days if date is available"""
        if self.date:
            return (datetime.now() - self.date).days
        return None


class RegistryManager:
    """Manages queries to container registries for available images"""
    
    def __init__(self):
        self.cache = {}
        
    def list_image_tags(self, registry: str, image: str, branch: str = "stable") -> List[RegistryImage]:
        """
        List available tags for an image from a registry
        
        Args:
            registry: Registry URL (e.g., "ghcr.io/ublue-os")
            image: Image name (e.g., "bazzite")
            branch: Branch to filter ("stable", "testing", "all")
            
        Returns:
            List of RegistryImage objects
        """
        cache_key = f"{registry}/{image}:{branch}"
        
        # Check cache (5 minute TTL)
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=5):
                return cached_data
        
        try:
            # Use skopeo to list tags
            # Check if we're in flatpak and use flatpak-spawn
            if 'FLATPAK_ID' in os.environ:
                cmd = ["flatpak-spawn", "--host", "skopeo", "list-tags", f"docker://{registry}/{image}"]
            else:
                cmd = ["skopeo", "list-tags", f"docker://{registry}/{image}"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"Failed to list tags: {result.stderr}")
                return []
            
            tags_data = json.loads(result.stdout)
            tags = tags_data.get('Tags', [])
            
            # Filter based on branch
            if branch != "all":
                # Filter for specific branch
                filtered_tags = []
                for tag in tags:
                    if branch == "stable" and (tag == "stable" or re.match(r'^\d+-stable', tag)):
                        filtered_tags.append(tag)
                    elif branch == "testing" and (tag == "testing" or re.match(r'^\d+-testing', tag)):
                        filtered_tags.append(tag)
                    elif tag.startswith(branch):
                        filtered_tags.append(tag)
                tags = filtered_tags
            
            # Convert to RegistryImage objects
            images = []
            for tag in tags:
                img = RegistryImage(
                    name=image,
                    tag=tag,
                    registry=f"{registry}"
                )
                
                # Try to parse date from tag
                img.date = self._parse_date_from_tag(tag)
                
                images.append(img)
            
            # Sort by date (newest first)
            images.sort(key=lambda x: x.date or datetime.min, reverse=True)
            
            # Cache the results
            self.cache[cache_key] = (datetime.now(), images)
            
            return images
            
        except subprocess.TimeoutExpired:
            print("Timeout while querying registry")
            return []
        except Exception as e:
            print(f"Error querying registry: {e}")
            return []
    
    def _parse_date_from_tag(self, tag: str) -> Optional[datetime]:
        """
        Try to parse a date from a tag
        
        Common formats:
        - 40-stable-20240722
        - stable-20240722
        - 20240722
        """
        # Look for YYYYMMDD pattern
        date_match = re.search(r'(\d{8})', tag)
        if date_match:
            date_str = date_match.group(1)
            try:
                return datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                pass
        
        return None
    
    def get_recent_images(self, registry: str, image: str, days: int = 90, 
                         branch: str = "stable") -> List[RegistryImage]:
        """
        Get images from the last N days
        
        Args:
            registry: Registry URL
            image: Image name
            days: Number of days to look back
            branch: Branch to filter
            
        Returns:
            List of RegistryImage objects from the last N days
        """
        all_images = self.list_image_tags(registry, image, branch)
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_images = []
        
        for img in all_images:
            if img.date and img.date >= cutoff_date:
                recent_images.append(img)
            elif not img.date and len(recent_images) < 20:
                # Include some non-dated tags if we don't have many results
                recent_images.append(img)
        
        return recent_images
    
    def get_image_info_from_deployment(self, deployment) -> Tuple[str, str, str]:
        """
        Extract registry, image name, and current tag from a deployment
        
        Args:
            deployment: Deployment object with origin field
            
        Returns:
            Tuple of (registry, image_name, current_tag)
        """
        origin = deployment.origin
        
        # Parse the origin URL
        if "ghcr.io/ublue-os/" in origin:
            # Universal Blue image
            parts = origin.split("/")
            if len(parts) >= 3:
                registry = "ghcr.io/ublue-os"
                image_tag = parts[-1]
                if ":" in image_tag:
                    image_name, tag = image_tag.split(":", 1)
                else:
                    image_name = image_tag
                    tag = "stable"
                return registry, image_name, tag
        
        elif "quay.io/fedora/" in origin:
            # Fedora image
            parts = origin.split("/")
            if len(parts) >= 3:
                registry = "quay.io/fedora"
                image_tag = parts[-1]
                if ":" in image_tag:
                    image_name, tag = image_tag.split(":", 1)
                else:
                    image_name = image_tag
                    tag = "stable"
                return registry, image_name, tag
        
        # Default fallback
        return "", "", ""
    
    def check_skopeo_available(self) -> bool:
        """Check if skopeo is available"""
        try:
            # Check if we're in flatpak and use flatpak-spawn
            if 'FLATPAK_ID' in os.environ:
                cmd = ["flatpak-spawn", "--host", "skopeo", "--version"]
            else:
                cmd = ["skopeo", "--version"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False