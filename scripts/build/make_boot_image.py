#!/usr/bin/env python3
"""
make_boot_image.py — package a bounded candidate boot-image file.

Layout constraints from the measured p11 backup:
  * the ramdisk is taken from the ORIGINAL p11 backup as RAW BYTES and must stay
    byte-identical (sha256 e65decde4922679644ee83ebe7c7fc2495a71bd17769aeb41594fa7007a79643)
  * every header field except kernel_size is copied from the original
  * the output is limited to the first 0x384000 bytes of p11 (= bootsize).
    It is NEVER a whole-8-MiB image, so the protected opaque blob at 0x384000 is never
    produced, never overwritten, and never recommended.

Usage:
  make_boot_image.py <original-p11.img> <new-kernel.zImage> <outdir>
"""
import hashlib
import os
import struct
import sys

MAGIC = b"ANDROID!"
BOOTSIZE = 0x384000                 # 3,686,400
EXPECT_RAMDISK = "e65decde4922679644ee83ebe7c7fc2495a71bd17769aeb41594fa7007a79643"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def ceil_page(n, page):
    return (n + page - 1) // page * page


def main(orig_path, kernel_path, outdir):
    from pathlib import Path
    original = Path(orig_path)
    kernel = Path(kernel_path)
    output = Path(outdir)
    if not original.is_file() or not kernel.is_file():
        sys.exit("ERROR: inputs must be regular files")
    if output.exists():
        sys.exit("ERROR: output directory must not already exist")
    orig = original.read_bytes()

    if len(orig) < 2048 or orig[:8] != MAGIC:
        sys.exit("ERROR: original is not an Android boot image")

    (k_size, k_addr, r_size, r_addr,
     s_size, s_addr, tags, page) = struct.unpack("<8I", orig[8:40])
    dt_size = struct.unpack("<I", orig[40:44])[0]
    if (page, k_addr, r_addr, s_addr, tags, s_size, dt_size) != (
            2048, 0x8000, 0x1000000, 0xf00000, 0x100, 0, 0):
        sys.exit("ERROR: unexpected boot geometry or unsupported second/DTB data")
    if page + ceil_page(k_size, page) + ceil_page(r_size, page) > min(len(orig), BOOTSIZE):
        sys.exit("ERROR: truncated or oversized original boot image")
    name = orig[48:64]
    cmdline = orig[64:64 + 512]

    print("=== ORIGINAL p11 BOOT IMAGE ===")
    print("  file            :", orig_path)
    print("  size            :", len(orig))
    print("  sha256          :", sha256(orig))
    print("  page_size       :", page)
    print("  kernel_size     :", k_size)
    print("  ramdisk_size    :", r_size)
    print("  kernel_addr     : 0x%X" % k_addr)
    print("  ramdisk_addr    : 0x%X" % r_addr)
    print("  second_addr     : 0x%X" % s_addr)
    print("  tags_addr       : 0x%X" % tags)
    print("  dt_size         :", dt_size)
    print("  cmdline         :", cmdline.split(b"\0")[0].decode())

    # --- original ramdisk, taken as raw bytes ---
    r_off = page * (1 + ceil_page(k_size, page) // page)
    r_blob = orig[r_off:r_off + r_size]
    got_r = sha256(r_blob)
    print()
    print("=== ORIGINAL RAMDISK ===")
    print("  length          :", len(r_blob))
    print("  sha256          :", got_r)
    if got_r != EXPECT_RAMDISK:
        sys.exit("ERROR: original ramdisk hash %s != expected %s" % (got_r, EXPECT_RAMDISK))
    print("  MATCHES the verified pmos-static-v3 ramdisk  OK")

    # --- new kernel ---
    k_blob = kernel.read_bytes()
    print()
    print("=== NEW KERNEL ===")
    print("  file            :", kernel_path)
    print("  size            :", len(k_blob))
    print("  sha256          :", sha256(k_blob))
    print("  delta vs original: %+d bytes" % (len(k_blob) - k_size))

    # --- rebuild header, changing ONLY kernel_size ---
    head = bytearray(orig[:page])
    struct.pack_into("<I", head, 8, len(k_blob))
    assert len(head) == page

    # --- assemble the boot image (header + kernel + ramdisk, page padded) ---
    img = bytearray()
    img += head
    img += k_blob
    img += b"\0" * (ceil_page(len(k_blob), page) - len(k_blob))
    img += r_blob
    img += b"\0" * (ceil_page(len(r_blob), page) - len(r_blob))

    if not k_blob or len(img) > BOOTSIZE:
        sys.exit("ERROR: empty kernel or candidate exceeds protected boot boundary")
    output.mkdir(parents=True, exist_ok=False)
    bootimg_path = os.path.join(outdir, "candidate-boot.img")
    Path(bootimg_path).write_bytes(bytes(img))
    print()
    print("=== CANDIDATE BOOT IMAGE (unpadded) ===")
    print("  file            :", bootimg_path)
    print("  size            :", len(img))

    # --- the flashable artefact: pad to bootsize, NEVER to the partition ---
    if len(img) > BOOTSIZE:
        sys.exit("ERROR: boot image %d > bootsize %d - would collide with the protected opaque blob"
                 % (len(img), BOOTSIZE))
    limited = bytes(img) + b"\0" * (BOOTSIZE - len(img))
    assert len(limited) == BOOTSIZE

    lim_path = os.path.join(outdir, "candidate-p11-first-0x384000.bin")
    Path(lim_path).write_bytes(limited)
    print()
    print("=== FLASHABLE ARTEFACT (first 0x384000 of p11) ===")
    print("  file            :", lim_path)
    print("  size            :", len(limited), "(0x%X)" % len(limited))
    print("  sha256          :", sha256(limited))
    print("  headroom in p11 :", 8388608 - len(limited), "bytes remain untouched")

    # --- verification: re-extract from the artefact and re-hash ---
    print()
    print("=== VERIFICATION (re-extracted from the artefact itself) ===")
    v = Path(lim_path).read_bytes()
    (vk, vka, vr, vra, vs, vsa, vt, vp) = struct.unpack("<8I", v[8:40])
    ok = True

    def chk(label, cond, extra=""):
        nonlocal ok
        print(("  OK   " if cond else "  FAIL ") + label + (" " + extra if extra else ""))
        if not cond:
            ok = False

    chk("page_size unchanged", vp == page, "%d" % vp)
    chk("kernel_addr unchanged", vka == k_addr, "0x%X" % vka)
    chk("ramdisk_addr unchanged", vra == r_addr, "0x%X" % vra)
    chk("second_addr unchanged", vsa == s_addr, "0x%X" % vsa)
    chk("tags_addr unchanged", vt == tags, "0x%X" % vt)
    chk("second_size still 0", vs == 0)
    chk("dt_size still 0", struct.unpack("<I", v[40:44])[0] == 0)
    chk("name unchanged", v[48:64] == name)
    chk("cmdline unchanged", v[64:64 + 512] == cmdline)
    chk("kernel_size == new kernel", vk == len(k_blob), "%d" % vk)
    chk("total length == bootsize", len(v) == BOOTSIZE)

    voff = vp * (1 + ceil_page(vk, vp) // vp)
    vram = v[voff:voff + vr]
    chk("ramdisk in artefact byte-identical", sha256(vram) == EXPECT_RAMDISK,
        sha256(vram))
    chk("new kernel in artefact matches input",
        sha256(v[vp:vp + vk]) == sha256(k_blob))

    # header equality, field by field, except kernel_size
    hdr_same = v[12:40] == orig[12:40] and v[40:64] == orig[40:64] and v[64:64 + 512] == orig[64:64 + 512]
    chk("all header fields except kernel_size identical", hdr_same)

    print()
    if ok:
        print("RESULT: ALL CHECKS PASSED")
    else:
        print("RESULT: CHECKS FAILED")
        sys.exit(1)

    print()
    print("NOTE: this artefact deliberately contains ONLY the first %d bytes of p11."
          % BOOTSIZE)
    print("      The protected opaque blob at 0x384000 (sha256 e071d1ea8378da1e001a79485b9eab82e91cab16eb1a7aeb17ceaa8a2b8211f8)")
    print("      is not included, not regenerated, and must never be overwritten.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
