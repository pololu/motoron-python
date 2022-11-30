#!/usr/bin/env python3

# This example shows how to control multiple Motoron Motor Controllers in an
# RS-485 network while checking for errors.
#
# This is similar to serial_careful_example.py but it uses the
# "Multi Device Write" command to efficiently send speeds to multiple Motorons
# and it uses the "Multi Device Error Check" command to efficiently check for
# errors on multiple Motorons.
#
# Note: If your Motorons have fewer than three motor channels, you should remove
# the commands that operate on the motors your controller does not have.
# Otherwise, those commands will cause a protocol error.

import sys
import time
import motoron
import serial

# TODO: change this to use the new commands

# TODO: change port to /dev/ttyS0
# TODO: change baud to 250000
port = serial.Serial("COM6", 250000, timeout=0.1, write_timeout=0.1)

device_numbers = [17, 18, 19]
motors_per_device = 2

mcs = []
for device_number in device_numbers:
  mc = motoron.MotoronSerial(port=port, device_number=device_number)
  mc.use_14bit_device_number()  # TODO: comment out
  mc.expect_7bit_responses()
  mcs.append(mc)

mc_broadcast = motoron.MotoronSerial(port=port)
mc_broadcast.use_14bit_device_number()  # TODO: comment out
mc_broadcast.expect_7bit_responses()

# Define which status flags the Motoron should treat as errors.
error_mask = (
  (1 << motoron.STATUS_FLAG_PROTOCOL_ERROR) |
  (1 << motoron.STATUS_FLAG_CRC_ERROR) |
  (1 << motoron.STATUS_FLAG_COMMAND_TIMEOUT_LATCHED) |
  (1 << motoron.STATUS_FLAG_MOTOR_FAULT_LATCHED) |
  (1 << motoron.STATUS_FLAG_NO_POWER_LATCHED) |
  (1 << motoron.STATUS_FLAG_SERIAL_ERROR) |
  (1 << motoron.STATUS_FLAG_RESET) |
  (1 << motoron.STATUS_FLAG_COMMAND_TIMEOUT))

def encode_speeds(speeds):
  b = []
  for speed in speeds: b += [ speed & 0x7F, speed >> 7 & 0x7F ]
  return b

def setup_motoron(mc):
  mc.reinitialize()
  mc.clear_reset_flag()
  mc.set_error_response(motoron.ERROR_RESPONSE_COAST)
  mc.set_error_mask(error_mask)
  mc.set_command_timeout_milliseconds(1000)
  for motor in range(1, motors_per_device + 1):
    mc.set_max_acceleration(motor, 140)
    mc.set_max_deceleration(motor, 300)
  while mc.get_motor_driving_flag(): pass
  mc.clear_motor_fault()

def check_for_problems(mc):
  time.sleep(0.001)  # workaround for a buggy USB adapter
  status = mc.get_status_flags()
  if (status & error_mask):
    # One of the error flags is set.  The Motoron should already be stopping
    # the motors.  We send a reset command to be extra careful.
    mc.reset()
    print("Controller error from device %d: 0x%x" % (mc.device_number, status),
      file=sys.stderr)
    sys.exit(1)

for mc in mcs:
  setup_motoron(mc)

speeds = [0] * len(device_numbers) * motors_per_device

try:
  while True:
    for mc in mcs:
      check_for_problems(mc)

    millis = int(time.monotonic() * 1000)
    for i in range(len(speeds)):
      speeds[i] = 800 if (millis - 512 * i) & 4096 else -800
    mc_broadcast.multi_device_write(min(device_numbers), len(device_numbers),
      2 * motors_per_device, motoron.CMD_SET_ALL_SPEEDS, encode_speeds(speeds))

except KeyboardInterrupt:
  pass
