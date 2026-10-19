# Hardware status

This table describes the last demonstrated development system through October 11,
2026, not a new retest or the old June download. Working means the stated behavior
was demonstrated; it does not mean every mode/profile is supported. See the
[verification records](development/verification.md) for the test boundaries.

| Function | Status | Demonstrated scope / limitation |
|---|---|---|
| Boot | Working | custom static-init ramdisk, p18 userspace; October source-built kernels ran |
| Framebuffer | Working | physical RGBX8888, 320×480, two pages; metadata/scanout helpers required |
| Xorg | Working | fbdev, explicit VT, handover; no accelerated graphics claim |
| XFCE | Working | physical desktop, menu, windows, keyboard; small-screen limits |
| Touchscreen | Working | translated pointer, clicks and drags; multitouch gestures untested |
| Home | Working | show desktop without closing apps |
| Back | Working | Alt+Left, tested navigation in NetSurf |
| Recent Apps | Working | xfwm4 Alt+Tab |
| Volume keys | Working | audible ALSA steps, true mute, OSD and held-key repeat |
| Capacitive illumination | Not working | actions work; symbols did not illuminate |
| USB RNDIS | Working | SSH link kept beside Wi-Fi; generic USB_ETH must stay off |
| SSH | Working | USB :2222; Wi-Fi used during battery-only tests |
| Wi-Fi | Working | 2.4 GHz scan/WPA2/DHCP/DNS/HTTPS; NM reconnect |
| Bluetooth HCI | Working | patched controller, UART/H4, reboot persistence |
| Bluetooth scanning | Working | real Classic and BLE discovery; external TX observation |
| Bluetooth profiles | Not tested | pairing/bonding, HID, file transfer, audio unverified |
| Audio playback | Working | built-in speaker through ALSA hw:0,0 |
| Audio recording | Working | built-in microphone speech capture; headset mic untested |
| Headphone/jack | Not tested | interfaces exist, physical hardware test absent |
| Battery | Working | percentage/state/voltage/temperature, XFCE icon; no time estimate |
| Charging | Working | external-power/charging/full states; no calibrated rate test |
| Suspend | Partial | real deep sleep tested without active USB gadget; USB wakelock limitation |
| Resume | Partial | same XFCE session survives tested cycles; DPMS/stale scanout and later sync timeouts remain |
| Shutdown | Working | stays off on battery; VBUS can restart offline charging |
| Reboot | Working | automatic desktop return; delayed reboot after some display faults |
| Accelerometer | Working | K2HH live axes, physical orientation, reboot/resume |
| Automatic rotation | Not tested | not implemented |
| Camera | Experimental | SR352 control/stream activity/partial DMA; no complete verified frame |
| Modem | Not tested | no demonstrated Linux modem integration |
| Calls | Not tested | no working call path demonstrated |
| SMS | Not tested | no working messaging path demonstrated |
| Mobile data | Not tested | no working cellular data path demonstrated |

Kernel #10 was last recorded running and contains the bad KPLED base experiment.
Kernel #11 was built with the revert, but not separately flashed. Neither is a
clean, fully validated release. The [published kernel recipe](building.md)
uses the demonstrated #8 display/transport baseline and keeps optional changes
separate; this publication did not build or flash it.
