#!/usr/bin/env bash
# Export the pinned source into a new directory; never edit the input checkout.
set -euo pipefail
src=${1:?usage: prepare-kernel.sh SOURCE_CHECKOUT NEW_OUTPUT_DIRECTORY}
dest=${2:?usage: prepare-kernel.sh SOURCE_CHECKOUT NEW_OUTPUT_DIRECTORY}
root=$(cd "$(dirname "$0")/../.." && pwd)
pkg="$root/linux-samsung-young23g"
revision=e05a1c16fb7334378bb12d8116d0def2ef83ff0d
test "$(git -C "$src" rev-parse HEAD)" = "$revision"
if [ -e "$dest" ]; then
    echo "Output already exists: $dest" >&2
    exit 1
fi
mkdir -p "$dest"
git -C "$src" archive "$revision" | tar -x -C "$dest"
for patch in 0001-gcc15-compatibility.patch 0002-sprdfb-resume.patch; do
    patch -d "$dest" -p1 --batch --forward < "$pkg/patches/$patch"
done
cp "$pkg/config-xfce.armv7" "$dest/.config"
echo "Prepared $dest; no build or device action has run."
