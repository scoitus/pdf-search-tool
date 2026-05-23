#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "=== PDF Search Tool Build Script ==="
echo ""

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: virtualenv not found at $VENV_DIR"
    echo "Set it up first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Clean previous build artifacts
rm -rf "$PROJECT_DIR/build" "$PROJECT_DIR/dist"

echo "Building with PyInstaller..."
echo ""

pyinstaller "$PROJECT_DIR/pyinstaller.spec" \
    --distpath "$PROJECT_DIR/dist" \
    --workpath "$PROJECT_DIR/build" \
    --clean \
    --noconfirm

echo ""
echo "Build complete: $PROJECT_DIR/dist/PDF Search Tool.app"
echo ""
echo "To install, run: ./scripts/install.sh"
