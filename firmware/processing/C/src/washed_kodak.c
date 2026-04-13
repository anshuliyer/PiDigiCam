#include "hdrs/washed_kodak.h"
#include "hdrs/stb_image.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define CONTRAST_SOFT -0.10f
#define SHADOWS_LIFT 0.10f
#define HIGHLIGHTS_GLOW 0.25f
#define GRAIN_AMOUNT 0.015f
#define VIGNETTE_STRENGTH 0.20f
#define FADE_AMOUNT 0.05f

static float clamp(float x, float min, float max) {
    return x < min ? min : (x > max ? max : x);
}

static void apply_red_heavy_bw(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height; i++) {
        int idx = i * channels;
        float r = data[idx] / 255.0f;
        float g = data[idx + 1] / 255.0f;
        float b = data[idx + 2] / 255.0f;
        float gray = clamp(r * 0.5f + g * 0.25f + b * 0.25f, 0.0f, 1.0f);
        unsigned char gray_byte = (unsigned char)(gray * 255.0f);
        data[idx] = gray_byte;
        data[idx + 1] = gray_byte;
        data[idx + 2] = gray_byte;
    }
}

static void apply_soft_contrast(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        pixel = (pixel - 0.5f) * (1.0f + CONTRAST_SOFT) + 0.5f;
        data[i] = (unsigned char)(clamp(pixel, 0.0f, 1.0f) * 255.0f);
    }
}

static void apply_shadow_lift(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        float lift = (1.0f - pixel) * SHADOWS_LIFT;
        pixel = clamp(pixel + lift, 0.0f, 1.0f);
        data[i] = (unsigned char)(pixel * 255.0f);
    }
}

static void apply_highlight_glow(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        if (pixel > 0.5f) {
            pixel = pixel + (1.0f - pixel) * HIGHLIGHTS_GLOW * 0.5f;
        }
        data[i] = (unsigned char)(clamp(pixel, 0.0f, 1.0f) * 255.0f);
    }
}

static void apply_blur(unsigned char* data, int width, int height, int channels) {
    size_t size = (size_t)width * (size_t)height * (size_t)channels;
    unsigned char* temp = (unsigned char*)malloc(size);
    if (!temp) return;
    memcpy(temp, data, size);

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            for (int c = 0; c < channels; c++) {
                float sum = 0.0f;
                int count = 0;
                for (int oy = -1; oy <= 1; oy++) {
                    int ny = y + oy;
                    if (ny < 0 || ny >= height) continue;
                    for (int ox = -1; ox <= 1; ox++) {
                        int nx = x + ox;
                        if (nx < 0 || nx >= width) continue;
                        sum += temp[(ny * width + nx) * channels + c];
                        count++;
                    }
                }
                data[(y * width + x) * channels + c] = (unsigned char)(sum / count);
            }
        }
    }

    free(temp);
}

static void apply_grain(unsigned char* data, int width, int height, int channels) {
    srand((unsigned int)time(NULL));
    for (int i = 0; i < width * height * channels; i++) {
        float noise = ((float)rand() / RAND_MAX - 0.5f) * 2.0f * GRAIN_AMOUNT;
        float pixel = data[i] / 255.0f;
        pixel = clamp(pixel + noise, 0.0f, 1.0f);
        data[i] = (unsigned char)(pixel * 255.0f);
    }
}

static void apply_vignette(unsigned char* data, int width, int height, int channels) {
    float cx = width / 2.0f;
    float cy = height / 2.0f;
    float maxd = sqrtf(cx * cx + cy * cy);
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float dx = x - cx;
            float dy = y - cy;
            float dist = sqrtf(dx * dx + dy * dy);
            float factor = 1.0f - (dist / maxd) * VIGNETTE_STRENGTH;
            factor = clamp(factor, 0.0f, 1.0f);
            for (int c = 0; c < channels; c++) {
                int idx = (y * width + x) * channels + c;
                float pixel = data[idx] / 255.0f;
                pixel *= factor;
                data[idx] = (unsigned char)(pixel * 255.0f);
            }
        }
    }
}

static void apply_fade(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        pixel = pixel * (1.0f - FADE_AMOUNT) + 0.5f * FADE_AMOUNT;
        data[i] = (unsigned char)(clamp(pixel, 0.0f, 1.0f) * 255.0f);
    }
}

void apply_washed_kodak_filter(unsigned char* data, int width, int height, int channels) {
    if (channels < 3) return;
    apply_red_heavy_bw(data, width, height, channels);
    apply_soft_contrast(data, width, height, channels);
    apply_shadow_lift(data, width, height, channels);
    apply_highlight_glow(data, width, height, channels);
    apply_blur(data, width, height, channels);
    apply_grain(data, width, height, channels);
    apply_vignette(data, width, height, channels);
    apply_fade(data, width, height, channels);
}
