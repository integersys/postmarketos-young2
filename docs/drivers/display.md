# Display: Spreadtrum sprdfb

I verified the SCX15/SC7715 display path on the SM-G130HN's physical 320×480 LCD.
It uses the downstream framebuffer driver, not DRM/KMS or a demonstrated GPU path.

## Hardware and kernel

Source paths under the pinned kernel revision are
`drivers/video/sprdfb/sprdfb_main.c`, `sprdfb_dispc.c` and `sprdfb.h`.
The measured buffer is 320×960 at 32 bpp, stride 1280, length 1228800 bytes.
Each visible page occupies 614400 bytes. Physical colour tests establish bytes
`R G B 00`: red `FF 00 00 00`, green `00 FF 00 00`, blue `00 00 FF 00`.

The original driver's red/green/blue offsets 24/16/8 disagree with that layout.
The correct offsets are 0/8/16, length 8 each, transparency length 0.
Transparency offset 0 or 24 is equivalent when its length is zero. The hardware
format and R/B switch are programmed in DISPC; Xorg reads the misleading metadata.

## Userspace and scanout

[98-fb0-node.start](../../userspace/display/98-fb0-node.start) discovers the node's
major/minor from sysfs and performs the boot-logo handover. The original 2016
kernel lacked devtmpfs; the October config enables it, but the old helpers remain.
The first pan after boot is swallowed by the frame-skip guard; two calls release
the logo buffer. Correct framebuffer memory alone does not prove visible output.

[98-rgb-bitfields.start](../../userspace/display/98-rgb-bitfields.start) invokes
[fbvar.py](../../userspace/display/fbvar.py) after the node exists. It changes only
colour metadata. This remains the reproduced RGB fix; the optional source RGB
patch is not in the validated kernel series.

The [Xorg config](../../userspace/display/xorg-scanout.conf) uses fbdev,
`ShadowFB "false"`, depth 24 and 32 bpp. An explicit `vt1` and
[start-x-with-handover](../../userspace/display/start-x-with-handover) provide
the physical handover. One pan after Xorg's mode set is sufficient; switching
RandR to logical 320×480 requires another. The kernel buffer remains 320×960.

## Resume patch

[0002-sprdfb-resume.patch](../../linux-samsung-young23g/patches/0002-sprdfb-resume.patch)
changes `sprdfb_check_var()`: validate visible x/y resolution and grayscale,
normalize virtual geometry and xoffset to the stored values. This prevents
Xorg's `fbdevHWEnterVT()` from failing when it resubmits its saved mode after a
pan/resume. The #8 test config was unchanged by this source fix.

The power-key daemon separately issues `FBIOPAN_DISPLAY(yoffset=0)` and
`xrefresh` after wake and once after boot. Kernel ioctl acceptance and correct
physical scanout require both layers.

## Verification and limits

September camera records show correct solid colours, Xorg, interactive clients
and XFCE. October power tests preserved the same Xorg/XFCE processes across real
deep sleep. These are stronger checks than opening `/dev/fb0` or taking a memory
screenshot. No new physical display test was run for publication.

DPMS blank/unblank can still select stale scanout; keep it disabled. A brief
panel-init white flash remains. Later suspend cycles also produced DISPC sync
timeouts and a delayed reboot; a fresh boot cleared them. 16 bpp, rotation and
hardware acceleration are not demonstrated. See [power](power.md).
