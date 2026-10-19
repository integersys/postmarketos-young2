#!/usr/bin/env python3
"""ts-xlate.py - touchscreen type-B -> standard X touchscreen translator (uinput).

WHY THIS EXISTS
    The Samsung Galaxy Young 2 touchscreen (ist30xx_ts_input) is a type-B
    multitouch device that does NOT report BTN_TOUCH, and the original 2016
    kernel had no udev daemon running (CONFIG_DEVTMPFS unset -> eudev refused).

    Consequences measured on this device (2026-09-19):
      * xf86-input-libinput needs the udev daemon to initialise a device even
        when given an explicit path -> "udev device never initialized" -> FAILS.
      * xf86-input-evdev, given the real device with no BTN_TOUCH, falls back to
        MOUSE mode and logs "ignoring absolute axes" -> it never reports a real
        touch contact (no press/release) -> FAILS for a touchscreen.

    This translator reads the raw type-B MT events from the real node and writes
    a SYNTHESISED virtual device via /dev/uinput that:
      - has BTN_TOUCH (synthesised from ABS_MT_TRACKING_ID)
      - has ABS_X / ABS_Y (0..320 / 0..480) and full ABS_MT_* axes
      - carries INPUT_PROP_DIRECT so evdev classifies it as a touchscreen
      - passes KEY_BACK (158) and KEY_RECENT (254) straight through
    evdev then attaches it as a real touchscreen with correct absolute
    coordinates and press/release.

NOTE ON THE LEGACY uinput ABI
    UI_DEV_SETUP / UI_GET_VERSION were added in Linux 3.17. This kernel is
    3.10.17, so we use the legacy write()-the-struct + UI_SET_* + UI_DEV_CREATE
    interface (same as input_probe.py's uinput round-trip test, which passed).

NODE HANDLING
    A uinput-created device gets NO /dev/input/eventN node automatically (same
    devtmpfs reason as everything else here). This translator finds its own
    /sys/class/input entry, reads the major:minor, and creates
    /dev/input/touchscreen-xlate. Xorg's InputDevice points at that path.

USAGE
    ts-xlate.py [source-device]
        source-device defaults to /dev/input/touchscreen (the real node, which
        the boot script symlinks to the ist30xx event node).
    Runs until killed. On exit it destroys the uinput device and removes the node.
"""

import fcntl
import glob
import os
import select
import signal
import struct
import sys
import time

# ---- ABI constants (same scheme as input_probe.py) -------------------------
def ioc(direction, type_, nr, size):
    return (direction << 30) | (size << 16) | (type_ << 8) | nr

UI_SET_EVBIT   = ioc(1, ord("U"), 100, 4)
UI_SET_KEYBIT  = ioc(1, ord("U"), 101, 4)
UI_SET_ABSBIT  = ioc(1, ord("U"), 103, 4)
UI_SET_PROPBIT = ioc(1, ord("U"), 110, 4)
UI_DEV_CREATE  = ioc(0, ord("U"), 1, 0)
UI_DEV_DESTROY = ioc(0, ord("U"), 2, 0)

UINPUT_MAX_NAME_SIZE = 80
ABS_CNT = 64

# evdev event type / code names we care about
EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
SYN_REPORT = 0
BTN_TOUCH = 0x14A
KEY_BACK = 158
KEY_RECENT = 254

ABS_X = 0x00
ABS_Y = 0x01
ABS_MT_SLOT = 0x2F
ABS_MT_TOUCH_MAJOR = 0x30
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36
ABS_MT_TRACKING_ID = 0x39

INPUT_PROP_DIRECT = 1

UINPUT_NAME = "young2-ts-xlate"
SRC_DEFAULT = "/dev/input/touchscreen"      # real ist30xx (boot script symlink)
DST_NODE = "/dev/input/touchscreen-xlate"   # what Xorg opens

EVENT_FMT = "<llHHi"   # timeval(2x32) + type(16) + code(16) + value(32) = 16 bytes
assert struct.calcsize(EVENT_FMT) == 16


def ioctl(fd, request, arg):
    fcntl.ioctl(fd, request, arg)


