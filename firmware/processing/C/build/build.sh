#!/bin/bash
# Build script for different architectures

ARCH=${1:-native}

if [ "$ARCH" = "armv8" ]; then
    CC="clang --target=aarch64-linux-gnu"
    PREBUILTS_DIR="../prebuilts_v8"
elif [ "$ARCH" = "x86" ]; then
    CC="gcc -m32"
    PREBUILTS_DIR="../prebuilts_x86"
elif [ "$ARCH" = "w" ]; then
    CC="arm-linux-gnueabi-gcc -mcpu=arm1176jzf-s"
    PREBUILTS_DIR="../prebuilts_w"
else
    CC="gcc"
    PREBUILTS_DIR="../prebuilts"
fi

mkdir -p $PREBUILTS_DIR

$CC -O3 -Wall -Wextra ../src/main.c ../src/cnn_inference.c ../src/cinematic_2000s.c ../src/washed_kodak.c ../src/golden_hour.c ../src/kodak_35mm.c -lm -o $PREBUILTS_DIR/enhance

echo "Build complete for $ARCH. Executable placed in: $PREBUILTS_DIR/enhance"
echo "Run with: ./$PREBUILTS_DIR/enhance <input.jpg> <output.png>"
