#!/usr/bin/env python3
"""young2-powerkey.py - power-button policy for the Samsung Young 2 (young23g).

WHY THIS EXISTS
  This kernel uses Android's wakelock/earlysuspend power model. Writing "mem" to
  /sys/power/state only *requests* suspend, and NOTHING in this userspace ever
  clears the suspended state again. On Android that job belongs to
  PowerManagerService. `request_suspend_state()` has exactly ONE caller in this
  kernel - the /sys/power/state write - so userspace must own the policy.

WHAT IT DOES
  Watches /dev/input/event0 (sci-keypad) and on a SHORT KEY_POWER press:
      display suspended -> write "on"   (wake, and stop the re-suspend loop)
      display running   -> write "mem"  (suspend)

HOW IT DECIDES (this is the important part)
  It does NOT trust a cached state file. The sprd framebuffer is put into
  FBINFO_STATE_SUSPENDED by sprdfb_early_suspend() and cleared by
  sprdfb_late_resume(); fb_read() returns -EPERM while that is set, so a 1-byte
  read of /dev/fb0 is a kernel-backed probe of the REAL display state. That
  survives wakes the daemon never saw - e.g. a VBUS / charger wake, which
  produces no input event at all and used to leave a cached state file lying.

DEBOUNCE
  One physical press has been observed to deliver more than one press/release
  pair, which made the old daemon do "mem" and then "on" in the same second and
  left the display off. Actions closer together than DEBOUNCE_S are ignored.

LONG PRESS
  A press held >= LONG_PRESS_S is ignored, so the kernel/hardware behaviour is
  untouched. No custom forced-shutdown is invented here.

USAGE
  young2-powerkey.py [--foreground]     (default: daemonise)
"""

import os
import select
import struct
import subprocess
import sys
import time

EVENT_DEV = "/dev/input/event0"      # sci-keypad
EVENT_FMT = "llHHi"                  # 32-bit ARM struct input_event
EVENT_SIZE = struct.calcsize(EVENT_FMT)
EV_KEY = 0x01
KEY_POWER = 116

DEBOUNCE_S = 1.5                     # ignore a 2nd action this soon after the last
LONG_PRESS_S = 6.0                   # >= this is ignored entirely
GUI = "/usr/local/bin/start-young2-gui"
LOG = "/var/log/young2-powerkey.log"
STATE_POWER = "/sys/power/state"
FB = "/dev/fb0"


def log(msg):
    try:
        with open(LOG, "a") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except OSError:
        pass


def display_suspended():
    """Kernel-backed probe: is the sprd framebuffer currently suspended?

    fb_read() returns -EPERM while fb->state == FBINFO_STATE_SUSPENDED, which
    sprdfb_early_suspend() sets and sprdfb_late_resume() clears.
    """
    try:
        fd = os.open(FB, os.O_RDONLY)
    except OSError as e:
        log("probe: cannot open %s (%s) -> assuming suspended" % (FB, e))
        return True
    try:
        os.read(fd, 1)
        return False                 # readable -> RUNNING
    except OSError:
        return True                  # EPERM -> SUSPENDED
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def set_power(word):
    try:
        with open(STATE_POWER, "w") as f:
            f.write(word)
        return True
    except OSError as e:
        log("FAILED to write %r to %s: %s" % (word, STATE_POWER, e))
        return False


def xorg_alive():
    try:
        return subprocess.run(["pgrep", "-f", "Xorg :0"],
                              stdout=subprocess.DEVNULL, timeout=5).returncode == 0
    except Exception:
        return True                  # assume alive; never make things worse


def session_env():
    """DISPLAY + the XFCE session's D-Bus address, for tools run from outside it."""
    env = dict(os.environ)
    env["DISPLAY"] = ":0"
    try:
        pid = subprocess.run(["pgrep", "-f", "xfce4-session"],
                             stdout=subprocess.PIPE, timeout=5).stdout.split()[0]
        with open("/proc/%s/environ" % pid.decode()) as f:
            for kv in f.read().split("\0"):
                if kv.startswith("DBUS_SESSION_BUS_ADDRESS="):
                    env["DBUS_SESSION_BUS_ADDRESS"] = kv.split("=", 1)[1]
    except Exception:
        pass
    return env


def reassert_scanout():
    """Re-issue FBIOPAN_DISPLAY with yoffset 0.

    The panel scans out one of TWO 320x480 pages selected by yoffset. The
    framebuffer CONTENT survives a deep sleep intact, but the controller's
    scanout address can come back stale - which shows a white/uninitialised
    page even though /dev/fb0 holds a perfectly good image. Re-asserting the
    pan is the cheap fix.
    """
    try:
        import fcntl
        import struct
        FBIOGET_VSCREENINFO = 0x4600
        FBIOPAN_DISPLAY = 0x4606
        fd = os.open(FB, os.O_RDWR)
        try:
            buf = bytearray(160)
            fcntl.ioctl(fd, FBIOGET_VSCREENINFO, buf, True)
            yo = struct.unpack_from("<I", buf, 20)[0]
            struct.pack_into("<I", buf, 16, 0)      # xoffset
            struct.pack_into("<I", buf, 20, 0)      # yoffset -> first page
            fcntl.ioctl(fd, FBIOPAN_DISPLAY, buf, True)
            log("  scanout re-asserted (was yoffset=%d, now 0)" % yo)
        finally:
            os.close(fd)
    except OSError as e:
        log("  scanout re-assert failed: %s" % e)


