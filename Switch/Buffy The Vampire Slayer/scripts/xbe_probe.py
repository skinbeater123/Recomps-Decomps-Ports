#!/usr/bin/env python3
"""Read-only XBE metadata probe for the Buffy feasibility audit.

Prints header, certificate, section, library-version and kernel-import
metadata as JSON. It never emits code or data bytes from the image, so its
output is safe to publish. Usage:

    python -I xbe_probe.py <path/to/default.xbe> [--kernel-names]

Structure offsets follow the public XBE format notes at
https://xboxdevwiki.net/Xbe (Caustik / Cxbx-Reloaded documentation).
"""
import hashlib
import json
import struct
import sys

ENTRY_KEYS = {"retail": 0xA8FC57AB, "debug": 0x94859D4B, "beta": 0xE682F45B}
THUNK_KEYS = {"retail": 0x5B6D40B6, "debug": 0xEFB1F152, "beta": 0x46437DCD}

SECTION_FLAGS = {
    0x01: "writable",
    0x02: "preload",
    0x04: "executable",
    0x08: "inserted_file",
    0x10: "head_page_ro",
    0x20: "tail_page_ro",
}

# Subset of xboxkrnl export ordinals, enough to name what Buffy imports.
# Source: public xboxkrnl export table (Cxbx-Reloaded / xboxdevwiki).
KERNEL_ORDINALS = {
    1: "AvGetSavedDataAddress", 2: "AvSendTVEncoderOption", 3: "AvSetDisplayMode",
    4: "AvSetSavedDataAddress", 8: "DbgPrint", 14: "ExAllocatePool",
    15: "ExAllocatePoolWithTag", 16: "ExEventObjectType", 17: "ExFreePool",
    23: "ExQueryPoolBlockSize", 24: "ExQueryNonVolatileSetting", 37: "FscSetCacheSize",
    40: "HalDiskCachePartitionCount", 44: "HalGetInterruptVector",
    46: "HalReadWritePCISpace", 47: "HalRegisterShutdownNotification",
    49: "HalReturnToFirmware", 65: "IoCreateDevice", 67: "IoCreateSymbolicLink",
    69: "IoDeleteSymbolicLink", 74: "IoInvalidDeviceRequest", 81: "IoStartNextPacket",
    83: "IoStartPacket", 87: "IofCompleteRequest", 91: "IoDismountVolumeByName", 95: "KeBugCheck", 97: "KeCancelTimer",
    98: "KeConnectInterrupt", 99: "KeDelayExecutionThread", 100: "KeDisconnectInterrupt",
    107: "KeInitializeDpc", 109: "KeInitializeInterrupt", 113: "KeInitializeTimerEx",
    119: "KeInsertQueueDpc", 125: "KeQueryInterruptTime", 128: "KeQuerySystemTime",
    129: "KeRaiseIrqlToDpcLevel", 137: "KeRemoveQueueDpc", 139: "KeRestoreFloatingPointState",
    142: "KeSaveFloatingPointState", 145: "KeSetEvent", 149: "KeSetTimer",
    150: "KeSetTimerEx", 151: "KeStallExecutionProcessor", 153: "KeSynchronizeExecution",
    156: "KeTickCount", 158: "KeWaitForMultipleObjects", 159: "KeWaitForSingleObject",
    160: "KfRaiseIrql", 161: "KfLowerIrql", 164: "LaunchDataPage",
    165: "MmAllocateContiguousMemory", 166: "MmAllocateContiguousMemoryEx",
    167: "MmAllocateSystemMemory", 168: "MmClaimGpuInstanceMemory",
    171: "MmFreeContiguousMemory", 172: "MmFreeSystemMemory", 173: "MmGetPhysicalAddress",
    175: "MmLockUnlockBufferPages", 176: "MmLockUnlockPhysicalPage",
    178: "MmPersistContiguousMemory", 179: "MmQueryAddressProtect",
    180: "MmQueryAllocationSize", 181: "MmQueryStatistics", 182: "MmSetAddressProtect",
    184: "NtAllocateVirtualMemory", 186: "NtClearEvent", 187: "NtClose",
    189: "NtCreateEvent", 190: "NtCreateFile", 196: "NtDeviceIoControlFile",
    198: "NtFlushBuffersFile", 199: "NtFreeVirtualMemory", 200: "NtFsControlFile",
    202: "NtOpenFile", 203: "NtOpenSymbolicLinkObject", 205: "NtPulseEvent",
    207: "NtQueryDirectoryFile", 210: "NtQueryFullAttributesFile",
    211: "NtQueryInformationFile", 215: "NtQuerySymbolicLinkObject",
    217: "NtQueryVirtualMemory", 218: "NtQueryVolumeInformationFile", 219: "NtReadFile",
    225: "NtSetEvent", 226: "NtSetInformationFile", 233: "NtWaitForSingleObject",
    234: "NtWaitForSingleObjectEx", 236: "NtWriteFile", 238: "NtYieldExecution",
    246: "ObReferenceObjectByHandle", 250: "ObfDereferenceObject",
    255: "PsCreateSystemThreadEx", 258: "PsTerminateSystemThread", 259: "PsThreadObjectType",
    260: "RtlAnsiStringToUnicodeString", 269: "RtlCompareMemoryUlong",
    277: "RtlEnterCriticalSection", 279: "RtlEqualString", 289: "RtlInitAnsiString",
    291: "RtlInitializeCriticalSection", 294: "RtlLeaveCriticalSection",
    301: "RtlNtStatusToDosError", 302: "RtlRaiseException", 304: "RtlTimeFieldsToTime",
    305: "RtlTimeToTimeFields", 312: "RtlUnwind", 321: "XboxEEPROMKey",
    322: "XboxHardwareInfo", 323: "XboxHDKey", 324: "XboxKrnlBuildNumber",
    325: "XboxSignatureKey", 327: "XeLoadSection", 328: "XeUnloadSection",
    335: "XcSHAInit", 336: "XcSHAUpdate", 337: "XcSHAFinal", 359: "IoMarkIrpMustComplete",
    354: "XboxAlternateSignatureKeys", 356: "HalBootSMCVideoMode",
    358: "HalIsResetOrShutdownPending", 360: "HalInitiateShutdown",
    104: "KeGetCurrentThread",
}


