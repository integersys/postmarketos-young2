# Troubleshooting

---

## Quick success check

Wait 60–90 seconds after boot, then from WSL:

```sh
ping 172.16.42.1
ssh -tt -p 2222 root@172.16.42.1
```

Release rootfs login: `root` / `root`. After logging in:

```sh
id
tty
cat /etc/alpine-release
ps | grep ssh
```

Good signs: `uid=0(root)`, `/dev/pts/0`, `3.24.0`, `sshd.pam`.

---

# Boot problems

## The phone looks stuck on the Samsung logo

Not always a failure — the display/framebuffer side is still experimental, so USB SSH is the main way to confirm boot. Wait 60–90 seconds, then check `ping 172.16.42.1` and `ssh -tt -p 2222 root@172.16.42.1`. If SSH works, Linux booted.

## The phone bootloops

Possible causes: wrong boot image, an old/failed test boot image, wrong rootfs partition, a rootfs image written incorrectly, a rootfs image that's too large or corrupt, or the wrong device variant.

**Check the boot image** — the working image is `pmos-static-v3-boot.img` (`pmos-static-v3-boot-SM-G130HN.img` in the release).

**Check the boot partition** — the boot image belongs on `/dev/block/mmcblk0p11`. Wrong partition = likely boot failure.

## Nothing happens after flashing the rootfs

Confirm the rootfs went to `/dev/block/mmcblk0p18`, not `/dev/block/mmcblk0p20` (userdata). From the TWRP terminal:

```sh
ls -l /dev/block/mmcblk0p18
ls -l /dev/block/mmcblk0p20
cat /proc/partitions
```

If the partition numbers don't match this guide, stop.

## I accidentally flashed the wrong partition

Stop flashing anything else. Reflash the correct image for whatever you overwrote:
- Boot (`/dev/block/mmcblk0p11`) → reflash the working boot image
- Rootfs (`/dev/block/mmcblk0p18`) → reflash the correct rootfs
- Recovery (`/dev/block/mmcblk0p12`) → reflash TWRP
- Userdata (`/dev/block/mmcblk0p20`) → Android userdata may be lost

---

# TWRP / recovery problems

## Odin does not detect the phone

Power off, hold `Volume Down + Home + Power`, then press `Volume Up` at the warning screen to enter Download Mode. Then connect USB and open Odin. If it still isn't detected: install Samsung USB drivers, try another cable/port, avoid USB hubs, avoid usb 3.0 ports, restart Odin, or reboot back into Download Mode.

## Odin flash fails

Check that you're using the AP slot, the file is for the Young 2, it's an Odin-flashable `.tar`/`.tar.md5`, the phone is actually in Download Mode, Samsung USB drivers are installed, and the cable is stable.

Don't flash the postmarketOS rootfs `.img`/`.img.xz` with Odin — Odin is only for TWRP/recovery. The rootfs and boot image are written from TWRP using `dd`.

## TWRP boots, but adb shell fails

TWRP may try to execute `/system/bin/sh` and fail, so interactive `adb shell` may not work. `adb devices`, `adb push`, and the TWRP terminal should still work.

Safer workflow: push images to `/data/pmos` with `adb push`, then run `dd` from the TWRP terminal:

```sh
mkdir -p /data/pmos
ls -lh /data/pmos

dd if=/data/pmos/system_pmos_raw.img of=/dev/block/mmcblk0p18 bs=4M
sync
dd if=/data/pmos/pmos-static-v3-boot.img of=/dev/block/mmcblk0p11 bs=4M
sync
```

## adb push is slow or appears stuck

The rootfs is around 1 GB after decompression — this takes time. Keep the USB cable stable, keep the phone in TWRP, don't let the computer sleep, and confirm the destination is `/data/pmos`. Check with `ls -lh /data/pmos` in the TWRP terminal.

---

# Rootfs image problems

## I accidentally pushed/flashed the .xz file

