# Hardware status

This table describes the last demonstrated development system through October 11,
2026, not a new retest or the old June download. Working means the stated behavior
was demonstrated. It does not mean every mode/profile is supported. See the
[verification records](development/verification.md) for the test boundaries.

| Function | Status | Demonstrated scope / limitation |
|---|---|---|
| Boot | Working | custom static-init ramdisk and p18 userspace. October source-built kernels ran |
| Framebuffer | Working | physical RGBX8888, 320×480, two pages, with metadata/scanout helpers required |
| Xorg | Working | fbdev, explicit VT and handover, without an accelerated graphics claim |
| XFCE | Working | physical desktop, menu, windows and keyboard, with small-screen limits |
| Touchscreen | Working | translated pointer, clicks and drags, with multitouch gestures untested |
| Home | Working | show desktop without closing apps |
| Back | Working | Alt+Left, tested navigation in NetSurf |
| Recent Apps | Working | xfwm4 Alt+Tab |
| Volume keys | Working | audible ALSA steps, true mute, OSD and held-key repeat |
| Capacitive illumination | Not working | actions work, but symbols did not illuminate |
| USB RNDIS | Working | SSH link kept beside Wi-Fi. Generic USB_ETH must stay off |
| SSH | Working | USB :2222, with Wi-Fi used during battery-only tests |
| Wi-Fi | Working | 2.4 GHz scan/WPA2/DHCP/DNS/HTTPS and NM reconnect |
| Bluetooth HCI | Working | patched controller, UART/H4, reboot persistence |
| Bluetooth scanning | Working | real Classic and BLE discovery, plus external TX observation |
| Bluetooth profiles | Not tested | pairing/bonding, HID, file transfer, audio unverified |
| Audio playback | Working | built-in speaker through ALSA hw:0,0 |
| Audio recording | Working | built-in microphone speech capture, with headset mic untested |
| Headphone/jack | Not tested | interfaces exist, physical hardware test absent |
| Battery | Working | percentage/state/voltage/temperature and XFCE icon, without a time estimate |
| Charging | Working | external-power/charging/full states, without a calibrated rate test |
| Suspend | Partial | real deep sleep tested without active USB gadget, with a USB wakelock limitation |
| Resume | Partial | same XFCE session survives tested cycles, but DPMS/stale scanout and later sync timeouts remain |
| Shutdown | Working | stays off on battery, but VBUS can restart offline charging |
| Reboot | Working | automatic desktop return, with delayed reboot after some display faults |
| Accelerometer | Working | K2HH live axes, physical orientation, reboot/resume |
| Automatic rotation | Not tested | not implemented |
| Camera | Experimental | SR352 control/stream activity/partial DMA, without a complete verified frame |
| Modem | Not tested | no demonstrated Linux modem integration |
| Calls | Not tested | no working call path demonstrated |
| SMS | Not tested | no working messaging path demonstrated |
| Mobile data | Not tested | no working cellular data path demonstrated |

Kernel #10 was last recorded running and contains the bad KPLED base experiment.
Kernel #11 was built with the revert, but not separately flashed. Neither is a
clean, fully validated release. The [published kernel recipe](building.md)
uses the demonstrated #8 display/transport baseline and keeps optional changes
separate. This publication did not build or flash it.
