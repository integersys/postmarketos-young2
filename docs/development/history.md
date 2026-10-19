# Development history

## June 2026: a reliable shell

I built the downstream device/kernel packages, then established the working
static-init boot path using the known-good 2016 kernel. The rootfs lived on p18,
with p11 for boot and p12 for TWRP. OpenRC scripts repaired essential nodes, PTYs,
USB RNDIS and SSH. The first meaningful result was a real Alpine shell that
returned after reboot. The published June image represents that headless stage.

The recovered June pmbootstrap kernel `3.10.17-pmos` is different from the reused
2016 kernel. Its package vmlinuz and the kernel in its generated boot.img are
byte-identical; there were not two different kernels. No preserved physical
boot evidence establishes that June binary running on the phone.

## September: physical graphics and touch

- September 17–18: found the devtmpfs/node problem, demonstrated raw RGBX drawing,
  corrected RGB metadata and made the correction run at boot.
- September 19: made Xorg reach the physical LCD with a post-mode-set pan; built
  the uinput touch translator after native input attempts failed.
- September 20: clicked the first real X client (`xmessage`), ran Openbox and
  demonstrated touch dragging. Fixed the boot touchscreen symlink and switched
  the logical desktop to 320×480 while keeping the two-page framebuffer.
- September 22: first real XFCE 4.20 session, with panel, desktop, windows,
  terminal and keyboard typing. gdk-pixbuf compatibility needed a downgrade.
- September 23: fixed the Applications menu's faccessat2 failure with a preload
  shim and integrated automatic GUI boot with a hard OpenRC dependency on local.
- September 24: window-bounds enforcement passed physical and reboot tests.
  A mobile keyboard candidate was rendered, but its proposed automatic manager
  did not become an established replacement in the preserved record.

## October: hardware and desktop integration

- October 3: built-in ALSA speaker/microphone and internal Broadcom Wi-Fi worked
  with persistent routes/nodes and firmware. A lightweight NetSurf browser was
  added during this period.
- October 4–5: reconstructed the source build with GCC 15.2.0, adjusted LZMA size
  and restored Android USB gadget parity. HCIUART/H4 then supplied Bluetooth
  transport; radio discovery and automatic firmware startup were demonstrated.
  These later source-built kernels must not be confused with the unproven June
  `3.10.17-pmos` binary.
- October 6–7: moved Wi-Fi to NetworkManager, added nm-applet/Blueman, repaired
  sprdfb's resume mode validation and power-key policy, verified real deep sleep,
  shutdown/reboot and session preservation. Added XFCE's battery presentation.
- October 7–9: enabled and physically checked K2HH readings, integrated real
  volume/OSD and Home/Back/Recent actions, and repeated reboot/suspend checks.
  KPLED experiments did not illuminate the capacitive symbols. Kernel #10's bad
  base change remained running; #11 was built to revert it, not separately flashed.
- October 11: SR352 sensor control, CCIR activity and partial DMA were established.
  Static HAL analysis corrected the supposed mode-table interpretation and exposed
  missing capture geometry. A revised local tool was prepared, but no complete
  frame was captured and that revision was not live-tested.

## Publication on this branch

The October 19 refresh preserves both existing branch histories and the root
README bytes. It publishes selected source/configuration and these technical
notes without firmware, images or a new release. Dates above come from the
preserved task records, not newly manufactured Git commits. See
[verification](verification.md) for the distinction between historical hardware
tests and publication checks.
