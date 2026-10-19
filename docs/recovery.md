# Recovery and boot-image boundaries

My recovery path is layered: repair the GUI through SSH if possible; use TWRP
only when the normal rootfs cannot be repaired; retain Download Mode as the
separate recovery-entry path. A black/logo/white screen does not establish a
failed userspace boot. Never sacrifice the working RNDIS/SSH foothold to repair
the display.

## Measured storage map

| Target | Role on the tested SM-G130HN | Recorded size |
|---|---|---:|
| mmcblk0p11 | boot / KERNEL | 8388608 bytes |
| mmcblk0p12 | recovery / TWRP | verify against the device before any operation |
| mmcblk0p18 | Linux rootfs in former system partition | about 1111490560 bytes; verify exactly |
| mmcblk0p20 | Android userdata / historical staging | not the Linux rootfs target |

Identify these from the actual partition map, by-name links and `/proc/partitions`,
not solely from remembered numbers. Read-only checks in the relevant boot context:

```sh
cat /proc/partitions
ls -l /dev/block/platform/*/by-name /dev/block/mmcblk0p11 /dev/block/mmcblk0p12 /dev/block/mmcblk0p18
blockdev --getsize64 /dev/block/mmcblk0p11
```

A missing by-name path or tool is a reason to inspect further, not to invent a
mapping. Do not run block-writing commands merely to test access.

## p11 is larger than the replaceable boot region

The verified pre-Bluetooth backup measured 8 MiB. The replaceable image envelope
is only the first **0x384000 = 3686400 bytes**. Starting at that offset is an
opaque 1288452-byte high-entropy blob, followed by fill and padding. Its role is
not proven; it must be preserved unconditionally. Do not call the rest of p11
free headroom or regenerate it as zeros.

The recorded SHA256 of the entire tail from 0x384000 to the partition end is
`b6639a6ab62846caf81a26ceadd1b78c2a158484ff9c986a362803eb4c9da345`.
The opaque blob alone hashes to
`e071d1ea8378da1e001a79485b9eab82e91cab16eb1a7aeb17ceaa8a2b8211f8`.
These identify this measured backup, not all devices of this model.

## Verify backups before depending on them

Keep an untouched full p11 backup, recovery backup and current rootfs backup in
separate verified storage, with exact byte counts and SHA256 manifests. Re-read
the live partition read-only and compare it with its intended backup before
approving a new experiment. Keep the known-good boot/rootfs pair together; the
old June rootfs is not a backup of the later graphical rootfs. TWRP's presence
alone is not proof that every partition is restorable.

The historical v3 boot image was 3686400 bytes, SHA256
`38d9004055dbcadc2124cf0ab13c41b33ff5abab16f7abdbeb3d590fd030ea25`.
It contains the 2016 kernel SHA256
`f0fdccabcfae5772bedb1a2689b451718362582b3bbbd8daab87aedcb764beaf`.
Verify local artifacts against their own manifests; do not select a file by name
alone. October builds used the same compressed ramdisk, SHA256
`e65decde4922679644ee83ebe7c7fc2495a71bd17769aeb41594fa7007a79643`.

## Rollback strategy

1. If SSH works, stop/repair `young2-gui` or disable only the offending helper.
   Preserve networking and init scripts. Keep originals of replaced config files.
2. If normal boot is unavailable, enter the known TWRP using Volume Up + Home +
   Power. ADB file transfer and TWRP's terminal were the proven maintenance path.
3. If recovery is unavailable, Download Mode uses Volume Down + Home + Power,
   then Volume Up. Recovery restoration needs the exact model's verified package
   and a deliberate plan; do not erase p12 while experimenting with p11.
4. Before a boot rollback, identify the exact verified source file, its length,
   matching ramdisk/layout and intended target. A candidate may affect at most
   the first 0x384000 bytes; compare the tail hash before and after. Never pad a
   replacement image to 8 MiB and overwrite the protected tail.
5. Restoring p18 is a separate, destructive rootfs rollback and loses its later
   changes. Confirm the backup really contains the desired state.

Boot geometry: page 2048, kernel address 0x8000, ramdisk 0x1000000,
second 0xf00000, tags 0x100. The recorded image has no second stage/DTB.
The [file packager](../scripts/build/make_boot_image.py) checks these before
creating a bounded candidate and does not flash it. Building a file is not proof
of a physical boot. Any partition write still requires a separately reviewed
plan and explicit human authorization; none was performed for this branch.
