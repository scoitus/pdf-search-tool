#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== PDF Search Tool Build Script ==="
echo ""

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is not installed."
    echo "Install it first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

cd "$PROJECT_DIR"

# Clean previous build artifacts
rm -rf "$PROJECT_DIR/build" "$PROJECT_DIR/dist"

echo "Building with PyInstaller..."
echo ""

# uv installs the locked dependencies (including PyInstaller, a dev
# dependency) into .venv if needed, then runs PyInstaller from it.
uv run pyinstaller "$PROJECT_DIR/pyinstaller.spec" \
    --distpath "$PROJECT_DIR/dist" \
    --workpath "$PROJECT_DIR/build" \
    --clean \
    --noconfirm

echo ""
echo "Build complete: $PROJECT_DIR/dist/PDF Search Tool.app"
