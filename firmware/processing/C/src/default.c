#include "hdrs/default.h"
#include "hdrs/stb_image.h"
#include "hdrs/stb_image_write.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Filter parameters for Coming-of-Age indie film aesthetic
#define WARM_RED_BOOST 1.08f
#define WARM_GREEN_BOOST 1.04f
#define WARM_BLUE_REDUCTION 0.90f
#define BLACK_LIFT_MULTIPLIER 0.9f
#define BLACK_LIFT_OFFSET 25.0f
#define BLOOM_STRENGTH 0.2f
#define SATURATION_BOOST 1.2f
#define CONTRAST_REDUCTION 0.95f
#define GRAIN_AMOUNT 8.0f
#define VIGNETTE_STRENGTH 0.3f
#define SMOOTHING_ITERATIONS 1

// Helper function to clamp values between 0 and 1
static float clamp(float x, float min, float max) {
    if (x < min) return min;
    if (x > max) return max;
    return x;
}

// Simple pseudo-random number generator
static float random_float(unsigned int* seed) {
    *seed = (*seed * 1103515245 + 12345) & 0x7fffffff;
    return ((float)(*seed) / 0x7fffffff);
}

// Box-Muller transform for Gaussian distribution
static float gaussian_random(unsigned int* seed) {
    float u1 = random_float(seed);
    float u2 = random_float(seed);
    if (u1 < 0.001f) u1 = 0.001f; // Avoid log(0)
    return sqrtf(-2.0f * logf(u1)) * cosf(2.0f * 3.14159f * u2);
}

// Convert RGB to HSL
static void rgb_to_hsl(float r, float g, float b, float* h, float* s, float* l) {
    float max = fmaxf(fmaxf(r, g), b);
    float min = fminf(fminf(r, g), b);
    *l = (max + min) / 2.0f;

    if (max == min) {
        *h = *s = 0.0f;
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

// Apply warm golden color grade
static void apply_warm_golden_grade(unsigned char* data, int width, int height, int channels, float intensity) {
    for (int i = 0; i < width * height * channels; i += channels) {
        if (channels >= 3) {
            float r = data[i] / 255.0f;
            float g = data[i + 1] / 255.0f;
            float b = data[i + 2] / 255.0f;

            // Warm color boost
            float intensity_factor = intensity * 0.5f + 0.5f;
            r = r * WARM_RED_BOOST * intensity_factor;
            g = g * WARM_GREEN_BOOST * intensity_factor;
            b = b * WARM_BLUE_REDUCTION;

            // Lift blacks for faded film look
            r = r * BLACK_LIFT_MULTIPLIER + (BLACK_LIFT_OFFSET / 255.0f);
            g = g * BLACK_LIFT_MULTIPLIER + (BLACK_LIFT_OFFSET / 255.0f);
            b = b * BLACK_LIFT_MULTIPLIER + (BLACK_LIFT_OFFSET / 255.0f);

            data[i] = (unsigned char)(clamp(r, 0.0f, 1.0f) * 255.0f);
            data[i + 1] = (unsigned char)(clamp(g, 0.0f, 1.0f) * 255.0f);
            data[i + 2] = (unsigned char)(clamp(b, 0.0f, 1.0f) * 255.0f);
        }
    }
}

// Simple Gaussian blur for bloom effect
static void apply_gaussian_blur(unsigned char* src, unsigned char* dst, int width, int height, 
                                int channels, int radius) {
    memcpy(dst, src, width * height * channels);
    
    // Simple box blur approximation (3 passes)
    for (int pass = 0; pass < 2; pass++) {
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                for (int c = 0; c < channels; c++) {
                    float sum = 0.0f;
                    int count = 0;
                    
                    for (int dy = -radius; dy <= radius; dy++) {
                        for (int dx = -radius; dx <= radius; dx++) {
                            int nx = x + dx;
                            int ny = y + dy;
                            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                                sum += dst[(ny * width + nx) * channels + c];
                                count++;
                            }
                        }
                    }
                    dst[(y * width + x) * channels + c] = (unsigned char)(sum / count);
                }
            }
        }
    }
}

// Apply pro-mist bloom effect (screen blend)
static void apply_bloom(unsigned char* data, unsigned char* bloom_data, int width, int height, 
                        int channels, float intensity) {
    for (int i = 0; i < width * height * channels; i += channels) {
        if (channels >= 3) {
            float r = data[i] / 255.0f;
            float g = data[i + 1] / 255.0f;
            float b = data[i + 2] / 255.0f;
            
            float br = bloom_data[i] / 255.0f;
            float bg = bloom_data[i + 1] / 255.0f;
            float bb = bloom_data[i + 2] / 255.0f;
            
            // Screen blend mode: 1 - (1-a)(1-b)
            float blend_strength = BLOOM_STRENGTH * intensity;
            r = 1.0f - (1.0f - r) * (1.0f - br * blend_strength);
            g = 1.0f - (1.0f - g) * (1.0f - bg * blend_strength);
            b = 1.0f - (1.0f - b) * (1.0f - bb * blend_strength);
            
            data[i] = (unsigned char)(clamp(r, 0.0f, 1.0f) * 255.0f);
            data[i + 1] = (unsigned char)(clamp(g, 0.0f, 1.0f) * 255.0f);
            data[i + 2] = (unsigned char)(clamp(b, 0.0f, 1.0f) * 255.0f);
        }
    }
}

