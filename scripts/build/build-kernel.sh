#!/usr/bin/env bash
# Recorded GCC 15.2 invocation. This builds files only; it never flashes.
set -euo pipefail
tree=${1:?usage: build-kernel.sh PREPARED_SOURCE_DIRECTORY}
cd "$tree"
test -f .config
cross=${CROSS_COMPILE:-arm-linux-gnueabihf-}
args=(ARCH=arm "CROSS_COMPILE=$cross" "CC=${cross}gcc -msoft-float")
"${cross}gcc" --version | head -n 1
cp .config .config.before-olddefconfig
make "${args[@]}" olddefconfig
make "${args[@]}" -j"${JOBS:-$(nproc)}"
sha256sum .config arch/arm/boot/zImage vmlinux System.map
