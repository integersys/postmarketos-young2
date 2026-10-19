# XFCE development documentation

I started with a headless Alpine/postmarketOS system in June 2026. This branch
collects the source and notes behind the later 320×480 XFCE system on my
Samsung Galaxy Young 2 SM-G130HN.

- [Hardware status](hardware-status.md): demonstrated features and test limits.
- [XFCE bring-up](xfce-bringup.md): framebuffer, touch, desktop and boot integration.
- Drivers: [display](drivers/display.md), [touchscreen and keys](drivers/touchscreen.md),
  [Wi-Fi](drivers/wifi.md), [Bluetooth](drivers/bluetooth.md), [audio](drivers/audio.md),
  [power](drivers/power.md), [accelerometer](drivers/accelerometer.md), [camera](drivers/camera.md).
- [Userspace installation map](../userspace/INSTALL.md): dependencies and exact target paths.
- [Building](building.md), [installation](installation.md), [recovery](recovery.md).
- [Known issues](known-issues.md), [development history](development/history.md),
  [verification records](development/verification.md), [changelog](../CHANGELOG.md).

Status describes the last recorded tests through October 11, 2026. The phone was
unreachable during this publication pass, so this is not a fresh hardware retest.
The older numbered documents and the unchanged root README describe the June
headless release. They do not describe a downloadable XFCE image.
