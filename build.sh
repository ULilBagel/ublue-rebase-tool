#!/bin/bash
set -e

APP_ID="io.github.ublue.RebaseTool"
BUILD_DIR="build"
REPO_DIR="repo"

echo "🏗️  Building Universal Blue Rebase Tool..."

rm -rf $BUILD_DIR $REPO_DIR

flatpak-builder --force-clean --sandbox --user --install-deps-from=flathub \
    --ccache --repo=$REPO_DIR $BUILD_DIR $APP_ID.json

echo "🔧 Installing locally..."
flatpak --user remote-add --if-not-exists --no-gpg-verify local-repo $REPO_DIR
flatpak --user install --reinstall local-repo $APP_ID

echo "✅ Build complete! Run with: flatpak run $APP_ID"
