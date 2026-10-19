#!/usr/bin/env python3
"""young2-frontkeys.py - front-control policy + capacitive key backlight for the Young 2.

THE THREE CONTROLS (all measured, not guessed)
  HOME    (centre, physical)   sci-keypad   /dev/input/event0   KEY_HOME      102
  BACK    (right, capacitive)  ist30xx_ts   /dev/input/event1   KEY_BACK      158
  RECENT  (left, capacitive)   ist30xx_ts   /dev/input/event1   keycode       254  (KEY_RECENT)

  They are on TWO different devices - Home is on the keypad matrix, Back/Recent come
  from the touchscreen controller. The live touchscreen driver is ist30xxb
  (CONFIG_TOUCHSCREEN_IST30XXB=y); ist30xx is NOT built, so its ist30xx_key_code[]
  table is not what runs. The ts-xlate uinput device (event4, what X reads) MIRRORS
  Back/Recent, so this daemon reads the RAW devices (event0/event1) and never the
  translator, avoiding a duplicate action.

ACTIONS (all use native XFCE/X11 mechanisms - nothing fake)
  HOME   -> wmctrl -k on                 EWMH "show desktop"; apps stay open
  RECENT -> xdotool key alt+Tab          xfwm4's OWN task switcher (see note below)
  BACK   -> xdotool key alt+Left         the desktop-standard "go back"; verified in NetSurf
                                         (PAGE-B -> PAGE-A). Deliberately ONE shortcut, not a
                                         shotgun of fallbacks, and NOT "close window".

  NOTE: `xfce4-popup-windowmenu` was the first choice for RECENT but it FAILS on this image
  (rc=1, even run by hand - it wants the panel's window-menu plugin).  alt+Tab is handled by
  xfwm4 itself and is verified working.  XF86Back/BackSpace do NOT navigate NetSurf.

THE BACKLIGHT
  /sys/class/leds/keyboard-backlight/brightness   (0-255, 16 hardware steps)
  Driver: drivers/leds/leds-sprd-kb.c (KPLED). It registers an early_suspend handler,
  so the kernel already turns the LEDs off on suspend - this daemon additionally forces
  them off before a suspend so a pending timeout cannot re-light them.

  NOTE: on this board the capacitive symbols are NOT on the KPLED rail, so the
  backlight is written but nothing lights. The mechanism is kept because it is correct
  and harmless; use `light off` to stop the writes entirely.

  One timer thread serves every press: a new press simply resets the deadline.

CLI (the daemon is a separate process, so these write small state files that the
daemon polls - see MODE_FILE / STATE)
  young2-frontkeys.py status
  young2-frontkeys.py light on|off|auto
  young2-frontkeys.py timeout <seconds>
"""

import os
import select
import struct
import subprocess
import sys
import threading
import time

# ------------------------------------------------------------------ the controls
DEV_HOME = ("/dev/input/event0", "sci-keypad")
DEV_TS = ("/dev/input/event1", "ist30xx_ts")
KEY_HOME = 102
KEY_BACK = 158
KEY_RECENT = 254

EVENT_FMT = "llHHi"
EVENT_SIZE = struct.calcsize(EVENT_FMT)
EV_KEY = 0x01

LED = "/sys/class/leds/keyboard-backlight/brightness"
LED_MAX = 255

LOG = "/var/log/young2-frontkeys.log"
# Persisted so `light ...` / `timeout ...` survive a reboot. /run is tmpfs and would
# forget them; /var/lib is on the rootfs.
STATE = "/var/lib/young2-frontkeys.timeout"
MODE_FILE = "/var/lib/young2-frontkeys.mode"

DEFAULT_TIMEOUT = 2.0
LIGHT_MODES = ("auto", "on", "off")


def log(msg):
    try:
        with open(LOG, "a") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except OSError:
        pass


