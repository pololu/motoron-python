import time
from motoron import MotoronI2C

mc = MotoronI2C()

mc.reinitialize()
mc.disable_crc()

mc.clear_reset_flag()

mc.set_max_acceleration(1, 140)
mc.set_max_deceleration(1, 300)

mc.set_max_acceleration(2, 200)
mc.set_max_deceleration(2, 300)

mc.set_max_acceleration(3, 80)
mc.set_max_deceleration(3, 300)

while True:
  if int(time.monotonic() * 1000) & 2048:
    mc.set_speed(1, 800)
  else:
    mc.set_speed(1, -800)

  mc.set_speed(2, 100)
  mc.set_speed(3, -100)

