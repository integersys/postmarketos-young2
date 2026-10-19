#!/usr/bin/env python3
"""fbvar.py - read and (optionally) rewrite the framebuffer colour metadata.

Queries the kernel directly with FBIOGET_VSCREENINFO / FBIOGET_FSCREENINFO, so it
reports what the DRIVER says, not what Xorg or fbset interpreted.

Struct layouts taken from the kernel headers used by this device:
    android_kernel_samsung_young23g/include/uapi/linux/fb.h
    FBIOGET_VSCREENINFO  = 0x4600
    FBIOPUT_VSCREENINFO  = 0x4601
    FBIOGET_FSCREENINFO  = 0x4602

fb_var_screeninfo is 160 bytes; fb_fix_screeninfo is 66 bytes (+2 padding = 68).

Usage:
    fbvar.py get                       # print var + fix metadata
    fbvar.py setbits ROFF RLEN GOFF GLEN BOFF BLEN [TOFF TLEN]
                                       # change ONLY the colour bitfields,
                                       # then read back and report
"""
import fcntl
import struct
import sys

FBIOGET_VSCREENINFO = 0x4600
FBIOPUT_VSCREENINFO = 0x4601
FBIOGET_FSCREENINFO = 0x4602

VAR_SIZE = 160
FIX_SIZE = 68

VAR_FMT = "<6I2I12I2I2II10II4I"
assert struct.calcsize(VAR_FMT) == VAR_SIZE, struct.calcsize(VAR_FMT)

FIX_FMT = "<16s5I3H2x4IH2H"
assert struct.calcsize(FIX_FMT) == 66, struct.calcsize(FIX_FMT)

VAR_FIELDS = ["xres", "yres", "xres_virtual", "yres_virtual", "xoffset", "yoffset",
              "bits_per_pixel", "grayscale",
              "red.offset", "red.length", "red.msb_right",
              "green.offset", "green.length", "green.msb_right",
              "blue.offset", "blue.length", "blue.msb_right",
              "transp.offset", "transp.length", "transp.msb_right",
              "nonstd", "activate", "height", "width", "accel_flags",
              "pixclock", "left_margin", "right_margin", "upper_margin",
              "lower_margin", "hsync_len", "vsync_len", "sync", "vmode",
              "rotate", "colorspace", "reserved0", "reserved1", "reserved2",
              "reserved3"]

FIX_FIELDS = ["id", "smem_start", "smem_len", "type", "type_aux", "visual",
              "xpanstep", "ypanstep", "ywrapstep", "line_length",
              "mmio_start", "mmio_len", "accel", "capabilities", "reserved"]

FB_TYPE = {0: "PACKED_PIXELS", 1: "PLANES", 2: "INTERLEAVED_PLANES",
           3: "TEXT", 4: "VGA_PLANES", 5: "FOURCC"}
FB_VISUAL = {0: "MONO01", 1: "MONO10", 2: "TRUECOLOR", 3: "PSEUDOCOLOR",
             4: "DIRECTCOLOR", 5: "STATIC_PSEUDOCOLOR", 6: "FOURCC"}


def ioctl_read(fd, request, size):
    buf = bytearray(size)
    fcntl.ioctl(fd, request, buf, True)
    return bytes(buf)


def get_var(fd):
    return ioctl_read(fd, FBIOGET_VSCREENINFO, VAR_SIZE)


def get_fix(fd):
    return ioctl_read(fd, FBIOGET_FSCREENINFO, FIX_SIZE)


def show_var(raw):
    v = struct.unpack(VAR_FMT, raw)
    print("  -- fb_var_screeninfo --")
    for name, val in zip(VAR_FIELDS, v):
        if name.startswith("reserved"):
            continue
        print("    %-18s %s" % (name, val))
    print("    %-18s %d,%d,%d" % ("RED  (off,len,msb)", v[8], v[9], v[10]))
    print("    %-18s %d,%d,%d" % ("GREEN(off,len,msb)", v[11], v[12], v[13]))
    print("    %-18s %d,%d,%d" % ("BLUE (off,len,msb)", v[14], v[15], v[16]))
    print("    %-18s %d,%d,%d" % ("TRANSP(off,len,msb)", v[17], v[18], v[19]))
    print("    %-18s %s" % ("=> fbset rgba", "rgba %d/%d,%d/%d,%d/%d,%d/%d"
                           % (v[9], v[8], v[12], v[11], v[15], v[14], v[18], v[17])))
    return v


