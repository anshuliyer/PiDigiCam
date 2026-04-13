# Build Instructions

This directory contains build scripts for the image enhancement tool targeting different architectures.

## Project Structure

```
firmware/processing/C/
├── src/
│   ├── hdrs/           # Header files
│   │   ├── cnn_inference.h
│   │   ├── stb_image.h
│   │   └── stb_image_write.h
│   ├── cnn_inference.c # CNN inference implementation
│   └── main.c          # Main application
├── build/              # Build scripts and Makefile
├── models/             # Model files
├── prebuilts/          # x86-64 binaries
├── prebuilts_v8/       # ARMv8 binaries
└── prebuilts_x86/      # 32-bit x86 binaries
```

## Features

The image enhancer now includes a **cinematic 2000s filter** that applies the following effects:

- **Exposure**: -0.5 (darker image)
- **Contrast**: +25% with S-curve (enhanced midtone contrast)
- **Saturation**: -15% (more muted colors)
- **Highlights**: -20% (reduced highlight intensity)
- **Shadows**: -15% (lifted shadow detail)
- **Gamma**: 1.1 (slightly brighter midtones)
- **Grain**: +0.02 noise (film-like texture)
- **Vignette**: 30% (darkened corners)
- **Color Tint**: Slight warm tone (R: +2%, G: 0%, B: -2%)

The filter creates a nostalgic, film-like aesthetic reminiscent of early 2000s digital cinema.

- **Default (x86-64)**: Native build for the host system (64-bit x86).
- **armv8**: Cross-compiled for ARM64 (ARMv8) architecture.
- **x86**: 32-bit x86 architecture.

## Using Make

### Default build (x86-64)
```bash
make clean && make
```

### ARMv8 build
```bash
make clean && make armv8
```

### x86 (32-bit) build
```bash
make clean && make x86
```

## Using Build Script

The `build.sh` script accepts an architecture argument:

```bash
./build.sh          # Default (x86-64)
./build.sh armv8    # ARM64
./build.sh x86      # 32-bit x86
```

## Output

Executables are placed in architecture-specific directories:
- `../prebuilts/enhance` (default, x86-64)
- `../prebuilts_v8/enhance` (ARMv8)
- `../prebuilts_x86/enhance` (32-bit x86)

## Requirements

- For ARMv8: clang with ARM64 target support
- For x86: gcc with multilib support (-m32)
- For default: standard gcc

## Usage

```bash
./enhance <input> <output> [--enhance=1] [--filter=0|1|2|3]
```

### Options

- `--enhance=1`: Apply 2x upscaling enhancement
- `--filter=0`: No filter (default)
- `--filter=1`: Apply cinematic 2000s filter
- `--filter=2`: Apply washed Kodak black-and-white filter
- `--filter=3`: Apply golden hour filter

### Examples

```bash
# Basic processing (no enhancement, no filter)
./enhance input.jpg output.png

# Apply enhancement only
./enhance input.jpg output.png --enhance=1

# Apply filter only
./enhance input.jpg output.png --filter=1

# Apply both enhancement and filter
./enhance input.jpg output.png --enhance=1 --filter=1
```