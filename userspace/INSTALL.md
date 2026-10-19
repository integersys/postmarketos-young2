# Installing the recovered userspace integration

These are the original helpers from the demonstrated system, with LF line endings
and a few corrected comments. I have not rewritten their device policy. Installing
all of them is not a complete fresh-rootfs installer: first establish the boot,
SSH and backup baseline described in [installation](../docs/installation.md).

## File destinations

Install executable helpers as mode 0755 and ordinary configuration as 0644.
The paths are explicit so files can be reviewed individually before installation.
Do not copy this entire directory onto `/`.

| Repository file(s), relative to userspace/ | Target |
|---|---|
| display/fbvar.py, display/start-x-with-handover | /usr/local/bin/ with the same names |
| display/98-fb0-node.start, display/98-rgb-bitfields.start | /etc/local.d/ with the same names |
| display/xorg-scanout.conf | /etc/young2/xorg-scanout.conf |
| input/97-input-nodes.start | /etc/local.d/97-input-nodes.start |
| input/ts-xlate.py, input/young2-frontkeys.py | /usr/local/bin/ with the same names |
| input/72-young2-frontkeys.start | /etc/local.d/72-young2-frontkeys.start |
| desktop/start-young2-gui, desktop/young2-window-bounds, desktop/young2-keyboard-place | /usr/local/bin/ with the same names |
| desktop/young2-gui | /etc/init.d/young2-gui |
| desktop/keyboard.xml | /usr/share/matchbox-keyboard/keyboard.xml (back up the packaged layout) |
| desktop/young2-faccessat-shim.c | build a shared library, install as /usr/local/lib/young2-faccessat-shim.so |
| audio/50-snd-nodes.start, audio/51-audio-route.start, audio/61-young2-volume.start | /etc/local.d/ with the same names |
| audio/young2-volume.py | /usr/local/bin/young2-volume.py |
| wifi/52-rfkill-node.start | /etc/local.d/52-rfkill-node.start |
| wifi/20-young2-rescue-unmanaged.conf | /etc/NetworkManager/conf.d/20-young2-rescue-unmanaged.conf |
| bluetooth/zzz-bluetooth.start | /etc/local.d/zzz-bluetooth.start |
| power/60-young2-powerkey.start | /etc/local.d/60-young2-powerkey.start |
| power/young2-powerkey.py | /usr/local/bin/young2-powerkey.py |
| sensors/70-young2-accel.start | /etc/local.d/70-young2-accel.start |
| sensors/young2-accel | /usr/local/bin/young2-accel |

The existing June rescue scripts remain under [scripts/](../scripts/).
They belong in `/etc/local.d/` on that historical rootfs. Do not overwrite a
later working networking configuration with those historical copies.

## Dependencies and package compatibility

The recorded system used Xorg/fbdev/evdev, xrandr, xset, xprop, xrefresh, Python 3,
libX11, XFCE 4.20 (session, xfwm4, panel, desktop, settings, xfconf, appfinder,
terminal, Thunar), fonts, an icon theme, D-Bus and Matchbox keyboard/libfakekey.
The kernel needs framebuffer, input, legacy uinput and a real VT. The October
kernel's devtmpfs supplies base nodes; the original node helpers also support
the older kernel's missing-node setup.

Keep the demonstrated gdk-pixbuf/loaders **2.42.12-r0** compatibility workaround;
2.44/glycin failed on the old kernel. These were historical Alpine v3.19 armv7
packages installed alongside newer packages, not a tested general upgrade path.
Use inspected, compatible package files and verify their origin/checksums. I do
not publish an exact locked APK set or recommend a blind upgrade.

Other dependencies by integration:

| Integration | Dependencies |
|---|---|
| Front keys | wmctrl, xdotool, Python, the X session |
| Audio/volume | alsa-utils (amixer/aplay/arecord), notify-send/libnotify, xfce4-notifyd |
| Wi-Fi | networkmanager + wifi/cli/openrc support, wpa_supplicant, network-manager-applet, iw, device firmware/NVRAM |
| Bluetooth | bluez/bluez-openrc, hciattach (deprecated BlueZ utilities), hciconfig, rfkill, device HCD, Blueman |
| Power | xfce4-power-manager, UPower, pm-utils, polkit, xrefresh |
| Accelerometer GUI | Python GI bindings, GTK3; no IIO service |

Build the original preload shim for **ARM musl**, not Windows or glibc:

```sh
python -m ziglang cc -target arm-linux-musleabihf -shared -fPIC -O2   -o young2-faccessat-shim.so userspace/desktop/young2-faccessat-shim.c
```

