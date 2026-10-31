# Samsung Galaxy Young 2 postmarketOS development

postmarketOS port for the Samsung Galaxy Young 2

## What is postmarketOS?

postmarketOS is a Linux distribution based on Alpine Linux, replacing the stock Android system with a real Linux userspace. Essentially, real Linux on a phone.

> Device page: [Samsung Galaxy Young 2 (samsung-young23g)](https://wiki.postmarketos.org/wiki/Samsung_Galaxy_Young_2_(samsung-young23g))

<div align="center">
  <table>
    <tr>
      <td align="center" valign="top">
        <img width="300" src="https://github.com/user-attachments/assets/98ee8379-a4b3-4397-82af-14a2acff524a"/>
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

The phone now boots directly into a usable postmarketOS system with an XFCE desktop. If you want to switch to a headless SSH only pmOS install, switch to the "working-ssh" branch.

The current XFCE v1 release includes the root filesystem, boot image, and Windows/TWRP installation scripts needed to install the tested system without manually copying large images into `/data` or typing raw `dd` commands.

### Working

- Kernel boots
- postmarketOS/Alpine root filesystem mounts
- OpenRC starts normally
- Xorg starts automatically
- XFCE starts automatically after boot
- 320×480 framebuffer/display output
- Touchscreen input
- On-screen keyboard
- USB RNDIS networking
- SSH rescue access over USB on port `2222`
- Wi-Fi
- NetworkManager
- Bluetooth controller and scanning
- Audio output/routing
- Battery reporting
- Power button handling
- Volume buttons
- Front hardware buttons
- Accelerometer
- Suspend and resume
- Reboot and shutdown
- Hardware startup fixes survive reboot and run automatically
  
### Experimental

- Camera bring-up exists and can produce preview output, but performance is still very slow and the camera is not considered ready for normal use
- Sleep mode is still iffy.

### Not working / not established

- Modem
- Phone calls
- SMS
- Mobile data


## Repository layout

The repository contains the device port itself as well as the scripts and documentation used during bring-up.

```text
device-samsung-young23g/
    postmarketOS device package and device configuration

linux-samsung-young23g/
    downstream Linux kernel package for the Young 2

scripts/
    device bring-up, hardware, networking and development helper scripts

docs/
    development notes, hardware findings and porting documentation

README.md
    project status and installation guide
```

The ready-to-install XFCE system itself is distributed through the GitHub Releases page rather than being stored directly in the repository.

## Future plans

- Improve camera performance and stability
- Continue investigating the modem
- Investigate calls, SMS and mobile data
- Continue improving Wi-Fi and Bluetooth reliability
- Improve power-management behaviour where possible
- Keep documenting device-specific Spreadtrum/Samsung behaviour

# Installation guide

This is an experimental raw-partition installation for the **Samsung Galaxy Young 2 SM-G130HN**.

Do not use these images or installer scripts on another phone model.
Verify your model in Android before starting: Settings -> About phone -> Model number

The release installer handles the raw flashing and verifies the written data afterward.

## Partition targets

The SM-G130HN port uses these partitions:

| Purpose | Device |
|---|---|
| Boot / kernel | `/dev/block/mmcblk0p11` |
| Recovery / TWRP | `/dev/block/mmcblk0p12` |
| postmarketOS rootfs | `/dev/block/mmcblk0p18` |
| Userdata | `/dev/block/mmcblk0p20` |

---

## 1. What you need

You need a Windows PC and:

- Samsung USB drivers
- Odin
- Android Platform Tools (`adb`)
- A compatible TWRP build for the SM-G130HN
- The **postmarketOS XFCE v1** release files

The current XFCE release is available here:

[postmarketOS XFCE v1 for Samsung Galaxy Young 2](https://github.com/integersys/postmarketos-young2/releases/tag/xfce-v1.0)

From the release, download:

```text
system_pmos_xfce-SM-G130HN.img.xz
pmos-xfce-boot-SM-G130HN.img
install-postmarketos-xfce.ps1
twrp-install-postmarketos.sh
```
After extracting the rootfs, your Downloads folder should contain:

```text
C:\Users\YourName\Downloads\
│
├── system_pmos_xfce-SM-G130HN.img.xz
├── system_pmos_xfce-SM-G130HN.img
├── pmos-xfce-boot-SM-G130HN.img
├── install-postmarketos-xfce.ps1
├── twrp-install-postmarketos.sh
```

The installer looks for its required files in the same directory as the `.ps1` file.

---

## 2. Extract the XFCE root filesystem

The root filesystem is distributed as:

```text
system_pmos_xfce-SM-G130HN.img.xz
```

Use 7-Zip and choose:

```text
7-Zip -> Extract Here
```

You should then have:

```text
system_pmos_xfce-SM-G130HN.img
```

Do not try to flash the `.xz` file directly.

## 3. Flash TWRP first

Download the TWRP recovery.

[Download TWRP from here](https://github.com/integersys/postmarketos-young2/releases/tag/pmos)

From that release, download:

```text
twrp_3.1.1-0_young23g_wulan17.tar.md5
```

Keep the `.tar.md5` file in your Downloads folder. This is the file you will select in Odin's **AP** slot.

If TWRP is already installed and working, skip to the next section.

Otherwise:

1. Install the Samsung USB drivers.
2. Open Odin.
3. Power off the Galaxy Young 2.
4. Hold:

   ```text
   Volume Down + Home + Power
   ```

5. Confirm Download Mode with `Volume Up`.
6. Connect the phone to the PC.
7. Wait for Odin to detect it.
8. Put the downloaded TWRP `.tar.md5` in the **AP** slot.
9. Make sure **Re-Partition is disabled**.
10. Disable **Auto Reboot**.
11. `F. Reset Time` can remain enabled.
12. Press **Start**.
13. Wait for Odin to show **PASS**.

### Boot directly into TWRP
After Odin finishes:

1. Hold `Volume Down + Home + Power` until the phone switches off.
2. Immediately switch to:

   ```text
   Volume Up + Home + Power
   ```

3. Keep holding until TWRP appears.

---

## 4. Connect TWRP to Windows

Leave the phone in TWRP and connect it over USB.

Open PowerShell and run:

```powershell
adb devices
```

The phone should appear as an ADB device, normally with the state:

```text
recovery
```

Example:

```text
List of devices attached
xxxxxxxxxxxxxxxx    recovery
```

The old TWRP build used on this device has many broken commands, such as adb shell. That is to be expected, that is why this installation uses this partition chunk flashing workaround. This is the only TWRP version available for this device, as far as i know.

---

## 5. Run the XFCE installer

Run the installer from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\install-postmarketos-xfce.ps1"
```

The Windows installer first checks:

- rootfs size
- rootfs SHA-256
- boot-image size
- boot-image SHA-256
- ADB/TWRP connectivity

The installer then pushes the helper to:

```text
/tmp/pmos-install.sh
```

Eventually Windows will display:

```text
ON THE PHONE:

TWRP -> Advanced -> Terminal

Type exactly:

    sh /tmp/pmos-install.sh
```

---

## 6. Start the TWRP-side installer

On the phone open:

```text
TWRP -> Advanced -> Terminal
```

Type exactly:

```sh
sh /tmp/pmos-install.sh
```

Leave the TWRP terminal open.

The phone should display:

```text
READY
Keep this TWRP terminal open.
The Windows installer can now transfer the rootfs.
```

Windows detects this automatically and starts the installation.

No other long commands need to be typed on the phone.

---

## 7. How the installer works

This TWRP build on this device rejects large ADB writes to `/data` or `/sdcard`.

The XFCE installer avoids those locations completely.

Instead, the rootfs is transferred through TWRP's temporary `/tmp` filesystem in small chunks.

## 9. Reboot into XFCE

On the phone choose:

```text
TWRP -> Reboot -> System
```

TWRP may display:

```text
No OS Installed!
```

This can be ignored. TWRP does not understand the Linux root filesystem used by this port.

If TWRP offers to install SuperSU or a TWRP application:

**do not install it.**

The phone should now boot directly into postmarketOS XFCE without requiring SSH commands or manual desktop setup.

---

# USB SSH access

The XFCE release includes an automatic USB RNDIS rescue/SSH setup.

The expected USB network is:

```text
Phone:   172.16.42.1
PC:      172.16.42.2
SSH:     TCP port 2222
```

Connect the phone over USB and try:

```powershell
ssh -tt -p 2222 root@172.16.42.1
```

### If USB networking is not reachable

Check Windows network interfaces:

```powershell
Get-NetIPConfiguration | Where-Object {$_.IPv4Address -and $_.NetAdapter.Status -eq "Up"} | Select-Object InterfaceAlias,@{N="IP";E={$_.IPv4Address.IPAddress}},@{N="Gateway";E={$_.IPv4DefaultGateway.NextHop}}
```

Look for the USB/RNDIS Ethernet adapter.

If Windows does not install it automatically, use Device Manager and select the **Remote NDIS Compatible Device** driver.

The PC side of the USB link should use:

```text
172.16.42.2/24
```

and the phone should be reachable at:

```text
172.16.42.1
```

# Sources

- [postmarketOS device page for the Samsung Galaxy Young 2](https://wiki.postmarketos.org/wiki/Samsung_Galaxy_Young_2_(samsung-young23g))
- [TWRP](https://4pda.to/forum/index.php?showtopic=731597)
