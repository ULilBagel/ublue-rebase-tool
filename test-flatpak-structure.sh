#!/bin/bash
#
# Test the Flatpak directory structure locally
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing Flatpak Structure${NC}"
echo "========================="

STAGING_DIR="flatpak-staging"

if [ ! -d "$STAGING_DIR" ]; then
    echo -e "${RED}Error: Staging directory not found. Run ./prepare-flatpak-files.sh first${NC}"
    exit 1
fi

# Test Python imports
echo -e "\n${YELLOW}Testing Python imports...${NC}"

export PYTHONPATH="$STAGING_DIR/lib/python3.11/site-packages:$PYTHONPATH"

python3 -c "
import sys
sys.path.insert(0, '$STAGING_DIR/lib/python3.11/site-packages')
try:
    import ublue_image_manager
    print('✓ ublue_image_manager imported successfully')
    import command_executor
    print('✓ command_executor imported successfully')
    import deployment_manager
    print('✓ deployment_manager imported successfully')
    import progress_tracker
    print('✓ progress_tracker imported successfully')
    import history_manager
    print('✓ history_manager imported successfully')
    from ui import confirmation_dialog
    print('✓ ui.confirmation_dialog imported successfully')
    print('\nAll imports successful!')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
"

# Check executable
echo -e "\n${YELLOW}Checking main executable...${NC}"
if [ -x "$STAGING_DIR/bin/ublue-image-manager" ]; then
    echo -e "${GREEN}✓ Main executable is properly set${NC}"
    head -n 1 "$STAGING_DIR/bin/ublue-image-manager"
else
    echo -e "${RED}✗ Main executable is not executable${NC}"
fi

# Check desktop file
echo -e "\n${YELLOW}Checking desktop file...${NC}"
if grep -q "Exec=ublue-image-manager" "$STAGING_DIR/share/applications/io.github.ublue.RebaseTool.desktop"; then
    echo -e "${GREEN}✓ Desktop file has correct Exec line${NC}"
else
    echo -e "${RED}✗ Desktop file has incorrect Exec line${NC}"
fi

# Check icon
echo -e "\n${YELLOW}Checking icon...${NC}"
if [ -f "$STAGING_DIR/share/icons/hicolor/scalable/apps/io.github.ublue.RebaseTool.svg" ]; then
    echo -e "${GREEN}✓ Icon file exists${NC}"
else
    echo -e "${RED}✗ Icon file missing${NC}"
fi

# Check web content
echo -e "\n${YELLOW}Checking web content...${NC}"
if [ -f "$STAGING_DIR/share/ublue-image-manager/index.html" ]; then
    echo -e "${GREEN}✓ Web content exists${NC}"
else
    echo -e "${RED}✗ Web content missing${NC}"
fi

echo -e "\n${GREEN}Structure validation complete!${NC}"
echo "=============================="
echo -e "\n${YELLOW}The files are ready for Flatpak packaging.${NC}"
echo "To build the actual Flatpak, you need to:"
echo "1. Install flatpak-builder on a system with Flatpak support"
echo "2. Run: flatpak-builder --force-clean build-flatpak io.github.ublue.RebaseTool.json"
echo "3. Create bundle: flatpak build-bundle repo ublue-rebase-tool.flatpak io.github.ublue.RebaseTool"