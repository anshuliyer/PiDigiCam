#!/usr/bin/env python3
"""
PiDigiCam Emulator: Demonstrates all filter and enhancement functionalities
Generates before/after comparisons of available filters and enhancements
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Define project paths
SCRIPT_DIR = Path(__file__).parent.resolve()
FIRMWARE_ROOT = SCRIPT_DIR.parent.parent.parent / "firmware"
INPUT_IMAGE = FIRMWARE_ROOT / "processing" / "test_inputs" / "hd_jpeg.jpg"
OUTPUT_DIR = SCRIPT_DIR / "out"
C_BUILD_DIR = FIRMWARE_ROOT / "processing" / "C" / "build"
PREBUILTS_DIR = FIRMWARE_ROOT / "processing" / "C" / "prebuilts"

# Filter configurations
FILTERS = {
    0: {"name": "none", "desc": "No filter applied"},
    1: {"name": "cinematic_2000s", "desc": "Cinematic 2000s Look"},
    2: {"name": "washed_kodak", "desc": "Washed Kodak Black & White"},
    3: {"name": "golden_hour", "desc": "Golden Hour"},
}

ENHANCEMENTS = {
    0: {"name": "none", "desc": "No enhancement (original resolution)"},
    1: {"name": "upscale_2x", "desc": "2x Upscaling Enhancement"},
}


def find_enhance_binary(arch=None):
    """Locate the compiled enhance binary for the specified architecture"""
    if arch is None or arch == "native":
        prebuilts = PREBUILTS_DIR
    elif arch == "armv8":
        prebuilts = FIRMWARE_ROOT / "processing" / "C" / "prebuilts_v8"
    elif arch == "x86":
        prebuilts = FIRMWARE_ROOT / "processing" / "C" / "prebuilts_x86"
    else:
        raise ValueError(f"Unknown architecture: {arch}")

    binary = prebuilts / "enhance"
    if not binary.exists():
        raise FileNotFoundError(
            f"Binary not found at {binary}. "
            f"Please build with 'make' in {C_BUILD_DIR}"
        )
    return binary


def build_c_binary(arch=None):
    """Build the C binary if needed"""
    print(f"Building C binary for {arch or 'native'} architecture...")
    cwd = C_BUILD_DIR
    if arch and arch != "native":
        result = subprocess.run(
            ["make", arch],
            cwd=cwd,
            capture_output=True,
            text=True
        )
    else:
        result = subprocess.run(
            ["make", "all"],
            cwd=cwd,
            capture_output=True,
            text=True
        )

    if result.returncode != 0:
        print(f"Build failed:\n{result.stderr}")
        return False
    print(f"✓ Build successful")
    return True


def process_image(input_path, output_path, filter_type=0, enhance=0, binary_path=None):
    """Process image using the C binary"""
    if binary_path is None:
        binary_path = find_enhance_binary()

    cmd = [str(binary_path), str(input_path), str(output_path)]
    if enhance:
        cmd.append("--enhance=1")
    cmd.append(f"--filter={filter_type}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error processing image: {result.stderr}")
        return False
    return True


def create_side_by_side_comparison(before_path, after_path, output_path, add_labels=True):
    """
    Create a side-by-side comparison image using PIL
    Returns True if successful, False otherwise
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        before = Image.open(before_path)
        after = Image.open(after_path)

        # Calculate composite dimensions
        bar_height = 40 if add_labels else 0
        gap = 20
        
        if before.size != after.size:
            total_width = before.width + after.width + gap
            max_height = max(before.height, after.height)
        else:
            total_width = before.width * 2 + gap
            max_height = before.height

        # Create composite with space for labels
        composite_height = max_height + bar_height
        composite = Image.new("RGB", (total_width, composite_height), color="white")
        
        # Paste images
        composite.paste(before, (0, bar_height))
        composite.paste(after, (before.width + gap, bar_height))

        # Add labels if requested
        if add_labels:
            try:
                draw = ImageDraw.Draw(composite)
                # Try to use a decent font, fall back to default
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                except:
                    font = ImageFont.load_default()
                
                # Draw labels on the colored bar
                draw.rectangle([(0, 0), (total_width, bar_height)], fill="#f0f0f0")
                draw.text((10, 10), "BEFORE", fill="black", font=font)
                draw.text((before.width + gap + 10, 10), "AFTER", fill="black", font=font)
            except:
                pass  # If labeling fails, just skip it

        composite.save(output_path, quality=90)
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"  Warning: Could not create comparison - {e}")
        return False


