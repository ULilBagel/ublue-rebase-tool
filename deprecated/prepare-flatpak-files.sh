#!/bin/bash
#
# Prepare files for Flatpak build (alternative when flatpak-builder is not available)
# This script prepares the directory structure that would be created by flatpak-builder
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Universal Blue Rebase Tool - Flatpak File Preparation${NC}"
echo "======================================================"

# Create staging directory
STAGING_DIR="flatpak-staging"
echo -e "\n${YELLOW}Creating staging directory...${NC}"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"/{bin,lib/python3.11/site-packages/ui,share/{applications,icons/hicolor/scalable/apps,metainfo,ublue-image-manager}}

# Copy application files
echo -e "\n${YELLOW}Copying application files...${NC}"

# Main executable
cp src/ublue-image-manager.py "$STAGING_DIR/bin/ublue-image-manager"
chmod +x "$STAGING_DIR/bin/ublue-image-manager"

# Python modules
cp src/ublue_image_manager.py "$STAGING_DIR/lib/python3.11/site-packages/"
cp src/ublue-image-manager.py "$STAGING_DIR/lib/python3.11/site-packages/"
cp src/command_executor.py "$STAGING_DIR/lib/python3.11/site-packages/"
cp src/deployment_manager.py "$STAGING_DIR/lib/python3.11/site-packages/"
cp src/progress_tracker.py "$STAGING_DIR/lib/python3.11/site-packages/"
cp src/history_manager.py "$STAGING_DIR/lib/python3.11/site-packages/"

# UI module
cp src/ui/__init__.py "$STAGING_DIR/lib/python3.11/site-packages/ui/"
cp src/ui/confirmation_dialog.py "$STAGING_DIR/lib/python3.11/site-packages/ui/"

# Desktop file
cp data/ublue-image-manager.desktop "$STAGING_DIR/share/applications/io.github.ublue.RebaseTool.desktop"

# Icon
cp data/icons/io.github.ublue.RebaseTool.svg "$STAGING_DIR/share/icons/hicolor/scalable/apps/"

# Metainfo
cp data/metainfo/io.github.ublue.RebaseTool.metainfo.xml "$STAGING_DIR/share/metainfo/"

# Web content
cp -r data/web/* "$STAGING_DIR/share/ublue-image-manager/"

# Fix shebang in main executable
sed -i '1s|.*|#!/usr/bin/env python3|' "$STAGING_DIR/bin/ublue-image-manager"

echo -e "\n${GREEN}File preparation completed!${NC}"
echo "======================================================"
echo -e "\nDirectory structure created in: ${YELLOW}$STAGING_DIR/${NC}"
echo -e "\nThis shows the structure that would be installed by Flatpak:"
tree "$STAGING_DIR" 2>/dev/null || find "$STAGING_DIR" -type f | sort

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Install flatpak-builder:"
echo "   ${YELLOW}sudo dnf install flatpak-builder${NC}"
echo ""
echo "2. Run the full build:"
echo "   ${YELLOW}./build-flatpak.sh${NC}"
echo ""
echo "3. Or manually create a bundle (requires flatpak-builder):"
echo "   ${YELLOW}flatpak-builder --force-clean build-flatpak io.github.ublue.RebaseTool.json${NC}"

# Create a tarball for manual distribution
echo -e "\n${YELLOW}Creating tarball for manual distribution...${NC}"
tar -czf ublue-rebase-tool-flatpak-files.tar.gz -C "$STAGING_DIR" .
echo -e "${GREEN}Created: ublue-rebase-tool-flatpak-files.tar.gz${NC}"

# Validate that all required files exist
echo -e "\n${YELLOW}Validating file structure...${NC}"
REQUIRED_FILES=(
    "bin/ublue-image-manager"
    "lib/python3.11/site-packages/ublue_image_manager.py"
    "lib/python3.11/site-packages/command_executor.py"
    "lib/python3.11/site-packages/deployment_manager.py"
    "lib/python3.11/site-packages/progress_tracker.py"
    "lib/python3.11/site-packages/history_manager.py"
    "lib/python3.11/site-packages/ui/__init__.py"
    "lib/python3.11/site-packages/ui/confirmation_dialog.py"
    "share/applications/io.github.ublue.RebaseTool.desktop"
    "share/icons/hicolor/scalable/apps/io.github.ublue.RebaseTool.svg"
    "share/metainfo/io.github.ublue.RebaseTool.metainfo.xml"
    "share/ublue-image-manager/index.html"
)

ALL_GOOD=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$STAGING_DIR/$file" ]; then
        echo -e "${RED}Missing: $file${NC}"
        ALL_GOOD=false
    else
        echo -e "${GREEN}✓ $file${NC}"
    fi
done

if $ALL_GOOD; then
    echo -e "\n${GREEN}All required files are present!${NC}"
else
    echo -e "\n${RED}Some files are missing!${NC}"
    exit 1
fi