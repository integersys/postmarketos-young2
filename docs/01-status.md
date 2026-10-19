> Historical June 2026 headless-release notes. For the later XFCE system,
> start with [the current documentation index](INDEX.md). Old release credentials
> are historical; use your own password/key for a new installation.

# Current status

This document records the current working and non-working status of the Samsung Galaxy Young 2 postmarketOS bring-up.

Tested device:

- **Device:** Samsung Galaxy Young 2
- **Model:** SM-G130HN
- **Codename:** `samsung-young23g`
- **Architecture:** ARMv7
- **Kernel:** downstream Samsung/Spreadtrum 3.10.17
- **Userspace:** postmarketOS / Alpine Linux

The current state is best described as:

```text
Headless / early-framebuffer postmarketOS bring-up with USB RNDIS and SSH access.
```

---

## Short status summary

```text
Boots: yes
Linux userspace: yes
OpenRC: yes
Framebuffer output: yes, basic/early
USB RNDIS: yes
SSH over USB: yes
PTY over SSH: yes
Wi-Fi: not configured
Modem/calls/SMS/mobile data: not working/tested
Sound: not tested
Camera: not tested
Daily-driver usable: no
```

The most important milestone so far is that the phone can boot into a real postmarketOS/Alpine userspace and provide persistent root access over USB SSH.

---

## What currently works

### Kernel boot

The downstream Samsung/Spreadtrum kernel boots on the tested SM-G130HN device.

The currently used kernel is from the old Android/downstream kernel family for this device.

Verified running kernel example:

```text
Linux localhost 3.10.17-young2
```

This means the kernel is not the main blocker anymore for basic userspace bring-up.

---

### postmarketOS / Alpine root filesystem

The phone successfully boots into an Alpine/postmarketOS root filesystem.

Verified userspace version:

```text
Alpine Linux 3.24.0
```

The root filesystem is mounted from the old Android system partition:

```text
/dev/block/mmcblk0p18
```

This is the current postmarketOS rootfs target.

---

### `/sbin/init`

The system reaches `/sbin/init` inside the postmarketOS/Alpine root filesystem.

This was one of the most important early bring-up milestones.

The custom boot image does not simply boot a ramdisk and stop. It enters the real root filesystem and starts the normal Linux userspace init process.

---

### OpenRC

OpenRC starts.

The system reaches enough of the normal Alpine/postmarketOS boot process for OpenRC services and local startup scripts to run.

Some OpenRC services still fail, but OpenRC itself is working enough to continue development.

---

### Basic framebuffer output

Basic framebuffer output has been seen.

The device is no longer only a completely headless target.

However, this does not mean the graphical stack is finished.

Current display state:

```text
Basic framebuffer output: yes
Full graphical desktop/UI: no
Xfce: not working as a finished setup yet
Touchscreen UI: not finished
```

The display is still considered early and incomplete.

---

### USB RNDIS networking

USB RNDIS networking works.

The device can expose a USB network interface to the host computer using the old Android USB gadget sysfs interface:

```text
/sys/class/android_usb/android0
```

The phone-side network interface is:

```text
rndis0
```

Current phone IP:

```text
172.16.42.1
```

Current host-side IP:

```text
172.16.42.2
```

This USB network link is the main way to access the phone.

---

### SSH over USB

SSH works over the USB RNDIS network.

The current SSH server binary used is:

```text
/usr/sbin/sshd.pam
```

SSH listens on port:

```text
2222
```

Connection command from the host computer:

```sh
ssh -tt -p 2222 root@172.16.42.1
```

The `-tt` option is useful because the device needs a proper interactive PTY.

---

### PTY allocation

PTY allocation works after the boot-time device-node fixes.

Verified terminal:

```text
/dev/pts/0
```

This matters because SSH could previously authenticate but fail to provide an interactive shell when `/dev/pts` or `/dev/ptmx` was missing or incorrect.

Current status:

```text
SSH login: yes
Interactive shell: yes
PTY allocation: yes
```

---

### Persistent access after reboot

The current setup survives reboot and becomes reachable again over USB.

After rebooting the phone:

1. USB RNDIS comes back
2. the phone responds to ping at `172.16.42.1`
3. SSH starts again on port `2222`
4. PTY allocation works
5. an interactive root shell is available

This is a major milestone because it means the setup is no longer only a one-time manual debug session.

---

### Root shell over SSH

A root shell is available over SSH.

Verified example:

```text
uid=0(root)
```

This makes the device useful as a development target.

From this shell, it is possible to inspect the system, edit files, test services, check logs, run commands, and continue porting work.

---

## Partially working

### Display / framebuffer

The display situation is partially working.

What works:

- basic framebuffer output has been seen
- the device can show Linux-side output in some form

What is not finished:

- no polished graphical environment
- no finished Xfce setup
- no finished touch-driven UI
- no proper phone shell
- no reliable graphical daily use

The display should currently be treated as an early bring-up area.

---

### Boot process

The boot process works, but it is not clean yet.

The current setup uses a custom static `/init` inside the boot image.

That static init:

1. creates early device nodes
2. mounts the root filesystem from `/dev/block/mmcblk0p18`
3. prepares `/proc`
4. prepares `/sys`
5. prepares `/dev`
6. prepares `/dev/pts`
7. attempts `pivot_root`
8. falls back to `chroot`
9. executes `/sbin/init`

This works, but it is still a bring-up workaround.

A cleaner final port should eventually use a more normal packaged boot flow.

