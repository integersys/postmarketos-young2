#!/usr/bin/env python3
"""young2-volume.py - physical volume-button policy for the Young 2 (SM-G130HN).

WHY THIS EXISTS
  The volume keys are on the keypad matrix (arch/arm/mach-sc/board-young2.c:394
  KEY(0,0,KEY_VOLUMEUP) / :395 KEY(1,0,KEY_VOLUMEDOWN)) and the driver reports
  them as ordinary input events on /dev/input/event0. Nothing in this userspace
  acted on them, so the buttons did nothing.

WHY NOT XFCE
  xfsettingsd is running but has NO volume bindings, there is no xfce4-volumed,
  and this image uses plain ALSA (no PulseAudio/PipeWire). Wiring the keys
  through XFCE would mean pulling in a sound server and risking the working
  audio stack, so the policy lives here instead - exactly one owner.

THE MIXER
  Card 0 (`sprdphone`). The proven speaker route (51-audio-route.start) sets
  'SPKL Playback Volume' and 'SPKR Playback Volume' to 8; those two controls are
  the speaker amplifier gain and are what actually change the audible level.
  Their real range is **0-15** (16 steps). DACL/DACR (0-7) are the DAC stage and
  are deliberately left at the route's value of 4 so the existing route is not
  disturbed.

  Both SPKL and SPKR must be written - they are separate (joined-mono) controls.

NO KERNEL KEY REPEAT
  The keypad does NOT emit value=2 repeat events: a 7-second hold produced only
  press+release. Holding a key is therefore repeated by this daemon.

OSD
  xfce4-notifyd + notify-send, using a fixed replacement id and the
  `int:value` hint so repeated presses UPDATE one popup instead of stacking.

USAGE
  young2-volume.py [--foreground]
"""

import os
import re
import select
import struct
import subprocess
import sys
import threading
import time

# ---------------------------------------------------------------- configuration
CARD = 0
# NOTE: amixer uses TWO different name forms for the same control -
#   `sget`  takes the SIMPLE control name  -> "SPKL"
#   `cset name=` takes the FULL control name -> "SPKL Playback Volume"
# Using the wrong form gives "Unable to find simple control 'SPKL Playback Volume'".
SGET_NAME = "SPKL"
CSET_NAMES = ("SPKL Playback Volume", "SPKR Playback Volume")

# The speaker chain is:  PCM -> DACL/DACR (digital, 0-7) -> SPKL/SPKR (analog amp, 0-15)
#                                                       -> Speaker
#
# MEASURED behaviour (confirmed by ear with a 440 Hz tone):
#   SPKL/SPKR = 0            -> quieter but STILL AUDIBLE  (the amp floor is -24 dB)
#   Speaker Mute = on        -> quieter but STILL AUDIBLE
#   DACL/DACR = 0            -> COMPLETELY SILENT
# so the DAC stage is what actually reaches silence. SPKL/SPKR has by far the
# wider, smoother range (-24 dB .. +21 dB in 3 dB steps) so it carries the volume
# curve; the DAC is dropped to 0 only at 0% to give a real mute.
#
# The proven route (51-audio-route.start) uses DAC=4 and SPK=8, and 8 = 0.00 dB
# (unity). 9-15 amplify ABOVE unity up to +21 dB, which is not the "existing safe
# maximum", so the scale deliberately stops at 8.
MIX_MAX = 8                     # safe maximum for SPKL/SPKR (0.00 dB)
LEVELS = MIX_MAX                # 9 logical steps -> 0..100% in 12.5% steps
DAC_NAMES = ("DACL Playback Volume", "DACR Playback Volume")
DAC_NORMAL = 4                  # the route's DAC value, restored above 0%
DAC_MUTE = 0                    # proven to give true silence

EVENT_DEV = "/dev/input/event0"  # sci-keypad - see the module docstring
EVENT_FMT = "llHHi"
EVENT_SIZE = struct.calcsize(EVENT_FMT)
EV_KEY = 0x01
KEY_VOLUMEDOWN = 114
KEY_VOLUMEUP = 115

HOLD_DELAY = 0.55               # s before a held key starts repeating
HOLD_RATE = 0.18                # s between repeats while held
NOTIFY_ID = 997                 # fixed id -> the OSD is replaced, not stacked
OSD_MS = 1600

LOG = "/var/log/young2-volume.log"
GUI = "/usr/local/bin/start-young2-gui"


def log(msg):
    try:
        with open(LOG, "a") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except OSError:
        pass


# ------------------------------------------------------------------- the mixer
def mixer_get():
    """Return the current SPKL value (0..MIX_MAX), or None.

    Uses the SIMPLE control name - `amixer sget SPKL`, not
    `amixer sget 'SPKL Playback Volume'` (which fails).
    """
    try:
        out = subprocess.run(["amixer", "-c", str(CARD), "sget", SGET_NAME],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             timeout=5).stdout.decode()
    except Exception as e:
        log("amixer sget failed: %s" % e)
        return None
    m = re.search(r"(?:Mono|Front Left):\s*Playback\s+(\d+)", out)
    if not m:
        m = re.search(r"Playback\s+(\d+)\s*\[", out)
    return int(m.group(1)) if m else None


