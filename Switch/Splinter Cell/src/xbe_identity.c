/* Refuse mismatched executable data before entering statically lifted code. */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include "xbe_identity.h"
#ifdef __SWITCH__
#include <switch.h>
#else
#include <windows.h>
#include <bcrypt.h>
#endif

int sc1_validate_xbe(const void *data, size_t size)
{
    unsigned char digest[32];
    char hex[65];
    size_t i;
#ifdef __SWITCH__
    sha256CalculateHash(digest, data, size);
#else
    BCRYPT_ALG_HANDLE algorithm;
    NTSTATUS status = BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, NULL, 0);
    if (status < 0) return 0;
    status = BCryptHash(algorithm, NULL, 0, (PUCHAR)data, (ULONG)size, digest, sizeof digest);
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (status < 0) return 0;
#endif
    for (i = 0; i < sizeof digest; ++i) sprintf(hex + 2*i, "%02x", digest[i]);
    for (i = 0; i < 64; ++i) if (hex[i] != SC1_XBE_SHA256[i]) return 0;
    return 1;
}
