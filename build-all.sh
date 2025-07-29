#!/bin/bash
# Build script for all applications

set -e

echo "Building all applications..."

# Build Atomic Image Manager
echo ""
echo "=== Building Atomic Image Manager ==="
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-manager io.github.ublue.RebaseTool.json

# Build Atomic Rollback Tool
echo ""
echo "=== Building Atomic Rollback Tool ==="
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-rollback io.github.ublue.RollbackTool.json

# Build Atomic Rebase Tool
echo ""
echo "=== Building Atomic Rebase Tool ==="
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-rebase io.github.ublue.AtomicRebaseTool.json

# Build Atomic OS Manager
echo ""
echo "=== Building Atomic OS Manager ==="
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-os-manager io.github.ublue.OSManager.json

echo ""
echo "All applications built and installed successfully!"
echo ""
echo "You can run them with:"
echo "  flatpak run io.github.ublue.RebaseTool       # Full image manager"
echo "  flatpak run io.github.ublue.RollbackTool     # Rollback tool only"
echo "  flatpak run io.github.ublue.AtomicRebaseTool  # Rebase tool only"
echo "  flatpak run io.github.ublue.OSManager         # OS-specific configurator"