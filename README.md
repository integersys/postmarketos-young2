# Samsung Galaxy Young 2 postmarketOS development

postmarketOS port for the Samsung Galaxy Young 2

> Device page: [Samsung Galaxy Young 2 (samsung-young23g)](https://wiki.postmarketos.org/wiki/Samsung_Galaxy_Young_2_(samsung-young23g))

<div align="center">
  <table>
    <tr>
      <td align="center" valign="top">
        <img width="300" src="https://github.com/user-attachments/assets/90c813bc-6898-4942-94a1-c5b54f512f05"/>
        <br>
        <em>Hey, look, there's me!</em>
      </td>
      <td align="center" valign="top">
        <img width="1132" height="682" src="https://github.com/user-attachments/assets/5e48533c-7175-4e20-9fc7-9a29c56a56db" />
        <br>
      </td>
    </tr>
  </table>
</div>

## Current status

The device currently boots into a headless postmarketOS/Alpine userspace and can be accessed over USB networking with SSH.

### Working

- Kernel boots
- postmarketOS/Alpine root filesystem mounts
- OpenRC starts
- USB RNDIS networking works
- SSH over USB works
- The setup survives reboot and becomes reachable again over USB

### Not working yet

- Graphical UI is not finished
- Wi-Fi is not configured
- NetworkManager is not working correctly yet
- Sound is not tested
- Camera is not tested
- Modem, calls, SMS, and mobile data are not working/tested
- This is not ready for normal phone use, but it sure is interesting to watch!

# Installation guide

**Warning:** This is a manual dev bring-up, not an official installer. Tested only on SM-G130HN — other models/firmware may brick. Verify your model first: `Settings -> About phone -> Model number`. Proceed at your own risk.

**End result:** Linux (Alpine/postmarketOS) boots and is reachable via USB SSH (`ssh -tt -p 2222 root@172.16.42.1`, login `root/root`). No GUI, Wi-Fi, sound, camera, modem, calls, SMS, or daily-driver use yet.

**Partition targets (SM-G130HN):**
| Partition | Device |
|---|---|
| Boot/Kernel | `/dev/block/mmcblk0p11` |
| Recovery (TWRP) | `/dev/block/mmcblk0p12` |
| System/rootfs | `/dev/block/mmcblk0p18` |
| Userdata | `/dev/block/mmcblk0p20` |

Choose one method below.

---

## Method 1: Release Artifact Install

1. **Download release files**
   - `system_pmos_raw-SM-G130HN.img.xz` (rootfs, compressed)
   - `pmos-static-v3-boot-SM-G130HN.img` (boot image)
   - `twrp_3.1.1-0_young23g_wulan17.tar.md5` (TWRP recovery)

2. **Decompress the rootfs**
Unzip it using 7zip, don't flash it as-is.

3. **Install Windows tools**: Samsung USB drivers, Odin, Android platform-tools aka adb.

4. **Boot phone into Download Mode**: power off, hold `Volume Down + Home + Power`, then press `Volume Up` at the warning screen.

5. **Flash TWRP with Odin**:
   - Connect phone via USB; confirm Odin detects it.
   - Click `AP`, select `twrp_3.1.1-0_young23g_wulan17.tar.md5`
   - Set `F. Reset Time: enabled`, disable `Auto Reboot` in Options
   - Click `Start`, wait for `PASS`.

6. **Boot directly into TWRP**: Turn off the phone immediately after flashing by taking out the battery and hold `Volume Up + Home + Power` to go into Recovery.

7. **Push files to the phone** (TWRP + USB connected):
   ```powershell
   .\adb.exe devices
   .\adb.exe shell mkdir -p /data/pmos   # or use TWRP terminal: mkdir -p /data/pmos
   .\adb.exe push C:\Users\User\Downloads\system_pmos_raw-SM-G130HN.img /data/pmos/system_pmos_raw.img
   .\adb.exe push C:\Users\User\Downloads\pmos-static-v3-boot-SM-G130HN.img /data/pmos/pmos-static-v3-boot.img
   ```
   (If `adb shell` fails, use the TWRP terminal instead — this is a known issue.)

8. **Verify files and partitions** (TWRP terminal):
   ```sh
   ls -lh /data/pmos
   cat /proc/partitions
   ls -l /dev/block/mmcblk0p11 /dev/block/mmcblk0p12 /dev/block/mmcblk0p18 /dev/block/mmcblk0p20
   ```

9. **Flash rootfs and boot image** (TWRP terminal):
   ```sh
   dd if=/data/pmos/system_pmos_raw.img of=/dev/block/mmcblk0p18 bs=4M
   sync
   dd if=/data/pmos/pmos-static-v3-boot.img of=/dev/block/mmcblk0p11 bs=4M
   sync
   ```

10. **Reboot the phone** and wait 60–90 seconds. (Screen may look stuck even when Linux is running — check from the PC instead.)

11. **Set up Windows RNDIS networking** (Admin PowerShell):
    ```powershell
    Get-NetAdapter | Format-Table Name,Status,InterfaceDescription -Auto
    Remove-NetIPAddress -InterfaceAlias "Ethernet" -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
    netsh interface ipv4 set interface "Ethernet" dadtransmits=0
    New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 172.16.42.2 -PrefixLength 24 -SkipAsSource $false
    ping 172.16.42.1
    ```
    (Replace `"Ethernet"` with your actual RNDIS adapter name; install "Remote NDIS Compatible Device" driver manually in Device Manager if needed.)

12. **SSH into the phone** (from WSL):
    ```sh
    ssh -tt -p 2222 root@172.16.42.1
    ```
    Login: root is username and password.

---

## Method 2: Manual Build

Use this if you want to build or modify the port yourself. Requires the release **boot image** unless you can rebuild it yourself.

1. **Install WSL build tools**:
   ```sh
   sudo apt update
   sudo apt install -y git curl wget unzip nano openssh-client netcat-openbsd iputils-ping build-essential python3 python3-pip python3-venv
   pip3 install --user pmbootstrap
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.profile
   . ~/.profile
   pmbootstrap --version
   ```

2. **Clone the repo**:
   ```sh
   cd /mnt/c/Users/User/Desktop
   git clone https://github.com/integersys/postmarketos-young2.git pm
   cd pm
   git switch working-ssh
   ```

3. **Initialize pmbootstrap**:
   ```sh
   pmbootstrap init
   ```
   Choose: Vendor `samsung`, Device `young23g`, Architecture `armv7`, UI `none`/`minimal` (no desktop yet).

4. **Copy device/kernel packages into pmaports and build**:
   ```sh
   cd /mnt/c/Users/User/Desktop/pm
   PMAPORTS="$HOME/.local/var/pmbootstrap/cache_git/pmaports"
   mkdir -p "$PMAPORTS/device/downstream"
   cp -a device-samsung-young23g "$PMAPORTS/device/downstream/"
   cp -a linux-samsung-young23g "$PMAPORTS/device/downstream/"

   pmbootstrap checksum device-samsung-young23g
   pmbootstrap checksum linux-samsung-young23g
   pmbootstrap build device-samsung-young23g
   pmbootstrap build linux-samsung-young23g
   ```

5. **Build the rootfs image**:
   ```sh
   pmbootstrap install
   find ~/.local/var/pmbootstrap -type f -name "*.img" | sort
   ```
   Confirm the image is a raw ext4 rootfs no larger than the system partition (~1,111,490,560 bytes on this device):
   ```sh
   ls -lh your-rootfs.img
   stat -c '%s bytes' your-rootfs.img
   ```

6. **Add startup scripts into the rootfs**:
   Copy `scripts/00-dev-fix.start`, `scripts/usb-rndis-debug.start`, `scripts/99-ssh-pty-rndis.start` into `/etc/local.d/` inside the rootfs, then inside the rootfs:
   ```sh
   chmod +x /etc/local.d/*.start
   rc-update add local default
   ```
   These handle device node fixes, USB RNDIS, phone IP (172.16.42.1), and starting `sshd.pam` on port 2222 (falls back to `/usr/sbin/sshd` if `sshd.pam` is missing).

7. **Set a root password** in the rootfs before flashing (the release default `root/root` does not apply to your own build). Before uploading/sharing any custom rootfs image, strip `/etc/shadow`, `/etc/ssh/ssh_host_*`, `/root/.ssh/authorized_keys`, `/root/.ash_history`, Wi-Fi configs, and logs.

8. **Get a boot image**: use the release `pmos-static-v3-boot-SM-G130HN.img` unless you already have the steps to rebuild the boot image (which does early device-node setup, mounts `/dev/block/mmcblk0p18`, `/proc`, `/sys`, `/dev/pts`, attempts `pivot_root`, falls back to `chroot`, then execs `/sbin/init`).

9. **Flash to the phone** — same as Method 1, steps 4–11: boot into Download Mode, flash TWRP with Odin, boot into TWRP, push your built rootfs image and the boot image to `/data/pmos/`, then:
   ```sh
   dd if=/data/pmos/<your-rootfs>.img of=/dev/block/mmcblk0p18 bs=4M
   sync
   dd if=/data/pmos/pmos-static-v3-boot.img of=/dev/block/mmcblk0p11 bs=4M
   sync
   ```

10. **Reboot, set up Windows RNDIS (172.16.42.2/24), and SSH in**:
    ```sh
    ssh -tt -p 2222 root@172.16.42.1
    ```


## Sources

* [TWRP](https://4pda.to/forum/index.php?showtopic=731597)
