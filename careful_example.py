#!/usr/bin/env python3

# This example shows how to control the Motoron Motor Controller if you want to
# shut down the motors whenever any problems are detected.
#
# The motors will stop and this program will terminate if:
# - Motor power (VIN) is interrupted
# - A motor fault occurs
# - A protocol error or CRC error occurs
# - The underlying Python I2C library reports an error
# - A command timeout occurs
# - The Motoron experiences a reset
#
# Note: If your Motoron has fewer than three motor channels, you should remove
# the commands that operate on the motors your controller does not have.
# Otherwise, those commands will cause a protocol error.


import sys
import time
import motoron

mc = motoron.MotoronI2C()

# ADC reference voltage
reference_mv = 3300

# Minimum allowed VIN voltage.  You can raise this to be closer to your power
# supply's expected voltage.
min_vin_voltage_mv = 4500

# Define which status flags the Motoron should treat as errors.
error_mask = (
  (1 << motoron.STATUS_FLAG_PROTOCOL_ERROR) |
  (1 << motoron.STATUS_FLAG_CRC_ERROR) |
  (1 << motoron.STATUS_FLAG_COMMAND_TIMEOUT_LATCHED) |
  (1 << motoron.STATUS_FLAG_MOTOR_FAULT_LATCHED) |
  (1 << motoron.STATUS_FLAG_NO_POWER_LATCHED) |
  (1 << motoron.STATUS_FLAG_RESET) |
  (1 << motoron.STATUS_FLAG_COMMAND_TIMEOUT))

mc.reinitialize()
mc.clear_reset_flag()

# Configure the Motoron to coast the motors while obeying deceleration limits if
# there is an error.
mc.set_error_response(motoron.ERROR_RESPONSE_COAST)

mc.set_error_mask(error_mask)

# Use a short command timeout of 100 ms: the Motoron will stop the motors if it
# does not get a command for 100 ms.
mc.set_command_timeout_milliseconds(100)

# Configure motor 1
mc.set_max_acceleration(1, 140)
mc.set_max_deceleration(1, 300)

# Configure motor 2
mc.set_max_acceleration(2, 200)
mc.set_max_deceleration(2, 300)

# Configure motor 3
mc.set_max_acceleration(3, 80)
mc.set_max_deceleration(3, 300)

# Depending on what was happening before this program started, the motors will
# either by stopped or decelerating.  This loop waits for them to stop so that
# when the rest of the code starts running, it will run from a more predictable
# starting point.  This is optional.
while mc.get_motor_driving_flag(): pass

mc.clear_motor_fault()

def check_for_problems():
  status = mc.get_status_flags()
  if (status & error_mask):
    # One of the error flags is set.  The Motoron should already be stopping
    # the motors.  We send a reset command to be extra careful.
    mc.reset()
    print("Controller error: 0x%x" % status, file=sys.stderr)
    sys.exit(1)

  voltage_mv = mc.get_vin_voltage_mv(reference_mv)
  if voltage_mv < min_vin_voltage_mv:
    mc.reset()
    print("VIN voltage too low:", voltage_mv, file=sys.stderr)
    sys.exit(1)

try:
  while True:
    check_for_problems()

    if int(time.monotonic() * 1000) & 2048:
      mc.set_speed(1, 800)
    else:
      mc.set_speed(1, -800)

    mc.set_speed(2, 100)
    mc.set_speed(3, -100)

    time.sleep(0.005)

except KeyboardInterrupt:
  pass
