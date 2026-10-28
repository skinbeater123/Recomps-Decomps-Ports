#ifndef SC1_SOFTWARE_COMBINER_H
#define SC1_SOFTWARE_COMBINER_H
#include <stdint.h>

/* The observed one-stage menu state: RGB = clamp(2 * T0 * V0),
 * alpha = T0.a * V0.a, and the final combiner outputs R0. */
static inline int sc1_menu_combiner_matches(uint32_t control, uint32_t color_in,
        uint32_t color_out, uint32_t alpha_in, uint32_t alpha_out,
        uint32_t final0, uint32_t final1)
{
    return control == 1u && color_in == 0x08040000u && color_out == 0x00010c00u &&
           alpha_in == 0x18140000u && alpha_out == 0x00000c00u &&
           final0 == 0x0000000cu && final1 == 0x00001c80u;
}

static inline uint32_t sc1_menu_combiner(uint32_t texture, uint32_t diffuse)
{
    uint32_t result = 0;
    for (unsigned shift = 0; shift < 32; shift += 8) {
        uint32_t a = (texture >> shift) & 255u, b = (diffuse >> shift) & 255u;
        uint32_t value = (a * b * (shift == 24 ? 1u : 2u) + 127u) / 255u;
        if (value > 255u) value = 255u;
        result |= value << shift;
    }
    return result;
}
#endif
