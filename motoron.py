# Copyright (C) Pololu Corporation.  See LICENSE.txt for details.

import math
import os
import struct
import time

try:
  from enum import Enum
  def enum_value(x): return x.value
except ImportError:
  Enum = object
  def enum_value(x): return x

from motoron_protocol import *

## \file motoron.py
##
## This is the main file for the Motoron Motor Controller Python library for
## Raspberry Pi.
##
## For more information about the library, see the main repository at:
## https://github.com/pololu/motoron-python

class CurrentSenseType(Enum):
  MOTORON_18V18 = 0b0001
  MOTORON_24V14 = 0b0101
  MOTORON_18V20 = 0b1010
  MOTORON_24V16 = 0b1101

class VinSenseType(Enum):
  MOTORON_256 =  0b0000  # M*256 Motorons
  MOTORON_HP  =  0b0010  # High-power Motorons
  MOTORON_550 =  0b0011  # M*550 Motorons

class MotoronBase():
  """
  Represents a connection to a Pololu Motoron Motoron Controller.
  """

  __DEFAULT_PROTOCOL_OPTIONS = (
    (1 << PROTOCOL_OPTION_I2C_GENERAL_CALL) |
    (1 << PROTOCOL_OPTION_CRC_FOR_COMMANDS) |
    (1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  ## The default value of the Motoron's "Error mask" variable.
  DEFAULT_ERROR_MASK = (
    (1 << STATUS_FLAG_COMMAND_TIMEOUT) |
    (1 << STATUS_FLAG_RESET))

  def __init__(self):
    ## The bits in this variable are defined by the
    ## motoron.PROTOCOL_OPTION_* constants.  See set_protocol_options().
    self.protocol_options = MotoronBase.__DEFAULT_PROTOCOL_OPTIONS

  def get_firmware_version(self):
    """
    Sends the "Get firmware version" command to get the device's firmware
    product ID and firmware version numbers.

    For more information, see the "Get firmware version"
    command in the Motoron user's guide.

    \return A dictionary in this format:
    ```{.py}
    {'product_id': 204, 'firmware_version': {'major': 1, 'minor': 0}}
    ```
    """
    cmd = [CMD_GET_FIRMWARE_VERSION]
    response = self._send_command_and_read_response(cmd, 4)
    product_id, minor, major = struct.unpack('<HBB', response)
    return {
      'product_id': product_id,
      'firmware_version': {'major': major, 'minor': minor}
    }

  def set_protocol_options(self, options):
    """
    Sends the "Set protocol options" command to the device to specify options
    related to how the device processes commands and sends responses.
    The options are also saved in this object and are used later
    when sending other commands or reading responses.

    When CRC for commands is enabled, this library generates the CRC
    byte and appends it to the end of each command it sends.  The Motoron
    checks it to help ensure the command was received correctly.

    When CRC for responses is enabled, this library reads the CRC byte sent
    by the Motoron in its responses and makes sure it is correct.  If the
    response CRC byte is incorrect, get_last_error() will return a non-zero
    error code after the command has been run.

    When the I2C general call address is enabled, the Motoron receives
    commands sent to address 0 in addition to its usual I2C address.
    The general call address is write-only; reading bytes from it is not
    supported.

    By default (in this libary and the Motoron itself), CRC for commands and
    responses is enabled, and the I2C general call address is enabled.

    This method always sends its command with a CRC byte, so it will work
    even if CRC was previously disabled but has been re-enabled on the device
    (e.g. due to a reset).

    The @p options argument should be 0 or combination of the following
    expressions made using the bitwise or operator (|):
    - (1 << motoron.PROTOCOL_OPTION_CRC_FOR_COMMANDS)
    - (1 << motoron.PROTOCOL_OPTION_CRC_FOR_RESPONSES)
    - (1 << motoron.PROTOCOL_OPTION_I2C_GENERAL_CALL)

    For more information, see the "Set protocol optons"
    command in the Motoron user's guide.

    @sa enable_crc(), disable_crc(),
      enable_crc_for_commands(), disable_crc_for_commands(),
      enable_crc_for_responses(), disable_crc_for_responses(),
      enable_i2c_general_call(), disable_i2c_general_call()
    """
    self.protocol_options = options
    cmd = [
      CMD_SET_PROTOCOL_OPTIONS,
      options & 0x7F,
      ~options & 0x7F
    ]
    self._send_command_core(cmd, True)

  def set_protocol_options_locally(self, options):
    """
    Sets the protocol options for this object, without sending a command to
    the Motoron.

    If the options you specify here do not match the actual configuration of
    the Motoron, future communication could fail.

    Most users should use set_protocol_options() instead of this.
    """
    self.protocol_options = options

  def enable_crc(self):
    """
    Enables CRC for commands and responses.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      | (1 << PROTOCOL_OPTION_CRC_FOR_COMMANDS)
      | (1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def disable_crc(self):
    """
    Disables CRC for commands and responses.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << PROTOCOL_OPTION_CRC_FOR_COMMANDS)
      & ~(1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def enable_crc_for_commands(self):
    """
    Enables CRC for commands.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      | (1 << PROTOCOL_OPTION_CRC_FOR_COMMANDS))

  def disable_crc_for_commands(self):
    """
    Disables CRC for commands.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << PROTOCOL_OPTION_CRC_FOR_COMMANDS))

  def enable_crc_for_responses(self):
    """
    Enables CRC for responses.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      | (1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def disable_crc_for_responses(self):
    """
    Disables CRC for responses.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def enable_i2c_general_call(self):
    """
    Enables the I2C general call address.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      | (1 << PROTOCOL_OPTION_I2C_GENERAL_CALL))

  def disable_i2c_general_call(self):
    """
    Disables the I2C general call address.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << PROTOCOL_OPTION_I2C_GENERAL_CALL))

  def read_eeprom(self, offset, length):
    """
    Reads the specified bytes from the Motoron's EEPROM memory.

    For more information, see the "Read EEPROM" command in the
    Motoron user's guide.
    """
    cmd = [
      CMD_READ_EEPROM,
      offset & 0x7F,
      length & 0x7F,
    ]
    return self._send_command_and_read_response(cmd, length)

  def read_eeprom_device_number(self):
    """
    Reads the EEPROM device number from the device.
    This is the I2C address that the device uses if it detects that JMP1
    is shorted to GND when it starts up.  It is stored in non-volatile
    EEPROM memory.
    """
    return self.read_eeprom(SETTING_DEVICE_NUMBER, 1)[0]

  def write_eeprom(self, offset, value):
    """
    Writes a value to one byte in the Motoron's EEPROM memory.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron's microcontroller is only rated for
    100,000 erase/write cycles.**

    For more information, see the "Write EEPROM" command in the
    Motoron user's guide.
    """
    cmd = [
      CMD_WRITE_EEPROM,
      offset & 0x7F,
      value & 0x7F,
      (value >> 7) & 1,
    ]
    cmd += [
      cmd[1] ^ 0x7F,
      cmd[2] ^ 0x7F,
      cmd[3] ^ 0x7F,
    ]
    self._send_command(cmd)
    time.sleep(0.006)

  def write_eeprom16(self, offset, value):
    """
    Writes a 2-byte value in the Motoron's EEPROM memory.

    This command only has an effect if JMP1 is shorted to GND.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron’s microcontroller is only rated for
    100,000 erase/write cycles.
    """
    self.write_eeprom(offset, value & 0xFF)
    self.write_eeprom(offset + 1, value >> 8 & 0xFF)

  def write_eeprom_device_number(self, number):
    """
    Writes to the EEPROM device number, changing it to the specified value.

    This command only has an effect if JMP1 is shorted to GND.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron's microcontroller is only rated for
    100,000 erase/write cycles.**
    """
    self.write_eeprom(SETTING_DEVICE_NUMBER, number & 0x7F)
    self.write_eeprom(SETTING_DEVICE_NUMBER + 1, number >> 7 & 0x7F)

  def write_eeprom_alternative_device_number(self, number):
    """
    Writes to the alternative device number stored in EEPROM, changing it to
    the specified value.

    This function is only useful on Motorons with a serial interface,
    and only has an effect if JMP1 is shorted to GND.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron's microcontroller is only rated for
    100,000 erase/write cycles.**

    @sa write_eeprom_disable_alternative_device_number()
    """
    self.write_eeprom(SETTING_ALTERNATIVE_DEVICE_NUMBER, (number & 0x7F) | 0x80)
    self.write_eeprom(SETTING_ALTERNATIVE_DEVICE_NUMBER + 1, number >> 7 & 0x7F)

  def write_eeprom_disable_alternative_device_number(self):
    """
    Writes to EEPROM to disable the alternative device number.

    This function is only useful on Motorons with a serial interface,
    and only has an effect if JMP1 is shorted to GND.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron's microcontroller is only rated for
    100,000 erase/write cycles.**

    @sa write_eeprom_alternative_device_number()
    """
    self.write_eeprom(SETTING_ALTERNATIVE_DEVICE_NUMBER, 0)
    self.write_eeprom(SETTING_ALTERNATIVE_DEVICE_NUMBER + 1, 0)

  def write_eeprom_communication_options(self, options):
    """
    Writes to the serial options byte stored in EEPROM, changing it to
    the specified value.

    The bits in this byte are defined by the
    MOTORON_COMMUNICATION_OPTION_* constants.

    This function is only useful on Motorons with a serial interface,
    and only has an effect if JMP1 is shorted to GND.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron's microcontroller is only rated for
    100,000 erase/write cycles.**
    """
    self.write_eeprom(SETTING_COMMUNICATION_OPTIONS, options)

  def write_eeprom_baud_rate(self, baud):
    """
    Writes to the baud rate stored in EEPROM, changing it to the
    specified value.

    This function is only useful on Motorons with a serial interface,
    and only has an effect if JMP1 is shorted to GND.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron's microcontroller is only rated for
    100,000 erase/write cycles.**
    """
    if (baud < MIN_BAUD_RATE): baud = MIN_BAUD_RATE
    if (baud > MAX_BAUD_RATE): baud = MAX_BAUD_RATE
    self.write_eeprom16(SETTING_BAUD_DIVIDER, round(16000000 / baud))

  def write_eeprom_response_delay(self, delay):
    """
    Writes to the serial response delay setting stored in EEPROM, changing
    it to the specified value, in units of microseconds.

    This function is only useful on Motorons with a serial interface,
    and only has an effect if JMP1 is shorted to GND.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron's microcontroller is only rated for
    100,000 erase/write cycles.**
    """
    self.write_eeprom(SETTING_RESPONSE_DELAY, delay)

  def reinitialize(self):
    """
    Sends a "Reinitialize" command to the Motoron, which resets most of the
    Motoron's variables to their default state.

    For more information, see the "Reinitialize" command in the Motoron
    user's guide.

    @sa reset()
    """
    # Always send the reinitialize command with a CRC byte to make it more reliable.
    cmd = [CMD_REINITIALIZE]
    self._send_command_core(cmd, True)
    self.protocol_options = MotoronBase.__DEFAULT_PROTOCOL_OPTIONS

  def reset(self, ignore_nack=True):
    """
    Sends a "Reset" command to the Motoron, which does a full hardware reset.

    This command is equivalent to briefly driving the Motoron's RST pin low.
    The Motoron's RST is briefly driven low by the Motoron itself as a
    result of this command.

    After running this command, we recommend waiting for at least 5
    milliseconds before you try to communicate with the Motoron.

    @param ignore_nack Optional argument: if `True` (the default), this method
      ignores a NACK error if it occurs on sending the Reset command. This is
      useful in case the Motoron has CRC off and executes the reset before it
      can ACK the CRC byte (which this method always sends to make it more
      reliable).

    @sa reinitialize()
    """
    # Always send the reset command with a CRC byte to make it more reliable.
    cmd = [CMD_RESET]
    try:
      self._send_command_core(cmd, True)
    except OSError as e:
      # Errno 5 (Input/output error) or 121 (Remote I/O error) indicates a
      # NACK of a data byte.  Ignore it if the ignore_nack argument is True.
      # In all other cases, re-raise the exception.
      if not (ignore_nack and (e.args[0] == 5 or e.args[0] == 121)): raise
    self.protocol_options = MotoronBase.__DEFAULT_PROTOCOL_OPTIONS

  def get_variables(self, motor, offset, length):
    """
    Reads information from the Motoron using a "Get variables" command.

    This library has helper methods to read every variable, but this method
    is useful if you want to get the raw bytes, or if you want to read
    multiple consecutive variables at the same time for efficiency.

    @param motor 0 to read general variables, or a motor number to read
      motor-specific variables.
    @param offset The location of the first byte to read.
    @param length How many bytes to read.
    """
    cmd = [
      CMD_GET_VARIABLES,
      motor & 0x7F,
      offset & 0x7F,
      length & 0x7F,
    ]
    return self._send_command_and_read_response(cmd, length)

  def get_var_u8(self, motor, offset):
    """
    Reads one byte from the Motoron using a "Get variables" command
    and returns the result as an unsigned 8-bit integer.

    @param motor 0 to read a general variable, or a motor number to read
      a motor-specific variable.
    @param offset The location of the byte to read.
    """
    return self.get_variables(motor, offset, 1)[0]

  def get_var_u16(self, motor, offset):
    """
    Reads two bytes from the Motoron using a "Get variables" command
    and returns the result as an unsigned 16-bit integer.

    @param motor 0 to read general variables, or a motor number to read
      motor-specific variables.
    @param offset The location of the first byte to read.
    """
    buffer = self.get_variables(motor, offset, 2)
    return struct.unpack('<H', buffer)[0]

  def get_var_s16(self, motor, offset):
    """
    Reads two bytes from the Motoron using a "Get variables" command
    and returns the result as a signed 16-bit integer.

    @param motor 0 to read general variables, or a motor number to read
      motor-specific variables.
    @param offset The location of the first byte to read.
    """
    buffer = self.get_variables(motor, offset, 2)
    return struct.unpack('<h', buffer)[0]

  def get_status_flags(self):
    """
    Reads the "Status flags" variable from the Motoron.

    The bits in this variable are defined by the STATUS_FLAGS_*
    constants in the motoron package:

    - motoron.STATUS_FLAG_PROTOCOL_ERROR
    - motoron.STATUS_FLAG_CRC_ERROR
    - motoron.STATUS_FLAG_COMMAND_TIMEOUT_LATCHED
    - motoron.STATUS_FLAG_MOTOR_FAULT_LATCHED
    - motoron.STATUS_FLAG_NO_POWER_LATCHED
    - motoron.STATUS_FLAG_RESET
    - motoron.STATUS_FLAG_COMMAND_TIMEOUT
    - motoron.STATUS_FLAG_MOTOR_FAULTING
    - motoron.STATUS_FLAG_NO_POWER
    - motoron.STATUS_FLAG_ERROR_ACTIVE
    - motoron.STATUS_FLAG_MOTOR_OUTPUT_ENABLED
    - motoron.STATUS_FLAG_MOTOR_DRIVING

    Here is some example code that uses bitwise operators to check
    whether there is currently a motor fault or a lack of power:

    ```{.py}
    mask = ((1 << motoron.STATUS_FLAG_NO_POWER) |
      (1 << motoron.STATUS_FLAG_MOTOR_FAULTING))
    if mc.get_status_flags() & mask: # do something
    ```

    This library has helper methods that make it easier if you just want to
    read a single bit:

    - get_protocol_error_flag()
    - get_crc_error_flag()
    - get_command_timeout_latched_flag()
    - get_motor_fault_latched_flag()
    - get_no_power_latched_flag()
    - get_reset_flag()
    - get_motor_faulting_flag()
    - get_no_power_flag()
    - get_error_active_flag()
    - get_motor_output_enabled_flag()
    - get_motor_driving_flag()

    The clear_latched_status_flags() method sets the specified set of latched
    status flags to 0.  The reinitialize() and reset() commands reset the
    latched status flags to their default values.

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return self.get_var_u16(0, VAR_STATUS_FLAGS)

  def get_protocol_error_flag(self):
    """
    Returns the "Protocol error" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_PROTOCOL_ERROR))

  def get_crc_error_flag(self):
    """
    Returns the "CRC error" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_CRC_ERROR))

  def get_command_timeout_latched_flag(self):
    """
    Returns the "Command timeout latched" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_COMMAND_TIMEOUT_LATCHED))

  def get_motor_fault_latched_flag(self):
    """
    Returns the "Motor fault latched" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_MOTOR_FAULT_LATCHED))

  def get_no_power_latched_flag(self):
    """
    Returns the "No power latched" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_NO_POWER_LATCHED))

  def get_reset_flag(self):
    """
    Returns the "Reset" bit from get_status_flags().

    This bit is set to 1 when the Motoron powers on, its processor is
    reset (e.g. by reset()), or it receives a reinitialize() command.
    It can be cleared using clear_reset_flag() or clear_latched_status_flags().

    By default, the Motoron is configured to treat this bit as an error,
    so you will need to clear it before you can turn on the motors.

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_RESET))

  def get_motor_faulting_flag(self):
    """
    Returns the "Motor faulting" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_MOTOR_FAULTING))

  def get_no_power_flag(self):
    """
    Returns the "No power" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_NO_POWER))

  def get_error_active_flag(self):
    """
    Returns the "Error active" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_ERROR_ACTIVE))

  def get_motor_output_enabled_flag(self):
    """
    Returns the "Motor output enabled" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_MOTOR_OUTPUT_ENABLED))

  def get_motor_driving_flag(self):
    """
    Returns the "Motor driving" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << STATUS_FLAG_MOTOR_DRIVING))

  def get_vin_voltage(self):
    """
    Reads voltage on the Motoron's VIN pin, in raw device units.

    For more information, see the "VIN voltage" variable in the Motoron
    user's guide.

    @sa get_vin_voltage_mv()
    """
    return self.get_var_u16(0, VAR_VIN_VOLTAGE)

  def get_vin_voltage_mv(self, reference_mv=3300, type=VinSenseType.MOTORON_256):
    """
    Reads the voltage on the Motoron's VIN pin and converts it to millivolts.

    For more information, see the "VIN voltage" variable in the Motoron
    user's guide.

    @param reference_mv The logic voltage of the Motoron, in millivolts.
      This is assumed to be 3300 by default.
    @param type Specifies what type of Motoron you are using.  This should be one
      of the members of the motoron.VinSenseType enum.

    @sa get_vin_voltage()
    """
    scale = 459 if enum_value(type) & 1 else 1047
    return self.get_vin_voltage() * reference_mv / 1024 * scale / 47

  def get_command_timeout_milliseconds(self):
    """
    Reads the "Command timeout" variable and converts it to milliseconds.

    For more information, see the "Command timeout" variable in the Motoron
    user's guide.

    @sa set_command_timeout_milliseconds()
    """
    return self.get_var_u16(0, VAR_COMMAND_TIMEOUT) * 4

  def get_error_response(self):
    """
    Reads the "Error response" variable, which defines how the Motoron will
    stop its motors when an error is happening.

    For more information, see the "Error response" variable in the Motoron
    user's guide.

    @sa set_error_response()
    """
    return self.get_var_u8(0, VAR_ERROR_RESPONSE)

  def get_error_mask(self):
    """
    Reads the "Error mask" variable, which defines which status flags are
    considered to be errors.

    For more information, see the "Error mask" variable in the Motoron
    user's guide.

    @sa set_error_mask()
    """
    return self.get_var_u16(0, VAR_ERROR_MASK)

  def get_jumper_state(self):
    """
    Reads the "Jumper state" variable.

    For more information, see the "Jumper state" variable in the Motoron
    user's guide
    """
    return self.get_var_u8(0, VAR_JUMPER_STATE)

  def get_target_speed(self, motor):
    """
    Reads the target speed of the specified motor, which is the speed at
    which the motor has been commanded to move.

    For more information, see the "Target speed" variable in the Motoron
    user's guide.

    @sa set_speed(), set_all_speeds(), set_all_speeds_using_buffers()
    """
    return self.get_var_s16(motor, MVAR_TARGET_SPEED)

  def get_target_brake_amount(self, motor):
    """
    Reads the target brake amount for the specified motor.

    For more information, see the "Target speed" variable in the Motoron
    user's guide.

    @sa set_target_brake_amount()
    """
    return self.get_var_u16(motor, MVAR_TARGET_BRAKE_AMOUNT)

  def get_current_speed(self, motor):
    """
    Reads the current speed of the specified motor, which is the speed that
    the Motoron is currently trying to apply to the motor.

    For more information, see the "Target speed" variable in the Motoron
    user's guide.

    @sa set_speed_now(), set_all_speeds_now(), set_all_speeds_now_using_buffers()
    """
    return self.get_var_s16(motor, MVAR_CURRENT_SPEED)

  def get_buffered_speed(self, motor):
    """
    Reads the buffered speed of the specified motor.

    For more information, see the "Buffered speed" variable in the Motoron
    user's guide.

    @sa set_buffered_speed(), set_all_buffered_speeds()
    """
    return self.get_var_s16(motor, MVAR_BUFFERED_SPEED)

  def get_pwm_mode(self, motor):
    """
    Reads the PWM mode of the specified motor.

    For more information, see the "PWM mode" variable in the Motoron
    user's guide.

    @sa set_pwm_mode()
    """
    return self.get_var_u8(motor, MVAR_PWM_MODE)

  def get_max_acceleration_forward(self, motor):
    """
    Reads the maximum acceleration of the specified motor for the forward
    direction.

    For more information, see the "Max acceleration forward" variable in the
    Motoron user's guide.

    @sa set_max_acceleration(), set_max_acceleration_forward()
    """
    return self.get_var_u16(motor, MVAR_MAX_ACCEL_FORWARD)

  def get_max_acceleration_reverse(self, motor):
    """
    Reads the maximum acceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max acceleration reverse" variable in the
    Motoron user's guide.

    @sa set_max_acceleration(), set_max_acceleration_reverse()
    """
    return self.get_var_u16(motor, MVAR_MAX_ACCEL_REVERSE)

  def get_max_deceleration_forward(self, motor):
    """
    Reads the maximum deceleration of the specified motor for the forward
    direction.

    For more information, see the "Max deceleration forward" variable in the
    Motoron user's guide.

    @sa set_max_deceleration(), set_max_deceleration_forward()
    """
    return self.get_var_u16(motor, MVAR_MAX_DECEL_FORWARD)

  def get_max_deceleration_reverse(self, motor):
    """
    Reads the maximum deceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max deceleration reverse" variable in the
    Motoron user's guide.

    @sa set_max_deceleration(), set_max_deceleration_reverse()
    """
    return self.get_var_u16(motor, MVAR_MAX_DECEL_REVERSE)


