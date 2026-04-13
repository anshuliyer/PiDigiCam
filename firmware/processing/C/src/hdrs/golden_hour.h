#ifndef GOLDEN_HOUR_H
#define GOLDEN_HOUR_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Apply a golden hour filter with warmth, glow, contrast, saturation,
 * light background blur, and vignette.
 */
void apply_golden_hour_filter(unsigned char* data, int width, int height, int channels);

#ifdef __cplusplus
}
#endif

#endif // GOLDEN_HOUR_H
