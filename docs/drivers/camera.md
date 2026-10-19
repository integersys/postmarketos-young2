# Camera: experimental SR352 bring-up

**No complete verified image has been captured.** I identified and initialized
the rear sensor and observed partial DCAM activity; preview and photos remain
unproven.

## Confirmed hardware and driver path

The Samsung SR352 is on I²C bus 0, 7-bit address `0x20`. Register `0x04`
returns `0xc2`. Transactions use an 8-bit register and 8-bit value; `0x03`
selects a sensor page/bank. The board's old `sensor_main` address `0x3c` is not
the measured chip address. A permanent board-address correction is queued,
not presented as a validated kernel patch here.

The kernel path is `sprd_sensor` for control and `sprd_dcam` for capture under
`drivers/media/sprd_sensor/` and `drivers/media/sprd_dcam/`, specifically
the SCX15 code. The interface is CCIR. The SCX15 CSI2 implementation is a stub;
this is not evidence of a working MIPI capture path.

## What was recovered

Static inspection of the device HAL established the table walker:

| Entry | Operation |
|---|---|
| ordinary register/value | Sensor_WriteReg(reg, val) |
| reg 0xff, val other than 0xff | usleep(val * 10000) |
| reg 0xff, val 0xff | end of table |
| reg 0x03 | sensor page selection |

The sequences at `0x0007F2D4` and `0x00080158` replayed and the sensor produced
CCIR activity. DCAM received activity and capture buffers changed. Those
sequences are PLL/LSC/timing sequences, **not resolution tables**: the later
analysis showed that they do not program the page-0xc0 window registers.

The later HAL map identifies a separate 640×480 table at `0x00080304` (62 entries),
800×480 at `0x0007fe22` and 1024×576 at `0x0007fb4e`. The recovered capture flow
uses interface setup, sensor size, format, frame decimation and capture crop.
The rewritten local capture tool includes those steps, but was not run against
the phone in the last session because it was unreachable.

## Present failure and next test

`DCAM: err, 0x400` is `DCAM_SN_LINE_ERR` (ISR bit 10). Its error handler disables
capture and resets DCAM; the 4096/8192-byte changed regions are partial DMA residue,
not completed pictures. The first tool omitted `CAPTURE_SENSOR_SIZE` and crop
programming, leaving a degenerate CCIR capture window. Correcting both sensor
resolution and DCAM geometry is the next evidence-based test, **not a confirmed
fix**. YUV ordering and sync polarities also remain unknown.

Linux's V4L2-looking interface contains vendor commands and 32-bit ABI details;
a successful STREAMON or changing buffer does not prove a frame. Acceptance needs
a complete buffer with coherent geometry and a visually checked image from a
known scene, followed by a second different scene.

## Publication boundary

I have not included `camera.scx15.so`, Android HAL binaries, vendor dumps or
recovered register tables. Their redistribution suitability is unresolved. The
local capture source depends on those tables, so publishing it here as a working
standalone tool would be misleading. Camera findings are documented without
shipping that material. No camera kernel was built or flashed for this branch.
