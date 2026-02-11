#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo "=== PDF Search Tool Build Script ==="
echo ""

# Activate venv
source "$VENV_DIR/bin/activate"

# Clean previous build
rm -rf "$PROJECT_DIR/build" "$PROJECT_DIR/dist"

echo "Building with PyInstaller..."
echo ""

# Run PyInstaller
pyinstaller "$PROJECT_DIR/pyinstaller.spec" \
    --distpath "$PROJECT_DIR/dist" \
    --workpath "$PROJECT_DIR/build" \
    --clean

echo ""
echo "Build complete: $PROJECT_DIR/dist/PDF Search Tool.app"
echo ""
echo "To install, run: ./scripts/install.sh"
