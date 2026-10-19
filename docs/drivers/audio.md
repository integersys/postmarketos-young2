# Audio: Spreadtrum VBC r2p0 and codec v3

I verified the built-in speaker and built-in microphone with the existing
Spreadtrum ALSA stack. A missing `/dev/snd` directory initially hid functional
kernel devices; this was a userspace node/routing problem.

## Kernel and interfaces

Card 0 is `sprdphone`, bound to `vbc-r2p0-sprd-codec-v3`. Its HiFi PCM is
`hw:0,0` for playback and capture. Other cards are `VIRTUALAUDIOW`, `saudiovoip`
and `alli2s`; their registration does not prove call or external-I²S operation.
The source lives under `sound/soc/sprd/`, including the VBC r2p0/codec-v3 machine
links and codec driver. The config enables the corresponding SND/SOC/SPRD paths.

There are 104 live mixer controls. Control names recovered from the device's
Android routing reference matched the live mixer; no Android audio HAL is needed
for these direct ALSA routes.

## Persistent routing

[50-snd-nodes.start](../../userspace/audio/50-snd-nodes.start) creates nodes from
sysfs. [51-audio-route.start](../../userspace/audio/51-audio-route.start) applies
the demonstrated amixer route at boot. Dependencies are `alsa-utils` and the
existing kernel sound devices; no custom UCM profile or sound server is supplied.

Playback uses DACL/DACR gain 4, SPKL/SPKR gain 8, both SPKL DAC mixer switches,
Speaker Function on and Speaker Mute off. Capture uses MainMIC to ADCL/ADCR,
Mic Function and bias enabled, ADC gain 63, MIC Boost 3 and VBC digital gain 60.
Do not raise the capture digital gain above 63: tested values 100/127 made the
capture path effectively silent despite the driver advertising a larger range.

The [volume daemon](../../userspace/audio/young2-volume.py) maps 0–100% to speaker
levels 0–8 (unity gain at 8, not the hardware maximum 15). At zero it also sets
DAC gain to zero: SPK level 0 and Speaker Mute alone were still audible. Keys
114/115 have userspace repeat because the keypad emits no repeat events.
`xfce4-notifyd` and `notify-send` provide one replacing OSD popup.

## Verification

On October 3 I heard a clear 440 Hz speaker tone in repeated tests, including
after reboot. A 15-second built-in microphone recording contained speech with
about 25 dB measured SNR and no clipping in the final settings. Commands used
`aplay -D hw:0,0` and `arecord` at 44100 Hz, S16_LE, stereo. Successful PCM opens
alone were not the acceptance test.

On October 7 the volume keys audibly raised/lowered output, reached real silence
at zero and restored sound above zero. OSD, held-key behavior, three suspend cycles
and two reboots passed. These tests establish direct ALSA use, not every desktop
application's audio backend.

Headphone output, jack detection, headset microphone, voice-call audio and
Bluetooth audio remain untested. No working PipeWire/PulseAudio setup is claimed;
the demonstrated route uses plain ALSA. An initial capture transient occurred
while ADC/bias settled, so short recordings need care.
