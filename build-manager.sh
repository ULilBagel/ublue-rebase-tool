#!/bin/bash
# Build script for Atomic Image Manager only

set -e

echo "Building Atomic Image Manager..."
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-manager io.github.ublue.RebaseTool.json

echo ""
echo "Atomic Image Manager built and installed successfully!"
echo "Run with: flatpak run io.github.ublue.RebaseTool"