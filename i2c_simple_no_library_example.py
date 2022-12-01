#!/usr/bin/env python3

# This example shows a simple way to control the Motoron Motor Controller.
# It is like i2c_simple_example.py but it does not use the Motoron library.

import math
import time
from smbus2 import SMBus, i2c_msg

def i2c_write(cmd):
  bus.i2c_rdwr(i2c_msg.write(address, cmd))

def set_max_acceleration(motor, accel):
  i2c_write([
    0x9C, motor, 10, accel & 0x7F, (accel >> 7) & 0x7F,
    0x9C, motor, 12, accel & 0x7F, (accel >> 7) & 0x7F])

def set_max_deceleration(motor, decel):
  i2c_write([
    0x9C, motor, 14, decel & 0x7F, (decel >> 7) & 0x7F,
    0x9C, motor, 16, decel & 0x7F, (decel >> 7) & 0x7F])

def set_speed(motor, speed):
  i2c_write([0xD1, motor, speed & 0x7F, (speed >> 7) & 0x7F])

bus = SMBus(1)
address = 16

i2c_write([
  # Reset the controller to its default settings using a "Reinitialize" command.
  0x96, 0x74,

  # Disable CRC using a "Set protocol options" command.
  0x8B, 0x04, 0x7B, 0x43,

  # Clear the reset flag using a "Clear latched status flags" command.
  0xA9, 0x00, 0x04,
])

# By default, the Motoron is configured to stop the motors if it does not get
# a motor control command for 1500 ms.  Uncomment a block of code below to
# adjust this time or disable the timeout feature.

# Change the command timeout using a "Set Variable" command.
# The maximmum timeout allowed is 65000 ms.
# timeout_ms = 1000
# timeout = math.ceil(timeout_ms / 4)
# i2c_write([0x9C, 0, 5, timeout & 0x7F, (timeout >> 7) & 0x7F])

# Disable the command timeout by using a "Set variable" command to clear
# the command timeout bit in the error mask.
# i2c_write([0x9C, 0, 8, 0, 4])

# Configure motor 1
set_max_acceleration(1, 140)
set_max_deceleration(1, 300)

# Configure motor 2
set_max_acceleration(2, 200)
set_max_deceleration(2, 300)

# Configure motor 3
set_max_acceleration(3, 80)
set_max_deceleration(3, 300)

try:
  while True:
    if int(time.monotonic() * 1000) & 2048:
      set_speed(1, 800)
    else:
      set_speed(1, -800)

    set_speed(2, 100)
    set_speed(3, -100)

    time.sleep(0.005)

except KeyboardInterrupt:
  pass
