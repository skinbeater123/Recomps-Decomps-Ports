#ifndef SC1_SOFTWARE_BLEND_H
#define SC1_SOFTWARE_BLEND_H
#include <stdint.h>

/* NV2A/OpenGL blend factors for the ADD equation. Returns 0 for a factor the
 * diagnostic rasterizer does not implement, leaving its caller's fallback. */
static inline int sc1_blend_factor(uint32_t factor, uint32_t source, uint32_t dest,
                                   unsigned shift, uint32_t *out)
{
    uint32_t s = (source >> shift) & 255u, d = (dest >> shift) & 255u;
    uint32_t sa = source >> 24, da = dest >> 24;
    switch (factor) {
    case 0: *out = 0; return 1;
    case 1: *out = 255; return 1;
    case 0x300: *out = s; return 1;
    case 0x301: *out = 255u - s; return 1;
    case 0x302: *out = sa; return 1;
    case 0x303: *out = 255u - sa; return 1;
    case 0x304: *out = da; return 1;
    case 0x305: *out = 255u - da; return 1;
    case 0x306: *out = d; return 1;
    case 0x307: *out = 255u - d; return 1;
    default: return 0;
    }
}

static inline int sc1_blend_add(uint32_t source, uint32_t dest,
                                 uint32_t sf, uint32_t df, uint32_t *out)
{
    uint32_t result = 0;
    for (unsigned shift = 0; shift < 32; shift += 8) {
        uint32_t s = (source >> shift) & 255u, d = (dest >> shift) & 255u;
        uint32_t a, b;
        if (!sc1_blend_factor(sf, source, dest, shift, &a) ||
            !sc1_blend_factor(df, source, dest, shift, &b)) return 0;
        uint32_t value = (s * a + d * b + 127u) / 255u;
        if (value > 255u) value = 255u;
        result |= value << shift;
    }
    *out = result;
    return 1;
}
#endif
