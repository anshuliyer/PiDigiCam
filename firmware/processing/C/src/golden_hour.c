#include "hdrs/golden_hour.h"
#include "hdrs/stb_image.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define WARMTH_R_SCALE 1.12f
#define WARMTH_B_SCALE 0.92f
#define EXPOSURE_BOOST 0.05f
#define GLOW_STRENGTH 0.35f
#define GLOW_RADIUS 7
#define CONTRAST_BOOST 0.10f
#define SATURATION_BOOST 0.10f
#define VIGNETTE_STRENGTH 0.25f
#define BACKGROUND_BLUR_RADIUS 2

static float clamp(float x, float min, float max) {
    return x < min ? min : (x > max ? max : x);
}

static void rgb_to_hsl(float r, float g, float b, float* h, float* s, float* l) {
    float max = fmaxf(fmaxf(r, g), b);
    float min = fminf(fminf(r, g), b);
    *l = (max + min) * 0.5f;

    if (max == min) {
        *h = *s = 0.0f;
    } else {
        float d = max - min;
        *s = *l > 0.5f ? d / (2.0f - max - min) : d / (max + min);
        if (max == r) {
            *h = (g - b) / d + (g < b ? 6.0f : 0.0f);
        } else if (max == g) {
            *h = (b - r) / d + 2.0f;
        } else {
            *h = (r - g) / d + 4.0f;
        }
        *h /= 6.0f;
    }
}

static float hue_to_rgb(float p, float q, float t) {
    if (t < 0.0f) t += 1.0f;
    if (t > 1.0f) t -= 1.0f;
    if (t < 1.0f/6.0f) return p + (q - p) * 6.0f * t;
    if (t < 1.0f/2.0f) return q;
    if (t < 2.0f/3.0f) return p + (q - p) * (2.0f/3.0f - t) * 6.0f;
    return p;
}

static void hsl_to_rgb(float h, float s, float l, float* r, float* g, float* b) {
    if (s == 0.0f) {
        *r = *g = *b = l;
    } else {
        float q = l < 0.5f ? l * (1.0f + s) : l + s - l * s;
        float p = 2.0f * l - q;
        *r = hue_to_rgb(p, q, h + 1.0f/3.0f);
        *g = hue_to_rgb(p, q, h);
        *b = hue_to_rgb(p, q, h - 1.0f/3.0f);
    }
}

static void apply_warmth(unsigned char* data, int width, int height, int channels) {
    if (channels < 3) return;
    for (int i = 0; i < width * height; i++) {
        int idx = i * channels;
        float r = data[idx] / 255.0f;
        float g = data[idx + 1] / 255.0f;
        float b = data[idx + 2] / 255.0f;

        r = clamp(r * WARMTH_R_SCALE, 0.0f, 1.0f);
        b = clamp(b * WARMTH_B_SCALE, 0.0f, 1.0f);

        data[idx] = (unsigned char)(r * 255.0f);
        data[idx + 1] = (unsigned char)(g * 255.0f);
        data[idx + 2] = (unsigned char)(b * 255.0f);
    }
}

static void apply_exposure(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        pixel = clamp(pixel + EXPOSURE_BOOST, 0.0f, 1.0f);
        data[i] = (unsigned char)(pixel * 255.0f);
    }
}

static void apply_contrast(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        pixel = (pixel - 0.5f) * (1.0f + CONTRAST_BOOST) + 0.5f;
        data[i] = (unsigned char)(clamp(pixel, 0.0f, 1.0f) * 255.0f);
    }
}

static void apply_saturation(unsigned char* data, int width, int height, int channels) {
    if (channels < 3) return;
    for (int i = 0; i < width * height; i++) {
        int idx = i * channels;
        float r = data[idx] / 255.0f;
        float g = data[idx + 1] / 255.0f;
        float b = data[idx + 2] / 255.0f;
        float h, s, l;
        rgb_to_hsl(r, g, b, &h, &s, &l);
        s = clamp(s * (1.0f + SATURATION_BOOST), 0.0f, 1.0f);
        hsl_to_rgb(h, s, l, &r, &g, &b);
        data[idx] = (unsigned char)(clamp(r, 0.0f, 1.0f) * 255.0f);
        data[idx + 1] = (unsigned char)(clamp(g, 0.0f, 1.0f) * 255.0f);
        data[idx + 2] = (unsigned char)(clamp(b, 0.0f, 1.0f) * 255.0f);
    }
}

static void apply_blur(unsigned char* data, int width, int height, int channels, int radius) {
    size_t size = (size_t)width * height * channels;
    unsigned char* temp = (unsigned char*)malloc(size);
    if (!temp) return;
    memcpy(temp, data, size);

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            for (int c = 0; c < channels; c++) {
                float sum = 0.0f;
                int count = 0;
                for (int oy = -radius; oy <= radius; oy++) {
                    int ny = y + oy;
                    if (ny < 0 || ny >= height) continue;
                    for (int ox = -radius; ox <= radius; ox++) {
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

static void apply_glow(unsigned char* data, int width, int height, int channels) {
    size_t size = (size_t)width * height * channels;
    unsigned char* temp = (unsigned char*)malloc(size);
    if (!temp) return;
    memcpy(temp, data, size);

    apply_blur(temp, width, height, channels, GLOW_RADIUS);

    for (int i = 0; i < width * height * channels; i++) {
        float original = data[i] / 255.0f;
        float blurred = temp[i] / 255.0f;
        float combined = clamp(original * (1.0f - GLOW_STRENGTH) + blurred * GLOW_STRENGTH, 0.0f, 1.0f);
        data[i] = (unsigned char)(combined * 255.0f);
    }

    free(temp);
}

static void apply_vignette(unsigned char* data, int width, int height, int channels) {
    float cx = width * 0.5f;
    float cy = height * 0.5f;
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
                data[idx] = (unsigned char)(clamp(pixel * factor, 0.0f, 1.0f) * 255.0f);
            }
        }
    }
}

void apply_golden_hour_filter(unsigned char* data, int width, int height, int channels) {
    apply_warmth(data, width, height, channels);
    apply_exposure(data, width, height, channels);
    apply_glow(data, width, height, channels);
    apply_contrast(data, width, height, channels);
    apply_saturation(data, width, height, channels);
    apply_blur(data, width, height, channels, BACKGROUND_BLUR_RADIUS);
    apply_vignette(data, width, height, channels);
}
