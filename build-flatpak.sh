#!/bin/bash
#
# Build script for Universal Blue Rebase Tool Flatpak
# This script builds the Flatpak for local testing and Flathub submission
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Universal Blue Rebase Tool - Flatpak Build Script${NC}"
echo "=================================================="

# Check for required tools
echo -e "\n${YELLOW}Checking requirements...${NC}"

if ! command -v flatpak &> /dev/null; then
    echo -e "${RED}Error: flatpak is not installed${NC}"
    echo "Please install flatpak first:"
    echo "  sudo dnf install flatpak"
    exit 1
fi

if ! command -v flatpak-builder &> /dev/null; then
    echo -e "${RED}Error: flatpak-builder is not installed${NC}"
    echo "Please install flatpak-builder first:"
    echo "  sudo dnf install flatpak-builder"
    exit 1
fi

# Add Flathub repository if not already added
echo -e "\n${YELLOW}Ensuring Flathub repository is configured...${NC}"
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install required runtimes
echo -e "\n${YELLOW}Installing required runtimes...${NC}"
flatpak install -y flathub org.gnome.Platform//46 org.gnome.Sdk//46

# Create build directory
BUILD_DIR="build-flatpak"
REPO_DIR="repo"

echo -e "\n${YELLOW}Creating build directories...${NC}"
rm -rf "$BUILD_DIR" "$REPO_DIR"
mkdir -p "$BUILD_DIR" "$REPO_DIR"

# Build the Flatpak
echo -e "\n${YELLOW}Building Flatpak...${NC}"
flatpak-builder --force-clean --repo="$REPO_DIR" "$BUILD_DIR" io.github.ublue.RebaseTool.json

# Create a bundle for distribution
echo -e "\n${YELLOW}Creating Flatpak bundle...${NC}"
flatpak build-bundle "$REPO_DIR" ublue-rebase-tool.flatpak io.github.ublue.RebaseTool

echo -e "\n${GREEN}Build completed successfully!${NC}"
echo "=================================================="
echo -e "\nTo install the Flatpak locally for testing:"
echo -e "  ${YELLOW}flatpak install --user ublue-rebase-tool.flatpak${NC}"
echo -e "\nTo run the application:"
echo -e "  ${YELLOW}flatpak run io.github.ublue.RebaseTool${NC}"
echo -e "\nTo uninstall:"
echo -e "  ${YELLOW}flatpak uninstall --user io.github.ublue.RebaseTool${NC}"

# Validate manifest for Flathub
echo -e "\n${YELLOW}Validating manifest for Flathub submission...${NC}"

# Check for common issues
if grep -q "type.*dir" io.github.ublue.RebaseTool.json; then
    echo -e "${YELLOW}Warning: Using 'dir' source type - Flathub requires git/archive sources${NC}"
    echo "For Flathub submission, you'll need to:"
    echo "1. Push your code to a git repository"
    echo "2. Create a release/tag"
    echo "3. Update the manifest to use git or archive source type"
fi

echo -e "\n${GREEN}Next steps for Flathub submission:${NC}"
echo "1. Fork https://github.com/flathub/flathub"
echo "2. Create a new branch for your app"
echo "3. Add your manifest (with proper source URLs)"
echo "4. Submit a pull request"
echo "5. Address any review feedback"

echo -e "\n${YELLOW}Manifest location:${NC} io.github.ublue.RebaseTool.json"
echo -e "${YELLOW}Bundle location:${NC} ublue-rebase-tool.flatpak"