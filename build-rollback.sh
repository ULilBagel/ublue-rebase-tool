#!/bin/bash
# Build script for Atomic Rollback Tool only

set -e

echo "Building Atomic Rollback Tool..."
flatpak run org.flatpak.Builder --user --install --force-clean build-dir-rollback io.github.ublue.RollbackTool.json

echo ""
echo "Atomic Rollback Tool built and installed successfully!"
echo "Run with: flatpak run io.github.ublue.RollbackTool"