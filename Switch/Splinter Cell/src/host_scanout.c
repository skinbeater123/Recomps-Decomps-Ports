/* Optional Windows diagnostic: capture the physical surface selected by PCRTC. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <windows.h>

extern ptrdiff_t xbox_GetMemoryOffset(void);
extern uint32_t xbox_mmio_read(uint32_t va, unsigned size);
extern uint32_t xbox_GetDisplayFramebuffer(uint32_t *pitch);

void sc1_dump_scanout(void)
{
    const char *prefix = getenv("SC1_SCANOUT_DUMP");
    const char *sw = getenv("SC1_SCANOUT_WIDTH"), *sh = getenv("SC1_SCANOUT_HEIGHT");
    uint32_t pitch, width, height, physical, bytes, file_size;
    uint8_t header[54] = {0};
    const uint8_t *base;
    char path[512];
    static unsigned sequence;
    static ULONGLONG last_capture;
    ULONGLONG now;
    FILE *f;
    if (!prefix || !sw || !sh) return;
    now = GetTickCount64();
    if (last_capture && now - last_capture < 1000) return;
    width = (uint32_t)strtoul(sw, NULL, 0);
    height = (uint32_t)strtoul(sh, NULL, 0);
    xbox_GetDisplayFramebuffer(&pitch);
    physical = xbox_mmio_read(0xFD600800u, 4) & 0x03ffffffu;
    if (!physical || !width || !height || width > 4096 || height > 4096 ||
        pitch < width * 4 || (uint64_t)physical + (uint64_t)pitch * height > 0x04000000u)
        return;
    bytes = (width * 3 + 3) & ~3u;
    file_size = 54 + bytes * height;
    snprintf(path, sizeof(path), "%s%03u.bmp", prefix, sequence++);
    if (!(f = fopen(path, "wb"))) return;
    last_capture = now;
    { extern void sc1_trace_actor_snapshot(void); sc1_trace_actor_snapshot(); }
    header[0] = 'B'; header[1] = 'M'; header[10] = 54; header[14] = 40;
    memcpy(header + 2, &file_size, 4); memcpy(header + 18, &width, 4);
    memcpy(header + 22, &height, 4); header[26] = 1; header[28] = 24;
    fwrite(header, 1, sizeof(header), f);
    base = (const uint8_t *)xbox_GetMemoryOffset() + (0x80000000u | physical);
    for (uint32_t y = height; y-- > 0;) {
        const uint8_t *row = base + (size_t)y * pitch;
        for (uint32_t x = 0; x < width; ++x) fwrite(row + x * 4, 1, 3, f);
        for (uint32_t x = width * 3; x < bytes; ++x) fputc(0, f);
    }
    fclose(f);
    fprintf(stderr, "[SC1] scanout %08X pitch %u %ux%u: %s\n", physical, pitch, width, height, path);
}
