#!/usr/bin/env python3

import time
import motoron

mc1 = motoron.MotoronI2C(address=17)
mc2 = motoron.MotoronI2C(address=18)

# TODO: add mc3 and mc4

def setup_motoron(mc):
  mc.reinitialize()
  mc.disable_crc()
  mc.clear_reset_flag()

setup_motoron(mc1)
setup_motoron(mc2)

mc1.set_max_acceleration(1, 140)
mc1.set_max_deceleration(1, 300)
mc1.set_max_acceleration(2, 200)
mc1.set_max_deceleration(2, 300)
mc1.set_max_acceleration(3, 80)
mc1.set_max_deceleration(3, 300)

mc2.set_max_acceleration(1, 140)
mc2.set_max_deceleration(1, 300)
mc2.set_max_acceleration(2, 200)
mc2.set_max_deceleration(2, 300)
mc2.set_max_acceleration(3, 80)
mc2.set_max_deceleration(3, 300)

try:
  while True:
    changing_speed = 800 if int(time.monotonic() * 1000) & 2048 else -800

    mc1.set_speed(1, changing_speed)
    mc1.set_speed(2, 100)
    mc1.set_speed(3, -100)

    mc2.set_speed(1, 100)
    mc2.set_speed(2, changing_speed)
    mc2.set_speed(3, -100)

except KeyboardInterrupt:
  pass
