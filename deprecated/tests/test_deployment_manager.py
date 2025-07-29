#!/usr/bin/env python3
"""
Unit tests for DeploymentManager service
Tests parsing of various rpm-ostree status formats and deployment management
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import subprocess
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from deployment_manager import DeploymentManager, Deployment


class TestDeploymentManager(unittest.TestCase):
    """Test cases for DeploymentManager service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = DeploymentManager()
        
        # Sample rpm-ostree status output
        self.sample_status = {
            "deployments": [
                {
                    "checksum": "abcdef1234567890abcdef1234567890abcdef1234567890",
                    "origin": "ghcr.io/ublue-os/bluefin:latest",
                    "version": "40.20240720.0",
                    "timestamp": 1721500000,
                    "booted": True,
                    "pinned": False
                },
                {
                    "checksum": "1234567890abcdef1234567890abcdef1234567890abcdef",
                    "origin": "ghcr.io/ublue-os/aurora:latest", 
                    "version": "40.20240715.0",
                    "timestamp": 1721000000,
                    "booted": False,
                    "pinned": False
                },
                {
                    "checksum": "fedcba0987654321fedcba0987654321fedcba0987654321",
                    "origin": "ghcr.io/ublue-os/bazzite:stable",
                    "version": "40.20240710.0",
                    "timestamp": 1720500000,
                    "booted": False,
                    "pinned": True
                }
            ]
        }
    
    def test_deployment_from_json(self):
        """Test creating Deployment from JSON data"""
        deployment_data = self.sample_status["deployments"][0]
        deployment = Deployment.from_json(deployment_data, 0)
        
        self.assertEqual(deployment.id, "abcdef123456")  # First 12 chars
        self.assertEqual(deployment.origin, "ghcr.io/ublue-os/bluefin:latest")
        self.assertEqual(deployment.version, "40.20240720.0")
        self.assertTrue(deployment.is_booted)
        self.assertFalse(deployment.is_pinned)
        self.assertEqual(deployment.index, 0)
        
        # Check timestamp formatting
        self.assertIn("2024", deployment.timestamp)
    
    @patch('subprocess.run')
    def test_get_all_deployments_success(self, mock_run):
        """Test successful retrieval of all deployments"""
        # Mock successful rpm-ostree status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(self.sample_status)
        mock_run.return_value = mock_result
        
        # Get deployments
        deployments = self.manager.get_all_deployments()
        
        # Verify
        self.assertEqual(len(deployments), 3)
        self.assertTrue(deployments[0].is_booted)
        self.assertEqual(deployments[0].origin, "ghcr.io/ublue-os/bluefin:latest")
        self.assertEqual(deployments[1].origin, "ghcr.io/ublue-os/aurora:latest")
        self.assertTrue(deployments[2].is_pinned)
        
        # Verify subprocess call
        mock_run.assert_called_once_with(
            ['rpm-ostree', 'status', '--json'],
            capture_output=True,
            text=True,
            timeout=5
        )
    
    @patch('subprocess.run')
    def test_get_all_deployments_fallback_demo(self, mock_run):
        """Test fallback to demo data when rpm-ostree unavailable"""
        # Mock command not found
        mock_run.side_effect = FileNotFoundError()
        
        # Get deployments
        deployments = self.manager.get_all_deployments()
        
        # Should return demo data
        self.assertEqual(len(deployments), 3)
        self.assertEqual(deployments[0].id, "demo12345678")
        self.assertTrue(deployments[0].is_booted)
    
    @patch('subprocess.run')
    def test_get_current_deployment(self, mock_run):
        """Test getting current booted deployment"""
        # Mock successful status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(self.sample_status)
        mock_run.return_value = mock_result
        
        # Get current deployment
        current = self.manager.get_current_deployment()
        
        self.assertIsNotNone(current)
        self.assertTrue(current.is_booted)
        self.assertEqual(current.origin, "ghcr.io/ublue-os/bluefin:latest")
    
    def test_format_deployment_info(self):
        """Test formatting deployment for display"""
        deployment = Deployment(
            id="abc123def456",
            origin="ghcr.io/ublue-os/bluefin:latest",
            version="40.20240720.0",
            timestamp="2024-07-20 10:00:00",
            is_booted=True,
            is_pinned=False,
            index=0
        )
        
        info = self.manager.format_deployment_info(deployment)
        
        self.assertEqual(info['title'], "Deployment 1")
        self.assertEqual(info['id'], "abc123def456")
        self.assertIn("Currently Booted", info['status'])
        self.assertEqual(info['image_name'], "Universal Blue - Bluefin")
    
    def test_format_deployment_info_pinned(self):
        """Test formatting pinned deployment"""
        deployment = Deployment(
            id="xyz789abc123",
            origin="fedora:40",
            version="40",
            timestamp="2024-07-15 08:00:00",
            is_booted=False,
            is_pinned=True,
            index=2
        )
        
        info = self.manager.format_deployment_info(deployment)
        
        self.assertIn("Pinned", info['status'])
        self.assertEqual(info['image_name'], "fedora:40")
    
    @patch('subprocess.run')
    def test_generate_rollback_command_previous(self, mock_run):
        """Test generating rollback command for previous deployment"""
        # Mock status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(self.sample_status)
        mock_run.return_value = mock_result
        
        # Get rollback command for index 1 (previous)
        command = self.manager.generate_rollback_command("1234567890ab")
        
        self.assertEqual(command, ["rpm-ostree", "rollback"])
    
    @patch('subprocess.run')
    def test_generate_rollback_command_specific(self, mock_run):
        """Test generating rollback command for specific deployment"""
        # Mock status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(self.sample_status)
        mock_run.return_value = mock_result
        
        # Get rollback command for index 2 (not previous)
        command = self.manager.generate_rollback_command("fedcba098765")
        
        self.assertEqual(command, ["rpm-ostree", "deploy", "fedcba098765"])
    
    @patch('subprocess.run')
    def test_generate_rollback_command_current(self, mock_run):
        """Test that current deployment cannot be rolled back to"""
        # Mock status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(self.sample_status)
        mock_run.return_value = mock_result
        
        # Try to rollback to current
        command = self.manager.generate_rollback_command("abcdef123456")
        
        self.assertIsNone(command)
    
    @patch('subprocess.run')
    def test_validate_deployment_selection_valid(self, mock_run):
        """Test validation of valid deployment selection"""
        # Mock status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(self.sample_status)
        mock_run.return_value = mock_result
        
        # Validate non-current deployment
        valid, error = self.manager.validate_deployment_selection("1234567890ab")
        
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    @patch('subprocess.run')
    def test_validate_deployment_selection_current(self, mock_run):
        """Test validation rejects current deployment"""
        # Mock status
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(self.sample_status)
        mock_run.return_value = mock_result
        
        # Try to select current deployment
        valid, error = self.manager.validate_deployment_selection("abcdef123456")
        
        self.assertFalse(valid)
        self.assertIn("currently booted", error)
    
    def test_validate_deployment_selection_not_found(self):
        """Test validation with non-existent deployment"""
        # Use demo data
        valid, error = self.manager.validate_deployment_selection("nonexistent")
        
        self.assertFalse(valid)
        self.assertIn("not found", error)
    
    @patch('subprocess.run')
    def test_deployment_with_missing_fields(self, mock_run):
        """Test handling deployments with missing fields"""
        # Status with minimal fields
        minimal_status = {
            "deployments": [
                {
                    "checksum": "minimal1234567890",
                    "booted": True
                },
                {
                    "origin": "some-image:latest",
                    "version": "unknown"
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(minimal_status)
        mock_run.return_value = mock_result
        
        # Should handle gracefully
        deployments = self.manager.get_all_deployments()
        
        self.assertEqual(len(deployments), 2)
        self.assertEqual(deployments[0].origin, "Unknown")
        self.assertEqual(deployments[0].version, "Unknown")
        self.assertEqual(deployments[1].id, "")  # Empty checksum


if __name__ == '__main__':
    unittest.main()