def _cset(name, value):
    try:
        subprocess.run(["amixer", "-c", str(CARD), "cset", "name=%s" % name, str(value)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return True
    except Exception as e:
        log("amixer cset %s failed: %s" % (name, e))
        return False


def mixer_set(value):
    """Set the volume.

    SPKL/SPKR carry the level. At 0 the DAC is dropped to 0 as well, because
    SPKL=0 alone (-24 dB) is still audible - only the DAC reaches true silence.
    Returns the read-back SPKL value.
    """
    value = max(0, min(MIX_MAX, int(value)))
    for c in CSET_NAMES:
        _cset(c, value)
    dac = DAC_MUTE if value == 0 else DAC_NORMAL
    for c in DAC_NAMES:
        _cset(c, dac)
    return mixer_get()


def to_percent(v):
    if v is None:
        return None
    return int(round(v * 100.0 / LEVELS))


def percent_to_mix(pct):
    return max(0, min(MIX_MAX, int(round(pct * LEVELS / 100.0))))


# ----------------------------------------------------------------------- the OSD
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


def osd_icon(pct):
    if pct <= 0:
        return "audio-volume-muted"
    if pct < 34:
        return "audio-volume-low"
    if pct < 67:
        return "audio-volume-medium"
    return "audio-volume-high"


def show_osd(pct):
    """One popup, updated in place via a fixed replacement id."""
    if pct is None:
        return
    if pct <= 0:
        text = "Muted"
    else:
        text = "%d%%" % pct
    try:
        subprocess.run(["notify-send",
                        "-r", str(NOTIFY_ID),
                        "-h", "int:value:%d" % pct,
                        "-i", osd_icon(pct),
                        "-t", str(OSD_MS),
                        "Volume", text],
                       env=session_env(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=5)
    except FileNotFoundError:
        log("notify-send not installed - no OSD")
    except Exception as e:
        log("notify-send failed: %s" % e)


# ------------------------------------------------------------------ the policy
class Volume(object):
    def __init__(self):
        self.lock = threading.Lock()

    def step(self, direction):
        """direction +1 or -1. Returns the new percentage, or None on failure."""
        with self.lock:
            cur = mixer_get()
            if cur is None:
                return None
            new = max(0, min(MIX_MAX, cur + direction))       # clamp, no wrap
            if new == cur:
                # already at the end - still show the OSD so the user sees why
                pct = to_percent(cur)
                log("VOL %s at limit (%d = %d%%)" % ("+" if direction > 0 else "-",
                                                     cur, pct))
                show_osd(pct)
                return pct
            back = mixer_set(new)
            pct = to_percent(back if back is not None else new)
            log("KEY_VOLUME%s: mixer %d -> %d  OSD %s"
                % ("UP" if direction > 0 else "DOWN", cur,
                   back if back is not None else new,
                   "MUTED" if pct == 0 else "%d%%" % pct))
            show_osd(pct)
            return pct


VOL = Volume()


def repeat_worker(direction, stop_evt):
    """Holding a key: wait HOLD_DELAY, then repeat until the key is released."""
    if stop_evt.wait(HOLD_DELAY):
        return
    while not stop_evt.is_set():
        VOL.step(direction)
        if stop_evt.wait(HOLD_RATE):
            return


# ---------------------------------------------------------------- the event loop
def run():
    if "--foreground" not in sys.argv:
        if os.fork() != 0:
            os._exit(0)
        os.setsid()
        if os.fork() != 0:
            os._exit(0)

    log("=== young2-volume started (pid %d) ===" % os.getpid())

    while True:
        try:
            fd = os.open(EVENT_DEV, os.O_RDONLY)
        except OSError as e:
            log("cannot open %s (%s) - retrying in 10s" % (EVENT_DEV, e))
            time.sleep(10)
            continue

        stop_evt = None
        held = None
        try:
            while True:
                r, _, _ = select.select([fd], [], [], 30)
                if not r:
                    continue
                try:
                    data = os.read(fd, EVENT_SIZE * 64)
                except OSError as e:
                    log("read error (%s) - reopening device" % e)
                    break
                for i in range(0, len(data) - EVENT_SIZE + 1, EVENT_SIZE):
                    try:
                        _s, _u, etype, code, value = struct.unpack(
                            EVENT_FMT, data[i:i + EVENT_SIZE])
                    except struct.error:
                        log("malformed event - skipped")
                        continue
                    if etype != EV_KEY or code not in (KEY_VOLUMEUP, KEY_VOLUMEDOWN):
                        continue

                    direction = 1 if code == KEY_VOLUMEUP else -1
                    if value == 1:                          # press
                        if held is not None:
                            continue                        # already holding
                        held = code
                        VOL.step(direction)                 # act immediately
                        stop_evt = threading.Event()
                        threading.Thread(target=repeat_worker,
                                         args=(direction, stop_evt),
                                         daemon=True).start()
                    elif value == 0:                        # release
                        held = None
                        if stop_evt is not None:
                            stop_evt.set()
                            stop_evt = None
        finally:
            if stop_evt is not None:
                stop_evt.set()
            try:
                os.close(fd)
            except OSError:
                pass


run()
