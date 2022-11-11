#!/usr/bin/env python3

# This example shows how to control the Motoron Motor Controller if you want
# your system to just keep working, ignoring or automatically recovering from
# errors as much as possible.
#
# The motors will stop but automatically recover if:
# - Motor power (VIN) is interrupted
# - A motor fault occurs
# - The Motoron experiences a reset
# - A command timeout occurs
#
# Errors reported by the underlying Python I2C library are caught so they
# do not cause the program to terminate.

import sys
import time
import motoron

mc = motoron.MotoronI2C()

def motors_init():
  global last_time_motors_init
  try:
    mc.clear_reset_flag()

    # Configure motor 1
    mc.set_max_acceleration(1, 70)
    mc.set_max_deceleration(1, 150)

    # Configure motor 2
    mc.set_max_acceleration(2, 100)
    mc.set_max_deceleration(2, 150)

    # Configure motor 3
    mc.set_max_acceleration(3, 40)
    mc.set_max_deceleration(3, 150)

    mc.clear_motor_fault_unconditional()

  except (OSError, RuntimeError) as e:
    print("Error: motors_init:", e, file=sys.stderr)

  last_time_motors_init = time.monotonic()

try:
  mc.reinitialize()
except (OSError, RuntimeError):
  pass

motors_init()

try:
  while True:
    try:
      if int(time.monotonic() * 1000) & 2048:
        mc.set_speed(1, 800)
      else:
        mc.set_speed(1, -800)
      mc.set_speed(2, 100)
      mc.set_speed(3, -100)
    except (OSError, RuntimeError):
      pass

    # Every 2 seconds, run motors_init to restart the motors
    # in case anything has caused them to shut down.
    if time.monotonic() - last_time_motors_init > 2:
      motors_init()

    time.sleep(0.005)

except KeyboardInterrupt:
  pass
