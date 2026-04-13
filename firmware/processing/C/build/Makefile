CC = gcc
CFLAGS = -O3 -Wall -Wextra
LIBS = -lm
PREBUILTS_DIR = ../prebuilts
SRC_DIR = ..

TARGET = $(PREBUILTS_DIR)/enhance

all: $(TARGET)

$(TARGET): enhance.o cnn_inference.o
	$(CC) $(CFLAGS) -o $(TARGET) enhance.o cnn_inference.o $(LIBS)

enhance.o: $(SRC_DIR)/main.c $(SRC_DIR)/cnn_inference.h $(SRC_DIR)/stb_image.h $(SRC_DIR)/stb_image_write.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/main.c -o enhance.o

cnn_inference.o: $(SRC_DIR)/cnn_inference.c $(SRC_DIR)/cnn_inference.h
	$(CC) $(CFLAGS) -c $(SRC_DIR)/cnn_inference.c -o cnn_inference.o

clean:
	rm -f *.o $(TARGET)
