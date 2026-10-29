#pragma once
#include <stdint.h>
#include <math.h>
static inline uint32_t sc1_texcoord(float coord, uint32_t size, uint32_t mode)
{
    if (!size || !isfinite(coord)) return 0;
    if (mode == 1) {
        float wrapped = fmodf(floorf(coord), (float)size);
        if (wrapped < 0.0f) wrapped += (float)size;
        return (uint32_t)wrapped;
    }
    if (coord < 0.0f) return 0;
    if (coord >= (float)size) return size - 1;
    return (uint32_t)coord;
}
