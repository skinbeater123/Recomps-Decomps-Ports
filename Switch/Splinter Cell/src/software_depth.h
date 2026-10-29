#pragma once
#include <stdint.h>

static inline uint32_t sc1_z24s8_clear(uint32_t old, uint32_t value, uint32_t flags)
{
    if (flags & 1u) old = (old & 0xffu) | (value & 0xffffff00u);
    if (flags & 2u) old = (old & 0xffffff00u) | (value & 0xffu);
    return old;
}
static inline int sc1_z24s8_test_write(uint32_t *pixel, uint32_t z, uint32_t func, int write)
{
    uint32_t current = *pixel >> 8;
    int pass;
    z &= 0xffffffu;
    switch (func) {
    case 0x200: pass = 0; break;
    case 0x201: pass = z < current; break;
    case 0x202: pass = z == current; break;
    case 0x203: pass = z <= current; break;
    case 0x204: pass = z > current; break;
    case 0x205: pass = z != current; break;
    case 0x206: pass = z >= current; break;
    case 0x207: pass = 1; break;
    default: return 0;
    }
    if (pass && write) *pixel = (z << 8) | (*pixel & 0xffu);
    return pass;
}
