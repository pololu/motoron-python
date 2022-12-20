#!/usr/bin/env python3

# This program is an interactive utility you can use to set the I2C
# addresses for a single Motoron controller or multiple controllers.
#
# When you run this program in an terminal, it prompts you to enter a
# command.  Type the command you want to run and then press Enter.

help_message = """
To assign an I2C address to a Motoron, type "a" followed by the address
(in decimal) while the JMP1 pin of the Motoron you wish to change is
shorted to GND.  For example, "a7" sets the address of the Motoron to
decimal 17.

Alternatively, you can type "a" by itself in order to automatically
to have this program automatically pick an address for you.

To make the Motoron start using its new address, you can reset it by
power cycling it, driving its RST line low, or by typing "r".

The "s" command does a simple scan of the bus to see which addresses
have devices responding.  This can help you make sure you have set up
your I2C bus correctly.

The "i" command goes further, sending extra commands to identify the
Motoron devices on the bus and print information about them.

Warning: The "i" command sends Motoron commands to every I2C device on
the bus.  If you have devices on your bus that are not Motorons, this
could cause undesired behavior.

Warning: The "a" and "r" commands use the I2C general call address (0), so
they might cause undesired behavior on other devices that use that address.
Also, they will not work if you disabled the general call address on a
Motoron.
"""

start_message = """Motoron Set I2C Addresses Utility

Type "h" for help, "a" followed by a number to assign an address, "r" to reset
Motorons, "s" to scan, "i" to identify devices, or Ctrl+C to quit.

Warning: If you have devices that are not Motorons, these commands could cause
undesired behavior.  Type "h" for more info.
"""

import readline
import sys
import time
import motoron
from smbus2 import SMBus, i2c_msg

# Make a MotoronI2C object configured to use the general call address (0).
mc = motoron.MotoronI2C(address=0)

# The next address this program will try to use when you send an "a" command
# to automatically assign an address.
next_address = 17

# This function defines which I2C addresses this program is
# allowed to communicate with.
def allow_address_communication(address):
  # Addresses cannot be larger than 127.
  if address >= 128: return False

  # If you have devices on your bus and you want to prevent this
  # code from talking to them, potentially causing unwanted
  # operations, add their 7-bit addresses here with a line like this:
  # if address == 0x6B: return False

  return True

# This function defines which I2C addresses this program is allowed
# to communicate with.
def allow_address_assignment(address):
  return allow_address_communication(address) and address != 0

# Checks to see if a device is responding at the specified address.
def scan_address(address):
  if not allow_address_communication(address): return False
  try:
    mc.bus.i2c_rdwr(i2c_msg.write(address, []))
    return True
  except OSError as e:
    if e.args[0] == 6 or e.args[0] == 121: return False
    raise

def assign_address(line):
  global next_address
  desired_address_specified = False
  desired_address = next_address
  if len(line) > 1:
    try:
      desired_address = int(line[1:]) & 127
      desired_address_specified = True
    except ValueError:
      pass

  while True:
    if allow_address_assignment(desired_address):
      # Unless the address was explicitly specified by the user,
      # make sure it is not already used by some other device.
      if desired_address_specified or not scan_address(desired_address):
        break
      print("Found a device at address %d." % desired_address)

    elif desired_address_specified:
      print("Assignment to address %d not allowed." % desired_address)

    # Try the next higher address.
    while True:
      desired_address = (desired_address + 1) & 127
      if allow_address_assignment(desired_address): break

  mc.enable_crc()

  # Send a command to set the EEPROM device number to the desired
  # address.  This command will only be received by Motorons that
  # are configured to listen to the general call address (which is
  # the default) and will only be obeyed by Motorons that have JMP1
  # shorted to GND.
  mc.write_eeprom_device_number(desired_address)

  print("Assigned address", desired_address)
  next_address = desired_address + 1

def scan_for_devices():
  print("Scanning for I2C devices...")
  for i in range(0, 128):
    if scan_address(i):
      print("Found device at address", i)

# Note: This routine writes to many different addresses on your
# I2C bus.  If you have any non-Motoron devices on your bus,
# this could cause unexpected changes to those devices.
# You can modify allow_address_communication() to prevent this.
def identify_devices():
  print("Identifying Motoron controllers...")
  for i in range(1, 128):
    if not allow_address_communication(i): continue
    test = motoron.MotoronI2C(bus=mc.bus, address=i)
    try:
      # Multiple Motorons on the same address sending different responses will
      # cause CRC errors but we would like to ignore them.
      test.disable_crc_for_responses()
      v = test.get_firmware_version()
      jumper_state = test.get_jumper_state() & 3
    except OSError:
      continue
    jumper_string = ['both', 'on', 'off', 'err'][jumper_state]
    print("%3d: product=0x%04X version=%x.%02x JMP1=%s" % (i, v['product_id'],
      v['firmware_version']['major'], v['firmware_version']['minor'], jumper_string))

def process_input_line(line):
  if not line: return
  elif line[0] == 'a': assign_address(line)
  elif line[0] == 'r':
    print("Reset")
    mc.reset()
  elif line[0] == 's': scan_for_devices()
  elif line[0] == 'i': identify_devices()
  elif line[0] == 'h' or line[0] == 'H' or line[0] == '?': print(help_message)
  elif line == 'q' or line == 'quit': sys.exit(0)
  else: print("Error: Unreocgnized command.  Type h for help.")

print(start_message)
try:
  while True:
    process_input_line(input('Enter command: '))
except (KeyboardInterrupt, EOFError):
  print()

