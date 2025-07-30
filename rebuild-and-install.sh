#!/bin/bash
# Script to rebuild and install flatpaks with automatic cleanup

set -e

echo "=== Flatpak Rebuild and Install Script ==="
echo

# Function to uninstall a flatpak if it exists
uninstall_if_exists() {
    local app_id=$1
    if flatpak list | grep -q "$app_id"; then
        echo "Uninstalling existing $app_id..."
        flatpak uninstall -y "$app_id"
    else
        echo "$app_id not installed, skipping uninstall."
    fi
}

# Function to build and install a flatpak
build_and_install() {
    local app_dir=$1
    local app_id=$2
    local app_name=$3
    
    echo
    echo "=== Building $app_name ==="
    cd "$app_dir"
    
    # Clean previous build
    rm -rf .flatpak-builder build-dir repo
    
    # Build the flatpak
    flatpak run org.flatpak.Builder --force-clean build-dir "$app_id.json"
    
    # Build bundle
    flatpak build-bundle repo "${app_id}.flatpak" "$app_id" main
    
    # Uninstall old version
    uninstall_if_exists "$app_id"
    
    # Install new version
    echo "Installing $app_name..."
    flatpak install -y --user "${app_id}.flatpak"
    
    echo "✓ $app_name installed successfully!"
    cd ..
}

# Main execution
echo "Which app do you want to rebuild?"
echo "1) Rollback Tool"
echo "2) Rebase Tool"
echo "3) OS Manager"
echo "4) All three apps"
echo
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        build_and_install "rollback-app" "io.github.ublue.RollbackTool" "Atomic Rollback Tool"
        ;;
    2)
        build_and_install "rebase-app" "io.github.ublue.AtomicRebaseTool" "Atomic Rebase Tool"
        ;;
    3)
        build_and_install "os-manager-app" "io.github.ublue.AtomicOSManager" "Atomic OS Manager"
        ;;
    4)
        echo "Building all three apps..."
        build_and_install "rollback-app" "io.github.ublue.RollbackTool" "Atomic Rollback Tool"
        build_and_install "rebase-app" "io.github.ublue.AtomicRebaseTool" "Atomic Rebase Tool"
        build_and_install "os-manager-app" "io.github.ublue.AtomicOSManager" "Atomic OS Manager"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo
echo "=== All done! ==="
echo
echo "You can run the apps with:"
echo "  flatpak run io.github.ublue.RollbackTool"
echo "  flatpak run io.github.ublue.AtomicRebaseTool"
echo "  flatpak run io.github.ublue.AtomicOSManager"