def force_repaint():
    """Ask X to repaint everything (xrefresh if present)."""
    try:
        subprocess.run(["xrefresh", "-white"], env=session_env(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=10)
        log("  xrefresh issued")
    except FileNotFoundError:
        log("  xrefresh not installed - skipping repaint")
    except Exception as e:
        log("  xrefresh failed: %s" % e)


def ensure_gui():
    if not xorg_alive():
        log("Xorg is gone after resume - restarting the GUI stack")
        try:
            subprocess.run([GUI, "start"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=120)
            log("GUI restart finished")
        except Exception as e:
            log("GUI restart failed: %s" % e)
        return
    reassert_scanout()
    force_repaint()


def do_action(reason):
    """One short press -> one action, chosen from the REAL display state."""
    suspended = display_suspended()
    log("action (%s): display_suspended=%s -> writing %r"
        % (reason, suspended, "on" if suspended else "mem"))
    if suspended:
        if set_power("on"):
            # Re-assert the scanout and repaint as EARLY as possible: the panel
            # comes back showing an uninitialised (white) page for a moment
            # otherwise. Both are cheap and idempotent.
            reassert_scanout()
            time.sleep(0.4)
            ensure_gui()
            log("  wake done, display_suspended=%s" % display_suspended())
    else:
        set_power("mem")


def boot_display_fix():
    """Re-latch the scanout once, shortly after boot.

    The sprd framebuffer is 320x960 - TWO 320x480 pages - and the panel scans out
    whichever page the controller's scanout address points at. After a BOOT that
    address can be stale, so the panel shows the uninitialised (all-white) page
    even though /dev/fb0 already holds a good image. fb_var_screeninfo keeps
    reporting yoffset=0 throughout, so only re-issuing FBIOPAN_DISPLAY re-latches
    it. Observed symptom before this: the screen stayed WHITE at boot until the
    user pressed POWER.

    This lives in the daemon (not local.d) because local.d backgrounds the helper
    and the job is reaped when the `local` service finishes.
    """
    log("boot: waiting for /dev/fb0 and Xorg before the display fix")
    for i in range(0, 150, 2):
        if os.path.exists(FB):
            break
        time.sleep(2)
    for i in range(0, 150, 2):
        if xorg_alive():
            break
        time.sleep(2)
    time.sleep(4)                      # let X finish its initial paint
    reassert_scanout()
    force_repaint()
    log("boot: display fix done")


def main():
    if "--foreground" not in sys.argv:
        if os.fork() != 0:
            os._exit(0)
        os.setsid()
        if os.fork() != 0:
            os._exit(0)

    log("=== young2-powerkey started (pid %d) ===" % os.getpid())

    # one-shot boot-time display fix, in its own thread so key handling starts now
    try:
        import threading
        threading.Thread(target=boot_display_fix, daemon=True).start()
    except Exception as e:
        log("could not start the boot display fix thread: %s" % e)

    last_action = 0.0

    while True:
        try:
            fd = os.open(EVENT_DEV, os.O_RDONLY)
        except OSError as e:
            log("cannot open %s (%s) - retrying in 10s" % (EVENT_DEV, e))
            time.sleep(10)
            continue

        press_at = None
        try:
            while True:
                r, _, _ = select.select([fd], [], [], 30)
                if not r:
                    continue
                data = os.read(fd, EVENT_SIZE * 64)
                now = time.time()
                acted_this_burst = False
                for i in range(0, len(data) - EVENT_SIZE + 1, EVENT_SIZE):
                    _s, _u, etype, code, value = struct.unpack(
                        EVENT_FMT, data[i:i + EVENT_SIZE])
                    if etype != EV_KEY or code != KEY_POWER:
                        continue
                    log("EVENT KEY_POWER value=%d" % value)
                    if value == 1:                          # press
                        press_at = now
                    elif value == 0:                        # release
                        if press_at is None:
                            log("  release with no press - ignored")
                            continue
                        held = now - press_at
                        press_at = None
                        if held >= LONG_PRESS_S:
                            log("  long press (%.1fs) - ignored" % held)
                            continue
                        # ONE action per read burst: a single physical press has
                        # been observed to deliver several press/release pairs in
                        # one go, and acting twice left the display off.
                        if acted_this_burst:
                            log("  DUPLICATE in same burst - ignored")
                            continue
                        since = now - last_action
                        if since < DEBOUNCE_S:
                            log("  DEBOUNCED (%.2fs since last action) - ignored" % since)
                            continue
                        acted_this_burst = True
                        last_action = now
                        do_action("short press %.2fs" % held)
        except OSError as e:
            log("event read error: %s - reopening" % e)
            time.sleep(2)
        finally:
            try:
                os.close(fd)
            except OSError:
                pass


main()
