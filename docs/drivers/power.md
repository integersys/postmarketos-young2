# Power, charging and suspend

The vendor kernel uses Android wakelocks and earlysuspend. I tested battery
reporting, real suspend-to-RAM, power-key wake, session preservation, shutdown and
reboot separately; turning the screen off is not proof of deep sleep.

## Battery and desktop integration

The power_supply class exposes battery/charger state through the board's
Spreadtrum power drivers (`drivers/power/`, including the sprd battery path).
UPower reads it and XFCE Power Manager supplies the normal tray indicator.
Recorded tests showed charging/full states on external power and discharging
percentage, voltage and temperature on battery. Capacity fell from 97% to 93%
during a battery test. `energy_full` is unavailable, so there is no credible
time-remaining estimate. USB `current_now` did not provide a useful draw measurement.

`xfce4-power-manager`, `pm-utils`, polkit and `xrefresh` were used. Without
`pm-is-supported` from pm-utils, XFCE reported suspend unavailable. The physical
power-button, sleep-button and hibernate-button actions in xfconf are set to 0;
the separate daemon owns the physical key. Automatic idle suspend stays disabled.

## Suspend and wake policy

[young2-powerkey.py](../../userspace/power/young2-powerkey.py) reads KEY_POWER 116
and writes `mem` or `on` to `/sys/power/state`. A one-byte framebuffer read probes
the actual earlysuspend state: fb_read returns EPERM while suspended. This replaced
a cached-state design that could perform suspend and wake from the same physical
press, then desynchronize after charger wakes. A 1.5-second debounce prevents
duplicate actions; a press held at least six seconds is ignored by this policy.

On wake the daemon reasserts `FBIOPAN_DISPLAY` with yoffset 0 and invokes
`xrefresh`. It also does a boot-time scanout repair from its own thread; a
background local.d attempt did not survive service cleanup. Startup is
[60-young2-powerkey.start](../../userspace/power/60-young2-powerkey.start).

The [sprdfb resume patch](../../linux-samsung-young23g/patches/0002-sprdfb-resume.patch)
prevents Xorg's saved mode from being rejected in EnterVT. It was validated in
kernel #8 and retained in later builds. This patch and userspace scanout repair
solve different parts of restoring the same session.

## Physical tests

October 6–7 tests recorded repeated `sprd_pm_deepsleep`, positive `deep_sus`,
`dep_fail=0` and power-key wake. Xorg, xfce4-session and panel remained the same
running session. Wi-Fi stayed associated, Bluetooth transport stayed up and
later sensor/volume/front-key tasks repeated suspend cycles. Wake sources included
the keypad, GPIO/EIC and VBUS. GUI Suspend, Shut Down and Restart were physically
tested; automatic desktop startup was rechecked after reboot and power-on.

The `usb_work` wakelock stays held while the USB gadget is active. With RNDIS/USB
connected, a suspend request can reach only earlysuspend/screen-off. Battery-only
tests established actual deep sleep; preserve a Wi-Fi access path when testing it.

## Current limits

- DPMS unblank is not covered by the power-key repair and can restore stale white
  scanout. The later front-key task disabled both X DPMS and the XFCE DPMS policy.
- A brief panel-init white flash remains even with wake repair.
- VBUS can power the phone back into Samsung offline charging (`lpcharge=1`)
  immediately after a genuine shutdown. It stayed off with the cable removed.
- There is no exposed RTC wakealarm or pm_test interface.
- Kernel #10's KPLED experiment warns during LED writes/resume. #11 reverts that
  address change, but was only built, not separately flashed.
- Later deep-sleep sequences produced DISPC sync timeouts and a roughly four-minute
  reboot. A fresh boot cleared them; repeated-cycle robustness is still limited.

The [installation map](../../userspace/INSTALL.md) gives the exact helper paths
and the DPMS settings needed by this setup.