# @cond

  # This function is used by Pololu for testing.
  def get_max_deceleration_temporary(self, motor):
    return self.get_var_u16(motor, MVAR_MAX_DECEL_TMP)

# \endcond

  def get_starting_speed_forward(self, motor):
    """
    Reads the starting speed for the specified motor in the forward direction.

    For more information, see the "Starting speed forward" variable in the
    Motoron user's guide.

    @sa set_starting_speed(), set_starting_speed_forward()
    """
    return self.get_var_u16(motor, MVAR_STARTING_SPEED_FORWARD)

  def get_starting_speed_reverse(self, motor):
    """
    Reads the starting speed for the specified motor in the reverse direction.

    For more information, see the "Starting speed reverse" variable in the
    Motoron user's guide.

    @sa set_starting_speed(), set_starting_speed_reverse()
    """
    return self.get_var_u16(motor, MVAR_STARTING_SPEED_REVERSE)

  def get_direction_change_delay_forward(self, motor):
    """
    Reads the direction change delay for the specified motor in the
    forward direction.

    For more information, see the "Direction change delay forward" variable
    in the Motoron user's guide.

    @sa set_direction_change_delay(), set_direction_change_delay_forward()
    """
    return self.get_var_u8(motor, MVAR_DIRECTION_CHANGE_DELAY_FORWARD)

  def get_direction_change_delay_reverse(self, motor):
    """
    Reads the direction change delay for the specified motor in the
    reverse direction.

    For more information, see the "Direction change delay reverse" variable
    in the Motoron user's guide.

    @sa set_direction_change_delay(), set_direction_change_delay_reverse()
    """
    return self.get_var_u8(motor, MVAR_DIRECTION_CHANGE_DELAY_REVERSE)

  def get_current_limit(self, motor):
    """
    Reads the current limit for the specified motor.

    This only works for the high-power Motorons.

    For more information, see the "Current limit" variable in the Motoron user's
    guide.

    @sa set_current_limit()
    """
    return self.get_var_u16(motor, MVAR_CURRENT_LIMIT)

  def get_current_sense_reading(self, motor):
    """
    Reads all the results from the last current sense measurement for the
    specified motor.

    This function reads the "Current sense raw", "Current sense speed", and
    "Current sense processed" variables from the Motoron using a single
    command, so the values returned are all guaranteed to be part of the
    same measurement.

    This only works for the high-power Motorons.

    @sa get_current_sense_raw_and_speed(), get_current_sense_processed_and_speed()
    """
    buffer = self.get_variables(motor, MVAR_CURRENT_SENSE_RAW, 6)
    raw, speed, processed = struct.unpack('<HhH', buffer)
    return { 'raw': raw, 'speed': speed, 'processed': processed }

  def get_current_sense_raw_and_speed(self, motor):
    """
    This is like get_current_sense_reading() but it only reads the raw current
    sense measurement and the speed.

    This only works for the high-power Motorons.
    """
    buffer = self.get_variables(motor, MVAR_CURRENT_SENSE_RAW, 4)
    raw, speed = struct.unpack('<Hh', buffer)
    return { 'raw': raw, 'speed': speed }

  def get_current_sense_processed_and_speed(self, motor):
    """
    This is like get_current_sense_reading() but it only reads the processed
    current sense measurement and the speed.

    This only works for the high-power Motorons.
    """
    buffer = self.get_variables(motor, MVAR_CURRENT_SENSE_SPEED, 4)
    speed, processed = struct.unpack('<hH', buffer)
    return { 'speed': speed, 'processed': processed }

  def get_current_sense_raw(self, motor):
    """
    Reads the raw current sense measurement for the specified motor.

    This only works for the high-power Motorons.

    For more information, see the "Current sense raw" variable
    in the Motoron user's guide.

    @sa get_current_sense_reading()
    """
    return self.get_var_u16(motor, MVAR_CURRENT_SENSE_RAW)


  def get_current_sense_processed(self, motor):
    """
    Reads the processed current sense reading for the specified motor.

    This only works for the high-power Motorons.

    The units of this reading depend on the logic voltage of the Motoron
    and on the specific model of Motoron that you have, and you can use
    current_sense_units_milliamps() to calculate the units.

    The accuracy of this reading can be improved by measuring the current
    sense offset and setting it with set_current_sense_offset().
    See the "Current sense processed" variable in the Motoron user's guide for
    or the current_sense_calibrate example for more information.

    Note that this reading will be 0xFFFF if an overflow happens during the
    calculation due to very high current.

    @sa get_current_sense_processed_and_speed()
    """
    return self.get_var_u16(motor, MVAR_CURRENT_SENSE_PROCESSED)

  def get_current_sense_offset(self, motor):
    """
    Reads the current sense offset setting.

    This only works for the high-power Motorons.

    For more information, see the "Current sense offset" variable in the
    Motoron user's guide.

    @sa set_current_sense_offset()
    """
    return self.get_var_u8(motor, MVAR_CURRENT_SENSE_OFFSET)

  def get_current_sense_minimum_divisor(self, motor):
    """
    Reads the current sense minimum divisor setting and returns it as a speed
    between 0 and 800.

    This only works for the high-power Motorons.

    For more information, see the "Current sense minimum divisor" variable in
    the Motoron user's guide.

    @sa set_current_sense_minimum_divisor()
    """
    return self.get_var_u8(motor, MVAR_CURRENT_SENSE_MINIMUM_DIVISOR) << 2


  def set_variable(self, motor, offset, value):
    """
    Configures the Motoron using a "Set variable" command.

    This library has helper methods to set every variable, so you should
    not need to call this function directly.

    @param motor 0 to set a general variable, or a motor number to set
      motor-specific variables.
    @param offset The address of the variable to set (only certain offsets
      are allowed).
    @param value The value to set the variable to.

    @sa get_variables()
    """
    if value > 0x3FFF: value = 0x3FFF
    cmd = [
      CMD_SET_VARIABLE,
      motor & 0x1F,
      offset & 0x7F,
      value & 0x7F,
      (value >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def set_command_timeout_milliseconds(self, ms):
    """
    Sets the command timeout period, in milliseconds.

    For more information, see the "Command timeout" variable
    in the Motoron user's guide.

    @sa disable_command_timeout(), get_command_timeout_milliseconds()
    """
    # Divide by 4, but round up.
    timeout = math.ceil(ms / 4)
    self.set_variable(0, VAR_COMMAND_TIMEOUT, timeout)

  def set_error_response(self, response):
    """
    Sets the error response, which defines how the Motoron will
    stop its motors when an error is happening.

    The response parameter should be one of these constants from the motoron
    package:

    - motoron.ERROR_RESPONSE_COAST
    - motoron.ERROR_RESPONSE_BRAKE
    - motoron.ERROR_RESPONSE_COAST_NOW
    - motoron.ERROR_RESPONSE_BRAKE_NOW

    For more information, see the "Error response" variable in the Motoron
    user's guide.

    @sa get_error_response()
    """
    self.set_variable(0, VAR_ERROR_RESPONSE, response)

  def set_error_mask(self, mask):
    """
    Sets the "Error mask" variable, which defines which status flags are
    considered to be errors.

    For more information, see the "Error mask" variable in the Motoron
    user's guide.

    @sa get_error_mask(), get_status_flags()
    """
    self.set_variable(0, VAR_ERROR_MASK, mask)

  def disable_command_timeout(self):
    """
    This disables the Motoron's command timeout feature by resetting the
    the "Error mask" variable to its default value but with the command
    timeout bit cleared.

    By default, the Motoron's command timeout will occur if no valid commands
    are received in 1500 milliseconds, and the command timeout is treated as
    an error, so the motors will shut down.  You can use this function if you
    want to disable that feature.

    Note that this function overrides any previous values you set in the
    "Error mask" variable, so if you are using set_error_mask() in your program
    to configure which status flags are treated as errors, you do not need to
    use this function and you probably should not use this function.

    @sa set_command_timeout_milliseconds(), set_error_mask()
    """
    self.set_error_mask(MotoronBase.DEFAULT_ERROR_MASK & ~(1 << STATUS_FLAG_COMMAND_TIMEOUT))

  def set_pwm_mode(self, motor, mode):
    """
    Sets the PWM mode for the specified motor.

    The mode parameter should be one of the following these constants from
    the motoron package:

    - motoron.PWM_MODE_DEFAULT (20 kHz)
    - motoron.PWM_MODE_1_KHZ 1
    - motoron.PWM_MODE_2_KHZ 2
    - motoron.PWM_MODE_4_KHZ 3
    - motoron.PWM_MODE_5_KHZ 4
    - motoron.PWM_MODE_10_KHZ 5
    - motoron.PWM_MODE_20_KHZ 6
    - motoron.PWM_MODE_40_KHZ 7
    - motoron.PWM_MODE_80_KHZ 8

    For more information, see the "PWM mode" variable in the Motoron user's
    guide.

    @sa get_pwm_mode(self)
    """
    self.set_variable(motor, MVAR_PWM_MODE, mode)

  def set_max_acceleration_forward(self, motor, accel):
    """
    Sets the maximum acceleration of the specified motor for the forward
    direction.

    For more information, see the "Max acceleration forward" variable in the
    Motoron user's guide.

    @sa set_max_acceleration(), get_max_acceleration_forward()
    """
    self.set_variable(motor, MVAR_MAX_ACCEL_FORWARD, accel)

  def set_max_acceleration_reverse(self, motor, accel):
    """
    Sets the maximum acceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max acceleration reverse" variable in the
    Motoron user's guide.

    @sa set_max_acceleration(), get_max_acceleration_reverse()
    """
    self.set_variable(motor, MVAR_MAX_ACCEL_REVERSE, accel)

  def set_max_acceleration(self, motor, accel):
    """
    Sets the maximum acceleration of the specified motor (both directions).

    If this function succeeds, it is equivalent to calling
    set_max_acceleration_forward() and set_max_acceleration_reverse().
    """
    self.set_max_acceleration_forward(motor, accel)
    self.set_max_acceleration_reverse(motor, accel)

  def set_max_deceleration_forward(self, motor, decel):
    """
    Sets the maximum deceleration of the specified motor for the forward
    direction.

    For more information, see the "Max deceleration forward" variable in the
    Motoron user's guide.

    @sa set_max_deceleration(), get_max_deceleration_forward()
    """
    self.set_variable(motor, MVAR_MAX_DECEL_FORWARD, decel)

  def set_max_deceleration_reverse(self, motor, decel):
    """
    Sets the maximum deceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max deceleration reverse" variable in the
    Motoron user's guide.

    @sa set_max_deceleration(), get_max_deceleration_reverse()
    """
    self.set_variable(motor, MVAR_MAX_DECEL_REVERSE, decel)

  def set_max_deceleration(self, motor, decel):
    """
    Sets the maximum deceleration of the specified motor (both directions).

    If this function succeeds, it is equivalent to calling
    set_max_deceleration_forward() and set_max_deceleration_reverse().
    """
    self.set_max_deceleration_forward(motor, decel)
    self.set_max_deceleration_reverse(motor, decel)

  def set_starting_speed_forward(self, motor, speed):
    """
    Sets the starting speed of the specified motor for the forward
    direction.

    For more information, see the "Starting speed forward" variable in the
    Motoron user's guide.

    @sa set_starting_speed(), get_starting_speed_forward()
    """
    self.set_variable(motor, MVAR_STARTING_SPEED_FORWARD, speed)

  def set_starting_speed_reverse(self, motor, speed):
    """
    Sets the starting speed of the specified motor for the reverse
    direction.

    For more information, see the "Starting speed reverse" variable in the
    Motoron user's guide.

    @sa set_starting_speed(), get_starting_speed_reverse()
    """
    self.set_variable(motor, MVAR_STARTING_SPEED_REVERSE, speed)

  def set_starting_speed(self, motor, speed):
    """
    Sets the starting speed of the specified motor (both directions).

    If this function succeeds, it is equivalent to calling
    set_starting_speed_forward() and set_starting_speed_reverse().
    """
    self.set_starting_speed_forward(motor, speed)
    self.set_starting_speed_reverse(motor, speed)

  def set_direction_change_delay_forward(self, motor, duration):
    """
    Sets the direction change delay of the specified motor for the forward
    direction, in units of 10 ms.

    For more information, see the "Direction change delay forward" variable
    in the Motoron user's guide.

    @sa set_direction_change_delay(), get_direction_change_delay_forward()
    """
    self.set_variable(motor, MVAR_DIRECTION_CHANGE_DELAY_FORWARD, duration)

  def set_direction_change_delay_reverse(self, motor, duration):
    """
    Sets the direction change delay of the specified motor for the reverse
    direction, in units of 10 ms.

    For more information, see the "Direction change delay reverse" variable
    in the Motoron user's guide.

    @sa set_direction_change_delay(), get_direction_change_delay_reverse()
    """
    self.set_variable(motor, MVAR_DIRECTION_CHANGE_DELAY_REVERSE, duration)

  def set_direction_change_delay(self, motor, duration):
    """
    Sets the direction change delay of the specified motor (both directions),
    in units of 10 ms.

    If this function succeeds, it is equivalent to calling
    set_direction_change_delay_forward() and set_direction_change_delay_reverse().
    """
    self.set_direction_change_delay_forward(motor, duration)
    self.set_direction_change_delay_reverse(motor, duration)

  def set_current_limit(self, motor, limit):
    """
    Sets the current limit for the specified motor.

    This only works for the high-power Motorons.

    The units of the current limit depend on the type of Motoron you have
    and the logic voltage of your system.  See the "Current limit" variable
    in the Motoron user's guide for more information, or see
    calculate_current_limit().

    @sa get_current_limit()
    """
    self.set_variable(motor, MVAR_CURRENT_LIMIT, limit)

  def set_current_sense_offset(self, motor, offset):
    """
    Sets the current sense offset setting for the specified motor.

    This is one of the settings that determines how current sense
    readings are processed.  It is supposed to be the value returned by
    get_current_sense_raw() when motor power is supplied to the Motoron and
    it is driving its motor outputs at speed 0.

    The current_sense_calibrate example shows how to measure the current
    sense offsets and load them onto the Motoron using this function.

    If you do not care about measuring motor current, you do not need to
    set this variable.

    For more information, see the "Current sense offset" variable in the
    Motoron user's guide.

    This only works for the high-power Motorons.

    @sa get_current_sense_offset()
    """
    self.set_variable(motor, MVAR_CURRENT_SENSE_OFFSET, offset)

  def set_current_sense_minimum_divisor(self, motor, speed):
    """
    Sets the current sense minimum divisor setting for the specified motor,
    given a speed between 0 and 800.

    This is one of the settings that determines how current sense
    readings are processed.

    If you do not care about measuring motor current, you do not need to
    set this variable.

    For more information, see the "Current sense minimum divisor" variable in
    the Motoron user's guide.

    This only works for the high-power Motorons.

    @sa get_current_sense_minimum_divisor()
    """
    self.set_variable(motor, MVAR_CURRENT_SENSE_MINIMUM_DIVISOR, speed >> 2)

  def coast_now(self):
    """
    Sends a "Coast now" command to the Motoron, causing all of the motors to
    immediately start coasting.

    For more information, see the "Coast now" command in the Motoron
    user's guide.
    """
    cmd = [CMD_COAST_NOW]
    self._send_command(cmd)

  def clear_motor_fault(self, flags=0):
    """
    Sends a "Clear motor fault" command to the Motoron.

    If any of the Motoron's motors chips are currently experiencing a
    fault (error), or bit 0 of the flags argument is 1, this command makes
    the Motoron attempt to recover from the faults.

    For more information, see the "Clear motor fault" command in the Motoron
    user's guide.

    @sa clear_motor_fault_unconditional(), get_motor_faulting_flag()
    """
    cmd = [ CMD_CLEAR_MOTOR_FAULT, (flags & 0x7F) ]
    self._send_command(cmd)

  def clear_motor_fault_unconditional(self):
    """
    Sends a "Clear motor fault" command to the Motoron with the
    "unconditional" flag set, so the Motoron will attempt to recover
    from any motor faults even if no fault is currently occurring.

    This is a more robust version of clear_motor_fault().
    """
    self.clear_motor_fault(1 << CLEAR_MOTOR_FAULT_UNCONDITIONAL)

  def clear_latched_status_flags(self, flags):
    """
    Clears the specified flags in get_status_flags().

    For each bit in the flags argument that is 1, this command clears the
    corresponding bit in the "Status flags" variable, setting it to 0.

    For more information, see the "Clear latched status flags" command in the
    Motoron user's guide.

    @sa get_status_flags(), set_latched_status_flags()
    """
    cmd = [
      CMD_CLEAR_LATCHED_STATUS_FLAGS,
      flags & 0x7F,
      (flags >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def clear_reset_flag(self):
    """
    Clears the Motoron's reset flag.

    The reset flag is a latched status flag in get_status_flags() that is
    particularly important to clear: it gets set to 1 after the Motoron
    powers on or experiences a reset, and it is considered to be an error
    by default, so it prevents the motors from running.  Therefore, it is
    necessary to call this function (or clear_latched_status_flags()) to clear
    the Reset flag before you can get the motors running.

    We recommend that immediately after you clear the reset flag. you should
    configure the Motoron's motor settings and error response settings.
    That way, if the Motoron experiences an unexpected reset while your system
    is running, it will stop running its motors and it will not start them
    again until all the important settings have been configured.

    @sa clear_latched_status_flags()
    """
    self.clear_latched_status_flags(1 << STATUS_FLAG_RESET)

  def set_latched_status_flags(self, flags):
    """
    Sets the specified flags in get_status_flags().

    For each bit in the flags argument that is 1, this command sets the
    corresponding bit in the "Status flags" variable to 1.

    For more information, see the "Set latched status flags" command in the
    Motoron user's guide.

    @sa get_status_flags(), set_latched_status_flags()
    """
    cmd = [
      CMD_SET_LATCHED_STATUS_FLAGS,
      flags & 0x7F,
      (flags >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def set_speed(self, motor, speed):
    """
    Sets the target speed of the specified motor.

    The current speed will start moving to the specified target speed,
    obeying any acceleration and deceleration limits.

    The motor number should be between 1 and the number of motors supported
    by the Motoron.

    The speed should be between -800 and 800.  Values outside that range
    will be clipped to -800 or 800 by the Motoron firmware.

    For more information, see the "Set speed" command in the Motoron
    user's guide.

    @sa set_speed_now(), set_all_speeds()
    """
    cmd = [
      CMD_SET_SPEED,
      motor & 0x7F,
      speed & 0x7F,
      (speed >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def set_speed_now(self, motor, speed):
    """
    Sets the target and current speed of the specified motor, ignoring
    any acceleration and deceleration limits.

    For more information, see the "Set speed" command in the Motoron
    user's guide.

    @sa set_speed(), set_all_speeds_now()
    """
    cmd = [
      CMD_SET_SPEED_NOW,
      motor & 0x7F,
      speed & 0x7F,
      (speed >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def set_buffered_speed(self, motor, speed):
    """
    Sets the buffered speed of the specified motor.

    This command does not immediately cause any change to the motor: it
    stores a speed for the specified motor in the Motoron so it can be
    used by later commands.

    For more information, see the "Set speed" command in the Motoron
    user's guide.

    @sa set_speed(), set_all_buffered_speeds(),
      set_all_speeds_using_buffers(), set_all_speeds_now_using_buffers()
    """
    cmd = [
      CMD_SET_BUFFERED_SPEED,
      motor & 0x7F,
      speed & 0x7F,
      (speed >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def set_all_speeds(self, *speeds):
    """
    Sets the target speeds of all the motors at the same time.

    The number of speed arguments you provide to this function must be equal
    to the number of motor channels your Motoron has, or else this command
    might not work.

    This is equivalent to calling set_speed() once for each motor, but it is
    more efficient because all of the speeds are sent in the same command.

    There are a few different ways you can call this method (and the related
    methods that set speeds for all the motors):

    ```{.py}
    # with separate arguments
    mc.set_all_speeds(100, -200, 300)

    # with arguments unpacked from a list
    speeds = [-400, 500, -600]
    mc.set_all_speeds(*speeds)
    ```

    For more information, see the "Set all speeds" command in the Motoron
    user's guide.

    @sa set_speed(), set_all_speeds_now(), set_all_buffered_speeds()
    """
    cmd = [CMD_SET_ALL_SPEEDS]
    for speed in speeds:
      cmd += [
        speed & 0x7F,
        (speed >> 7) & 0x7F,
      ]
    self._send_command(cmd)

  def set_all_speeds_now(self, *speeds):
    """
    Sets the target and current speeds of all the motors at the same time.

    The number of speed arguments you provide to this function must be equal
    to the number of motor channels your Motoron has, or else this command
    might not work.

    This is equivalent to calling set_speed_now() once for each motor, but it is
    more efficient because all of the speeds are sent in the same command.

    For more information, see the "Set all speeds" command in the Motoron
    user's guide.

    @sa set_speed(), set_speed_now(), set_all_speeds()
    """
    cmd = [CMD_SET_ALL_SPEEDS_NOW]
    for speed in speeds:
      cmd += [
        speed & 0x7F,
        (speed >> 7) & 0x7F,
      ]
    self._send_command(cmd)

  def set_all_buffered_speeds(self, *speeds):
    """
    Sets the buffered speeds of all the motors.

    The number of speed arguments you provide to this function must be equal
    to the number of motor channels your Motoron has, or else this command
    might not work.

    This command does not immediately cause any change to the motors: it
    stores speed for each motor in the Motoron so they can be used by later
    commands.

    For more information, see the "Set all speeds" command in the Motoron
    user's guide.

    @sa set_speed(), set_buffered_speed(), set_all_speeds(),
      set_all_speeds_using_buffers(), set_all_speeds_now_using_buffers()
    """
    cmd = [CMD_SET_ALL_BUFFERED_SPEEDS]
    for speed in speeds:
      cmd += [
        speed & 0x7F,
        (speed >> 7) & 0x7F,
      ]
    self._send_command(cmd)

  def set_all_speeds_using_buffers(self):
    """
    Sets each motor's target speed equal to the buffered speed.

    This command is the same as set_all_speeds() except that the speeds are
    provided ahead of time using set_buffered_speed() or set_all_buffered_speeds().

    @sa set_all_speeds_now_using_buffers(), set_buffered_speed(),
      set_all_buffered_speeds()
    """
    cmd = [CMD_SET_ALL_SPEEDS_USING_BUFFERS]
    self._send_command(cmd)

  def set_all_speeds_now_using_buffers(self):
    """
    Sets each motor's target speed and current speed equal to the buffered
    speed.

    This command is the same as set_all_speeds_now() except that the speeds are
    provided ahead of time using set_buffered_speed() or set_all_buffered_speeds().

    @sa set_all_speeds_using_buffers(), set_buffered_speed(),
      set_all_buffered_speeds()
    """
    cmd = [CMD_SET_ALL_SPEEDS_NOW_USING_BUFFERS]
    self._send_command(cmd)

  def set_braking(self, motor, amount):
    """
    Commands the motor to brake, coast, or something in between.

    Sending this command causes the motor to decelerate to speed 0 obeying
    any relevant deceleration limits.  Once the current speed reaches 0, the
    motor will attempt to brake or coast as specified by this command, but
    due to hardware limitations it might not be able to.

    The motor number parameter should be between 1 and the number of motors
    supported by the Motoron.

    The amount parameter gets stored in the "Target brake amount" variable
    for the motor and should be between 0 (coasting) and 800 (braking).
    Values above 800 will be clipped to 800 by the Motoron firmware.

    See the "Set braking" command in the Motoron user's guide for more
    information.

    @sa set_braking_now(), get_target_brake_amount()
    """
    cmd = [
      CMD_SET_BRAKING,
      motor & 0x7F,
      amount & 0x7F,
      (amount >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def set_braking_now(self, motor, amount):
    """
    Commands the motor to brake, coast, or something in between.

    Sending this command causes the motor's current speed to change to 0.
    The motor will attempt to brake or coast as specified by this command,
    but due to hardware limitations it might not be able to.

    The motor number parameter should be between 1 and the number of motors
    supported by the Motoron.

    The amount parameter gets stored in the "Target brake amount" variable
    for the motor and should be between 0 (coasting) and 800 (braking).
    Values above 800 will be clipped to 800 by the Motoron firmware.

    See the "Set braking" command in the Motoron user's guide for more
    information.

    @sa set_braking(), get_target_brake_amount()
    """
    cmd = [
      CMD_SET_BRAKING_NOW,
      motor & 0x7F,
      amount & 0x7F,
      (amount >> 7) & 0x7F,
    ]
    self._send_command(cmd)

  def reset_command_timeout(self):
    """
    Resets the command timeout.

    This prevents the command timeout status flags from getting set for some
    time.  (The command timeout is also reset by every other Motoron command,
    as long as its parameters are valid.)

    For more information, see the "Reset command timeout" command in the
    Motoron user's guide.

    @sa disable_command_timeout(), set_command_timeout_milliseconds()
    """
    cmd = [CMD_RESET_COMMAND_TIMEOUT]
    self._send_command(cmd)

  def _send_command(self, cmd):
    send_crc = bool(self.protocol_options & (1 << PROTOCOL_OPTION_CRC_FOR_COMMANDS))
    self._send_command_core(cmd, send_crc)

  def _send_command_and_read_response(self, cmd, response_length):
    self._send_command(cmd)
    return self._read_response(response_length)

def calculate_current_limit(milliamps, type, reference_mv, offset):
  """
  Calculates a current limit value that can be passed to the Motoron
  using set_current_limit().

  @param milliamps The desired current limit, in units of mA.
  @param type Specifies what type of Motoron you are using.  This should be one
    of the members of the motoron.CurrentSenseType enum.
  @param reference_mv The reference voltage (IOREF), in millivolts.
    For example, use 3300 for a 3.3 V system or 5000 for a 5 V system.
  @param offset The offset of the raw current sense signal for the Motoron
    channel.  This is the same measurement that you would put into the
    Motoron's "Current sense offset" variable using set_current_sense_offset(),
    so see the documentation of that function for more info.
    The offset is typically 10 for 5 V systems and 15 for 3.3 V systems,
    (50*1024/reference_mv) but it can vary widely.
  """
  if milliamps > 1000000: milliamps = 1000000
  limit = offset * 125 / 128 + milliamps * 20 / (reference_mv * (enum_value(type) & 3))
  if limit > 1000: limit = 1000
  return math.floor(limit)

def current_sense_units_milliamps(type, reference_mv):
  """
  Calculates the units for the Motoron's current sense reading returned by
  get_current_sense_processed(), in milliamps.

  To convert a reading from get_current_sense_processed() to milliamps
  multiply it by the value returned from this function.

  @param type Specifies what type of Motoron you are using.  This should be one
    of the members of the motoron.CurrentSenseType enum.
  @param reference_mv The reference voltage (IOREF), in millivolts.
    For example, use 3300 for a 3.3 V system or 5000 for a 5 V system.
  """
  return reference_mv * (enum_value(type) & 3) * 25 / 512

class MotoronI2C(MotoronBase):
  """
  Represents an I2C connection to a Pololu Motoron Motor Controller.
  """

  def __init__(self, *, bus=1, address=16):
    """
    Creates a new MotoronI2C object to communicate with the Motoron over I2C.

    @param bus Optional argument that specifies which I2C bus to use.
      This can be an integer, an SMBus object from the smbus2 package, or an
      object with an interface similar to SMBus.
      The default bus is 1, which corresponds to `/dev/i2c-1`.
    @param address Optional argument that specifies the 7-bit I2C address to
      use.  This must match the address that the Motoron is configured to use.
      The default address is 16.
    """
    super().__init__()

    self.set_bus(bus)

    ## The 7-bit I2C address used by this object. The default is 16.
    self.address = address

    """
    Configures this object to use the specified I2C bus object.

    The bus argument should be one of the following:
    - The number of an I2C bus to open with smbus2
      (e.g. 2 for `/dev/i2c-2`)
    - An SMBus object from smbus2.
    - A machine.I2C object from MicroPython.
    """
  def set_bus(self, bus):
    if isinstance(bus, int):
      import smbus2
      bus = smbus2.SMBus(bus)

    try:
      bus.i2c_rdwr
      type_is_smbus = True
    except AttributeError:
      type_is_smbus = False

    if type_is_smbus:
      self._send_command_core = self._smbus_send_command_core
      self._read_response = self._smbus_read_response
      import smbus2
      self._msg = smbus2.i2c_msg
    else:
      self._send_command_core = self._mpy_send_command_core
      self._read_response = self._mpy_read_response

    self.bus = bus

  def _smbus_send_command_core(self, cmd, send_crc):
    if send_crc:
      write = self._msg.write(self.address, cmd + [calculate_crc(cmd)])
    else:
      write = self._msg.write(self.address, cmd)
    self.bus.i2c_rdwr(write)

  def _smbus_read_response(self, length):
    # On some Raspberry Pis with buggy implementations of I2C clock stretching,
    # sleeping for 0.5 ms might be necessary in order to give the Motoron time
    # to prepare its response, so it does not need to stretch the clock.
    time.sleep(0.0005)

    crc_enabled = bool(self.protocol_options & (1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))
    read = self._msg.read(self.address, length + crc_enabled)
    self.bus.i2c_rdwr(read)
    response = bytes(read)
    if crc_enabled:
      crc = response[-1]
      response = response[:-1]
      if crc != calculate_crc(response):
        raise RuntimeError('Incorrect CRC received.')
    return response

  def _mpy_send_command_core(self, cmd, send_crc):
    if send_crc:
      self.bus.writeto(self.address, bytes(cmd + [calculate_crc(cmd)]))
    else:
      self.bus.writeto(self.address, bytes(cmd))

  def _mpy_read_response(self, length):
    crc_enabled = bool(self.protocol_options & (1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))
    response = self.bus.readfrom(self.address, length + crc_enabled)
    if crc_enabled:
      crc = response[-1]
      response = response[:-1]
      if crc != calculate_crc(response):
        raise RuntimeError('Incorrect CRC received.')
    return response


class MotoronSerial(MotoronBase):
  """
  Represents a serial connection to a Pololu Motoron Motor Controller.
  """

  def __init__(self, *, port=None, device_number=None):
    """
    Creates a new MotoronSerial object.

    The `deviceNumber` argument is optional.  If it is omitted or None,
    the object will use the compact protocol.

    The `port` argument specifies the serial port to use and is passed
    directly to set_port().
    """
    super().__init__()

    self.set_port(port)

    ## The device number that will be included in commands sent by this object.
    ## The default is None, which means to not send a device number and use the
    ## compact protocol instead.
    self.device_number = device_number

    ## The serial options used by this object.  This must match the serial
    ## options in the EEPROM of the Motoron you are communicating with.
    ## The default is 7-bit device numbers and 8-bit responses.
    ##
    ## The bits in this variable are defined by the
    ## motoron.COMMUNICATION_OPTION_* constants.  The bits that affect the
    ## behavior of this library are:
    ## - motoron.COMMUNICATION_OPTION_7BIT_RESPONSES
    ## - motoron.COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER
    self.communication_options = 0

  def set_port(self, port):
    """
    Configures this object to use the specified serial port object.

    The port argument should be one of the following:
    - The name of a serial port to open with pyserial
      (e.g. "COM6" or "/dev/ttyS0")
    - A Serial object from pyserial.
    - A machine.UART object from MicroPython.
    """
    if isinstance(port, str):
      import serial
      self.port = serial.Serial(port, 115200, timeout=0.1, write_timeout=0.1)
    else:
      ## The serial port used by this object.  See set_port().
      self.port = port

  def expect_7bit_responses(self):
    """
    Configures this object to work with Motorons that are configured to send
    7-bit serial responses.
    """
    self.communication_options |= (1 << COMMUNICATION_OPTION_7BIT_RESPONSES)

  def expect_8bit_responses(self):
    """
    Configures this object to work with Motorons that are configured to send
    responses in the normal 8-bit format.
    """
    self.communication_options &= ~(1 << COMMUNICATION_OPTION_7BIT_RESPONSES)

  def use_14bit_device_number(self):
    """
    Configures this object to send 14-bit device numbers when using the
    Pololu protocol, instead of the default 7-bit.
    """
    self.communication_options |= (1 << COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER)

  def use_7bit_device_number(self):
    """
    Configures this object to send 7-bit device numbers, which is the default.
    """
    self.communication_options &= ~(1 << COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER)

  def multi_device_error_check_start(self, starting_device_number, device_count):
    """
    Sends a "Multi-device error check" command but does not read any
    responses.

    Note: Before using this, most users should make sure the MotoronSerial
    object is configured to use the compact protocol: construct the object
    without specifying a device number, or set device_number to None.
    """
    if self.communication_options & (1 << COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER):
      if device_count < 0 or device_count > 0x3FFF:
        raise RuntimeError('Invalid device count.')
      cmd = [
        CMD_MULTI_DEVICE_ERROR_CHECK,
        starting_device_number & 0x7F,
        starting_device_number >> 7 & 0x7F,
        device_count & 0x7F,
        device_count >> 7 & 0x7F,
      ]
    else:
      if device_count < 0 or device_count > 0x7F:
        raise RuntimeError('Invalid device count.')
      cmd = [
        CMD_MULTI_DEVICE_ERROR_CHECK,
        starting_device_number & 0x7F,
        device_count,
      ]

    self._send_command(cmd)
    self.port.flush()

  def multi_device_error_check(self, starting_device_number, device_count):
    """
    Sends a "Multi-device error check" command and reads the responses.

    This function assumes that each addressed Motoron can see the responses
    sent by the other Motorons (e.g. they are in a half-duplex RS-485 network).

    Returns the number of devices that indicated they have no errors.
    If the return value is less than device count, you can add the return
    value to the starting_device_number to get the device number of the
    first device where the check failed.  This device either did not
    respond or it responded with an indication that it has an error, or an
    unexpected byte was received for some reason.

    Note: Before using this, most users should make sure the MotoronSerial
    object is configured to use the compact protocol: construct the object
    without specifying a device number, or set device_number to None.
    """
    self.multi_device_error_check_start(starting_device_number, device_count)
    responses = self.port.read(device_count)
    for i, v in enumerate(responses):
      if v != ERROR_CHECK_CONTINUE: return i
    return len(responses)

  def multi_device_write(self, starting_device_number, device_count,
    command_byte, data):
    """
    Sends a "Multi-device write" command.

    Note: Before using this, most users should make sure the MotoronSerial
    object is configured to use the compact protocol: construct the object
    without specifying a device number, or call setDeviceNumber with an
    argument of 0xFFFF.
    """

    if bool(self.communication_options & (1 << COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER)):
      if device_count < 0 or device_count > 0x3FFF:
        raise RuntimeError('Invalid device count.')
      cmd = [
        CMD_MULTI_DEVICE_WRITE,
        starting_device_number & 0x7F,
        starting_device_number >> 7 & 0x7F,
        device_count & 0x7F,
        device_count >> 7 & 0x7F,
      ]
    else:
      if device_count < 0 or device_count > 0x7F:
        raise RuntimeError('Invalid device count.')
      cmd = [
        CMD_MULTI_DEVICE_WRITE,
        starting_device_number & 0x7F,
        device_count,
      ]

    if data == None: data = []
    if len(data) % device_count:
      raise RuntimeError("Expected data length to be a multiple of " \
        f"{device_count}, got {len(data)}.")
    bytes_per_device = len(data) // device_count
    if bytes_per_device > 15: raise RuntimeError('Data too long.')

    cmd += [bytes_per_device, command_byte & 0x7F]
    cmd += data

    self._send_command(cmd)

  def _send_command_core(self, cmd, send_crc):
    if self.device_number != None:
      if self.communication_options & (1 << COMMUNICATION_OPTION_14BIT_DEVICE_NUMBER):
        cmd = [
          0xAA,
          self.device_number & 0x7F,
          self.device_number >> 7 & 0x7F,
          cmd[0] & 0x7F
        ] + cmd[1:]
      else:
        cmd = [
          0xAA,
          self.device_number & 0x7F,
          cmd[0] & 0x7F
        ] + cmd[1:]

    if send_crc: cmd += [calculate_crc(cmd)]

    self.port.write(bytes(cmd))

  def _read_response(self, length):
    crc_enabled = bool(self.protocol_options & (1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES))
    response_7bit = bool(self.communication_options & (1 << COMMUNICATION_OPTION_7BIT_RESPONSES))

    if response_7bit and length > 7:
      raise RuntimeError('The Motoron does not support response payloads ' \
        'longer than 7 bytes in 7-bit response mode.')

    self.port.flush()
    read_length = length + response_7bit + crc_enabled
    response = self.port.read(read_length)
    if response is None: response = b''
    if len(response) != read_length:
      raise RuntimeError(f"Expected to read {read_length} bytes, got {len(response)}.")

    if crc_enabled:
      crc = response[-1]
      response = response[:-1]
      if crc != calculate_crc(response):
        raise RuntimeError('Incorrect CRC received.')

    if response_7bit:
      msbs = response[-1]
      response = bytearray(response[:-1])
      for i in range(length):
        if msbs & 1: response[i] |= 0x80
        msbs >>= 1
      response = bytes(response)

    return response
