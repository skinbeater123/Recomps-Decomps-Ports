/* Windows-only clock_gettime bridge for the fork's renderer statistics. */
#pragma once
#include <windows.h>
#include <time.h>
#include <stdlib.h>
#define CLOCK_MONOTONIC 1
static inline int sc1_clock_gettime(int clock_id, struct timespec *value)
{
    LARGE_INTEGER now, frequency;
    (void)clock_id;
    if (!QueryPerformanceCounter(&now) || !QueryPerformanceFrequency(&frequency)) return -1;
    value->tv_sec = (time_t)(now.QuadPart / frequency.QuadPart);
    value->tv_nsec = (long)((now.QuadPart % frequency.QuadPart) * 1000000000ll / frequency.QuadPart);
    return 0;
}
#define clock_gettime sc1_clock_gettime
static inline int sc1_setenv(const char *name, const char *value, int overwrite)
{
    if (!overwrite && getenv(name)) return 0;
    return _putenv_s(name, value) ? -1 : 0;
}
static inline int sc1_unsetenv(const char *name) { return _putenv_s(name, "") ? -1 : 0; }
#define setenv sc1_setenv
#define unsetenv sc1_unsetenv