That is the recorded cross-build command. It was not rerun for this publication.
The launcher exports LD_PRELOAD into the session. The shim's proven use is this
root XFCE session's file-existence checks; it is not a general access-control shim.

## Configuration and startup order

1. Verify the keypad/touchscreen/accelerometer names against sysfs. Original policy
   daemons assume the observed event0/event1/event3 enumeration and 32-bit ARM ABI.
2. Install the display/input files, the compact keyboard and the built shim.
   Enable OpenRC `local`. Input nodes/symlink and fb0 must exist before GUI startup;
   `98-rgb-bitfields.start` must follow `98-fb0-node.start`.
3. Install `young2-gui` and its launcher/helpers. Enable with
   `rc-update add young2-gui default`; control it with
   `rc-service young2-gui start|stop|restart|status` (choose one action).
   Its hard `need local` avoids the observed soft-ordering cycle.
4. Audio nodes and routes run at 50/51; volume at 61. The packaged notification
   autostart also supplies notifyd once XFCE has its D-Bus session.
5. Power key runs at 60, sensor enable at 70, front keys at 72. For the running
   #10 kernel persist `/var/lib/young2-frontkeys.mode` as `off` and timeout as `2`
   before startup, or use `young2-frontkeys.py light off`. The CLI name includes
   `.py`; no extensionless wrapper is required. This disables LED attempts; key
   actions remain active. Some boot/resume LED-off writes still originate in the
   preserved script/kernel path and can warn on #10.
6. Bluetooth's `zzz-bluetooth.start` runs after rfkill and mounted firmware.
   It calls the packaged bluetooth service after transport setup. Do not install
   a competing hciattach startup or independently enable an early bluetooth daemon.

The recovered launcher starts a root session. The recorded XFCE preferences were
under `/.config/xfce4/`; do not assume a nonroot home is equivalent. Selected
panel/dock/theme preferences remain in the current rootfs; this repository does
not copy a complete home directory. The existing XFCE status-tray plugin hosts
nm-applet and Blueman through their packaged XDG autostart entries.

Within that session use the measured policy (create properties with the
corresponding bool/int type if a fresh xfconf tree lacks them):

```sh
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/power-button-action -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/sleep-button-action -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/hibernate-button-action -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-enabled -s false
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-ac -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-battery -s 0
DISPLAY=:0 xset -dpms
DISPLAY=:0 xset s off
```

These commands require the same D-Bus environment as xfce4-session; running them
in an unrelated SSH session is insufficient. UPower/Power Manager provide the
battery icon; enable its tray display in Settings. Automatic idle suspend remains
off. A future DPMS-unblank fix must be verified before re-enabling DPMS.

## NetworkManager migration

Install the explicit rndis0-unmanaged rule first and preserve the static USB
address and SSH link route. Disable `zzz-wifi.start`, the old standalone
wpa_supplicant runlevel service, and any old `10-young2-wlan0-unmanaged.conf` rule.
The recorded latter rule was superseded by migration; a fresh setup should not
carry it. Enable NetworkManager with wlan0 managed and let it own its supplicant,
DHCP and DNS. Do not publish or reuse a saved connection from another phone.

Create a connection through nm-applet or, interactively:

```sh
nmcli --ask device wifi connect 'YOUR_SSID' name young2-internet ifname wlan0
nmcli connection modify young2-internet connection.autoconnect yes ipv4.route-metric 100
```

Adapt the existing RNDIS internet script to metric 500 and remove any stale
metric-0 default without removing `172.16.42.0/24 dev rndis0`. It must defer DNS
to NM rather than overwrite resolv.conf. This branch documents the measured
migration instead of automatically rewriting a working rescue script. Confirm
one NM-owned supplicant, no competing udhcpc, real WLAN HTTPS/DNS and preserved
USB SSH before reboot. [Wi-Fi notes](../docs/drivers/wifi.md) explain the traps.

Firmware files listed in the wireless driver documents must be obtained and
verified independently. The Bluetooth helper checks its exact HCD hash and
creates the `4343A0.hcd` alias. Run [blueman-menu.sh](../scripts/setup/blueman-menu.sh)
on the target if the Settings category override is desired.

## What remains manual

The build recipe and these files recover source-level integration, not the
complete phone: original boot ramdisk, firmware, compatible package set, saved
networks, some XFCE preferences and the latest tailored RNDIS script are outside
the repo. No new installation, reboot, suspend or physical test was performed
for this publication. Keep per-file backups and verify one subsystem at a time.