def build_uinput_struct():
    dev = bytearray(UINPUT_MAX_NAME_SIZE + 8 + 4 + 4 * ABS_CNT * 4)
    struct.pack_into("%ds" % UINPUT_MAX_NAME_SIZE, dev, 0, UINPUT_NAME.encode())
    # id: bustype(BUS_VIRTUAL=0x06), vendor, product, version
    struct.pack_into("HHHH", dev, UINPUT_MAX_NAME_SIZE, 0x06, 0x1337, 0x0002, 0x0100)
    base = UINPUT_MAX_NAME_SIZE + 8 + 4
    absmin = [0] * ABS_CNT
    absmax = [0] * ABS_CNT
    absfuzz = [0] * ABS_CNT
    absflat = [0] * ABS_CNT
    spans = {
        ABS_X: (0, 320),
        # X's LOGICAL screen is now 320x480 (start-x-with-handover switches the
        # fbdev output to its built-in 320x480 mode), even though the kernel
        # framebuffer stays 320x960 virtual. This ancient xf86-input-evdev
        # (0.5.0) has no CoordinateTransformationMatrix and maps the device axis
        # range LINEARLY onto the screen, so the advertised Y range must equal the
        # SCREEN height: advertise 0..480 and emit the true physical Y (0..480)
        # -> screen_y = phys_y. (With a 320x960 screen it had to be 0..960; the
        # range tracks the X screen, NOT the framebuffer.)
        ABS_Y: (0, 480),
        ABS_MT_SLOT: (0, 9),
        ABS_MT_TRACKING_ID: (0, 65535),
        ABS_MT_POSITION_X: (0, 320),
        ABS_MT_POSITION_Y: (0, 480),
        ABS_MT_TOUCH_MAJOR: (0, 63),  # hardware 6-bit field, observed 10..63
    }
    for a, (lo, hi) in spans.items():
        absmin[a] = lo
        absmax[a] = hi
    struct.pack_into("%di" % ABS_CNT, dev, base, *absmax)
    struct.pack_into("%di" % ABS_CNT, dev, base + 256, *absmin)
    struct.pack_into("%di" % ABS_CNT, dev, base + 512, *absfuzz)
    struct.pack_into("%di" % ABS_CNT, dev, base + 768, *absflat)
    return dev


def create_uinput_device():
    ufd = os.open("/dev/uinput", os.O_RDWR | os.O_NONBLOCK)
    dev = build_uinput_struct()
    os.write(ufd, dev)
    ioctl(ufd, UI_SET_EVBIT, EV_KEY)
    ioctl(ufd, UI_SET_EVBIT, EV_ABS)
    for k in (BTN_TOUCH, KEY_BACK, KEY_RECENT):
        ioctl(ufd, UI_SET_KEYBIT, k)
    for a in (ABS_X, ABS_Y, ABS_MT_SLOT, ABS_MT_TRACKING_ID,
              ABS_MT_POSITION_X, ABS_MT_POSITION_Y, ABS_MT_TOUCH_MAJOR):
        ioctl(ufd, UI_SET_ABSBIT, a)
    ioctl(ufd, UI_SET_PROPBIT, INPUT_PROP_DIRECT)
    ioctl(ufd, UI_DEV_CREATE, 0)
    return ufd


def find_and_create_node():
    # The uinput device appears under /sys/class/input with our name.
    for d in sorted(glob.glob("/sys/class/input/input*")):
        try:
            nm = open(d + "/name").read().strip()
        except OSError:
            continue
        if nm != UINPUT_NAME:
            continue
        events = sorted(glob.glob(d + "/event*"))
        if not events:
            continue
        ev = events[0]
        maj, min_ = open(ev + "/dev").read().strip().split(":")
        maj, min_ = int(maj), int(min_)
        node = DST_NODE
        if os.path.lexists(node):
            try:
                os.remove(node)
            except OSError:
                pass
        os.mknod(node, 0o666 | 0o020000, os.makedev(maj, min_))
        os.chmod(node, 0o666)
        return node, maj, min_
    raise RuntimeError("uinput device %s not found in /sys/class/input" % UINPUT_NAME)


