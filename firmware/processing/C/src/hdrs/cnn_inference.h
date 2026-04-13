#ifndef CNN_INFERENCE_H
#define CNN_INFERENCE_H

#include <stddef.h>

typedef struct {
    float *weights;
    float *bias;
    int in_channels;
    int out_channels;
    int kernel_size;
} ConvLayer;

typedef struct {
    float *weights;
    float *bias;
    int in_channels;
    int out_channels;
    int kernel_size;
    int stride;
} DeconvLayer;

// Activation: PReLU is used in FSRCNN.
void prelu(float *data, float *slope, int channels, int width, int height);

// PixelShuffle (Sub-pixel Convolution) for x2 upsampling
void pixel_shuffle_x2(float *input, float *output, int in_h, int in_w, int in_ch);

// Standard 2D Convolution
void conv2d(float *input, float *output, int in_h, int in_w, ConvLayer *layer);

#endif // CNN_INFERENCE_H
