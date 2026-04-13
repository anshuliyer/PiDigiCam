# PiDigiCam Test Suite

Comprehensive testing and demonstration tool for PiDigiCam image processing filters and enhancements.

## Overview

The `emulator.py` script demonstrates all available filters and enhancement functionalities by processing test images and generating output comparisons. It supports building for multiple target architectures (native, x86, armv8).

## Directory Structure

```
test/
├── emulator.py          # Main demonstration script
├── __init__.py          # Python package marker
├── out/                 # Output directory for processed images
└── README.md            # This file
```

## Available Filters

| ID  | Name              | Description                    |
|-----|-------------------|--------------------------------|
| 0   | None              | No filter applied (baseline)   |
| 1   | Cinematic 2000s    | Cinematic look with teal tint  |
| 2   | Washed Kodak      | Washed black & white effect    |
| 3   | Golden Hour       | Warm golden hour aesthetic     |

## Available Enhancements

| ID  | Name            | Description          |
|-----|-----------------|----------------------|
| 0   | None            | Original resolution  |
| 1   | Upscale 2x      | 2x resolution boost  |

## Prerequisites

### Build Dependencies

Install required build tools:

```bash
# Install dependencies for your target architecture(s)
cd firmware/build
./get-deps.sh              # Install native dependencies
./get-deps.sh x86          # Install x86 cross-compilation
./get-deps.sh armv8        # Install ARMv8 cross-compilation
./get-deps.sh all          # Install all architectures
```

### Setup Python Environment

```bash
cd firmware/build
source setup_venv.sh       # Sets up virtual environment
```

Or manually:

```bash
cd firmware
python3 -m venv .venv
source .venv/bin/activate
pip install Pillow matplotlib numpy  # Optional: for image utilities
```

## Building C Binaries

Build the C image processing binary:

```bash
cd firmware/processing/C/build

# Native architecture (default)
make all

# Specific architecture
make x86                   # Build 32-bit x86
make armv8                 # Build ARMv8 64-bit

# Clean
make clean
```

Generated binaries are placed in:
- `prebuilts/enhance` (native)
- `prebuilts_x86/enhance` (x86 32-bit)
- `prebuilts_v8/enhance` (ARMv8 64-bit)

## Usage

### Basic Usage

```bash
cd host/python/test

# Test all filters and enhancements
python3 emulator.py

# Test specific filter
python3 emulator.py --filter 1

# Test specific enhancement
python3 emulator.py --enhance 1

# Test specific combination
python3 emulator.py --filter 1 2 --enhance 0 1
```

### Advanced Usage

```bash
# Build and test for ARMv8
python3 emulator.py --arch armv8

# Test for x86 without rebuilding
python3 emulator.py --arch x86 --no-build

# Test multiple filters with enhancement
python3 emulator.py --filter 0 1 2 3 --enhance 1

# Show help
python3 emulator.py --help
```

## Output

### Generated Files

The `out/` directory contains:
- Processed images: `f{filter_id}_e{enhance_id}_result.jpg`
- Manifest file: `manifest_YYYYMMDD_HHMMSS.txt` (documents metadata of all outputs)

### Manifest Example

```
PiDigiCam Emulator Output Manifest
Generated: 2024-04-13T15:30:45.123456
Architecture: native
Input: /workspaces/PiDigiCam/firmware/processing/test_inputs/hd_jpeg.jpg

======================================================================

Filter: Cinematic 2000s Look
Enhancement: No enhancement (original resolution)
Output File: f1_e0_result.jpg
Filter ID: 1, Enhancement ID: 0
```

## Examples

### Example 1: Basic Demonstration
```bash
python3 emulator.py
# Generates all filter/enhancement combinations
```

### Example 2: Single Filter Test
```bash
python3 emulator.py --filter 1
# Tests filter 1 (Cinematic 2000s) with both enhancement options
# Output: f1_e0_result.jpg, f1_e1_result.jpg
```

### Example 3: Enhancement-Only Test
```bash
python3 emulator.py --enhance 1 --filter 0
# Tests upscaling enhancement with baseline filter
# Output: f0_e1_result.jpg
```

### Example 4: Cross-Platform Testing
```bash
# Test natively
python3 emulator.py --no-build

# Test for ARM
python3 emulator.py --arch armv8

# Test for x86
python3 emulator.py --arch x86
```

## Input Images

Test images are located in `firmware/processing/test_inputs/`:
- `hd_jpeg.jpg` - Main test image (HD resolution)
- `small.png` - Reference test image (smaller resolution)

## Troubleshooting

### Binary Not Found
```
Error: Binary not found at .../prebuilts/enhance
```
Solution: Build the binary first
```bash
cd firmware/processing/C/build
make all
```

### 32-bit Compilation Error (x86)
```
Error: gcc -m32: No such file or directory
```
Solution: Install multilib support
```bash
./get-deps.sh x86
# or manually:
sudo apt-get install gcc-multilib libc6-dev-i386
```

### ARM Cross-Compilation Error
```
Error: clang --target=aarch64-linux-gnu: command not found
```
Solution: Install ARM toolchain
```bash
./get-deps.sh armv8
# or manually:
sudo apt-get install gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu
```

### PIL/Pillow Import Error
```
ModuleNotFoundError: No module named 'PIL'
```
Solution: Install optional dependencies
```bash
pip install Pillow
```
Note: This is optional; the emulator works without it but won't create side-by-side comparisons.

## Architecture Reference

### Native
- Default architecture for your system
- No special dependencies beyond gcc/clang
- Fastest execution on development machine

### x86 (32-bit)
- Cross-compilation to 32-bit x86
- Useful for testing compatibility with older systems
- Requires: `gcc-multilib`, `libc6-dev-i386`

### ARMv8 (64-bit ARM)
- Cross-compilation for ARM 64-bit systems
- Target for Raspberry Pi 4, etc.
- Requires: `gcc-aarch64-linux-gnu`, `binutils-aarch64-linux-gnu`, `clang`

## Scripts Reference

### emulator.py
Main demonstration and testing script.

```
Arguments:
  --filter FILTER_IDS     Filter IDs to test (0 1 2 3)
  --enhance ENHANCE_IDS   Enhancement IDs to test (0 1)
  --arch {native,x86,armv8}  Target architecture
  --no-build              Skip building, use existing binary
  --help                  Show detailed help
```

### get-deps.sh
Build dependency installer (in `firmware/build/`).

```
Usage: ./get-deps.sh [ARCHITECTURE|all]

Arguments:
  native (default)  Install native build dependencies
  x86               Install x86 cross-compilation
  armv8             Install ARMv8 cross-compilation
  all               Install all dependencies
```

## Performance Notes

- **Native builds**: Fastest execution
- **x86 builds**: May be slightly slower than native on 64-bit systems
- **ARMv8 builds**: Cross-compiled; actual performance depends on target hardware
- **2x Upscaling**: Doubles output resolution, increases file size and processing time

## Additional Resources

- [PiDigiCam Main Documentation](../../README.md)
- [C Source Code](../../firmware/processing/C/src/)
- [Build System](../../firmware/processing/C/build/)

## License

See project root LICENSE file.
