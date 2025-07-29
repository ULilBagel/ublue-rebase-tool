#!/bin/bash
# Build script for Atomic OS Manager only

set -e

echo "Building Atomic OS Manager..."
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-os-manager io.github.ublue.OSManager.json

echo ""
echo "Atomic OS Manager built and installed successfully!"
echo "Run with: flatpak run io.github.ublue.OSManager"