def _read_text(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


def _write_text(path, text):
    try:
        with open(path, "w") as f:
            f.write(text)
        return True
    except OSError:
        return False


# ------------------------------------------------------------------------ the LED
def led_write(value):
    try:
        with open(LED, "w") as f:
            f.write(str(int(value)))
        return True
    except OSError as e:
        log("LED write failed: %s" % e)
        return False


class Backlight(object):
    """One timer thread for every front-key press.

    The CLI runs in a SEPARATE process, so it cannot touch this object. It writes
    MODE_FILE / STATE instead, and the thread below polls them. That is what makes
    `light ...` and `timeout ...` actually take effect on the running daemon (the
    first version of this file mutated its own local object and did nothing).
    """

    def __init__(self):
        self.timeout = DEFAULT_TIMEOUT
        t = _read_text(STATE).strip()
        if t:
            try:
                v = float(t)
                if v > 0:
                    self.timeout = v
            except ValueError:
                pass
        m = _read_text(MODE_FILE).strip()
        self.mode = m if m in LIGHT_MODES else "auto"
        self.deadline = 0.0
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        last_mode = self.mode
        last_timeout = self.timeout
        while True:
            # --- pick up changes made by the CLI ---
            mode = _read_text(MODE_FILE).strip()
            if mode in LIGHT_MODES and mode != last_mode:
                last_mode = mode
                log("CLI: light -> %s" % mode)
                self.set_mode(mode)
            tmo = _read_text(STATE).strip()
            if tmo:
                try:
                    t = float(tmo)
                except ValueError:
                    t = 0.0
                if t > 0 and t != last_timeout:
                    last_timeout = t
                    log("CLI: timeout -> %ss" % t)
                    with self.cv:
                        self.timeout = t
                        if self.deadline:
                            self.deadline = time.time() + t
                        self.cv.notify()

            # --- the single timeout ---
            fire = False
            with self.cv:
                if self.mode == "auto" and self.deadline:
                    left = self.deadline - time.time()
                    if left <= 0:
                        self.deadline = 0.0
                        fire = True
                    else:
                        self.cv.wait(min(left, 0.5))
                else:
                    self.cv.wait(0.5)
            if fire:
                led_write(0)
                log("LED off (timeout)")

    def pulse(self):
        """A front key was used: light up and (re)start the single timeout."""
        if self.mode == "off":
            return
        led_write(LED_MAX)
        if self.mode == "on":
            return
        with self.cv:
            self.deadline = time.time() + self.timeout
            self.cv.notify()

    def force_off(self):
        """Called before suspend: no glow through sleep, and no pending re-light."""
        with self.cv:
            self.deadline = 0.0
            self.cv.notify()
        led_write(0)

    def set_mode(self, mode):
        if mode not in LIGHT_MODES:
            return False
        with self.cv:
            self.mode = mode
            self.deadline = 0.0
            self.cv.notify()
        if mode == "on":
            led_write(LED_MAX)
        else:
            led_write(0)
        return True


# --------------------------------------------------------------------- X helpers
def session_env():
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


def run_cmd(argv, what):
    try:
        rc = subprocess.run(argv, env=session_env(), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=10).returncode
        log("%s -> rc=%d" % (what, rc))
    except FileNotFoundError:
        log("%s -> MISSING binary %s" % (what, argv[0]))
    except Exception as e:
        log("%s -> failed: %s" % (what, e))


def act_home():
    run_cmd(["wmctrl", "-k", "on"], "HOME: show desktop (wmctrl -k on)")


def act_recent():
    # xfce4-popup-windowmenu FAILS on this image (rc=1, even run by hand) - it needs the
    # panel's window-menu plugin.  alt+Tab is xfwm4's OWN task switcher, which is both
    # more native and actually works (verified: the active window changes).
    run_cmd(["xdotool", "key", "--clearmodifiers", "alt+Tab"],
            "RECENT: xfwm4 task switcher (alt+Tab)")


def act_back():
    run_cmd(["xdotool", "key", "--clearmodifiers", "alt+Left"],
            "BACK: xdotool key alt+Left")


# ------------------------------------------------------------------ the main loop
def serve(light):
    fds = {}
    for path, name in (DEV_HOME, DEV_TS):
        try:
            fds[os.open(path, os.O_RDONLY)] = (path, name)
        except OSError as e:
            log("cannot open %s (%s)" % (path, e))
    if not fds:
        return False

    held = set()
    while True:
        try:
            r, _, _ = select.select(list(fds), [], [], 30)
            for fd in r:
                path, name = fds[fd]
                try:
                    data = os.read(fd, EVENT_SIZE * 64)
                except OSError as e:
                    log("read error on %s (%s) - restarting" % (path, e))
                    return False
                for i in range(0, len(data) - EVENT_SIZE + 1, EVENT_SIZE):
                    try:
                        _s, _u, etype, code, value = struct.unpack(
                            EVENT_FMT, data[i:i + EVENT_SIZE])
                    except struct.error:
                        continue
                    if etype != EV_KEY:
                        continue
                    if code not in (KEY_HOME, KEY_BACK, KEY_RECENT):
                        continue

                    if value == 2:                      # repeat - ignore entirely
                        continue
                    if value == 1:                      # press
                        if code in held:
                            continue
                        held.add(code)
                        light.pulse()
                        if code == KEY_HOME:
                            act_home()
                        elif code == KEY_RECENT:
                            act_recent()
                        else:
                            act_back()
                    elif value == 0:                    # release
                        held.discard(code)
        except Exception as e:
            log("loop error: %s" % e)
            time.sleep(1)


def _daemon_running():
    try:
        out = subprocess.run(["pgrep", "-fc", "young2-frontkeys.py"],
                             stdout=subprocess.PIPE, timeout=5).stdout.decode().strip()
        return out not in ("", "0")
    except Exception:
        return False


def cli(argv):
    """Runs in a short-lived process; talks to the daemon via MODE_FILE / STATE."""
    if len(argv) < 2 or argv[1] == "status":
        mode = _read_text(MODE_FILE).strip() or "auto"
        tmo = _read_text(STATE).strip() or str(DEFAULT_TIMEOUT)
        led = _read_text(LED).strip() or "?"
        print("frontkeys: light=%s timeout=%ss led=%s daemon=%s" % (
            mode, tmo, led, "running" if _daemon_running() else "not running"))
        return 0

    cmd = argv[1]
    if cmd == "light" and len(argv) >= 3:
        if argv[2] not in LIGHT_MODES:
            print("light %s: bad mode (want auto|on|off)" % argv[2])
            return 1
        _write_text(MODE_FILE, argv[2])
        led_write(LED_MAX if argv[2] == "on" else 0)   # immediate feedback
        print("light %s: ok" % argv[2])
        return 0
    if cmd == "timeout" and len(argv) >= 3:
        try:
            t = float(argv[2])
        except ValueError:
            t = 0.0
        if t <= 0:
            print("timeout: bad value (want > 0 seconds)")
            return 1
        _write_text(STATE, str(t))
        print("timeout: ok (%ss)" % t)
        return 0
    print(__doc__)
    return 1


def main():
    # CLI mode: exit before the daemon thread is started.
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv))

    if os.fork() != 0:
        os._exit(0)
    os.setsid()
    if os.fork() != 0:
        os._exit(0)

    # Start the backlight (and its timer thread) AFTER the fork.  A thread does NOT
    # survive fork(): the child has only the thread that called fork, so building
    # Backlight() before daemonising left the timeout thread dead - the LEDs lit on a
    # press and then stayed on forever, and the CLI's mode/timeout files were never
    # polled.
    light = Backlight()

    log("=== young2-frontkeys started (pid %d) mode=%s timeout=%ss ==="
        % (os.getpid(), light.mode, light.timeout))

    # The LEDs must start DARK unless the persisted mode says otherwise. Without
    # this the daemon inherits whatever the backlight was left at (e.g. from a
    # manual sysfs test) and, because the timeout only starts on a press, it would
    # glow forever.
    if light.mode == "on":
        led_write(LED_MAX)
    else:
        led_write(0)

    while True:
        if not serve(light):
            time.sleep(3)


main()
