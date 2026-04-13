#include "hdrs/cinematic_2000s.h"
#include "hdrs/stb_image.h"
#include "hdrs/stb_image_write.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Filter parameters for cinematic 2000s look
#define EXPOSURE_ADJUSTMENT -0.5f
#define CONTRAST_S_CURVE 0.25f  // +25%
#define SATURATION_ADJUSTMENT -0.15f  // -15%
#define HIGHLIGHTS_ADJUSTMENT -0.20f  // -20%
#define SHADOWS_ADJUSTMENT -0.15f  // -15%
#define GAMMA_CORRECTION 1.1f
#define GRAIN_AMOUNT 0.02f
#define VIGNETTE_STRENGTH 0.30f  // 30%

// Color tint - slight warm/teal balance
#define WARM_TINT_R 1.02f
#define WARM_TINT_G 1.00f
#define WARM_TINT_B 0.98f

// Helper function to clamp values between 0 and 1
static float clamp(float x, float min, float max) {
    if (x < min) return min;
    if (x > max) return max;
    return x;
}

// Forward declarations
static float hue_to_rgb(float p, float q, float t);

// Convert RGB to HSL
static void rgb_to_hsl(float r, float g, float b, float* h, float* s, float* l) {
    float max = fmaxf(fmaxf(r, g), b);
    float min = fminf(fminf(r, g), b);
    *l = (max + min) / 2.0f;

    if (max == min) {
        *h = *s = 0.0f; // achromatic
    } else {
        float d = max - min;
        *s = (*l > 0.5f) ? d / (2.0f - max - min) : d / (max + min);

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

// Convert HSL to RGB
static void hsl_to_rgb(float h, float s, float l, float* r, float* g, float* b) {
    if (s == 0.0f) {
        *r = *g = *b = l; // achromatic
    } else {
        float q = l < 0.5f ? l * (1.0f + s) : l + s - l * s;
        float p = 2.0f * l - q;
        *r = hue_to_rgb(p, q, h + 1.0f/3.0f);
        *g = hue_to_rgb(p, q, h);
        *b = hue_to_rgb(p, q, h - 1.0f/3.0f);
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

// Apply exposure adjustment
static void apply_exposure(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        pixel = pixel * powf(2.0f, EXPOSURE_ADJUSTMENT);
        data[i] = (unsigned char)clamp(pixel * 255.0f, 0.0f, 255.0f);
    }
}

// Apply contrast with S-curve
static void apply_contrast_s_curve(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        // S-curve: enhanced contrast in midtones
        pixel = (pixel - 0.5f) * (1.0f + CONTRAST_S_CURVE) + 0.5f;
        // Apply sigmoid-like curve for S-curve effect
        pixel = 1.0f / (1.0f + expf(-(pixel - 0.5f) * 4.0f));
        data[i] = (unsigned char)clamp(pixel * 255.0f, 0.0f, 255.0f);
    }
}

// Apply saturation adjustment
static void apply_saturation(unsigned char* data, int width, int height, int channels) {
    if (channels < 3) return; // Need RGB channels

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int idx = (y * width + x) * channels;
            float r = data[idx] / 255.0f;
            float g = data[idx + 1] / 255.0f;
            float b = data[idx + 2] / 255.0f;

            float h, s, l;
            rgb_to_hsl(r, g, b, &h, &s, &l);

            s = s * (1.0f + SATURATION_ADJUSTMENT);
            s = clamp(s, 0.0f, 1.0f);

            hsl_to_rgb(h, s, l, &r, &g, &b);

            data[idx] = (unsigned char)(r * 255.0f);
            data[idx + 1] = (unsigned char)(g * 255.0f);
            data[idx + 2] = (unsigned char)(b * 255.0f);
        }
    }
}

// Apply highlights and shadows adjustment
static void apply_highlights_shadows(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;

        if (pixel > 0.5f) {
            // Highlights
            pixel = pixel + (pixel - 0.5f) * HIGHLIGHTS_ADJUSTMENT;
        } else {
            // Shadows
            pixel = pixel + (0.5f - pixel) * SHADOWS_ADJUSTMENT;
        }

        data[i] = (unsigned char)clamp(pixel * 255.0f, 0.0f, 255.0f);
    }
}

// Apply gamma correction
static void apply_gamma(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        pixel = powf(pixel, 1.0f / GAMMA_CORRECTION);
        data[i] = (unsigned char)(pixel * 255.0f);
    }
}

// Add grain/noise
static void apply_grain(unsigned char* data, int width, int height, int channels) {
    srand(time(NULL)); // Seed random number generator

    for (int i = 0; i < width * height * channels; i++) {
        float noise = ((float)rand() / RAND_MAX - 0.5f) * 2.0f * GRAIN_AMOUNT;
        float pixel = data[i] / 255.0f;
        pixel = clamp(pixel + noise, 0.0f, 1.0f);
        data[i] = (unsigned char)(pixel * 255.0f);
    }
}

// Apply vignette
static void apply_vignette(unsigned char* data, int width, int height, int channels) {
    float center_x = width / 2.0f;
    float center_y = height / 2.0f;
    float max_distance = sqrtf(center_x * center_x + center_y * center_y);

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float distance = sqrtf((x - center_x) * (x - center_x) + (y - center_y) * (y - center_y));
            float vignette_factor = 1.0f - (distance / max_distance) * VIGNETTE_STRENGTH;
            vignette_factor = clamp(vignette_factor, 0.0f, 1.0f);

            for (int c = 0; c < channels; c++) {
                int idx = (y * width + x) * channels + c;
                float pixel = data[idx] / 255.0f;
                pixel *= vignette_factor;
                data[idx] = (unsigned char)(pixel * 255.0f);
            }
        }
    }
}

// Apply color tint
static void apply_color_tint(unsigned char* data, int width, int height, int channels) {
    if (channels < 3) return; // Need RGB channels

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int idx = (y * width + x) * channels;
            float r = data[idx] / 255.0f;
            float g = data[idx + 1] / 255.0f;
            float b = data[idx + 2] / 255.0f;

            r *= WARM_TINT_R;
            g *= WARM_TINT_G;
            b *= WARM_TINT_B;

            data[idx] = (unsigned char)clamp(r * 255.0f, 0.0f, 255.0f);
            data[idx + 1] = (unsigned char)clamp(g * 255.0f, 0.0f, 255.0f);
            data[idx + 2] = (unsigned char)clamp(b * 255.0f, 0.0f, 255.0f);
        }
    }
}

// Main filter function
void apply_cinematic_2000s_filter(unsigned char* data, int width, int height, int channels) {
    // Apply effects in order
    apply_exposure(data, width, height, channels);
    apply_contrast_s_curve(data, width, height, channels);
    apply_saturation(data, width, height, channels);
    apply_highlights_shadows(data, width, height, channels);
    apply_gamma(data, width, height, channels);
    apply_grain(data, width, height, channels);
    apply_vignette(data, width, height, channels);
    apply_color_tint(data, width, height, channels);
}