/* Command side effects for the existing NV2A executor. No guest overrides.
 * Register/DMA layout follows the NV2A definitions already shipped by xboxrecomp.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static uint32_t semaphore_handle, semaphore_offset;
#define GPU32(a) (*(volatile uint32_t *)(memory + (uint32_t)(a)))

int sc1_gpu_command(uint8_t *memory, uint32_t subch, uint32_t method, uint32_t param)
{
    if (subch != 0) return 0;
    if (method == 0x1D8C) GPU32(0xFD401A88u) = param;
    if (method == 0x1D90) GPU32(0xFD40186Cu) = param;
    if (method == 0x01A4) semaphore_handle = param;
    if (method == 0x1D6C) semaphore_offset = param;
    if (method == 0x1D70 && semaphore_handle) {
        uint32_t ramht = GPU32(0xFD002210u);
        uint32_t table = 0xFD700000u + ((ramht & 0x1F0u) << 8);
        uint32_t size = 4096u << ((ramht >> 16) & 3u);
        for (uint32_t i = 0; i < size; i += 8) {
            uint32_t context = GPU32(table + i + 4);
            if (GPU32(table + i) == semaphore_handle && (context & 0x80000000u)) {
                uint32_t object = 0xFD700000u + ((context & 0xFFFFu) << 4);
                uint32_t flags = GPU32(object), limit = GPU32(object + 4);
                uint32_t frame = GPU32(object + 8);
                uint32_t base = ((frame & 0xFFFFF000u) | (flags >> 20)) & 0x07FFFFFFu;
                uint64_t physical = (uint64_t)base + semaphore_offset;
                if ((semaphore_offset & 3u) || limit < 3u ||
                        semaphore_offset > limit - 3u || physical > 0x03FFFFFCu)
                    break;
                /* DMA physical RAM is the runtime's contiguous window. */
                GPU32(0x80000000u | (uint32_t)physical) = param;
                return 1;
            }
        }
        fprintf(stderr, "[SC1 GPU] invalid semaphore DMA handle=%08X offset=%08X\n",
                semaphore_handle, semaphore_offset);
        abort();
    }
    return 0;
}
