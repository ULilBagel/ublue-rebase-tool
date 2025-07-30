#!/bin/bash
# Universal rebuild script for any of the three tools

set -e

echo "=== Tool Rebuild Script ==="
echo
echo "Which tool do you want to rebuild?"
echo "1) Rollback Tool"
echo "2) Rebase Tool"  
echo "3) OS Manager"
echo
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        APP_ID="io.github.ublue.RollbackTool"
        APP_NAME="Atomic Rollback Tool"
        BUILD_DIR="build-dir-rollback"
        JSON_FILE="io.github.ublue.RollbackTool.json"
        ;;
    2)
        APP_ID="io.github.ublue.AtomicRebaseTool"
        APP_NAME="Atomic Rebase Tool"
        BUILD_DIR="build-dir-rebase"
        JSON_FILE="io.github.ublue.AtomicRebaseTool.json"
        ;;
    3)
        APP_ID="io.github.ublue.OSManager"
        APP_NAME="Atomic OS Manager"
        BUILD_DIR="build-dir-os-manager"
        JSON_FILE="io.github.ublue.OSManager.json"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo
echo "=== Rebuilding $APP_NAME ==="

# Uninstall if exists
if flatpak list | grep -q "$APP_ID"; then
    echo "Uninstalling existing $APP_NAME..."
    flatpak uninstall -y "$APP_ID"
fi

# Build and install
echo "Building $APP_NAME..."
flatpak run org.flatpak.Builder --user --install --force-clean "$BUILD_DIR" "$JSON_FILE"

echo
echo "✓ $APP_NAME rebuilt and installed successfully!"
echo "Run with: flatpak run $APP_ID"