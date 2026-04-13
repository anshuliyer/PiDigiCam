#include "hdrs/cnn_inference.h"
#include <stdlib.h>
#include <string.h>

void prelu(float *data, float *slope, int channels, int width, int height) {
    int plane_size = width * height;
    for (int c = 0; c < channels; c++) {
        float s = slope[c];
        for (int i = 0; i < plane_size; i++) {
            float val = data[c * plane_size + i];
            if (val < 0) {
                data[c * plane_size + i] = val * s;
            }
        }
    }
}

void conv2d(float *input, float *output, int in_h, int in_w, ConvLayer *layer) {
    int kh = layer->kernel_size;
    int kw = layer->kernel_size;
    int pad = kh / 2;
    int out_h = in_h; // Stride 1 assumed
    int out_w = in_w;
    
    int in_ch = layer->in_channels;
    int out_ch = layer->out_channels;
    
    memset(output, 0, out_h * out_w * out_ch * sizeof(float));
    
    for (int oc = 0; oc < out_ch; oc++) {
        float b = layer->bias[oc];
        for (int ic = 0; ic < in_ch; ic++) {
            for (int i = 0; i < out_h; i++) {
                for (int j = 0; j < out_w; j++) {
                    float sum = 0;
                    for (int ki = 0; ki < kh; ki++) {
                        for (int kj = 0; kj < kw; kj++) {
                            int ii = i + ki - pad;
                            int jj = j + kj - pad;
                            if (ii >= 0 && ii < in_h && jj >= 0 && jj < in_w) {
                                float val = input[(ic * in_h + ii) * in_w + jj];
                                float weight = layer->weights[(((oc * in_ch + ic) * kh) + ki) * kw + kj];
                                sum += val * weight;
                            }
                        }
                    }
                    output[(oc * out_h + i) * out_w + j] += sum;
                }
            }
        }
        // Add bias
        for (int i = 0; i < out_h * out_w; i++) {
            output[oc * out_h * out_w + i] += b;
        }
    }
}

void pixel_shuffle_x2(float *input, float *output, int in_h, int in_w, int in_ch) {
    // scale = 2, so out_ch = in_ch / 4. 
    // Here we expect in_ch = 4 to produce out_ch = 1
    int out_h = in_h * 2;
    int out_w = in_w * 2;
    
    for (int i = 0; i < in_h; i++) {
        for (int j = 0; j < in_w; j++) {
            // channel 0 -> (0,0), 1 -> (0,1), 2 -> (1,0), 3 -> (1,1)
            output[(i * 2 + 0) * out_w + (j * 2 + 0)] = input[(0 * in_h + i) * in_w + j];
            output[(i * 2 + 0) * out_w + (j * 2 + 1)] = input[(1 * in_h + i) * in_w + j];
            output[(i * 2 + 1) * out_w + (j * 2 + 0)] = input[(2 * in_h + i) * in_w + j];
            output[(i * 2 + 1) * out_w + (j * 2 + 1)] = input[(3 * in_h + i) * in_w + j];
        }
    }
}
