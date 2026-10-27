/* Windows equivalents of the fork's Horizon host scheduling helpers. */
#include <windows.h>
#include <stdlib.h>
#include <stdio.h>
void xbox_guest_pin(int interrupt)
{
    const char *mode = getenv("RECOMP_GUEST_ONE_CORE");
    DWORD_PTR allowed, system, chosen = 1;
    if (!mode || (*mode != '1' && *mode != '2') || (interrupt && *mode == '2')) return;
    if (!GetProcessAffinityMask(GetCurrentProcess(), &allowed, &system)) return;
    for (unsigned bit = 0; bit < sizeof(allowed)*8; ++bit)
        if (allowed & ((DWORD_PTR)1 << bit)) chosen = (DWORD_PTR)1 << bit;
    if (!SetThreadAffinityMask(GetCurrentThread(), chosen))
        fprintf(stderr,"[host] guest affinity failed: %lu\n", GetLastError());
}
void xbox_nx_retag_thread(void *entry)
{
    wchar_t name[64];
    swprintf(name, sizeof name / sizeof name[0], L"Xbox guest %p", entry);
    SetThreadDescription(GetCurrentThread(), name);
}
void xbox_nx_raise_host_thread(void)
{
    if (!SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_HIGHEST))
        fprintf(stderr,"[host] audio priority failed: %lu\n",GetLastError());
}
