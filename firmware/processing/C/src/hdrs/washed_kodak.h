#ifndef WASHED_KODAK_H
#define WASHED_KODAK_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Apply a washed-out Kodak-style black-and-white filter with soft contrast,
 * lifted shadows, highlight glow, blur, grain, vignette and fade.
 */
void apply_washed_kodak_filter(unsigned char* data, int width, int height, int channels);

#ifdef __cplusplus
}
#endif

#endif // WASHED_KODAK_H
