#ifndef DEFAULT_H
#define DEFAULT_H

#include <stdio.h>

/**
 * Apply Coming-of-Age indie film aesthetic filter
 * 
 * Characteristics:
 * - Warm golden tones
 * - Pro-mist style bloom effect
 * - Lifted shadows for faded film print look
 * - High saturation with slightly reduced contrast
 * - Fine film grain
 * - Subtle lens vignette
 * - Smooth quality
 * 
 * @param input_path Path to input image file
 * @param output_path Path to save output image
 * @param intensity Filter intensity (0.0 to 1.0+); 1.0 is standard
 */
void apply_coming_of_age_filter(const char* input_path, const char* output_path, float intensity);

#endif // DEFAULT_H
