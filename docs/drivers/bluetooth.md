# Bluetooth: BCM4343A0 over UART

The combo chip's Bluetooth function uses `/dev/ttyS0` with H4, RTS/CTS and
115200 baud for both initialization and operation. The working command is:

```sh
hciattach -n -t 60 -s 115200 /dev/ttyS0 bcm43xx 115200 flow nosleep
```

The process must stay alive: it owns the UART transport, not just firmware upload.
The vendor `bcm_bt_lpm_tty` discipline is separate from `n_hci` and cannot replace it.

## Kernel and firmware

`CONFIG_BT_HCIUART=y` and `CONFIG_BT_HCIUART_H4=y` supply `n_hci` discipline 15.
Source is `drivers/bluetooth/hci_ldisc.c`, `hci_h4.c`, `hci_uart.h` and their
Kconfig/Makefile. These options are in [config-xfce.armv7](../../linux-samsung-young23g/config-xfce.armv7).
No new transport implementation was required. Keep the proven Android USB gadget
configuration while enabling Bluetooth; an earlier generic USB Ethernet config
lost the expected rescue gadget.

The tested firmware is
`BCM4343A0_001.001.034.0038.0090_ORC_Vivalto-3G_3MC.hcd`, SHA256
`312c196f94eb0c04296a8b46626ba0e636228f4222d722e051383d2bc9af5d97`.
It is independently required in `/lib/firmware`; no blob is shipped here.
`/lib/firmware/4343A0.hcd` must resolve to it because hciattach selects a file from
the controller's ROM local name. After upload the measured name was
`BCM4343A0-26MHz Vivalto-3G 3M(SM-G313H)-0038`, revision 0x5a.

bluetoothd changes the local name. Reattaching without a power cycle can therefore
look for a firmware file named after BlueZ and silently continue unpatched.
The proven [boot script](../../userspace/bluetooth/zzz-bluetooth.start) checks the
firmware hash, cycles Bluetooth rfkill, starts one hciattach, waits for hci0,
brings it up, records firmware identity, then starts the packaged bluetooth service.
Its measured power cycle left the shared WLAN rail on and Wi-Fi associated.

## BlueZ and Blueman

The recorded userspace was BlueZ 5.87 and Blueman 2.4.6. The helper calls
`rc-service bluetooth start` after HCI is ready; do not separately enable an
early, competing transport startup. Blueman autostarts through the packaged XDG
entry. [The menu helper](../../scripts/setup/blueman-menu.sh) reproduces the
desktop-entry category override for XFCE Settings without copying vendor code.

## Verification and boundaries

On October 5 raw HCI, kernel management and BlueZ scans received real BLE devices;
Classic inquiry found discoverable phones. An external phone discovered the
Young 2, establishing RF transmission too. Two automatic reboots loaded patchram
and brought up hci0 with one hciattach and one bluetoothd. October 6 added the GUI.

Pairing/bond persistence, file transfer, HID and Bluetooth audio are not verified.
Linux 3.10 provides management API 1.3, so BlueZ reports unsupported optional
advertising/filter commands; basic discovery still worked. Blueman's missing
PulseAudioProfile plugin does not establish or disprove audio support.
The tested HCD embeds a generic controller address; unique address provisioning
is unresolved and its use for pairing has not been validated.
