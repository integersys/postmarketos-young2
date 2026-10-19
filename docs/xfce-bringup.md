# Bringing XFCE to the Young 2

I built the graphical system in stages, keeping USB RNDIS and SSH available while
each new layer was tested. The result is XFCE 4.20 on the physical 320×480 LCD,
with touch, a keyboard, network applets and hardware controls. It is still a
development system with limited memory and an old downstream kernel.

## The headless starting point

In June I got Alpine 3.24.0/postmarketOS running from `/dev/block/mmcblk0p18`.
The successful v3 boot image reused the 2016 `3.10.17-young2` kernel and replaced
its ramdisk with a static `/init` that mounted the real rootfs and executed
`/sbin/init`. OpenRC local scripts repaired random devices, PTYs and the legacy
Android USB gadget. SSH on `172.16.42.1:2222` survived reboot.

The Samsung logo could remain visible while Linux and SSH were healthy. I treated
userspace boot and physical LCD output as separate tests.

## Framebuffer first

Spreadtrum `sprdfb` registered correctly, but the original kernel had no devtmpfs.
The installed eudev refused to start, leaving `/dev` on plain tmpfs. Creating
`/dev/fb0` from its sysfs major/minor solved access; it did not by itself establish
scanout. The boot script unblanked the panel and issued two pan calls, because
the first refresh after boot is discarded by `SPRDFB_FRAMES_TO_SKIP`.

Direct physical colour tests established RGBX8888: bytes `R G B 00`, stride 1280,
320×480 visible, 320×960 virtual, two 614400-byte pages. The driver's reported
offsets 24/16/8 were wrong. The working offsets are red 0, green 8, blue 16, with
8 bits each and no alpha. I made the runtime correction persistent with
`98-rgb-bitfields.start` and `fbvar.py`. The source RGB patch remains optional;
it is not part of the recorded October kernel build.

## Xorg reaching the LCD

I used Xorg, `xf86-video-fbdev`, `xf86-input-evdev` and small X11 utilities rather
than starting with a desktop. The [configuration](../userspace/display/xorg-scanout.conf)
uses `/dev/fb0`, depth 24, framebuffer bpp 32 and `ShadowFB "false"`.
The [launcher](../userspace/display/start-x-with-handover) selects `vt1` explicitly.

Xorg could render valid framebuffer memory while the LCD scanned an old white
buffer. One pan after Xorg's mode set made the physical panel follow it. The
boot-time two-pan requirement and this later one-pan requirement are different.
Changing the logical mode also needs another pan.

The kernel buffer stays 320×960. `xrandr --output default --mode 320x480` makes the
X root window 320×480 without shrinking that buffer. Setting `Virtual 320 480`
directly failed with the original driver's strict `FBIOPUT_VSCREENINFO` check.

On September 20, `xmessage` became the first real interactive X application:
the touchscreen clicked its button, with physical observation and a clean repeat.
Openbox then demonstrated decorated windows and touch dragging. It needed a real
font; the initial fontless setup crashed.

## Touch input

The IST30xxB device reports type-B multitouch but no `BTN_TOUCH` or single-touch
`ABS_X/ABS_Y`. Native evdev ignored its absolute axes; the original libinput
attempt also depended on a udev path that was unavailable.

[ts-xlate.py](../userspace/input/ts-xlate.py) reads the raw touchscreen, creates a
legacy uinput device and synthesizes the missing single-touch events. It creates
its own `/dev/input/touchscreen-xlate` node. Xorg opens that path explicitly.
The stable raw touchscreen symlink is selected by device name, not event number.

Coordinates increase right and down, with no swap or inversion. The advertised
Y range must match the logical X height: 0–480 for today's 320×480 desktop.
The earlier 0–960 advertisement was appropriate only while X itself was 960 high.
Measured pointer positions reached the top and bottom with approximately 1:1
mapping. Application clicks and window drags supplied stronger evidence than
raw events alone. Two-finger gestures remain untested.

## The first XFCE session

On September 22 I started XFCE 4.20 on the existing `:0` server using
`dbus-run-session -- startxfce4`. The session included `xfce4-session`, `xfwm4`,
`xfce4-panel`, `xfdesktop`, `xfce4-settings`, `xfconf`, Thunar, `xfce4-terminal`
and `xfce4-appfinder`, with an icon theme and fonts.

Two old-kernel compatibility problems mattered:

- gdk-pixbuf 2.44's glycin loader needed `memfd_create`, absent on Linux 3.10.
  Loading icons failed and xfwm4 aborted. The demonstrated workaround was
  gdk-pixbuf and loaders 2.42.12-r0 from Alpine v3.19.
- GLib/GIO existence checks reached `faccessat2`, also absent. Existing desktop
  entries appeared missing, producing an empty Applications menu. The original
  [faccessat shim](../userspace/desktop/young2-faccessat-shim.c), preloaded into
  the session, restored the menu. Its demonstrated scope is this root session's
  existence checks; it is not a general permission or libc replacement.

The menu then launched a terminal by touch. The panel, desktop icons, launcher
dock, window dragging, maximizing and keyboard typing were physically verified.
I did not replace XFCE with a custom shell.

## Fitting applications into 320×480

The panel leaves `_NET_WORKAREA = 0,27,320,453`. Desktop-sized application minimum
hints could still push windows outside that area. xfwm4's placement and snapping
settings did not solve oversized initial windows.