// Apply saturation boost
static void apply_saturation(unsigned char* data, int width, int height, int channels, float intensity) {
    if (channels < 3) return;

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int idx = (y * width + x) * channels;
            float r = data[idx] / 255.0f;
            float g = data[idx + 1] / 255.0f;
            float b = data[idx + 2] / 255.0f;

            float h, s, l;
            rgb_to_hsl(r, g, b, &h, &s, &l);

            s = s * SATURATION_BOOST * intensity;
            s = clamp(s, 0.0f, 1.0f);

            hsl_to_rgb(h, s, l, &r, &g, &b);

            data[idx] = (unsigned char)(clamp(r, 0.0f, 1.0f) * 255.0f);
            data[idx + 1] = (unsigned char)(clamp(g, 0.0f, 1.0f) * 255.0f);
            data[idx + 2] = (unsigned char)(clamp(b, 0.0f, 1.0f) * 255.0f);
        }
    }
}

// Apply contrast reduction
static void apply_contrast_reduction(unsigned char* data, int width, int height, int channels) {
    for (int i = 0; i < width * height * channels; i++) {
        float pixel = data[i] / 255.0f;
        pixel = (pixel - 0.5f) * CONTRAST_REDUCTION + 0.5f;
        data[i] = (unsigned char)(clamp(pixel, 0.0f, 1.0f) * 255.0f);
    }
}

// Apply film grain
static void apply_film_grain(unsigned char* data, int width, int height, int channels, float intensity) {
    unsigned int seed = time(NULL);
    
    for (int i = 0; i < width * height * channels; i++) {
        float grain = gaussian_random(&seed) * GRAIN_AMOUNT * intensity;
        float pixel = data[i] / 255.0f;
        pixel = pixel + grain / 255.0f;
        data[i] = (unsigned char)(clamp(pixel, 0.0f, 1.0f) * 255.0f);
    }
}

// Apply vignette effect
static void apply_vignette(unsigned char* data, int width, int height, int channels, float intensity) {
    int center_x = width / 2;
    int center_y = height / 2;
    float max_dist = sqrtf(center_x * center_x + center_y * center_y);

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float dx = x - center_x;
            float dy = y - center_y;
            float dist = sqrtf(dx * dx + dy * dy);
            
            // Radial vignette (darkening edges)
            float vignette_factor = 1.0f - (dist / max_dist) * VIGNETTE_STRENGTH * intensity;
            vignette_factor = clamp(vignette_factor, 0.0f, 1.0f);

            int idx = (y * width + x) * channels;
            for (int c = 0; c < channels; c++) {
                float pixel = data[idx + c] / 255.0f;
                pixel = pixel * vignette_factor;
                data[idx + c] = (unsigned char)(pixel * 255.0f);
            }
        }
    }
}

// Apply smoothing filter (simple box filter)
static void apply_smoothing(unsigned char* data, int width, int height, int channels) {
    unsigned char* temp = malloc(width * height * channels);
    if (!temp) return;
    
    memcpy(temp, data, width * height * channels);

    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            for (int c = 0; c < channels; c++) {
                int sum = 0;
                for (int dy = -1; dy <= 1; dy++) {
                    for (int dx = -1; dx <= 1; dx++) {
                        sum += temp[((y + dy) * width + (x + dx)) * channels + c];
                    }
                }
                data[(y * width + x) * channels + c] = (unsigned char)(sum / 9);
            }
        }
    }
    
    free(temp);
}

// Main filter function
void apply_coming_of_age_filter(const char* input_path, const char* output_path, float intensity) {
    int width, height, channels;
    unsigned char* img = stbi_load(input_path, &width, &height, &channels, 0);
    
    if (!img) {
        fprintf(stderr, "Failed to load image: %s\n", input_path);
        return;
    }

    // Convert to RGB if needed
    if (channels == 4) {
        channels = 3; // Strip alpha
    }

    // Allocate working buffers
    unsigned char* bloom_buffer = malloc(width * height * channels);
    if (!bloom_buffer) {
        stbi_image_free(img);
        return;
    }

    // Apply filters
    // 1. Warm golden color grade
    apply_warm_golden_grade(img, width, height, channels, intensity);

    // 2. Pro-mist bloom effect
    memcpy(bloom_buffer, img, width * height * channels);
    apply_gaussian_blur(bloom_buffer, bloom_buffer, width, height, channels, 5);
    apply_bloom(img, bloom_buffer, width, height, channels, intensity);

    // 3. Saturation boost
    apply_saturation(img, width, height, channels, intensity);

    // 4. Contrast reduction
    apply_contrast_reduction(img, width, height, channels);

    // 5. Film grain
    apply_film_grain(img, width, height, channels, intensity);

    // 6. Vignette
    apply_vignette(img, width, height, channels, intensity);

    // 7. Smoothing
    for (int i = 0; i < SMOOTHING_ITERATIONS; i++) {
        apply_smoothing(img, width, height, channels);
    }

    // Save result
    int success = stbi_write_png(output_path, width, height, channels, img, width * channels);
    
    if (success) {
        printf("Coming-of-Age filter applied: %s\n", output_path);
    } else {
        fprintf(stderr, "Failed to save image: %s\n", output_path);
    }

    free(bloom_buffer);
    stbi_image_free(img);
}
