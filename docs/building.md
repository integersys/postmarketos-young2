# Building the development kernel

The successful October builds used WSL2 Ubuntu 26.04 on its Linux filesystem,
`arm-linux-gnueabihf-gcc` 15.2.0-16ubuntu1 and binutils 2.46. I used source from
[jnkcode/android_kernel_samsung_young23g](https://github.com/jnkcode/android_kernel_samsung_young23g)
at `e05a1c16fb7334378bb12d8116d0def2ef83ff0d`. This is a Samsung/Spreadtrum
downstream Linux 3.10.17 tree, not mainline.

## What is reproduced here

[config-xfce.armv7](../linux-samsung-young23g/config-xfce.armv7) was copied from the
existing October build and matches its saved suspendfix config byte for byte.
The default patch series reproduces the compiler preparation and #8 resume
source changes. It is a reproducible source recipe, not a claim that this newly
packaged recipe was rebuilt or flashed during publication.

| Build | Recorded status |
|---|---|
| 2016 `3.10.17-young2` | proven basis of June v3; no surviving exact source-to-binary path |
| June `3.10.17-pmos` | recovered package binary; physical boot UNKNOWN |
| October source builds through #8 | booted; USB parity, HCI UART and display resume demonstrated |
| #9 | requested KPLED brightness no longer forced to zero; symbols still dark |
| #10 | last recorded running; unsuccessful analog-base experiment causes ADI warnings |
| #11 | built/packaged with that base change reverted; not separately flashed |

The later booted kernels do not retroactively prove that the June pmbootstrap
binary booted. Build numbers are historical outputs, not version tags assigned
to the source recipe below. The build below will have its own timestamp/number.

## Source preparation and build

Work outside this packaging repository, on WSL's Linux filesystem. Install the
recorded build tools if absent: make, gcc-arm-linux-gnueabihf, bc, bison, flex,
perl, git, patch, Python 3 and cpio. The scripts take explicit paths:

```sh
git clone https://github.com/jnkcode/android_kernel_samsung_young23g.git young2-upstream
git -C young2-upstream checkout --detach e05a1c16fb7334378bb12d8116d0def2ef83ff0d
bash /path/to/postmarketos-young2/scripts/build/prepare-kernel.sh     "$PWD/young2-upstream" "$PWD/young2-xfce-build"
bash /path/to/postmarketos-young2/scripts/build/build-kernel.sh     "$PWD/young2-xfce-build"
```

Preparation refuses an existing output directory, exports the pinned commit,
applies two ordered patches and installs the recorded config. Building runs
olddefconfig then make with explicit `ARCH=arm`, `CROSS_COMPILE` and
`CC=arm-linux-gnueabihf-gcc -msoft-float`. Keep a copy/hash of .config before and
after normalization; historical #8/#9 normalization had no functional config
delta. A modern environment is not automatically the recorded environment.

The source Makefile overrides an environment-only CROSS_COMPILE. Command-line
assignment is necessary. Putting `-msoft-float` in CC also makes its early
`cc-option` probe accept ARMv7: without it Ubuntu GCC's default hard-float ABI
rejected `-march=armv7-a` without an FPU, selecting an ARMv5 fallback.

For an interrupted build, rerun only `make` with those same arguments in the
prepared directory. A WSL VM restart kills builds; rerunning preparation or
olddefconfig can invalidate objects. Check process state, log freshness and
output hashes before declaring a build finished.

## Patch/config content

- [0001-gcc15-compatibility.patch](../linux-samsung-young23g/patches/0001-gcc15-compatibility.patch)
  consolidates the actual prepared tree: compiler-gcc15 header, GNU89 host/target
  mode, GCC7 ilog2/GCC8 put_user fixes, dtc yylloc fix, ARM section syntax and
  sortextable stub. This retains the historical stub limitation rather than
  pretending it is a complete modern toolchain port.
- [0002-sprdfb-resume.patch](../linux-samsung-young23g/patches/0002-sprdfb-resume.patch)
  is the tested sprdfb mode-validation change. RGB metadata is still corrected by
  the userspace boot helper.
- Config: LZMA is necessary to fit the reserved boot region; DEVTMPFS is enabled,
  Android/Samsung composite gadget support is enabled and USB_ETH is disabled.
  HCIUART/H4, IST30XXB, K2HH, ALSA, earlysuspend and wakelocks remain enabled.
- [Optional patches](../linux-samsung-young23g/patches/optional/STATUS.md) are not
  automatically applied: RGB source metadata was prepared but not physically
  tested; the KPLED patch records #11's reverted-base state. The bad #10 address
  change is deliberately omitted.

## Packaging a file, not flashing a phone

The kernel package installs `/boot/vmlinuz-linux-samsung-young23g` and matching
modules. The updated [APKBUILD](../linux-samsung-young23g/APKBUILD) uses the same
source/config/patch inputs; the full abuild/pmbootstrap integration remains
unbuilt in this publication pass. It does not reproduce the custom ramdisk.
Device package layout stays recognizable and `deviceinfo_flash_method=none`
remains. No automated flashing is configured.

For the historical working layout I reused the exact compressed static-init
ramdisk from a verified backup. [make_boot_image.py](../scripts/build/make_boot_image.py)
adapts the original file packager, verifies the expected ramdisk SHA256, preserves
the original header except kernel_size and limits output to 0x384000 bytes:

```sh
python3 /path/to/postmarketos-young2/scripts/build/make_boot_image.py     /path/to/verified-p11-backup.img     /path/to/young2-xfce-build/arch/arm/boot/zImage     /path/to/new-empty-output-directory
```

It never writes a device. The output is an experimental file until separately
authorized and physically tested. Read [recovery](recovery.md): the rest of p11
contains protected opaque data and is not spare space. The earlier gzip kernel
did not fit this envelope; fitting the full 8 MiB partition is insufficient.

The packager's original validation-state bug, output-overwrite behavior and
oversized intermediate output were corrected for publication. Its original
assembly flow and expected ramdisk remain. Run the synthetic ordinary-file tests
with `python3 scripts/build/test_boot_image.py`; no backup or phone is opened.
Set `YOUNG2_TEST_TMPDIR` if the host's default temporary directory is restricted.

## Rootfs and missing inputs

The June rootfs came from pmbootstrap plus manual node/PTY/RNDIS/SSH repairs.
The current graphical rootfs accumulated carefully tested package and config
changes. This repository is not a locked package mirror or an end-to-end XFCE
image builder. Reproduction still needs compatible armv7 userspace packages,
pixbuf 2.42.12, the built preload shim, device firmware/NVRAM, the verified
static-init ramdisk and selected local XFCE preferences. See
[userspace installation](../userspace/INSTALL.md) and [installation](installation.md).
