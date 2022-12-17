#!/usr/bin/env python3

# This example shows how to control multiple Motoron Motor Controllers in a
# half-duplex RS-485 network while checking for errors.
#
# This is similar to serial_careful_example.py but it uses the
# "Multi-device write" command to efficiently send speeds to multiple Motorons
# and it uses the "Multi-device error check" command to efficiently check for
# errors on multiple Motorons.
#
# The error checking code only works if each addressed Motoron can see the
# repsonses sent by the other Motorons (e.g. they are in a half-duplex RS-485
# network).
#
# This code assumes you have configured the Motorons to send 7-bit responses,
# which is important because it prevents a Motoron from interpreting a response
# from another Motoron as a command.
#
# You will need to change the following settings in this code to match your
# hardware configuration: port, starting_device_number, device_count,
# motors_per_device.

import sys
import time
import motoron
import serial

# Define the range of Motoron device numbers to control.
# (Note that this code does send some Compact protocol commands which will
# affect all Motorons regardless of their device number.)
starting_device_number = 17
device_count = 3

# Define the number of motor channels per Motoron.
# It is OK if some of the Motorons in the system have fewer channels than this.
motors_per_device = 2

communication_options = 1 << motoron.COMMUNICATION_OPTION_7BIT_RESPONSES
# communication_options |= 1 << motoron.COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER

port = serial.Serial("/dev/serial0", 115200, timeout=0.1, write_timeout=0.1)

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
    error_index = mc_broadcast.multi_device_error_check(
      starting_device_number, device_count)
    if error_index != device_count:
      mc_broadcast.coast_now()
      mc = mcs[error_index]
      status = mcs[error_index].get_status_flags()
      print("Error from device %d: status 0x%x" % (mc.device_number, status),
        file=sys.stderr)
      sys.exit(1)

    # Calculate motor speeds that will drive each motor forward briefly and
    # repeat every 4 seconds.
    millis = int(time.monotonic() * 1000)
    for i in range(len(speeds)):
      phase = (millis - 512 * i) % 4096
      speeds[i] = 400 if phase <= 500 else 0

    # Send the motor speeds.
    mc_broadcast.multi_device_write(starting_device_number, device_count,
      motoron.CMD_SET_ALL_SPEEDS, encode_speeds(speeds))

except KeyboardInterrupt:
  mc_broadcast.reset()
  pass
except Exception:
  mc_broadcast.reset()
  raise
