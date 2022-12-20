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
"""
# For more information about each command, see the comments below.

start_message = """
Motoron Serial Setup Utility

Type "h" for help.
"""

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

def process_command(line):
  if not line: return
  elif line[0] == 'a': pass # TODO
  elif line[0] == 'r': pass # TODO
  elif line[0] == 'i': identify_devices()
  elif line[0] == 'b': pass # TODO
  elif line[0] == 'o': pass # TODO
  elif line[0] == 'n': pass # TODO
  elif line[0] == 'j': pass # TODO
  elif line[0] == 'k': pass # TODO
  elif line[0] == 'h' or line[0] == 'H' or line[0] == '?': print(help_message)
  elif line == 'q' or line == 'quit': sys.exit(0)
  else: print("Error: Unreocgnized command.  Type h for help.")

print(start_message)
try:
  while True:
    process_command(input("Enter command: "))
except (KeyboardInterrupt, EOFError):
  print()

