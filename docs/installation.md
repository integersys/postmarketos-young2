# Installation scope

I maintain two different states: the historical June headless release and the
later XFCE development rootfs. The June downloads do not contain the current
desktop, hardware helpers or source-built October kernel. This branch does not
publish a replacement rootfs or promise a one-command fresh installation.

The tested model is SM-G130HN (`young23g` / `young2nfc3g`), ARMv7. Other variants
require their own partition/board verification. On this phone p11 is boot, p12 is
recovery/TWRP and p18 is the Linux rootfs; p20 is Android userdata, not this
installation's rootfs target.

## Starting from the historical release

The original process used Odin to install the matching TWRP package, then TWRP's
own terminal for partition checks and manually authorized writes. `adb push`
worked even when interactive adb shell did not. The compressed rootfs had to be
extracted and its size/hash verified before use. These are historical mechanics,
not permission to overwrite the current phone or recovery.

The old numbered documents retain June details because existing links point to
them. Their old login is not a recommendation for a new installation. Set a unique
password or your own SSH key; generate new SSH host keys and avoid copying saved
credentials. Keep a tested USB rescue link before changing the graphical stack.

## Adding the development integration

Use the [installation map](../userspace/INSTALL.md) for explicit file destinations,
dependencies and services. Stage and inspect files before replacing anything on
a real rootfs. These steps assume an already bootable, backed-up system with
matching firmware and a working rescue path. They were not executed on a fresh
rootfs during this refresh.

Package directories alone are insufficient: postmarketOS-generated initramfs and
boot.img are not automatically the custom static-init image. The current XFCE
setup also depends on package versions, local settings and proprietary firmware
that are intentionally absent here. Read [building](building.md) for that boundary.

## Acceptance checks

Check kernel identity, a real shell/PTY, `rndis0` and SSH on port 2222 first.
Then check framebuffer geometry/metadata, logical X=320×480, translator events,
the GUI service and actual physical display/touch. Verify Wi-Fi DNS/HTTPS and its
selected route independently of USB SSH. Check each audio/Bluetooth/power claim
at its documented scope. See [hardware status](hardware-status.md).

Before any separately approved partition operation, follow [recovery](recovery.md).
No recovery action, raw storage write or image installation is part of this
repository refresh.
