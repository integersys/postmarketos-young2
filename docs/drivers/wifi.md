# Wi-Fi: Broadcom bcmdhd

I brought up the internal BCM43430 Wi-Fi function over SDIO (`02d0:a9a6`) using
the built-in downstream `bcmdhd`/`bcmsdh_sdmmc` driver (DHD 1.141.64).
Relevant source is `drivers/net/wireless/bcmdhd/` and the young2 board support.
The exposed interface is `wlan0`, with `p2p0` also registered.

## Firmware and initial bring-up

The driver requests `/system/etc/wifi/bcmdhd_sta.bin` and
`/system/etc/wifi/nvram_net.txt`. Both must be independently obtained for this
board; they are not redistributed here. The tested station firmware was 335650
bytes, version 7.10.226.54, FWID 01-16179e91, SHA256
`007c471ad172eb0f3520de07fd032f27876207bdab47cf9b1ef93a78d8073bdd`.
The tested board NVRAM was 1178 bytes, SHA256
`5cba1912da497a7ddfb85fb880ab9c1e05af6188d41a1991d5384c77319a9cbe`.
Do not substitute factory calibration or another board's NVRAM.

Probe initially failed before the rootfs was mounted. Bringing wlan0 up after
the firmware files were available let `dhd_open()` load them. A boot-time
`bus is down` message alone did not mean the later userspace bring-up failed.
cfg80211/nl80211 tools (`iw`) worked; Wireless Extensions scanning did not.
[52-rfkill-node.start](../../userspace/wifi/52-rfkill-node.start) creates the misc
rfkill node from `/proc/misc` for userspace tools. The measured radio was already
unblocked. Do not unbind/rebind `bcmdhd_wlan`: that previously crashed the phone.

I first used wpa_supplicant plus udhcpc and a custom boot worker. On October 6 I
replaced that ownership with NetworkManager; the old worker is deliberately
not published as the active setup.

## Current ownership and XFCE

NetworkManager owns wlan0, its supplicant, internal DHCP, DNS and reconnect.
`network-manager-applet` provides nm-applet and nm-connection-editor; packaged
XDG autostart puts one applet in the existing XFCE status tray.

[20-young2-rescue-unmanaged.conf](../../userspace/wifi/20-young2-rescue-unmanaged.conf)
keeps rndis0 outside NetworkManager. Wi-Fi default metric is 100 and RNDIS
internet fallback metric 500. The SSH route `172.16.42.0/24 dev rndis0` is separate
and must stay. Remove a stale metric-0 RNDIS default explicitly: adding a
metric-500 default does not replace it. RNDIS startup must not overwrite NM's DNS.

Disable the old `zzz-wifi.start` worker, the separate wpa_supplicant default
runlevel service and any old wlan0-unmanaged rule when migrating. Two owners
caused failed association during testing. Use nm-applet or `nmcli --ask` to save
your own network; no connection keyfile, SSID, PSK or credential is included here.
See [installation mapping](../../userspace/INSTALL.md).

## Demonstrated behavior

October 3 tests established scanning, WPA2 association, DHCP, DNS and HTTPS with
`ip route get` proving traffic used wlan0 while RNDIS SSH remained available.
A 20 MB transfer measured about 2.8 MB/s; this is one recorded test, not a general
benchmark. Reboot persistence was demonstrated first with the worker and then
twice with NetworkManager on October 6. Later power tests kept the connection.

Only 2.4 GHz is exposed; no 5 GHz band is present. AP mode, P2P and broader
security-mode coverage are untested. Windows ICS internet fallback was not
revalidated during the NetworkManager migration; USB SSH was. Firmware and a
locally provisioned network remain prerequisites for reproduction.
