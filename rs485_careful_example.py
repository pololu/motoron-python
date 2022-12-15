#!/usr/bin/env python3

# This example shows how to control multiple Motoron Motor Controllers in an
# RS-485 network while checking for errors.
#
# This is similar to serial_careful_example.py but it uses the
# "Multi Device Write" command to efficiently send speeds to multiple Motorons
# and it uses the "Multi Device Error Check" command to efficiently check for
# errors on multiple Motorons.
#
# You will need to change the following variables to match your configuration:
# port, starting_device_number, device_count, motors_per_device,
# communication_options.
#
# Note: If your Motorons have fewer than three motor channels, you should remove
# the commands that operate on the motors your controller does not have.
# Otherwise, those commands will cause a protocol error.

import sys
import time
import motoron
import serial

port = serial.Serial("/dev/serial0", 115200, timeout=0.1, write_timeout=0.1)

starting_device_number = 17
device_count = 3
motors_per_device = 2

communication_options = 1 << motoron.COMMUNICATION_OPTION_7BIT_RESPONSES
# communication_options |= 1 << motoron.COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER

mcs = []
for i in range(device_count):
  mc = motoron.MotoronSerial(port = port, device_number = starting_device_number + i)
  mc.communication_options = communication_options
  mcs.append(mc)

mc_broadcast = motoron.MotoronSerial(port=port)
mc_broadcast.communication_options = communication_options

# Define which status flags the Motoron should treat as errors.
error_mask = (
  (1 << motoron.STATUS_FLAG_PROTOCOL_ERROR) |
  (1 << motoron.STATUS_FLAG_CRC_ERROR) |
  (1 << motoron.STATUS_FLAG_COMMAND_TIMEOUT_LATCHED) |
  (1 << motoron.STATUS_FLAG_MOTOR_FAULT_LATCHED) |
  (1 << motoron.STATUS_FLAG_NO_POWER_LATCHED) |
  (1 << motoron.STATUS_FLAG_UART_ERROR) |
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

for mc in mcs:
  setup_motoron(mc)

speeds = [0] * device_count * motors_per_device

try:
  while True:
    # Check for errors on all the Motorons.
    device_error_index = mc_broadcast.multi_device_error_check(
      starting_device_number, device_count)
    if device_error_index != device_count:
      mc = mcs[device_error_index]
      status = mcs[device_error_index].get_status_flags()
      print("Controller error from device %d: 0x%x" % (mc.device_number, status),
        file=sys.stderr)
      mc_broadcast.reset()
      sys.exit(1)

    # Set the speeds of all the Motorons.
    millis = int(time.monotonic() * 1000)
    for i in range(len(speeds)):
      speeds[i] = 800 if (millis - 512 * i) & 4096 else -800
    mc_broadcast.multi_device_write(starting_device_number, device_count,
      motoron.CMD_SET_ALL_SPEEDS, encode_speeds(speeds))

except KeyboardInterrupt:
  mc_broadcast.reset()
  pass
except Exception:
  mc_broadcast.reset()
  raise
