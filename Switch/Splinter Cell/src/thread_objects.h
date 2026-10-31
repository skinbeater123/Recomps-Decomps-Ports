/* Guest-visible thread references. The host thread handle may outlive the
 * worker's TIB and registration, so its dispatcher state needs its own object.
 * Included inside the bridge, after its platform and guest-memory definitions. */
#ifndef SC1_THREAD_OBJECTS_H
#define SC1_THREAD_OBJECTS_H

#define SC1_THREAD_OBJECT_MAX 256
typedef struct {
    HANDLE source, duplicate;
    DWORD tid;
    uint32_t guest, refs;
} Sc1ThreadObject;
static Sc1ThreadObject sc1_thread_objects[SC1_THREAD_OBJECT_MAX];
static SRWLOCK sc1_thread_objects_lock = SRWLOCK_INIT;

static void sc1_thread_destroy(Sc1ThreadObject *entry)
{
    CloseHandle(entry->duplicate);
    xbox_HeapFree(entry->guest);
    memset(entry, 0, sizeof(*entry));
}

static uint32_t sc1_thread_reference(HANDLE source)
{
    DWORD code, tid;
    Sc1ThreadObject *entry = NULL, *empty = NULL;
    if (!source || !GetExitCodeThread(source, &code) || !(tid = GetThreadId(source))) return 0;
    AcquireSRWLockExclusive(&sc1_thread_objects_lock);
    for (int i = 0; i < SC1_THREAD_OBJECT_MAX; ++i) {
        if (sc1_thread_objects[i].source == source) { entry = &sc1_thread_objects[i]; break; }
        if (!empty && !sc1_thread_objects[i].guest) empty = &sc1_thread_objects[i];
    }
    if (!entry && empty) {
        HANDLE duplicate = NULL;
        uint32_t guest = xbox_HeapAlloc(0x124, 16);
        if (guest && DuplicateHandle(GetCurrentProcess(), source, GetCurrentProcess(),
                                     &duplicate, 0, FALSE, DUPLICATE_SAME_ACCESS)) {
            memset(XBOX_TO_NATIVE(guest), 0, 0x124);
            empty->source = source; empty->duplicate = duplicate;
            empty->tid = tid; empty->guest = guest; entry = empty;
        } else if (guest) xbox_HeapFree(guest);
    }
    if (entry) {
        int exited = WaitForSingleObject(source, 0) == WAIT_OBJECT_0;
        if (exited) GetExitCodeThread(source, &code);
        BRIDGE_MEM32(entry->guest + 4) = exited ? 1u : 0u;
        BRIDGE_MEM32(entry->guest + 0x120) = code;
        ++entry->refs;
    }
    uint32_t result = entry ? entry->guest : 0;
    ReleaseSRWLockExclusive(&sc1_thread_objects_lock);
    return result;
}

static HANDLE sc1_thread_host(uint32_t guest)
{
    HANDLE result = NULL;
    if (!guest) return NULL;
    AcquireSRWLockExclusive(&sc1_thread_objects_lock);
    for (int i = 0; i < SC1_THREAD_OBJECT_MAX; ++i)
        if (sc1_thread_objects[i].guest == guest) { result = sc1_thread_objects[i].duplicate; break; }
    ReleaseSRWLockExclusive(&sc1_thread_objects_lock);
    return result;
}

static int sc1_thread_addref(uint32_t guest)
{
    int found = 0;
    if (!guest) return 0;
    AcquireSRWLockExclusive(&sc1_thread_objects_lock);
    for (int i = 0; i < SC1_THREAD_OBJECT_MAX; ++i)
        if (sc1_thread_objects[i].guest == guest) { ++sc1_thread_objects[i].refs; found = 1; break; }
    ReleaseSRWLockExclusive(&sc1_thread_objects_lock);
    return found;
}

static int sc1_thread_dereference(uint32_t guest)
{
    int found = 0;
    AcquireSRWLockExclusive(&sc1_thread_objects_lock);
    for (int i = 0; i < SC1_THREAD_OBJECT_MAX; ++i) {
        Sc1ThreadObject *entry = &sc1_thread_objects[i];
        if (entry->guest != guest || !guest) continue;
        found = 1;
        if (entry->refs) --entry->refs;
        if (!entry->refs && !entry->source) sc1_thread_destroy(entry);
        break;
    }
    ReleaseSRWLockExclusive(&sc1_thread_objects_lock);
    return found;
}

static void sc1_thread_close(HANDLE source)
{
    AcquireSRWLockExclusive(&sc1_thread_objects_lock);
    for (int i = 0; i < SC1_THREAD_OBJECT_MAX; ++i) {
        Sc1ThreadObject *entry = &sc1_thread_objects[i];
        if (entry->source != source || !source) continue;
        entry->source = NULL;
        if (!entry->refs) sc1_thread_destroy(entry);
        break;
    }
    ReleaseSRWLockExclusive(&sc1_thread_objects_lock);
}

static void sc1_thread_exit(DWORD tid, uint32_t code)
{
    AcquireSRWLockExclusive(&sc1_thread_objects_lock);
    for (int i = 0; i < SC1_THREAD_OBJECT_MAX; ++i) {
        Sc1ThreadObject *entry = &sc1_thread_objects[i];
        if (entry->guest && entry->tid == tid) {
            BRIDGE_MEM32(entry->guest + 0x120) = code;
            BRIDGE_MEM32(entry->guest + 4) = 1;
        }
    }
    ReleaseSRWLockExclusive(&sc1_thread_objects_lock);
}
#endif
