#!/usr/bin/env bash
set -euo pipefail
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
export DEVKITPRO="$(cygpath -u "${DEVKITPRO:-C:/Programming/devkitPro}")"
export DEVKITA64="$DEVKITPRO/devkitA64"
export PATH="/usr/bin:$DEVKITA64/bin:$DEVKITPRO/tools/bin:$PATH"
cmake -S "$PROJECT" -B "$PROJECT/build/switch" -G 'Unix Makefiles' \
  -DCMAKE_TOOLCHAIN_FILE="$DEVKITPRO/cmake/Switch.cmake" -DCMAKE_BUILD_TYPE=Release \
  -DSC1_GEN_OPT="${SC1_GEN_OPT:--O1}"
cmake --build "$PROJECT/build/switch" --target sc1_nro --parallel "${SC1_JOBS:-2}"