def run_demonstrations(filters=None, enhancements=None, arch=None, build=True):
    """Run demonstrations for all or specified filters/enhancements"""
    if filters is None:
        filters = list(FILTERS.keys())
    if enhancements is None:
        enhancements = list(ENHANCEMENTS.keys())

    # Verify input image exists
    if not INPUT_IMAGE.exists():
        print(f"✗ Input image not found: {INPUT_IMAGE}")
        sys.exit(1)

    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"PiDigiCam Emulator - Filter & Enhancement Demonstration")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Input Image: {INPUT_IMAGE}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Architecture: {arch or 'native'}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Try to find or build binary
    try:
        binary_path = find_enhance_binary(arch)
    except FileNotFoundError as e:
        if build:
            print(f"⚠ {e}")
            print("Attempting to build...")
            if not build_c_binary(arch):
                print("✗ Failed to build C binary")
                sys.exit(1)
            binary_path = find_enhance_binary(arch)
        else:
            print(f"✗ {e}")
            sys.exit(1)

    print(f"✓ Using binary: {binary_path}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    comparisons = []

    # Create baseline images first (no filter, no enhancement) as reference
    baseline_no_enhance_path = OUTPUT_DIR / "baseline_f0_e0.jpg"
    baseline_with_enhance_path = OUTPUT_DIR / "baseline_f0_e1.jpg"
    
    baseline_created = False
    if not baseline_no_enhance_path.exists():
        print("Creating baseline reference images...")
        if process_image(INPUT_IMAGE, baseline_no_enhance_path, filter_type=0, enhance=0, binary_path=binary_path):
            baseline_created = True
            print("✓ Baseline created (no filter, no enhancement)\n")
        else:
            print("⚠ Could not create baseline\n")
    else:
        baseline_created = True

    # Test each combination
    for enhance in enhancements:
        for filter_id in filters:
            filter_info = FILTERS[filter_id]
            enhance_info = ENHANCEMENTS[enhance]

            print(f"Processing: {filter_info['desc']:30} + {enhance_info['desc']:30}...", end=" ", flush=True)

            # Generate unique filenames
            config_str = f"f{filter_id}_e{enhance}"
            output_name = f"{config_str}_result.jpg"
            output_path = OUTPUT_DIR / output_name

            # Process image
            if process_image(INPUT_IMAGE, output_path, filter_type=filter_id, enhance=enhance, binary_path=binary_path):
                print("✓", end="")
                results.append({
                    "filter": filter_id,
                    "filter_name": filter_info["name"],
                    "filter_desc": filter_info["desc"],
                    "enhance": enhance,
                    "enhance_name": enhance_info["name"],
                    "enhance_desc": enhance_info["desc"],
                    "output_file": output_name,
                })
                
                # Create side-by-side comparison if this isn't the baseline and PIL is available
                if baseline_created and (filter_id != 0 or enhance != 0):
                    baseline_ref = baseline_with_enhance_path if enhance == 1 else baseline_no_enhance_path
                    
                    # Generate comparison filename
                    if filter_id == 0:
                        # Enhancement-only comparison
                        comparison_name = f"comparison_enhancement_2x.jpg"
                    else:
                        # Filter-based comparison
                        enhance_suffix = "_upscaled" if enhance == 1 else ""
                        comparison_name = f"comparison_{filter_info['name']}{enhance_suffix}.jpg"
                    
                    comparison_path = OUTPUT_DIR / comparison_name
                    print("", end="")
                    if create_side_by_side_comparison(str(baseline_ref), str(output_path), str(comparison_path)):
                        print(f" [→ {comparison_name}]", end="")
                        comparisons.append({
                            "filter": filter_id,
                            "enhance": enhance,
                            "comparison_file": comparison_name,
                        })
                print()
            else:
                print("✗")

    # Generate summary
    print()
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Results Summary ({len(results)} images, {len(comparisons)} comparisons)")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for result in results:
        print(
            f"  • {result['filter_desc']:30} + {result['enhance_desc']:30}\n"
            f"    → {result['output_file']}\n"
        )

    if comparisons:
        print()
        print(f"Side-by-Side Comparisons ({len(comparisons)} created):")
        print(f"{'─' * 70}")
        for comp in comparisons:
            print(f"  ◇ {comp['comparison_file']}")

    # Create manifest
    manifest_path = OUTPUT_DIR / f"manifest_{timestamp}.txt"
    with open(manifest_path, "w") as f:
        f.write("PiDigiCam Emulator Output Manifest\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Architecture: {arch or 'native'}\n")
        f.write(f"Input: {INPUT_IMAGE}\n")
        f.write(f"Total Images: {len(results)}\n")
        f.write(f"Total Comparisons: {len(comparisons)}\n")
        f.write("\n" + "=" * 70 + "\n\n")
        
        f.write("PROCESSED IMAGES:\n")
        f.write("─" * 70 + "\n\n")
        for result in results:
            f.write(f"Filter: {result['filter_desc']}\n")
            f.write(f"Enhancement: {result['enhance_desc']}\n")
            f.write(f"Output File: {result['output_file']}\n")
            f.write(f"Filter ID: {result['filter']}, Enhancement ID: {result['enhance']}\n")
            f.write("\n")
        
        if comparisons:
            f.write("\n" + "=" * 70 + "\n\n")
            f.write("SIDE-BY-SIDE COMPARISONS:\n")
            f.write("─" * 70 + "\n\n")
            for comp in comparisons:
                f.write(f"File: {comp['comparison_file']}\n")
                f.write(f"Filter: {FILTERS[comp['filter']]['desc']}\n")
                f.write(f"Enhancement: {ENHANCEMENTS[comp['enhance']]['desc']}\n")
                f.write("\n")

    print(f"\n✓ Manifest saved to: {manifest_path}")
    print(f"✓ All outputs in: {OUTPUT_DIR}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="PiDigiCam Emulator - Demonstrate filter and enhancement functionalities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all filters and enhancements
  python emulator.py

  # Test specific filter
  python emulator.py --filter 1

  # Test with enhancement only
  python emulator.py --enhance 1

  # Test multiple configurations
  python emulator.py --filter 1 2 3 --enhance 0 1

  # Build and test for ARMv8
  python emulator.py --arch armv8

  # Test without building (use existing binary)
  python emulator.py --no-build
        """
    )

    parser.add_argument(
        "--filter",
        type=int,
        nargs="+",
        choices=[0, 1, 2, 3],
        help="Filter IDs to test (0=none, 1=cinematic_2000s, 2=washed_kodak, 3=golden_hour)"
    )
    parser.add_argument(
        "--enhance",
        type=int,
        nargs="+",
        choices=[0, 1],
        help="Enhancement IDs to test (0=none, 1=2x_upscale)"
    )
    parser.add_argument(
        "--arch",
        choices=["native", "armv8", "x86"],
        help="Target architecture (native uses default, armv8 and x86 require specific build)"
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip building C binary, use existing one"
    )

    args = parser.parse_args()

    run_demonstrations(
        filters=args.filter,
        enhancements=args.enhance,
        arch=args.arch,
        build=not args.no_build
    )


if __name__ == "__main__":
    main()
