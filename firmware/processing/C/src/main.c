#define STB_IMAGE_IMPLEMENTATION
#include "hdrs/stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "hdrs/stb_image_write.h"

#include "hdrs/cinematic_2000s.h"
#include "hdrs/washed_kodak.h"
#include "hdrs/golden_hour.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * PiDigiCam: Minimal C Image Processor for ARMv6
 *
 * This entry point is designed for debian-based ARMv6 microcontrollers.
 * It uses the 'stb' single-header libraries for zero-dependency image I/O.
 *
 * Usage: program <input> <output> [--enhance=1] [--filter=0|1|2]
 *   --enhance=1: Apply 2x upscaling enhancement
 *   --filter=0: No filter (default)
 *   --filter=1: Apply cinematic 2000s filter
 *   --filter=2: Apply washed Kodak black-and-white filter
 */

// Simple Bilinear Upscaling (Baseline Enhancement)
void upscale_x2(unsigned char* src, int sw, int sh, unsigned char* dst) {
    int dw = sw * 2;
    int dh = sh * 2;
    for (int y = 0; y < dh; y++) {
        for (int x = 0; x < dw; x++) {
            float gx = (float)x / 2.0f;
            float gy = (float)y / 2.0f;
            int gxi = (int)gx;
            int gyi = (int)gy;

            // Simple nearest/bilinear mix for performance on ARMv6
            dst[y * dw + x] = src[gyi * sw + gxi];
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <input> <output> [--enhance=1] [--filter=0|1|2|3]\n", argv[0]);
        fprintf(stderr, "  --enhance=1: Apply 2x upscaling enhancement\n");
        fprintf(stderr, "  --filter=0: No filter (default)\n");
        fprintf(stderr, "  --filter=1: Apply cinematic 2000s filter\n");
        fprintf(stderr, "  --filter=2: Apply washed Kodak black-and-white filter\n");
        fprintf(stderr, "  --filter=3: Apply golden hour filter\n");
        return 1;
    }

    const char* input_path = argv[1];
    const char* output_path = argv[2];

    // Parse command line arguments
    int apply_enhancement = 0;
    int filter_type = 0;

    for (int i = 3; i < argc; i++) {
        if (strcmp(argv[i], "--enhance=1") == 0) {
            apply_enhancement = 1;
        } else if (strcmp(argv[i], "--filter=1") == 0) {
            filter_type = 1;
        } else if (strcmp(argv[i], "--filter=2") == 0) {
            filter_type = 2;
        } else if (strcmp(argv[i], "--filter=3") == 0) {
            filter_type = 3;
        } else if (strcmp(argv[i], "--filter=0") == 0) {
            filter_type = 0;
        } else {
            fprintf(stderr, "Unknown argument: %s\n", argv[i]);
            return 1;
        }
    }

    int width, height, channels;
    printf("Loading image: %s\n", input_path);
    unsigned char* img = stbi_load(input_path, &width, &height, &channels, 0);

    if (!img) {
        fprintf(stderr, "Error: Could not load image %s\n", input_path);
        return 1;
    }

    printf("Image Loaded: %dx%d, %d channels\n", width, height, channels);

    unsigned char* out_img;
    int out_w = width;
    int out_h = height;

    if (apply_enhancement) {
        out_w = width * 2;
        out_h = height * 2;
        out_img = (unsigned char*)malloc(out_w * out_h * channels);

        if (!out_img) {
            fprintf(stderr, "Error: Out of memory\n");
            stbi_image_free(img);
            return 1;
        }

        printf("Enhancing image to %dx%d...\n", out_w, out_h);

        // Process each channel
        for (int c = 0; c < channels; c++) {
            unsigned char* src_c = (unsigned char*)malloc(width * height);
            unsigned char* dst_c = (unsigned char*)malloc(out_w * out_h);

            // Extract channel
            for (int i = 0; i < width * height; i++) src_c[i] = img[i * channels + c];

            upscale_x2(src_c, width, height, dst_c);

            // Insert channel back
            for (int i = 0; i < out_w * out_h; i++) out_img[i * channels + c] = dst_c[i];

            free(src_c);
            free(dst_c);
        }
    } else {
        // No enhancement, just copy the image
        out_img = (unsigned char*)malloc(width * height * channels);
        if (!out_img) {
            fprintf(stderr, "Error: Out of memory\n");
            stbi_image_free(img);
            return 1;
        }
        memcpy(out_img, img, width * height * channels);
        printf("Processing image without enhancement...\n");
    }

    // Apply filter if requested
    if (filter_type == 1) {
        printf("Applying cinematic 2000s filter...\n");
        apply_cinematic_2000s_filter(out_img, out_w, out_h, channels);
    } else if (filter_type == 2) {
        printf("Applying washed Kodak filter...\n");
        apply_washed_kodak_filter(out_img, out_w, out_h, channels);
    } else if (filter_type == 3) {
        printf("Applying golden hour filter...\n");
        apply_golden_hour_filter(out_img, out_w, out_h, channels);
    }

    printf("Writing output: %s\n", output_path);
    if (!stbi_write_png(output_path, out_w, out_h, channels, out_img, out_w * channels)) {
        fprintf(stderr, "Error: Could not save image %s\n", output_path);
        stbi_image_free(img);
        free(out_img);
        return 1;
    } else {
        printf("Successfully processed image!\n");
    }

    stbi_image_free(img);
    free(out_img);

    return 0;
}