def cstr(buf, off, maxlen=256):
    end = buf.find(b"\0", off, off + maxlen)
    return buf[off:end if end >= 0 else off + maxlen].decode("latin-1")


def main(argv):
    path = argv[1]
    want_names = "--kernel-names" in argv
    with open(path, "rb") as f:
        img = f.read()
    out = {"file_size": len(img),
           "sha256": hashlib.sha256(img).hexdigest().upper(),
           "sha1": hashlib.sha1(img).hexdigest().upper()}
    if img[:4] != b"XBEH":
        out["error"] = "not an XBE (magic mismatch)"
        print(json.dumps(out, indent=2))
        return 2
    (base, size_headers, size_image, size_image_header, timedate, cert_addr,
     num_sections, section_headers_addr, init_flags, entry_enc, tls_addr,
     stack_commit, heap_reserve, heap_commit, pe_base, pe_size_image, pe_checksum,
     pe_timedate, debug_path_addr, debug_file_addr, debug_unicode_addr,
     thunk_enc, nonkernel_import_dir, num_lib_versions, lib_versions_addr,
     kernel_lib_addr, xapi_lib_addr, logo_addr, logo_size) = struct.unpack_from(
        "<29I", img, 0x104)

    def off(va):
        return va - base

    def classify(enc, keys):
        hits = {}
        for name, key in keys.items():
            va = enc ^ key
            if base <= va < base + size_image:
                hits[name] = va
        return hits

    entry = classify(entry_enc, ENTRY_KEYS)
    thunk = classify(thunk_enc, THUNK_KEYS)
    out["header"] = {
        "base_address": hex(base), "size_of_headers": hex(size_headers),
        "size_of_image": hex(size_image), "timedate": hex(timedate),
        "init_flags": hex(init_flags), "tls_addr": hex(tls_addr),
        "pe_stack_commit": hex(stack_commit), "pe_heap_reserve": hex(heap_reserve),
        "pe_heap_commit": hex(heap_commit), "pe_base": hex(pe_base),
        "pe_size_of_image": hex(pe_size_image), "pe_timedate": hex(pe_timedate),
        "debug_path": cstr(img, off(debug_path_addr)) if debug_path_addr else None,
        "debug_filename": cstr(img, off(debug_file_addr)) if debug_file_addr else None,
        "entry_point_decoded": {k: hex(v) for k, v in entry.items()},
        "kernel_thunk_decoded": {k: hex(v) for k, v in thunk.items()},
        "nonkernel_import_dir": hex(nonkernel_import_dir),
    }

    c = off(cert_addr)
    (cert_size, cert_time, title_id) = struct.unpack_from("<3I", img, c)
    title_name = img[c + 0xC:c + 0xC + 80].decode("utf-16-le").split("\0")[0]
    (media, region, ratings, disk, version) = struct.unpack_from("<5I", img, c + 0x9C)
    out["certificate"] = {
        "timedate": hex(cert_time), "title_id": "%08X" % title_id,
        "title_id_publisher": img[c + 8 + 3:c + 8 + 1:-1].decode("latin-1", "replace"),
        "title_id_number": title_id & 0xFFFF, "title_name": title_name,
        "allowed_media": hex(media), "game_region": hex(region),
        "game_ratings": hex(ratings), "disk_number": disk, "version": hex(version),
    }

    sections = []
    for i in range(num_sections):
        h = off(section_headers_addr) + i * 56
        (flags, vaddr, vsize, raw_addr, raw_size, name_addr) = struct.unpack_from("<6I", img, h)
        raw = img[raw_addr:raw_addr + raw_size]
        sections.append({
            "name": cstr(img, off(name_addr), 16), "vaddr": hex(vaddr), "vsize": hex(vsize),
            "raw_addr": hex(raw_addr), "raw_size": hex(raw_size),
            "flags": [n for b, n in SECTION_FLAGS.items() if flags & b],
            "raw_sha1": hashlib.sha1(raw).hexdigest().upper(),
        })
    out["sections"] = sections

    libs = []
    for i in range(num_lib_versions):
        l = off(lib_versions_addr) + i * 16
        name = img[l:l + 8].split(b"\0")[0].decode("latin-1")
        major, minor, build, fl = struct.unpack_from("<4H", img, l + 8)
        libs.append({"name": name, "version": "%d.%d.%d" % (major, minor, build),
                     "qfe": fl & 0x1FFF, "approved": (fl >> 13) & 3,
                     "debug": bool(fl & 0x8000)})
    out["library_versions"] = libs

    def va_to_file(va):
        for s in sections:
            v, r = int(s["vaddr"], 16), int(s["raw_addr"], 16)
            if v <= va < v + int(s["raw_size"], 16):
                return r + (va - v)
        return off(va)  # header region maps 1:1

    if thunk:
        tva = next(iter(thunk.values()))
        ords = []
        p = va_to_file(tva)
        while True:
            (v,) = struct.unpack_from("<I", img, p)
            if v == 0:
                break
            ords.append(v & 0x7FFFFFFF if v & 0x80000000 else v)
            p += 4
        out["kernel_imports"] = {"count": len(ords)}
        if want_names:
            out["kernel_imports"]["names"] = sorted(
                KERNEL_ORDINALS.get(o, "ordinal_%d" % o) for o in ords)
        unknown = [o for o in ords if o not in KERNEL_ORDINALS]
        out["kernel_imports"]["unnamed_ordinals"] = sorted(unknown)

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
