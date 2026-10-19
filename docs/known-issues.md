# Known issues and unverified areas

I keep solved bring-up failures in the history rather than treating them as
current blockers. The present limits are:

- **Camera:** SR352 initializes and produces partial DMA, but no complete verified
  frame. DCAM line errors abort capture; geometry/timing corrections await a live test.
- **Display:** DPMS unblank can restore stale scanout. Keep X DPMS and XFCE's DPMS
  policy disabled. Power-key wake repair does not cover that path. A brief white
  flash and occasional later DISPC sync timeouts remain; a reboot can be delayed.
- **Power:** the active USB gadget's wakelock prevents deep sleep. Battery-only
  suspend tests passed, but long-term power use is unmeasured. No RTC wakealarm
  or trustworthy battery time estimate is exposed.
- **KPLED:** #10 writes the wrong analog base and warns. #11 has the revert but
  was built only. Capacitive symbols remained dark with the valid register too.
  Use front-key light mode off on the running setup.
- **Desktop:** 320×480 and roughly 461 MB usable RAM constrain applications.
  Window bounds cannot redesign fixed-size dialogs. Matchbox placement is static;
  automatic text-focus keyboard behavior is not established. Switch User has no
  demonstrated display-manager handoff.
- **Old-kernel packages:** gdk-pixbuf 2.44/glycin and GLib/musl faccessat2 behavior
  caused real failures. Keep the demonstrated pixbuf workaround and menu shim;
  do not assume current packages work merely because they install.
- **Bluetooth:** pairing/bonding, audio, HID and file transfer are unverified.
  Optional modern BlueZ management commands are absent in Linux 3.10; the tested
  firmware also uses a generic address with unresolved unique provisioning.
- **Other audio routes:** headphones, headset microphone, jack insertion and voice
  paths have not been physically tested. Direct ALSA success does not prove all
  sound-server clients work.
- **Wi-Fi:** 2.4 GHz only; P2P/AP operation is untested. Firmware/NVRAM and your own
  saved connection are required. Windows ICS internet fallback is host-dependent.
- **Sensors/input:** automatic rotation and two-finger gestures are not verified.
  Several preserved helper daemons assume the recorded event numbering.
- **Cellular:** modem, calls, SMS and mobile data have no demonstrated integration.
- **Reproduction:** there is no released XFCE image or fully automated clean-rootfs
  installer. Firmware, original recovery/ramdisk assets and some XFCE preferences
  remain outside the repository. See [building](building.md) and
  [userspace installation](../userspace/INSTALL.md).

The empty Applications menu, missing input symlink, absent sound nodes and
second-cycle power-key state bug were fixed; they are not current open tasks.
