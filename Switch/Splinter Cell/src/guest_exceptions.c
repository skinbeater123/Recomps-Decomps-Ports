#include "guest_exceptions.h"

#if defined(_MSC_VER)
#define SC1_TLS __declspec(thread)
#else
#define SC1_TLS _Thread_local
#endif

static SC1_TLS Sc1EhFrame *sc1_eh_top;
static SC1_TLS int sc1_eh_dispatch_depth;
static SC1_TLS uint32_t sc1_eh_landing_target;

void sc1_eh_enter(Sc1EhFrame *frame, uint32_t ebp, uint32_t esp,
                  const uint32_t *labels, size_t count)
{
    frame->previous = sc1_eh_top;
    frame->guest_ebp = ebp;
    frame->guest_esp = esp;
    frame->labels = labels;
    frame->label_count = count;
    frame->dispatch_depth = sc1_eh_dispatch_depth;
    sc1_eh_get_gil(&frame->gil_depth, &frame->gil_atomic);
    sc1_eh_top = frame;
}

void sc1_eh_leave(Sc1EhFrame *frame)
{
    Sc1EhFrame **slot = &sc1_eh_top;
    while (*slot && *slot != frame) slot = &(*slot)->previous;
    if (*slot) *slot = frame->previous;
}

void sc1_eh_dispatch_enter(void) { ++sc1_eh_dispatch_depth; }
void sc1_eh_dispatch_leave(void) { if (sc1_eh_dispatch_depth) --sc1_eh_dispatch_depth; }
uint32_t sc1_eh_target(void) { return sc1_eh_landing_target; }

int sc1_eh_resume(uint32_t target, uint32_t esp)
{
    Sc1EhFrame *frame;
    if (!sc1_eh_dispatch_depth) return 0;
    for (frame = sc1_eh_top; frame; frame = frame->previous) {
        if (frame->guest_esp != esp) continue;
        for (size_t i = 0; i < frame->label_count; ++i) {
            if (frame->labels[i] != target) continue;
            sc1_eh_landing_target = target;
            sc1_eh_top = frame; /* deeper native frames are about to disappear */
            sc1_eh_dispatch_depth = frame->dispatch_depth;
            sc1_eh_restore_gil(frame->gil_depth, frame->gil_atomic);
            longjmp(frame->landing, 1);
        }
    }
    return 0;
}

void sc1_eh_reset(void) { sc1_eh_top = NULL; sc1_eh_dispatch_depth = 0; sc1_eh_landing_target = 0; }
