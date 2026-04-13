#ifndef CINEMATIC_2000S_H
#define CINEMATIC_2000S_H

/**
 * Cinematic 2000s Filter
 *
 * Applies a nostalgic film look with the following parameters:
 * - Exposure: -0.5
 * - Contrast: +25% (S-curve)
 * - Saturation: -15%
 * - Highlights: -20%
 * - Shadows: -15%
 * - Gamma: 1.1
 * - Grain: +0.02 noise
 * - Vignette: 30%
 * - Color tint: slight warm
 */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Apply the cinematic 2000s filter to an image
 *
 * @param data     Image data (RGB/RGBA)
 * @param width    Image width in pixels
 * @param height   Image height in pixels
 * @param channels Number of color channels (3 for RGB, 4 for RGBA)
 */
void apply_cinematic_2000s_filter(unsigned char* data, int width, int height, int channels);

#ifdef __cplusplus
}
#endif

#endif // CINEMATIC_2000S_H