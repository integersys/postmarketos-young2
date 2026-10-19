# Optional changes, excluded from the default build

`sprdfb-rgb-bitfields.patch` is the September metadata source fix. The physical
RGB values were proven through userspace ioctls, but this source patch was not
physically validated. The default build keeps `98-rgb-bitfields.start` instead.

`kpled-requested-brightness.patch` records the final #11 source state: requested
brightness is no longer forced to zero and the original SCX35-first base is
retained. The removed clamp was exercised in #9; #11 was built after reverting
the bad #10 base change and was not separately flashed. Capacitive symbols did
not illuminate even with correct register writes. This is not a working-light fix.

Neither patch is named in APKBUILD's source/prepare list or applied by
prepare-kernel.sh. Apply one only as a separate, reviewed source experiment.
The #10 wrong-base change and the queued camera board-address change are not
part of this series. See [building](../../../docs/building.md).
