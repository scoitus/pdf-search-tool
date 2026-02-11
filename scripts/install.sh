#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SRC="$PROJECT_DIR/dist/PDF Search Tool.app"
APP_DEST="/Applications/_MY APPS/PDF Search Tool.app"

if [ ! -d "$APP_SRC" ]; then
    echo "Error: Build the app first with ./scripts/build.sh"
    exit 1
fi

# Remove old version if it exists
if [ -d "$APP_DEST" ]; then
    echo "Removing previous installation..."
    rm -rf "$APP_DEST"
fi

echo "Installing to $APP_DEST..."
cp -R "$APP_SRC" "$APP_DEST"

echo ""
echo "Done! PDF Search Tool installed to:"
echo "  $APP_DEST"
