# Accelerometer: K2HH / K2HHTR

The fitted motion sensor is the STM K2HHTR, reported by the kernel as K2HH.
Board source registers `I2C_BOARD_INFO("k2hh", 0x1d)` on GPIO I²C bus 5.
Probe read chip ID `0x41`; sysfs reports vendor `STM` and name `K2HH`.
The schematic identifies the accelerometer as U404.

## Kernel and interface

Source: `drivers/sensors/k2hh.c`, `include/linux/k2hh.h`,
`drivers/sensors/Kconfig`, `arch/arm/mach-sc/board-young2.c`.
`CONFIG_SENSORS_K2HH=y`, `CONFIG_NEW_SENSORS=y` and `CONFIG_SENSORS_CORE=y`
were already enabled in the proven config. No sensor kernel patch was needed.

`/sys/class/sensors/accelerometer_sensor/raw_data` exposes X,Y,Z.
Enable and poll_delay live on the input device, recorded as
`/sys/class/input/event3/device/{enable,poll_delay}`. EV_REL reports REL_X/Y/Z;
there is no IIO interface. `iio-sensor-proxy` therefore cannot consume it directly.
The driver polls with a workqueue rather than using the wired interrupt.

[70-young2-accel.start](../../userspace/sensors/70-young2-accel.start) sets
poll_delay 200 ms and enable 1. [young2-accel](../../userspace/sensors/young2-accel)
is the original GTK3 bubble-level diagnostic (Python, GI/GTK3 already installed).
Check the event node's name before using this original fixed-path boot helper.

## Verification

October 7 tests showed live samples such as `431,-804,15378`,
`-205,-667,15471` and `570,-390,15336`, approximately 16384 counts/g.
Physical poses established X right, Y toward the top edge, Z out of the screen:
screen-up Z about +0.94 g, screen-down Z about -1.06 g, bottom-edge-down positive Y.
No axis remap was required. The bubble and readings followed real tilts.

Two reboots restored enable=1 and 200 ms polling. Three real deep-sleep cycles
preserved enablement and changing samples without I²C errors. Driver suspend/resume
switches chip mode through its dev_pm_ops.

## Limits

Automatic display/touch rotation is not implemented or verified. The available
orientation data alone does not establish rotation. Calibration data is absent,
so the samples are uncalibrated. Other motion/environment sensors have no
corresponding registration in the inspected young2 board/config; this work does
not create substitute devices.
