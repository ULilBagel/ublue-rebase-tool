#!/bin/bash
# Quick rebuild script for the rollback tool

set -e

echo "=== Quick Rebuild: Atomic Rollback Tool ==="
echo

cd rollback-app

# Uninstall existing version
if flatpak list | grep -q "io.github.ublue.RollbackTool"; then
    echo "Uninstalling existing rollback tool..."
    flatpak uninstall -y io.github.ublue.RollbackTool
fi

# Clean and build
echo "Building rollback tool..."
rm -rf .flatpak-builder build-dir repo
flatpak run org.flatpak.Builder --force-clean build-dir io.github.ublue.RollbackTool.json
flatpak build-bundle repo io.github.ublue.RollbackTool.flatpak io.github.ublue.RollbackTool main

# Install
echo "Installing rollback tool..."
flatpak install -y --user io.github.ublue.RollbackTool.flatpak

echo
echo "✓ Rollback tool rebuilt and installed successfully!"
echo "Run with: flatpak run io.github.ublue.RollbackTool"