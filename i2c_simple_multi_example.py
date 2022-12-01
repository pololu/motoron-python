#!/usr/bin/env python3

# This example shows a simple way to control multiple
# Motoron Motor Controllers.
#
# The motors will stop but automatically recover if:
# - Motor power (VIN) is interrupted
# - A temporary motor fault occurs
# - A command timeout occurs
#
# This program will terminate if it does not receive an acknowledgment bit from
# a Motoron for a byte it has written or if any other exception is thrown by
# the underlying Python I2C library.
#
# The motors will stop until you restart this program if any Motoron
# experiences a reset.
#
# If a latched motor fault occurs, the motors experiencing the fault will stop
# until you power cycle motor power (VIN) or cause the motors to coast.

import time
import motoron

# Creates an object for each Motoron controller. Each address argument below
# should be the 7-bit I2C address of the controller.
#
# You should use the i2c_set_addresses_example.py utility to assign a unique
# address to each Motoron, and then modify the list below to match your setup.
mc1 = motoron.MotoronI2C(address=17)
mc2 = motoron.MotoronI2C(address=18)
mc3 = motoron.MotoronI2C(address=19)
mc4 = motoron.MotoronI2C(address=20)

def setup_motoron(mc):
  mc.reinitialize()
  mc.disable_crc()

  # Clear the reset flag, which is set after the controller reinitializes
  # and counts as an error.
  mc.clear_reset_flag()

  # By default, the Motoron is configured to stop the motors if it does not get
  # a motor control command for 1500 ms.  You can uncomment a line below to
  # adjust this time or disable the timeout feature.
  # mc.set_command_timeout_milliseconds(1000)
  # mc.disable_command_timeout()

setup_motoron(mc1)
setup_motoron(mc2)
setup_motoron(mc3)
setup_motoron(mc4)

mc1.set_max_acceleration(1, 80)
mc1.set_max_deceleration(1, 300)

mc1.set_max_acceleration(2, 80)
mc1.set_max_deceleration(2, 300)

mc1.set_max_acceleration(3, 80)
mc1.set_max_deceleration(3, 300)

mc2.set_max_acceleration(1, 80)
mc2.set_max_deceleration(1, 300)

mc2.set_max_acceleration(2, 80)
mc2.set_max_deceleration(2, 300)

mc2.set_max_acceleration(3, 80)
mc2.set_max_deceleration(3, 300)

mc3.set_max_acceleration(1, 80)
mc3.set_max_deceleration(1, 300)

mc3.set_max_acceleration(2, 80)
mc3.set_max_deceleration(2, 300)

mc3.set_max_acceleration(3, 80)
mc3.set_max_deceleration(3, 300)

mc4.set_max_acceleration(1, 80)
mc4.set_max_deceleration(1, 300)

mc4.set_max_acceleration(2, 80)
mc4.set_max_deceleration(2, 300)

mc4.set_max_acceleration(3, 80)
mc4.set_max_deceleration(3, 300)

try:
  while True:
    if int(time.monotonic() * 1000) & 2048:
      changing_speed = 800
    else:
      changing_speed = -800

    mc1.set_speed(1, changing_speed)
    mc1.set_speed(2, 100)
    mc1.set_speed(3, -100)

    mc2.set_speed(1, 100)
    mc2.set_speed(2, changing_speed)
    mc2.set_speed(3, -100)

    mc3.set_speed(1, 100)
    mc3.set_speed(2, -100)
    mc3.set_speed(3, changing_speed)

    mc4.set_speed(1, changing_speed)
    mc4.set_speed(2, -changing_speed)
    mc4.set_speed(3, changing_speed)

    time.sleep(0.005)

except KeyboardInterrupt:
  pass
