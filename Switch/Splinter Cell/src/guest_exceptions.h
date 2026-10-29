#ifndef SC1_GUEST_EXCEPTIONS_H
#define SC1_GUEST_EXCEPTIONS_H

#include <setjmp.h>
#include <stddef.h>
#include <stdint.h>

typedef struct Sc1EhFrame {
    struct Sc1EhFrame *previous;
    jmp_buf landing;
    uint32_t guest_ebp, guest_esp;
    const uint32_t *labels;
    size_t label_count;
    int gil_depth, gil_atomic, dispatch_depth;
} Sc1EhFrame;

void sc1_eh_reset(void);
void sc1_eh_enter(Sc1EhFrame *, uint32_t, uint32_t, const uint32_t *, size_t);
void sc1_eh_leave(Sc1EhFrame *);
void sc1_eh_dispatch_enter(void);
void sc1_eh_dispatch_leave(void);
int sc1_eh_resume(uint32_t, uint32_t);
uint32_t sc1_eh_target(void);
void sc1_eh_get_gil(int *, int *);
void sc1_eh_restore_gil(int, int);

#endif
