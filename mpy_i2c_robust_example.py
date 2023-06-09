# This example shows how to control the Motoron Motor Controller
# I2C interface using the machine.I2C class in MicroPython if you want
# your system to just keep working, ignoring or automatically recovering from
# errors as much as possible.
#
# The motors will stop but automatically recover if:
# - Motor power (VIN) is interrupted
# - A motor fault occurs
# - The Motoron experiences a reset
# - A command timeout occurs
#
# Errors reported by the machine.I2C class are caught so they
# do not cause the program to terminate.

import time
import motoron
from machine import I2C, Pin

bus = I2C(0, scl=Pin(5), sda=Pin(4))
mc = motoron.MotoronI2C(bus=bus)

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

  except OSError as e:
    print("Error: motors_init:", e)

  last_time_motors_init = time.ticks_ms()

try:
  mc.reinitialize()
except OSError:
  pass

motors_init()

while True:
  try:
    if time.ticks_ms() & 2048:
      mc.set_speed(1, 800)
    else:
      mc.set_speed(1, -800)
    mc.set_speed(2, 100)
    mc.set_speed(3, -100)
  except OSError:
    pass

  # Every 2000 ms, run motors_init to restart the motors
  # in case anything has caused them to shut down.
  if time.ticks_ms() - last_time_motors_init > 2000:
    motors_init()
