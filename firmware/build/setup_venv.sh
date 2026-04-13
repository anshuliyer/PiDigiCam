#!/bin/bash

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Project root is one level up from build/
FIRMWARE_ROOT="$(dirname "$SCRIPT_DIR")"

# Define venv path in firmware/
VENV_PATH="$FIRMWARE_ROOT/.venv"

echo "------------------------------------------------"
echo "Setting up PiDigiCam Firmware Environment"
echo "Venv path: $VENV_PATH"
echo "------------------------------------------------"

# Create venv
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
else
    echo "Virtual environment already exists."
fi

# Activate venv
# Note: On some systems, source might not work if script is run with 'sh', so we use '.'
. "$VENV_PATH/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Checking for requirements files..."
REQUIREMENTS_FILES=(
    "$FIRMWARE_ROOT/processing/requirements.txt"
    "$FIRMWARE_ROOT/requirements.txt"
)

for REQ in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$REQ" ]; then
        echo "Installing dependencies from $REQ..."
        pip install -r "$REQ"
    fi
done

echo "------------------------------------------------"
echo "Setup complete!"
echo "To activate the environment, run:"
echo "source firmware/.venv/bin/activate"
echo "------------------------------------------------"
