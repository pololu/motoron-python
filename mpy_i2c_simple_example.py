# This example shows a simple way to control the Motoron Motor Controller
# I2C interface using the machine.I2C class in MicroPython.
#
# The motors will stop but automatically recover if:
# - Motor power (VIN) is interrupted
# - A temporary motor fault occurs
# - A command timeout occurs
#
# This program will terminate if it does not receive an acknowledgment bit from
# the Motoron for a byte it has written or if any other exception is thrown by
# the underlying Python I2C library.
#
# The motors will stop until you restart this program if the Motoron
# experiences a reset.
#
# If a latched motor fault occurs, the motors experiencing the fault will stop
# until you power cycle motor power (VIN) or cause the motors to coast.

import time
import motoron
from machine import I2C, Pin

bus = I2C(0, scl=Pin(5), sda=Pin(4))
mc = motoron.MotoronI2C(bus=bus)

# Reset the controller to its default settings, then disable CRC.  The bytes for
# each of these commands are shown here in case you want to implement them on
# your own without using the library.
mc.reinitialize()  # Bytes: 0x96 0x74
mc.disable_crc()   # Bytes: 0x8B 0x04 0x7B 0x43

# Clear the reset flag, which is set after the controller reinitializes and
# counts as an error.
mc.clear_reset_flag()  # Bytes: 0xA9 0x00 0x04

# By default, the Motoron is configured to stop the motors if it does not get
# a motor control command for 1500 ms.  You can uncomment a line below to
# adjust this time or disable the timeout feature.
# mc.set_command_timeout_milliseconds(1000)
# mc.disable_command_timeout()

# Configure motor 1
mc.set_max_acceleration(1, 140)
mc.set_max_deceleration(1, 300)

# Configure motor 2
mc.set_max_acceleration(2, 200)
mc.set_max_deceleration(2, 300)

# Configure motor 3
mc.set_max_acceleration(3, 80)
mc.set_max_deceleration(3, 300)

while True:
  if time.ticks_ms() & 2048:
    mc.set_speed(1, 800)
  else:
    mc.set_speed(1, -800)

  mc.set_speed(2, 100)
  mc.set_speed(3, -100)