def show_fix(raw):
    f = struct.unpack(FIX_FMT, raw[:66])
    print("  -- fb_fix_screeninfo --")
    print("    %-18s %r" % ("id", f[0].split(b"\0")[0].decode(errors="replace")))
    for name, val in zip(FIX_FIELDS[1:], f[1:]):
        print("    %-18s %s" % (name, val))
    print("    %-18s %s" % ("type(decoded)", FB_TYPE.get(f[3], f[3])))
    print("    %-18s %s" % ("visual(decoded)", FB_VISUAL.get(f[5], f[5])))
    print("    %-18s %s" % ("=> expected bytes/line",
                           "xres*bpp/8 = %d" % (struct.unpack(VAR_FMT, get_var(FD_CACHE[0]))[0] * 4)
                           if FD_CACHE else "?"))
    return f


def describe_bitfields(v):
    """Translate the bitfields into the byte layout a little-endian CPU produces."""
    out = []
    for name, base in (("R", 8), ("G", 11), ("B", 14), ("T", 17)):
        off, ln = v[base], v[base + 1]
        if ln == 0:
            out.append("%s: length=0 (absent)" % name)
            continue
        lo_byte = off // 8
        out.append("%s: offset=%d length=%d -> bits %d..%d -> byte %d"
                   % (name, off, ln, off, off + ln - 1, lo_byte))
    return out


FD_CACHE = []


def main():
    path = "/dev/fb0"
    mode = sys.argv[1] if len(sys.argv) > 1 else "get"
    fd = open(path, "r+b", buffering=0)
    FD_CACHE.append(fd)

    if mode == "get":
        print("device: %s" % path)
        show_var(get_var(fd))
        print()
        show_fix(get_fix(fd))
        print()
        v = struct.unpack(VAR_FMT, get_var(fd))
        print("  -- byte layout implied by the metadata (little-endian) --")
        for line in describe_bitfields(v):
            print("    " + line)
        print()
        print("  -- physical layout already PROVEN for this panel --")
        print("    R: bits 0..7   -> byte 0")
        print("    G: bits 8..15  -> byte 1")
        print("    B: bits 16..23 -> byte 2")
        print("    4th byte unused (00)")
        return 0

    if mode == "setbits":
        if len(sys.argv) < 8:
            print("usage: fbvar.py setbits ROFF RLEN GOFF GLEN BOFF BLEN [TOFF TLEN]")
            return 2
        a = [int(x) for x in sys.argv[2:]]
        ro, rl, go, gl, bo, bl = a[:6]
        to, tl = (a[6], a[7]) if len(a) >= 8 else (24, 0)

        raw = get_var(fd)
        before = struct.unpack(VAR_FMT, raw)
        print("BEFORE:")
        show_var(raw)

        new = list(before)
        new[8], new[9], new[10] = ro, rl, 0
        new[11], new[12], new[13] = go, gl, 0
        new[14], new[15], new[16] = bo, bl, 0
        new[17], new[18], new[19] = to, tl, 0
        # keep everything else identical: resolution, bpp, timing, offsets
        buf = bytearray(struct.pack(VAR_FMT, *new))
        print()
        print("attempting FBIOPUT_VSCREENINFO with red=%d/%d green=%d/%d blue=%d/%d transp=%d/%d"
              % (ro, rl, go, gl, bo, bl, to, tl))
        try:
            fcntl.ioctl(fd, FBIOPUT_VSCREENINFO, buf, True)
            print("  ioctl returned OK")
        except OSError as exc:
            print("  ioctl FAILED: %s" % exc)
            return 1

        raw2 = get_var(fd)
        after = struct.unpack(VAR_FMT, raw2)
        print()
        print("AFTER (read back from the kernel):")
        show_var(raw2)
        print()
        accepted = (after[8], after[9]) == (ro, rl) and \
                   (after[11], after[12]) == (go, gl) and \
                   (after[14], after[15]) == (bo, bl)
        print("bitfields %s" % ("ACCEPTED AND PERSISTED" if accepted
                                else "REJECTED OR REWRITTEN BY THE KERNEL"))
        for i, nm in ((8, "red"), (11, "green"), (14, "blue"), (17, "transp")):
            print("   %-7s requested %d/%d   got %d/%d"
                  % (nm, (ro, rl, go, gl, bo, bl, to, tl)[(i - 8) // 3 * 2],
                     (ro, rl, go, gl, bo, bl, to, tl)[(i - 8) // 3 * 2 + 1],
                     after[i], after[i + 1]))
        # did anything else change?
        for idx, name in enumerate(VAR_FIELDS):
            if name.startswith("reserved"):
                continue
            if before[idx] != after[idx]:
                print("   !! %s changed: %s -> %s" % (name, before[idx], after[idx]))
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