[young2-window-bounds](../userspace/desktop/young2-window-bounds) watches X events,
reads the live workarea and clamps decorated normal windows. It sanitizes large
minimum hints, retries when GTK reasserts them, and asks xfwm4 to move windows
through EWMH. Moving the frame directly caused a fight with the window manager.
Panels, the desktop and keyboard are excluded; fullscreen/maximized windows are
left to xfwm4. Tested dialogs are moved or resized where their hints permit it;
fixed-size dialogs can still be awkward on such a small screen.

Fresh Terminal and Thunar windows, maximize/restore and dragging against the
edges passed physical tests and reboot validation on September 24. The helper
used about 6.7 MB RSS in that test. It cannot redesign an application's contents.

## On-screen keyboard

The persistent configuration recovered here uses `matchbox-keyboard --xid`, the
[compact XML layout](../userspace/desktop/keyboard.xml) and
[young2-keyboard-place](../userspace/desktop/young2-keyboard-place), which maps a
320×120 window at `(0,360)`. `--daemon` alone did not show a usable window.
Typing in xfce4-terminal was physically demonstrated. This placement is manual
within the startup sequence, without automatic text-focus detection.

I later rendered and map/unmap-tested `svkbd-mobile-intl`, but the preserved
records do not establish a completed automatic replacement. October reboot
records still list Matchbox. The unfinished keyboard manager is not installed
by these files.

## Hardware controls

The original [front-key daemon](../userspace/input/young2-frontkeys.py) reads raw
events: Home 102 on `sci-keypad`; Back 158 and Recent 254 on the IST30xx device.
Home uses `wmctrl -k on`, Recent uses xfwm4's `alt+Tab`, and Back sends `alt+Left`
through XTEST. Recent cannot be fixed with XKB alone: 254+8 exceeds the core X
keycode range. The raw handler bypasses that limitation. All three actions were
physically accepted on October 9; Back navigation was also tested in NetSurf.

Volume keys 115/114 are handled by the [ALSA volume daemon](../userspace/audio/young2-volume.py).
It uses speaker gain 0–8, restores DAC gain 4 above zero and mutes the DAC at zero.
The keys and notification OSD passed listening, suspend and reboot tests.
Capacitive-symbol illumination was not achieved; do not confuse key actions
with backlighting.

## Wireless and desktop applets

Wi-Fi first worked with bcmdhd firmware, wpa_supplicant and DHCP from a custom
worker. On October 6 I moved wlan0 ownership to NetworkManager and its internal
DHCP client. The old worker and standalone wpa_supplicant boot service must be
disabled to avoid competing owners. `nm-applet` uses packaged XDG autostart and
the existing XFCE status tray. Wi-Fi defaults use metric 100; the RNDIS fallback
uses 500. An explicit unmanaged rule protects `rndis0` and the SSH link route.

Bluetooth uses BlueZ, Broadcom firmware and a persistent `hciattach` transport
on `/dev/ttyS0`. Kernel HCIUART/H4 support was necessary. The
[boot helper](../userspace/bluetooth/zzz-bluetooth.start) initializes HCI before
starting bluetoothd. Blueman's packaged autostart supplies the tray icon; a local
desktop-entry category override puts Bluetooth Manager in XFCE Settings.
Controller initialization and real Classic/BLE discovery are demonstrated;
pairing and audio profiles are separate, unproven claims.

## Power and persistence

UPower feeds the battery indicator in XFCE Power Manager. `pm-utils` was needed
for its suspend capability detection. The physical power button belongs to
[young2-powerkey.py](../userspace/power/young2-powerkey.py); XFCE's power-button
actions are disabled so there is one policy owner.

Short presses request `mem` or `on` through the Android earlysuspend interface.
The daemon probes real framebuffer state, debounces presses and reasserts scanout
plus `xrefresh` on wake. The kernel resume patch keeps Xorg's EnterVT ioctl from
failing. Real suspend/resume cycles preserved the same graphical session.
USB's `usb_work` wakelock prevents deep sleep while the gadget is active; screen
off on USB is not proof of suspend-to-RAM. Shutdown and reboot were physically
tested; attached VBUS can immediately boot offline charging mode after shutdown.

DPMS remains a separate gap: its unblank path can leave stale scanout. The later
front-key task disabled DPMS again. Keep both X DPMS and XFCE Power Manager's
DPMS policy disabled until that path is fixed.

[young2-gui](../userspace/desktop/young2-gui) is an OpenRC service with a hard
`need local` dependency. A soft `after local` formed an ordering cycle with
`local`'s `after *` and started the GUI too early. The
[launcher](../userspace/desktop/start-young2-gui) waits for prerequisites, starts
translation, Xorg, bounds handling, D-Bus/XFCE and the keyboard. Independent
local scripts provide audio, Bluetooth, power keys, volume, front keys and sensor
enablement. Multiple recorded reboots required no manual desktop repair.

## Current result and reproduction boundary

I can use a touch-driven XFCE desktop with a working Applications menu, keyboard,
Wi-Fi, Bluetooth discovery, speaker/microphone, battery display and physical
controls. A light application at a time is a sensible expectation for roughly
461 MB usable RAM. Some dialogs remain cramped, DPMS needs care, and the camera
has no complete verified frame.

The repository now contains the recovered integration source, config and build
patches. It does not contain a complete modern rootfs, firmware, saved networks,
the private recovery ramdisk or every XFCE preference. Follow the
[installation map](../userspace/INSTALL.md) and [build limits](building.md);
copying the June image alone does not reproduce this desktop.
