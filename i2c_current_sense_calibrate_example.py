#!/usr/bin/env python3

# This example for the Motoron M2H controllers shows how to automatically
# measure the current sense offsets at startup and load them into the Motoron so
# that the processed current measurements are more accurate.
#
# It also uses those current sense offsets to help set current limits.

import time
import motoron

mc = motoron.MotoronI2C()

# ADC reference voltage
reference_mv = 3300

# Specifies what type of Motoron you are using, which is needed for converting
# current sense readings to milliamps.
type = motoron.CurrentSenseType.MOTORON_18V18

# Minimum allowed VIN voltage.  This example does not take current calibration
# readings while VIN is below this configurable level.
min_vin_voltage_mv = 6500

units = motoron.current_sense_units_milliamps(type, reference_mv)

def calibrate_current():
  mc.set_speed(1, 0)
  mc.set_speed(2, 0)

  desired_sample_count = 32
  sample_count = 0
  totals = [ 0, 0 ]

  last_time_conditions_not_met = time.monotonic()
  while True:
    status_mask = ((1 << motoron.STATUS_FLAG_MOTOR_FAULTING) |
      (1 << motoron.STATUS_FLAG_NO_POWER) |
      (1 << motoron.STATUS_FLAG_MOTOR_OUTPUT_ENABLED) |
      (1 << motoron.STATUS_FLAG_MOTOR_DRIVING))
    status_desired = 1 << motoron.STATUS_FLAG_MOTOR_OUTPUT_ENABLED

    if ((mc.get_status_flags() & status_mask) != status_desired or
      (mc.get_vin_voltage_mv(reference_mv) < min_vin_voltage_mv)):
        last_time_conditions_not_met = time.monotonic()
        sample_count = 0
        totals = [0, 0]

    if (time.monotonic() - last_time_conditions_not_met) > 0.02:
      totals[0] += mc.get_current_sense_raw(1)
      totals[1] += mc.get_current_sense_raw(2)
      sample_count += 1
      if sample_count == desired_sample_count: break

  mc.set_current_sense_offset(1, round(totals[0] / desired_sample_count))
  mc.set_current_sense_offset(2, round(totals[1] / desired_sample_count))
  mc.set_current_sense_minimum_divisor(1, 100)
  mc.set_current_sense_minimum_divisor(2, 100)

  print(f"Current sense offsets: {mc.get_current_sense_offset(1)} {mc.get_current_sense_offset(2)}")

mc.reinitialize()
mc.clear_reset_flag()

# By default, the Motoron is configured to stop the motors if
# it does not get a motor control command for 1500 ms.  You
# can uncomment a line below to adjust this time or disable
# the timeout feature.
# mc.set_command_timeout_milliseconds(1000)
# mc.disable_command_timeout()

# Configure motor 1
mc.set_max_acceleration(1, 200)
mc.set_max_deceleration(1, 200)

# Configure motor 2
mc.set_max_acceleration(2, 200)
mc.set_max_deceleration(2, 200)

calibrate_current()

# Set current limits using the offsets we just measured.
# The second argument to calculate_current_limit is a current limit
# in milliamps.
mc.set_current_limit(1, motoron.calculate_current_limit(10000,
  type, reference_mv, mc.get_current_sense_offset(1)))
mc.set_current_limit(2, motoron.calculate_current_limit(10000,
  type, reference_mv, mc.get_current_sense_offset(2)))

try:
  while True:
    mc.set_speed(1, 200)
    time.sleep(1)
    processed = mc.get_current_sense_processed(1)
    print(f"Motor 1 current: {processed} = {round(processed * units)} mA")
    mc.set_speed(1, 0)
    time.sleep(1)

    mc.set_speed(2, 200)
    time.sleep(1)
    processed = mc.get_current_sense_processed(2)
    print(f"Motor 2 current: {processed} = {round(processed * units)} mA")
    mc.set_speed(2, 0)
    time.sleep(1)

except KeyboardInterrupt:
  pass
