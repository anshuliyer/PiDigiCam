#!/bin/bash
# Simple build script for ARMv6 Debian
gcc -O3 -Wall -Wextra ../main.c ../cnn_inference.c -lm -o ../prebuilts/enhance
echo "Build complete. Executable placed in: ../prebuilts/enhance"
echo "Run with: ./../prebuilts/enhance <input.jpg> <output.png>"
