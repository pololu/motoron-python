#!/usr/bin/env python3

# This example code provides an interactive utility you can use to set the
# device number, baud rate, and all the other settings in the EEPROM of a
# a Motoron with a UART serial interface.
#
# For this code to work the Motoron must be wired properly to your
# computer so it can receive serial commands.  It must also be operating
# at a known baud rate, and the baud rate must be one that your serial
# hardware can generate accurately.  If you are not sure what baud
# rate your Motoron is using or whether your hardware can generate it
# accurately, you can short JMP1 to GND and then power cycle or reset the
# Motoron to ensure it uses 9600 baud.

help_message = """
Command          | Summary
-----------------|----------------------------------------------------------
a [NUM] [ALTNUM] | Write all settings to EEPROM (JMP1 must be low).
r                | Reset devices.
i                | Identify devices.
b BAUD           | Use a different baud rate to communicate.
o [OPTS]         | Use different communication options.
n                | Use 115200 baud, 8-bit responses, 7-bit device number.
j                | Use 9600 baud, 8-bit responses, 7-bit device number.
k                | Use the options & baud rate we're assigning to devices.

For more information about each command, see the comments in the
source code.
"""

start_message = """
Motoron Serial Setup Utility

Type "h" for help.
"""

import readline
import sys
import time
import serial
import motoron

# The serial parameters below are assigned to a device when you use the "a"
# command.  You can modify these lines to assign different parameters.
assign_baud_rate = 115200
assign_7bit_responses = False
assign_14bit_device_number = False
assign_err_is_de = False
assign_response_delay = 0

if assign_baud_rate < motoron.MIN_BAUD_RATE or \
  assign_baud_rate > motoron.MAX_BAUD_RATE:
  raise RuntimeError("Invalid baud rate.")

assign_communication_options = \
  (assign_7bit_responses << motoron.COMMUNICATION_OPTION_7BIT_RESPONSES) | \
  (assign_14bit_device_number << motoron.COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER) | \
  (assign_err_is_de << motoron.COMMUNICATION_OPTION_ERR_IS_DE)

port = serial.Serial("/dev/serial0", 115200, timeout=0.01, write_timeout=0.1)

mc = motoron.MotoronSerial(port=port)

last_device_number = 16

# Command syntax: a [NUM] [ALTNUM]
#
# This command sends a series of "Write EEPROM" commands using the
# compact protocol to set all the settings in Motoron's EEPROM.
# For this command to work, the Motoron must be using the same baud rate as
# the Arduino and the Motoron's JMP1 line must be low.
#
# NUM should be the desired device number for the Motoron.
# If NUM is omitted or equal to "-1", the program will automatically pick a
# device number.
#
# ALTNUM should be the desired *alternative* device number for the Motoron.
# If ALTNUM is omitted or equal to "-1", the feature is disabled.
#
# The other settings are set according to the constants above
# (e.g. assignBaudRate).
#
# Settings written to the Motoron's EEPROM do not have an immediate affect,
# but you can use the "r" command to reset the Motoron and make the new
# settings take effect.
#
# Examples:
#   a
#   a 17
#   a -1 0
#   a 0x123 0x456
def assign_all_settings(line):
  global last_device_number
  max_device_number = 0x3FFF if assign_14bit_device_number else 0x7F

  device_number = -1
  alt_device_number = -1

  parts = line[1:].split()
  if len(parts) >= 1:
    try:
      device_number = int(parts[0])
    except ValueError:
      print("Invalid device number argument.")
      return
  if len(parts) >= 2:
    try:
      alt_device_number = int(parts[1])
    except ValueError:
      print("Invalid alternative device number argument.")
      return

  if device_number == -1:
    # The user did not specify a device number, so pick one.
    device_number = (last_device_number + 1) & max_device_number

  if not device_number in range(0, max_device_number + 1):
    print("Invalid device number.")
    return

  if not alt_device_number in range(-1, max_device_number + 1):
    print("Invalid alternative device number.")
    return

  mc.enable_crc()
  mc.write_eeprom_device_number(device_number)
  if alt_device_number == -1:
    mc.write_eeprom_disable_alternative_device_number()
  else:
    mc.write_eeprom_alternative_device_number(alt_device_number)
  mc.write_eeprom_baud_rate(assign_baud_rate)
  mc.write_eeprom_communication_options(assign_communication_options)
  mc.write_eeprom_response_delay(assign_response_delay)

  print("Assigned device number", device_number, end='')

  if alt_device_number != -1:
    print(" and", alt_device_number, end='')
  print(",", assign_baud_rate, "baud", end='')

  if assign_14bit_device_number:
    print(", 14-bit device number", end='')
  else:
    print(", 7-bit device number", end='')

  if assign_7bit_responses:
    print(", 7-bit responses", end='')
  else:
    print(", 8-bit responses", end='')

  if assign_err_is_de:
    print(", ERR is DE", end='')
  else:
    print(", ERR is normal", end='')

  print(".")

  last_device_number = device_number