class Translator:
    def __init__(self, src, ufd, node):
        self.src = src
        self.ufd = ufd
        self.node = node
        self.slot = 0
        self.x = 160
        self.y = 240
        self.active = False
        self.fd = os.open(src, os.O_RDONLY | os.O_NONBLOCK)

    def w(self, typ, code, val):
        # self.ufd is an integer fd (os.open), so use os.write, not .write()
        os.write(self.ufd, struct.pack(EVENT_FMT, 0, 0, typ, code, val))

    def translate(self, typ, code, val):
        if typ == EV_ABS:
            if code == ABS_MT_SLOT:
                self.slot = val
            elif code == ABS_MT_TRACKING_ID:
                if val >= 0:
                    self.active = True
                    self.w(EV_KEY, BTN_TOUCH, 1)
                    self.w(EV_ABS, ABS_X, self.x)
                    self.w(EV_ABS, ABS_Y, self.y)
                    self.w(EV_ABS, ABS_MT_SLOT, 0)
                    self.w(EV_ABS, ABS_MT_TRACKING_ID, val)
                    self.w(EV_ABS, ABS_MT_POSITION_X, self.x)
                    self.w(EV_ABS, ABS_MT_POSITION_Y, self.y)
                else:
                    self.active = False
                    self.w(EV_ABS, ABS_MT_SLOT, 0)
                    self.w(EV_ABS, ABS_MT_TRACKING_ID, -1)
                    self.w(EV_KEY, BTN_TOUCH, 0)
            elif code == ABS_MT_POSITION_X:
                self.x = val
                if self.active:
                    self.w(EV_ABS, ABS_X, val)
                    self.w(EV_ABS, ABS_MT_POSITION_X, val)
            elif code == ABS_MT_POSITION_Y:
                self.y = val
                if self.active:
                    self.w(EV_ABS, ABS_Y, val)
                    self.w(EV_ABS, ABS_MT_POSITION_Y, val)
            elif code == ABS_MT_TOUCH_MAJOR:
                self.w(EV_ABS, ABS_MT_TOUCH_MAJOR, val)
            # any other ABS on the real device is ignored (we only need X/Y)
        elif typ == EV_KEY:
            # pass KEY_BACK / KEY_RECENT (and anything else) through
            self.w(EV_KEY, code, val)
        elif typ == EV_SYN and code == SYN_REPORT:
            self.w(EV_SYN, SYN_REPORT, 0)

    def run(self):
        fmt = EVENT_FMT
        while True:
            r, _, _ = select.select([self.fd], [], [], 0.5)
            if not r:
                continue
            try:
                data = os.read(self.fd, 16 * 256)
            except OSError as e:
                # source device disappeared; stop cleanly
                print("source read error: %s" % e, file=sys.stderr)
                break
            for off in range(0, len(data) - 15, 16):
                sec, usec, typ, code, val = struct.unpack_from(fmt, data, off)
                try:
                    self.translate(typ, code, val)
                except Exception as e:
                    # never let one malformed event kill the translator
                    print("translate error (ignored): %s" % e, file=sys.stderr)


def _live_translator_node():
    """Return True if a uinput device with our name is currently live in sysfs
    (i.e. a translator process is actually running and owning it)."""
    for d in glob.glob("/sys/class/input/input*"):
        try:
            nm = open(d + "/name").read().strip()
        except OSError:
            continue
        if nm == UINPUT_NAME:
            return True
    return False


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SRC_DEFAULT
    if os.path.exists(DST_NODE) and _live_translator_node():
        # a translator is genuinely running and owning the device; exit.
        print("translator already running (live %s); exiting" % DST_NODE)
        return 0
    if os.path.exists(DST_NODE) and not _live_translator_node():
        # stale node (e.g. held open by a previous Xorg) - clear it so we can
        # recreate a fresh device.
        try:
            os.remove(DST_NODE)
        except OSError:
            pass
    if not os.path.exists(src):
        print("ERROR: source device %s missing" % src, file=sys.stderr)
        return 1

    ufd = create_uinput_device()
    # give the kernel a moment to register the input device
    node = None
    for _ in range(50):
        try:
            node, maj, min_ = find_and_create_node()
            break
        except RuntimeError:
            time.sleep(0.1)
    if node is None:
        print("ERROR: could not locate/register uinput node", file=sys.stderr)
        ioctl(ufd, UI_DEV_DESTROY)
        return 1
    print("translator ready: %s -> %s (13:%d) via uinput" % (src, node, min_))

    tr = Translator(src, ufd, node)

    def cleanup(signum, frame):
        try:
            ioctl(ufd, UI_DEV_DESTROY, 0)
        except OSError:
            pass
        try:
            if os.path.lexists(DST_NODE):
                os.remove(DST_NODE)
        except OSError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    tr.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
