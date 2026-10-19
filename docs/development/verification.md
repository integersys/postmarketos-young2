# Verification records and source provenance

I use physical observations for display/touch/audio claims and protocol or
connectivity tests for the corresponding interfaces. Probe success, process
startup and image generation are separate from working hardware.

The development records remain in my local archive. This compact index records
their identifiers and acceptance scope without publishing raw logs or private
state. They are not GitHub links or files required at runtime.

| Record | Accepted evidence |
|---|---|
| 2026-09-18_23-27_persistent-framebuffer-rgb-metadata | fresh reboot, ioctl readback, five physical colours |
| 2026-09-19_00-07_xorg-physical-scanout-handover | controlled pan/unblank matrix and physical LCD |
| 2026-09-19_14-42_xorg-touchscreen-input | raw events versus X pointer/press/release |
| 2026-09-20_21-53_first-interactive-x-application | physical xmessage click and repeat |
| 2026-09-20_22-18_fix-touchscreen-symlink-persistence | name-based symlink after fresh reboot |
| 2026-09-20_22-36_first-window-manager-session | decorated Openbox window dragged by touch |
| 2026-09-20_23-14_xorg-logical-320x480-desktop | X=320×480, fb=320×960, pointer reaches panel edges |
| 2026-09-22_20-09_first-manual-xfce-session | physical XFCE/terminal/keyboard and typing |
| 2026-09-23_17-55_fix-xfce-applications-menu | syscall trace, menu launch by touch, clean repeat |
| 2026-09-23_19-31_automatic-xfce-boot | two automatic reboots, menu/typing, failure leaves SSH |
| 2026-09-23_21-40_xfce-window-bounds | physical drags, fresh apps, decorated frame/workarea audit, reboot |
| audio/2026-10-03_13-49_audio-bringup | repeated audible speaker, speech recording and reboot routes |
| wifi/2026-10-03_16-05_wifi-bringup | route-proven WLAN DNS/HTTPS, DHCP and reboot |
| bluetooth/2026-10-05_runtime-radio-discovery | real Classic/BLE RX and external discovery of phone TX |
| bluetooth/2026-10-05_bluetooth-persistence | two reboots with patch identity and one transport/daemon |
| gui/2026-10-06_xfce-connectivity-gui | two reboots, NM ownership, network connectivity and applets |
| power/2026-10-06_power-management FINAL_REPORT | repeated real deep sleep, session preservation, GUI shutdown/reboot |
| sensors/2026-10-07_sensors | physical poses, changing samples, three sleeps and two reboots |
| audio/2026-10-07_volume-buttons | audible changes/true mute, OSD, held keys, sleep/reboot |
| input/2026-10-07_front-buttons final October 9 sections | physical Home/Back/Recent, sleep/reboot; failed illumination |
| camera/2026-10-11_camera session 2 | source/HAL geometry analysis; no live test of revised tool |

Within a task, later corrections take precedence over early summaries. In
particular, the front-key file's early claim that the analog base needed changing
was disproven in its later register analysis. The power FINAL_REPORT supersedes
its earlier deep-sleep-blocked summary. Camera session 2 supersedes the first
interpretation of the PLL tables as resolution modes.

## Published source

The Python power/front-key/volume helpers match the recorded final source
revisions (before line-ending normalization). The touch translator is the
320×480 revision, SHA256
`907ec1632f6a53fdca2bb9d3913cae7957fe616e5b26765cbb11d392cda66099`.
GUI startup and keyboard placement come from the preserved boot stack; bounds
handling comes from the final September 24 result. NetworkManager protection and
Blueman category setup reproduce the measured configuration without saved secrets.

The kernel compatibility patch is the source-only difference between upstream
`e05a1c16fb7334378bb12d8116d0def2ef83ff0d` and prepared tree
`c8d61376344158f6bea5426e56bcf25e26baa419`, excluding generated configuration and
build artifacts. The resume patch is the measured subsequent sprdfb source diff.
The copied current .config is byte-identical to `suspendfix.config.after`.
The optional KPLED patch represents #11's source state and is not automatically
applied. Compiler compatibility work includes the existing pmaports GCC7/GCC8/
dtc/GNU89/ARM section fixes; existing source copyright notices remain in context.

## Publication checks versus hardware tests

This refresh checks script syntax, configuration, local links, patch application,
source selection, staged contents and README identity. It does not rebuild the
kernel, install packages, modify the phone, or repeat physical tests. One bounded
SSH inspection timed out. Current live state is therefore UNKNOWN; the hardware
table describes the last recorded demonstrated state.