def print_communication_settings():
  print(port.baudrate, 'baud', end='')
  if mc.communication_options & (1 << motoron.COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER):
    print(', 14-bit device number', end='')
  else:
    print(', 7-bit device number', end='')
  if mc.communication_options & (1 << motoron.COMMUNICATION_OPTION_7BIT_RESPONSES):
    print(', 7-bit responses', end='')
  else:
    print(', 8-bit responses', end='')

def print_communication_settings_line():
  print("Using ", end='')
  print_communication_settings();
  print(".")

def print_device_info_if_possible():
  firmware = mc.get_firmware_version()
  product_id = firmware['product_id']
  firmware_version = firmware['firmware_version']

  jumper_state = mc.get_jumper_state() & 3
  if jumper_state == 0b10: jumper_string = 'off'
  elif jumper_state == 0b01: jumper_string = 'on'
  else: jumper_string = 'err'

  # We fetch EEPROM with two requests because the maximum payload size in
  # 7-bit response mode is 7 bytes.
  eeprom = mc.read_eeprom(1, 4) + mc.read_eeprom(5, 4)

  print("%3d: product=0x%04X version=%x.%02x JMP1=%s EEPROM=%s" % (
    mc.device_number, product_id,
    firmware_version['major'], firmware_version['minor'], jumper_string,
    ' '.join(('%02X' % b for b in eeprom))))

# Command syntax: i
#
# This command tries to communicate with every possible device number using
# the current communication settings and the Pololu protocol.  If it finds a
# Motoron it prints out some information about it.
#
# Note: When using 14-bit device numbers, this command might take several minutes.
def identify_devices():
  if mc.communication_options & (1 << motoron.COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER):
    max_device_number = 0x3FFF
  else:
    max_device_number = 0x7F

  print("Identifying Motoron controllers (", end='')
  print_communication_settings()
  print(")...")
  for i in range(max_device_number + 1):
    port.reset_input_buffer()
    mc.device_number = i
    try:
      mc.enable_crc()
      print_device_info_if_possible()
    except RuntimeError:
      pass
  print("Done.")
  mc.device_number = None

# Command syntax: b BAUD
#
# This command configures the Arduino to use a different baud rate when
# communicating with the Motoron.
#
# Example: b 38600
def command_set_baud_rate(line):
  try:
    baud_rate = int(line[1:])
  except ValueError:
    print("Invalid baud rate.")
    return
  if baud_rate < motoron.MIN_BAUD_RATE or baud_rate > motoron.MAX_BAUD_RATE:
    print("Invalid baud rate.")
    return
  print(baud_rate)
  port.baudrate = baud_rate
  print_communication_settings_line()

# Command syntax: o [OPTS]
#
# This command configures the Arduino to use different serial options when
# communicating with the Motoron.
#
# If OPTS is omitted, this command cycles through the four different possible
# sets of serial options.
#
# Otherwise, OPTS should be a number between 0 and 3:
#   0 = 8-bit responses, 7-bit device numbers
#   1 = 7-bit responses, 7-bit device numbers
#   2 = 8-bit responses, 14-bit device numbers
#   3 = 7-bit responses, 14-bit device numbers
def command_set_communication_options(line):
  try:
    mc.communication_options = int(line[1:])
  except ValueError:
    mc.communication_options = (mc.communication_options + 1) & 3
    pass
  print_communication_settings_line()

def process_command(line):
  if not line: return
  elif line[0] == 'a': assign_all_settings(line)
  elif line[0] == 'r':
    print("Reset")
    mc.reset()
  elif line[0] == 'i': identify_devices()
  elif line[0] == 'b': command_set_baud_rate(line)
  elif line[0] == 'o': command_set_communication_options(line)
  elif line[0] == 'n':
    port.baudrate = 115200
    mc.communication_options = 0
    print_communication_settings_line()
  elif line[0] == 'j':
    port.baudrate = 9600
    mc.communication_options = 0
    print_communication_settings_line()
  elif line[0] == 'k':
    port.baudrate = assign_baud_rate
    mc.communication_options = assign_communication_options
    print_communication_settings_line()
  elif line[0] == 'h' or line[0] == 'H' or line[0] == '?': print(help_message)
  elif line == 'q' or line == 'quit': sys.exit(0)
  else: print("Error: Unreocgnized command.  Type h for help.")

print(start_message)
try:
  while True:
    process_command(input("Enter command: "))
except (KeyboardInterrupt, EOFError):
  print()