---

### USB networking setup on Windows

USB RNDIS works, but Windows-side configuration may need manual setup.

The host computer may need:

- the correct RNDIS driver selected
- the RNDIS adapter configured with `172.16.42.2`
- reconnect/reconfigure after unplugging or rebooting
- extra setup if sharing the host internet connection to the phone

This is usable for development, but not polished.

---

### Device node setup

Several important `/dev` nodes need boot-time repair.

The current scripts fix or recreate:

```text
/dev/random
/dev/urandom
/dev/zero
/dev/ptmx
/dev/pts
```

This is needed for SSH, entropy, and interactive terminal support.

The current fix works, but it should eventually be handled in a cleaner way.

---

## Not working yet

### Full graphical UI

A full graphical UI is not working yet.

Not currently finished:

- Xfce desktop as a usable phone display
- touch-driven graphical session
- postmarketOS phone shell
- reliable Xorg or Wayland setup
- normal graphical login/session handling

This is one of the biggest future goals.

---

### Wi-Fi

Wi-Fi is not configured.

Current status:

```text
Wi-Fi: not working/configured
```

NetworkManager currently does not work correctly, and Wi-Fi has not been brought up as a usable network interface.

---

### NetworkManager

NetworkManager is not working correctly yet.

This may be related to missing device support, broken services, dbus issues, incomplete kernel/userspace integration, or general bring-up state.

Current development access does not depend on NetworkManager because USB RNDIS is used instead.

---

### dbus

`dbus` is not cleanly working yet.

Some services that depend on dbus may fail or behave incorrectly.

This is expected for the current early bring-up stage.

---

### Sound

Sound is not tested.

Current status:

```text
Sound: not tested
```

No claim is made that speakers, microphone, audio routing, ALSA, PulseAudio, PipeWire, or call audio work.

---

### Camera

Camera is not tested.

Current status:

```text
Camera: not tested
```

No claim is made that the camera hardware works under postmarketOS.

---

### Modem, calls, SMS, and mobile data

Phone features are not working or not tested.

Current status:

```text
Calls: not working/tested
SMS: not working/tested
Mobile data: not working/tested
Modem: not working/tested
```

This bring-up should not be considered a usable phone system.

---

### Sensors

Sensors are not tested.

This includes things like:

- accelerometer
- proximity sensor
- light sensor
- vibration motor
- hardware buttons beyond basic boot/recovery use

No claim is made that these work.

---

### Power management

Power management is not finished.

Not currently verified:

- battery reporting
- charging status
- suspend
- resume
- thermal behavior
- CPU frequency scaling
- proper shutdown/reboot behavior beyond basic development use

This is important for any future daily use, but it is not solved yet.

---

## Current access method

The current recommended development access method is USB RNDIS + SSH.

Phone:

```text
172.16.42.1
```

Host:

```text
172.16.42.2
```

SSH port:

```text
2222
```

Connection command:

```sh
ssh -tt -p 2222 root@172.16.42.1
```

This is currently the most reliable way to work with the device.

---

## Verified commands

Useful commands that were verified from the running system include:

```sh
id
```

Expected result:

```text
uid=0(root)
```

```sh
tty
```

Expected result:

```text
/dev/pts/0
```

```sh
cat /etc/alpine-release
```

Expected result:

```text
3.24.0
```

```sh
ps | grep ssh
```

Expected result includes `sshd.pam` running as the SSH listener.

---

## Current practical use

Right now, the device is useful as:

- a real ARMv7 Linux development target
- a Samsung/Spreadtrum postmarketOS bring-up device
- a USB-connected SSH Linux box
- a platform for framebuffer experiments
- a platform for learning old Android device Linux boot flow
- a base for future display, touchscreen, Wi-Fi, and service work

It is not useful yet as:

- a normal smartphone
- a daily-driver postmarketOS device
- a reliable graphical handheld
- a phone for calls/SMS/mobile data
- a standalone Wi-Fi Linux device

---

## Main achievement

The main achievement so far is that the phone can boot real Linux userspace.

Earlier development was blocked by broken images, unreliable flashing paths, no usable shell, broken TWRP adb shell behavior, and no clear confirmation that postmarketOS userspace was actually running.

The current state proves:

```text
kernel boots
rootfs mounts
/sbin/init runs
OpenRC starts
USB networking works
SSH works
interactive root shell works
```

That is the point where the device becomes a real development target instead of only a flashing experiment.

---

## Current limitations

The biggest limitations right now are:

1. the graphical stack is not finished
2. Wi-Fi is not working
3. OpenRC services need cleanup
4. the boot process still uses a custom debug init
5. USB SSH setup depends on helper scripts
6. phone-specific hardware is not supported yet
7. the installation process is still manual

These are expected limitations for an early downstream-kernel device bring-up.

---

## Next goals

Important next goals:

- document the installation process
- clean up the boot image process
- clean up static init behavior
- improve `/dev` setup
- make USB RNDIS/SSH startup cleaner
- investigate framebuffer output
- try to bring up Xorg or another graphical stack
- test touchscreen input
- investigate Wi-Fi
- inspect failed OpenRC services
- test battery reporting
- test shutdown and reboot behavior
- document recovery steps
- make the port easier to reproduce

---

## Final status statement

It boots into Alpine/postmarketOS userspace, starts OpenRC, brings up USB RNDIS, starts SSH, and provides an interactive root shell over USB.

It is not a daily driver and not a finished phone port, but it is a successful development foothold for further work.