The phone won't boot from the compressed file. Decompress it first, then reflash the decompressed `system_pmos_raw-SM-G130HN.img` to `/dev/block/mmcblk0p18`.

## The rootfs image is too large

The tested device's system partition is about 1,111,490,560 bytes. Check before flashing:

```sh
ls -lh system_pmos_raw.img
stat -c '%s bytes' system_pmos_raw.img
```

Don't flash if it's larger than the partition.

## The release rootfs boots but SSH does not work

Confirm these exist and are enabled:

```sh
ls -l /etc/local.d
rc-update show | grep local
```

You should see `/etc/local.d/00-dev-fix.start`, `/etc/local.d/usb-rndis-debug.start`, and `/etc/local.d/99-ssh-pty-rndis.start`, with the `local` service enabled (`/etc/runlevels/default/local -> /etc/init.d/local`). If not:

```sh
chmod +x /etc/local.d/*.start
rc-update add local default
```

`99-ssh-pty-rndis.start` is the important one — it runs late and restarts RNDIS/SSH after device nodes and PTY support are fixed.

---

# USB RNDIS problems

## Windows does not show a RNDIS adapter

```powershell
Get-NetAdapter | Format-Table Name,Status,InterfaceDescription -Auto
```

Look for "Remote NDIS Compatible Device." If it's missing: wait 90 seconds after boot, try another cable/port, unplug/replug, or manually select it in Device Manager.

## Windows shows an unknown device or missing driver

In Device Manager, manually select "Remote NDIS Compatible Device" when you're installing the missing driver from the "all drivers on my Computer" section. (naming may vary slightly by Windows version). Recheck with `Get-NetAdapter` afterward.

## RNDIS adapter exists, but ping does not work

Expected network: phone `172.16.42.1`, host `172.16.42.2`. Find your adapter name with `Get-NetAdapter`, then (as Administrator, using your actual adapter name — e.g. `Ethernet`, `Ethernet 3`, `Local Area Connection`):

```powershell
Remove-NetIPAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
netsh interface ipv4 set interface "Ethernet" dadtransmits=0
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 172.16.42.2 -PrefixLength 24 -SkipAsSource $false
ping 172.16.42.1
```

## Windows says the IP is tentative or invalid

Run `netsh interface ipv4 set interface "Ethernet" dadtransmits=0`, then remove and re-add the IP as above, then `ping 172.16.42.1`. Replace `"Ethernet"` with your actual adapter name.

---

# SSH problems

## Ping works but SSH does not connect

```sh
ssh -tt -p 2222 root@172.16.42.1
```

Make sure you're using port 2222, not 22. Release login is `root`/`root`. If port 2222 refuses connection, SSH may not have started — the working binary on this rootfs is `/usr/sbin/sshd.pam`, not necessarily `/usr/sbin/sshd` (the startup scripts try `sshd.pam` first).

## SSH says password denied

Release image default is `root`/`root`. For your own manually built rootfs, this doesn't apply — set your own password. If you have shell access: `passwd root`, then restart SSH or reboot.

## SSH connects but says PTY allocation failed

From WSL:

```sh
ssh -p 2222 root@172.16.42.1 'mkdir -p /dev/pts; umount /dev/pts 2>/dev/null || true; mount -t devpts devpts /dev/pts -o mode=620; rm -f /dev/ptmx; mknod /dev/ptmx c 5 2; chmod 666 /dev/ptmx'
```

Then retry `ssh -tt -p 2222 root@172.16.42.1`. If this fixes it, make sure `/etc/local.d/99-ssh-pty-rndis.start` exists and is executable (`chmod +x`, `rc-update add local default`).

## SSH works only sometimes after reboot

Wait longer — the late startup script (`/etc/local.d/99-ssh-pty-rndis.start`) sleeps, repairs `/dev/pts`, recreates `/dev/ptmx`, reconfigures RNDIS, kills old SSH processes, and restarts SSH. Wait 90 seconds, then `ping 172.16.42.1` and `ssh -tt -p 2222 root@172.16.42.1`.

