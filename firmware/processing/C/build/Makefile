# --- Source and Project Config ---
SRC_DIR = ../src
TARGET_NAME = enhance
SRCS = $(SRC_DIR)/main.c $(SRC_DIR)/cnn_inference.c $(SRC_DIR)/cinematic_2000s.c \
       $(SRC_DIR)/washed_kodak.c $(SRC_DIR)/golden_hour.c $(SRC_DIR)/kodak_35mm.c

# --- 1. Pi Zero W (ARMv6) Config ---
CC_W = arm-linux-gnueabihf-gcc
DIR_W = ../prebuilts_w
CFLAGS_W = -O3 -Wall -Wextra -marm -march=armv6kz -mtune=arm1176jzf-s \
           -mfpu=vfp -mfloat-abi=hard -mno-unaligned-access -fno-pie

# --- 2. Pi Zero 2W / CM4 / CM5 (ARMv8) Config ---
CC_V8 = aarch64-linux-gnu-gcc
DIR_V8 = ../prebuilts_v8
# Optimized for Cortex-A53/A72/A76 cores
CFLAGS_V8 = -O3 -Wall -Wextra -march=armv8-a -mtune=cortex-a53

# --- 3. x86_64 (PC/Server) Config ---
CC_X86 = gcc
DIR_X86 = ../prebuilts_x86
CFLAGS_X86 = -O3 -Wall -Wextra -march=native

# --- Shared Linker Settings ---
LIBS = -lm -static
LDFLAGS = -static -no-pie

# --- Build Rules ---

.PHONY: all w v8 x86 clean directories

all: w v8 x86

# Raspberry Pi Zero W Target
w: directories
	$(CC_W) $(CFLAGS_W) $(LDFLAGS) $(SRCS) -o $(DIR_W)/$(TARGET_NAME) $(LIBS)
	@echo "Built Pi Zero W (ARMv6) binary."

# Raspberry Pi ARMv8 (Zero 2, 4, 5) Target
v8: directories
	$(CC_V8) $(CFLAGS_V8) $(LDFLAGS) $(SRCS) -o $(DIR_V8)/$(TARGET_NAME) $(LIBS)
	@echo "Built ARMv8 (64-bit) binary."

# Local x86 Target
x86: directories
	$(CC_X86) $(CFLAGS_X86) $(LDFLAGS) $(SRCS) -o $(DIR_X86)/$(TARGET_NAME) $(LIBS)
	@echo "Built x86_64 binary."

directories:
	@mkdir -p $(DIR_W) $(DIR_V8) $(DIR_X86)

clean:
	rm -rf $(DIR_W)/$(TARGET_NAME) $(DIR_V8)/$(TARGET_NAME) $(DIR_X86)/$(TARGET_NAME)