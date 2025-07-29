#!/bin/bash
# Build script for Atomic Rebase Tool only

set -e

echo "Building Atomic Rebase Tool..."
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-rebase io.github.ublue.AtomicRebaseTool.json

echo ""
echo "Atomic Rebase Tool built and installed successfully!"
echo "Run with: flatpak run io.github.ublue.AtomicRebaseTool"