CC = gcc
CFLAGS = -O3 -Wall -Wextra
LIBS = -lm
PREBUILTS_DIR = ../prebuilts
SRC_DIR = ../src

TARGET = $(PREBUILTS_DIR)/enhance

# Architecture-specific settings
ifeq ($(ARCH), armv8)
    CC = clang --target=aarch64-linux-gnu
    PREBUILTS_DIR = ../prebuilts_v8
    TARGET = $(PREBUILTS_DIR)/enhance
else ifeq ($(ARCH), x86)
    CFLAGS += -m32
    PREBUILTS_DIR = ../prebuilts_x86
    TARGET = $(PREBUILTS_DIR)/enhance
else ifeq ($(ARCH), w)
    CC = arm-linux-gnueabihf-gcc
    # -marm: No Thumb instructions
    # -march=armv6kz: Strict Pi Zero architecture
    # -mno-unaligned-access: CRITICAL for Pi Zero W to prevent Segfaults
    # -fno-stack-protector: Removes some complex start-up code that can fail on older ABIs
    CFLAGS += -marm -march=armv6kz -mtune=arm1176jzf-s -mfpu=vfp -mfloat-abi=hard \
              -mno-unaligned-access -fno-stack-protector
    
    PREBUILTS_DIR = ../prebuilts_w
    TARGET = $(PREBUILTS_DIR)/enhance
endif


all: $(TARGET)

$(TARGET): enhance.o cnn_inference.o cinematic_2000s.o washed_kodak.o golden_hour.o kodak_35mm.o | $(PREBUILTS_DIR)
	$(CC) $(CFLAGS) -o $(TARGET) enhance.o cnn_inference.o cinematic_2000s.o washed_kodak.o golden_hour.o kodak_35mm.o $(LIBS)

$(PREBUILTS_DIR):
	mkdir -p $(PREBUILTS_DIR)

# Compilation rules
enhance.o: $(SRC_DIR)/main.c $(SRC_DIR)/hdrs/cnn_inference.h $(SRC_DIR)/hdrs/stb_image.h $(SRC_DIR)/hdrs/stb_image_write.h $(SRC_DIR)/hdrs/cinematic_2000s.h $(SRC_DIR)/hdrs/washed_kodak.h $(SRC_DIR)/hdrs/golden_hour.h $(SRC_DIR)/hdrs/kodak_35mm.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/main.c -o enhance.o

cnn_inference.o: $(SRC_DIR)/cnn_inference.c $(SRC_DIR)/hdrs/cnn_inference.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/cnn_inference.c -o cnn_inference.o

cinematic_2000s.o: $(SRC_DIR)/cinematic_2000s.c $(SRC_DIR)/hdrs/cinematic_2000s.h $(SRC_DIR)/hdrs/stb_image.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/cinematic_2000s.c -o cinematic_2000s.o

washed_kodak.o: $(SRC_DIR)/washed_kodak.c $(SRC_DIR)/hdrs/washed_kodak.h $(SRC_DIR)/hdrs/stb_image.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/washed_kodak.c -o washed_kodak.o

golden_hour.o: $(SRC_DIR)/golden_hour.c $(SRC_DIR)/hdrs/golden_hour.h $(SRC_DIR)/hdrs/stb_image.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/golden_hour.c -o golden_hour.o

kodak_35mm.o: $(SRC_DIR)/kodak_35mm.c $(SRC_DIR)/hdrs/kodak_35mm.h $(SRC_DIR)/hdrs/stb_image.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/kodak_35mm.c -o kodak_35mm.o

clean:
	rm -f *.o $(TARGET)

# Build targets for different architectures
armv8:
	$(MAKE) ARCH=armv8

x86:
	$(MAKE) ARCH=x86

w:
	$(MAKE) ARCH=w