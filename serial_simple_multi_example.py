#!/usr/bin/env python3

# This example shows a simple way to control multiple
# Motoron Motor Controllers using serial.
#
# The motors will stop but automatically recover if:
# - Motor power (VIN) is interrupted
# - A temporary motor fault occurs
# - A command timeout occurs
#
# The motors will stop until you restart this program if any Motoron
# experiences a reset.
#
# If a latched motor fault occurs, the motors experiencing the fault will stop
# until you power cycle motor power (VIN) or cause the motors to coast.

import time
import motoron
import serial

port = serial.Serial("/dev/serial0", 115200, timeout=0.1, write_timeout=0.1)

# Create an object for each Motoron controller. The device numbers below must
# match the way you have configured your Motorons.
mc1 = motoron.MotoronSerial(device_number=17)
mc2 = motoron.MotoronSerial(device_number=18)
mc3 = motoron.MotoronSerial(device_number=19)

def setup_motoron(mc):
  mc.set_port(port)

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

mc1.set_max_acceleration(1, 80)
mc1.set_max_deceleration(1, 300)

mc1.set_max_acceleration(2, 80)
mc1.set_max_deceleration(2, 300)

mc2.set_max_acceleration(1, 80)
mc2.set_max_deceleration(1, 300)

mc2.set_max_acceleration(2, 80)
mc2.set_max_deceleration(2, 300)

mc3.set_max_acceleration(1, 80)
mc3.set_max_deceleration(1, 300)

mc3.set_max_acceleration(2, 80)
mc3.set_max_deceleration(2, 300)

try:
  while True:
    if int(time.monotonic() * 1000) & 2048:
      changing_speed = 800
    else:
      changing_speed = -800

    mc1.set_speed(1, changing_speed)
    mc1.set_speed(2, -changing_speed)

    mc2.set_speed(1, 400)
    mc2.set_speed(2, changing_speed)

    mc3.set_speed(1, changing_speed)
    mc3.set_speed(2, 400)

    time.sleep(0.005)

except KeyboardInterrupt:
  pass
