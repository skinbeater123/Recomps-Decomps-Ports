/* Original CPU writes (Bink / loading pictures) share the Xbox framebuffer
 * with GPU draws. The Vulkan image must observe those bytes before drawing
 * an overlay or presenting. GPU-only frames retain their image contents. */
static uint32_t sc1_surface_cpu_bytes(const VkSurf *s)
{
    uint64_t bytes = (uint64_t)s->sc1_pitch * s->h;
    if (s->sc1_bpp != 4 || s->sc1_pitch < s->w * 4u ||
        bytes > 0x04000000u || (s->va & 0x03ffffffu) + bytes > 0x04000000u)
        return 0;
    return (uint32_t)bytes;
}

static int sc1_cpu_scanout_enabled(void)
{
    static int enabled = -1;
    if (enabled < 0) {
        const char *e = getenv("SC1_CPU_SCANOUT");
        enabled = !(e && *e == '0');
    }
    return enabled;
}

static void sc1_surface_cpu_baseline(VkSurf *s)
{
    uint32_t bytes = sc1_surface_cpu_bytes(s);
    if (!bytes) return;
    s->sc1_cpu_hash = bytes_hash_full(s->va, bytes);
    s->sc1_cpu_known = 1;
}

static int sc1_surface_cpu_sync(VkSurf *s)
{
    uint32_t bytes = sc1_surface_cpu_bytes(s), hash;
    VkDeviceSize at;
    void *mapped;
    VkBufferImageCopy copy;
    if (!sc1_cpu_scanout_enabled() || !bytes || s->pw != s->w || s->ph != s->h) return 0;
    hash = bytes_hash_full(s->va, bytes);
    if (s->sc1_cpu_known && hash == s->sc1_cpu_hash) return 0;
    at = ring_alloc(bytes, 16, &mapped);
    if (!mapped) return 0;
    memcpy(mapped, (const uint8_t *)xbox_GetMemoryOffset() + s->va, bytes);
    pend_flush();
    end_rendering();
    barrier_all();
    memset(&copy, 0, sizeof copy);
    copy.bufferOffset = at;
    copy.bufferRowLength = s->sc1_pitch / 4;
    copy.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    copy.imageSubresource.layerCount = 1;
    copy.imageExtent.width = s->w;
    copy.imageExtent.height = s->h;
    copy.imageExtent.depth = 1;
    vkCmdCopyBufferToImage(s_cb, s_f->ring, s->image, VK_IMAGE_LAYOUT_GENERAL, 1, &copy);
    barrier_all();
    s->dirty = 1;
    ++s->gen;
    s->sc1_cpu_hash = hash;
    s->sc1_cpu_known = 1;
    s_drew_any = 1;
    {
        static uint32_t uploaded;
        if (++uploaded <= 8 || uploaded % 120 == 0)
            LOGE("CPU framebuffer upload %u: VA %08X %ux%u pitch %u hash %08X\n",
                 uploaded, s->va, s->w, s->h, s->sc1_pitch, hash);
    }
    return 1;
}

static VkSurf *sc1_scanout_surface(VkSurf *fallback)
{
    extern uint32_t xbox_mmio_read(uint32_t, unsigned);
    uint32_t scanout = xbox_mmio_read(0xFD600800u, 4) & 0x03ffffffu;
    VkSurf *found = NULL;
    if (!sc1_cpu_scanout_enabled() || !scanout) return fallback;
    for (int i = 0; i < VK_MAX_SURF; ++i) {
        VkSurf *s = &s_surf[i];
        if (s->image && (s->va & 0x03ffffffu) == scanout &&
            (!found || s->used > found->used)) found = s;
    }
    return found ? found : fallback;
}