---

# Device node problems

## random/urandom/zero are missing or broken

```sh
rm -f /dev/random /dev/urandom /dev/zero
mknod /dev/random c 1 8
mknod /dev/urandom c 1 9
mknod /dev/zero c 1 5
chmod 666 /dev/random /dev/urandom /dev/zero
```

Matters because SSH key generation and other programs may fail if randomness is broken.

## /dev/ptmx or /dev/pts is broken

```sh
mkdir -p /dev/pts
umount /dev/pts 2>/dev/null || true
mount -t devpts devpts /dev/pts -o mode=620

rm -f /dev/ptmx
mknod /dev/ptmx c 5 2
chmod 666 /dev/ptmx
```

Matters because SSH with a real terminal needs PTY support.

## ssh-keygen fails with PRNG or randomness errors

Fix the random devices (as above), then:

```sh
haveged -w 1024 &
ssh-keygen -A
```

The release rootfs scripts already try to do this automatically.

---

# Manual build problems

## pmbootstrap does not know the device

```sh
PMAPORTS="$HOME/.local/var/pmbootstrap/cache_git/pmaports"
mkdir -p "$PMAPORTS/device/downstream"
cp -a device-samsung-young23g "$PMAPORTS/device/downstream/"
cp -a linux-samsung-young23g "$PMAPORTS/device/downstream/"

pmbootstrap checksum device-samsung-young23g
pmbootstrap checksum linux-samsung-young23g
pmbootstrap build device-samsung-young23g
pmbootstrap build linux-samsung-young23g
```

## pmbootstrap build fails

This port is experimental — the pmaports folders may need cleanup. Check APKBUILD syntax, checksums, source paths, kernel package files, `deviceinfo`, architecture, and depends/makedepends. Then re-run `pmbootstrap checksum ...` and rebuild.

## Manual rootfs does not have the startup scripts

The repo stores them in `scripts/`; inside the rootfs they must be installed to `/etc/local.d/`, then:

```sh
chmod +x /etc/local.d/*.start
rc-update add local default
```

Without this, Linux may boot but RNDIS/SSH won't come up.

## Manual rootfs has no root password

The release rootfs uses `root`/`root` — a manual build doesn't inherit that. Set a password before flashing, or with shell access run `passwd root` (and confirm SSH config allows password login).

## Manual build has /usr/sbin/sshd missing

The working SSH server during bring-up was `/usr/sbin/sshd.pam`; `/usr/sbin/sshd` didn't exist on that rootfs. The scripts handle this:

```sh
SSHD=/usr/sbin/sshd.pam
[ -x "$SSHD" ] || SSHD=/usr/sbin/sshd
```

If neither exists, install OpenSSH packages in the rootfs.

The hashes should match.

---

# When to restore stock firmware

Consider restoring stock firmware if recovery no longer boots, the boot or system partition is corrupted, Odin/TWRP flashing can't recover the setup, or you flashed the wrong partition. Use stock firmware for the exact tested model (SM-G130HN) — don't flash firmware for a different model unless you know it's compatible.

---

# Final checklist

Before concluding the install failed, confirm:

1. Device model is SM-G130HN.
2. TWRP boots.
3. Rootfs was decompressed from `.xz`.
4. Rootfs image was written to `/dev/block/mmcblk0p18`.
5. Boot image was written to `/dev/block/mmcblk0p11`.
6. Phone was given 60–90 seconds to boot.
7. Windows sees a "Remote NDIS Compatible Device."
8. Host RNDIS IP is `172.16.42.2/24`.
9. Phone responds to `ping 172.16.42.1`.
10. SSH command uses port 2222.
11. Login is `root`/`root` for the release rootfs.
12. PTY fix has been applied if SSH connects but no terminal opens.

If all of these check out and it still doesn't work, the next useful step is pulling logs from recovery, framebuffer output, or any available shell.