/* SC1 bring-up diagnostics. No game functions are replaced. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef void (*recomp_func_t)(void);
void print_guest_state(void);
void sc1_guest_cache_sync(void);

recomp_func_t recomp_lookup_manual(uint32_t va)
{
    (void)va;
    return NULL;
}

void recomp_icall_fail_log(uint32_t va)
{
    fprintf(stderr, "[SC1] Unresolved guest call: %08X\n", va);
    print_guest_state();
    fflush(stderr);
    abort();
}

void recomp_icall_not_code_log(uint32_t va)
{
    fprintf(stderr, "[SC1] Guest call outside executable memory: %08X\n", va);
    print_guest_state();
    fflush(stderr);
    abort();
}

void recomp_unimpl(const char *text, uint32_t va)
{
    if (strcmp(text, "wbinvd") == 0) {
        sc1_guest_cache_sync();
        return;
    }
    fprintf(stderr, "[SC1] Unsupported instruction reached: %08X %s\n", va, text);
    print_guest_state();
    fflush(stderr);
    abort();
}
