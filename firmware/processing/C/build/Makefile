CC = arm-linux-gnueabi-gcc
# Force static linking for all libraries to avoid version mismatches
LIBS = -lm -static
# CFLAGS specifically tuned for Pi Zero W (ARMv6)
# -marm: Use 32-bit ARM mode (required for Hard Float on ARMv6)
# -mno-unaligned-access: Prevents Segfaults on older ARM chips
# -fno-pie: Disables position-independent code which often crashes at _start
CFLAGS = -O3 -Wall -Wextra -marm -march=armv6kz -mtune=arm1176jzf-s \
         -mfpu=vfp -mfloat-abi=softfp -mno-unaligned-access -fno-pie

# Linker flags to ensure a truly static, non-PIE binary
LDFLAGS = -static -no-pie

PREBUILTS_DIR = ../prebuilts_w
SRC_DIR = ../src
TARGET = $(PREBUILTS_DIR)/enhance

# Object files
OBJS = enhance.o cnn_inference.o cinematic_2000s.o washed_kodak.o golden_hour.o kodak_35mm.o

all: $(TARGET)

$(TARGET): $(OBJS) | $(PREBUILTS_DIR)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $(TARGET) $(OBJS) $(LIBS)
	@echo "------------------------------------------------"
	@echo "Build Complete. Checking binary type..."
	@file $(TARGET)
	@echo "------------------------------------------------"

$(PREBUILTS_DIR):
	mkdir -p $(PREBUILTS_DIR)

# Compilation rules
enhance.o: $(SRC_DIR)/main.c
	$(CC) $(CFLAGS) -c $< -o $@

cnn_inference.o: $(SRC_DIR)/cnn_inference.c
	$(CC) $(CFLAGS) -c $< -o $@

cinematic_2000s.o: $(SRC_DIR)/cinematic_2000s.c
	$(CC) $(CFLAGS) -c $< -o $@

washed_kodak.o: $(SRC_DIR)/washed_kodak.c
	$(CC) $(CFLAGS) -c $< -o $@

golden_hour.o: $(SRC_DIR)/golden_hour.c
	$(CC) $(CFLAGS) -c $< -o $@

kodak_35mm.o: $(SRC_DIR)/kodak_35mm.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o $(TARGET)

# Quick command for building specifically for W
w: clean all