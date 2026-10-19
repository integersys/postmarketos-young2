# Touchscreen and physical keys

The phone uses IST30xxB on I²C bus 1, address `0x50`, with input name
`ist30xx_ts_input`. The active config is `CONFIG_TOUCHSCREEN_IST30XXB=y`, with
`CONFIG_TOUCHSCREEN_IST30XX` unset. Relevant source is
`drivers/input/touchscreen/ist30xxb/ist30xxb.c`, its associated headers, and
`arch/arm/mach-sc/board-young2.c` for the keypad.

## Raw interface

The touchscreen advertises type-B MT slots 0–9, X 0–320, Y 0–480 and tracking IDs.
It has no `BTN_TOUCH` or single-touch ABS_X/ABS_Y. A nonnegative tracking ID starts
a contact and -1 ends it. X increases right; Y increases down. Physical corner
tests needed no inversion or axis swap. The width field can exceed its declared
maximum 15, so that declaration should not be used to clamp raw samples.

Input nodes were originally missing because there was no devtmpfs.
[97-input-nodes.start](../../userspace/input/97-input-nodes.start) discovers nodes
from sysfs and matches the raw touchscreen by name. Its symlink block must stay
before `exit 0`; an earlier version had unreachable symlink code.

## Xorg translation

[ts-xlate.py](../../userspace/input/ts-xlate.py) uses the Linux 3.10 legacy
write-`uinput_user_dev` plus `UI_DEV_CREATE` ABI, not the newer UI_DEV_SETUP API.
It synthesizes BTN_TOUCH and ABS_X/ABS_Y and creates
`/dev/input/touchscreen-xlate`, which the [evdev config](../../userspace/display/xorg-scanout.conf)
opens. The advertised Y maximum is 480 because the X screen is now 320×480.
Advertising 960 on that screen halves Y; advertising 480 on the old 960-high
screen doubled it. This was a logical geometry error, not physical calibration.

The preserved code uses native 32-bit ARM input structures. Do not run it as an
input decoder on a 64-bit host and expect the same event size: on the phone an
`input_event` is 16 bytes. The single-pointer interaction was physically tested;
two-finger gestures have not been established.

## Key policy

| Key | Raw device | Linux code | Current action |
|---|---|---:|---|
| Home | sci-keypad, recorded event0 | 102 | show desktop, keep applications open |
| Back | IST30xxB, recorded event1 | 158 | Alt+Left through XTEST |
| Recent | IST30xxB, recorded event1 | 254 | xfwm4 Alt+Tab |
| Volume up/down | sci-keypad | 115 / 114 | ALSA level and OSD |
| Power | sci-keypad | 116 | suspend/wake policy |

[young2-frontkeys.py](../../userspace/input/young2-frontkeys.py) reads the two raw
devices so the translator does not cause duplicate actions. Recent's Linux code
254 becomes X code 262 and is dropped by core X; raw handling avoids it. The
initial `xfce4-popup-windowmenu` approach required a missing panel plugin and was
replaced with Alt+Tab. Back navigation was demonstrated in NetSurf; other apps
must implement Alt+Left themselves. It is not a universal close action.

## Verification and limitations

I tested pointer tracking, application clicks, decorated-window dragging and
typing during the September GUI work. On October 9, all three front-key actions
were physically accepted, with reboot and suspend records showing one daemon.
See [audio](audio.md) and [power](power.md) for the separately verified keys.

The original policy daemons retain observed event0/event1/event3 paths. Verify
their sysfs names before installing on a differently enumerated system; the node
creation script itself discovers major/minor dynamically. Capacitive illumination
was not achieved. Kernel #10's KPLED writes warn; persist `light off` and do not
present the unflashed #11 revert as physically validated.
