import math
import time
from smbus2 import SMBus, i2c_msg
from motoron_protocol import Motoron

class MotoronI2C():
  """
  Represents an I2C connection to a Pololu Motoron Motor Controller.
  """

  DEFAULT_PROTOCOL_OPTIONS = (
    (1 << Motoron.PROTOCOL_OPTION_I2C_GENERAL_CALL) |
    (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_COMMANDS) |
    (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  DEFAULT_ERROR_MASK = (
    (1 << Motoron.STATUS_FLAG_COMMAND_TIMEOUT) |
    (1 << Motoron.STATUS_FLAG_RESET))

  def __init__(self, address=16):
    """
    Creates a new MotoronI2C object to communicate with the Motoron over I2C.

    The `address` parameter specifies the 7-bit I2C address to use, and it
    must match the address that the Motoron is configured to use.
    """
    self.bus = SMBus(1)
    self.address = address
    self.protocol_options = MotoronI2C.DEFAULT_PROTOCOL_OPTIONS

  def set_bus(self, bus):
    """
    Configures this object to use the specified I2C bus.
    """
    self.bus = bus

  def set_address(self, address):
    """
    Configures this object to use the specified 7-bit I2C address.
    This must match the address that the Motoron is configured to use.
    """
    self.address = address

  def get_address(self):
    """
    Returns the 7-bit I2C address that this object is configured to use.
    """
    return self.address

  def get_firmware_version(self):
    """
    Sends the "Get firmware version" command to get the device's firmware
    product ID and firmware version numbers.

    For more information, see the "Get firwmare version"
    command in the Motoron user's guide.
    """
    cmd = [Motoron.CMD_GET_FIRMWARE_VERSION]
    response = self.__send_command_and_read_response(cmd, 4)
    return dict(
      product_id = response[0] | (response[1] << 8),
      firmware_version = dict(minor = response[2], major = response[3]))

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
    by the Motoron in its repsonses and makes sure it is correct.  If the
    response CRC byte is incorrect, get_last_error() will return a non-zero
    error code after the command has been run.

    When the I2C general call address is enabled, the Motoron receives
    commands sent to address 0 in addition to its usual I2C address.
    The general call address is write-only; reading bytes from it is not
    supported.

    By default (self, in this libary and the Motoron itself), CRC for commands and
    responses is enabled, and the I2C general call address is enabled.

    This method always sends its command with a CRC byte, so it will work
    even if CRC was previously disabled but has been re-enabled on the device
    (e.g. due to a reset).

    The \p options argument should be 0 or combination of the following
    expressions made using the bitwise or operator (|):
    - (1 << PROTOCOL_OPTION_CRC_FOR_COMMANDS)
    - (1 << PROTOCOL_OPTION_CRC_FOR_RESPONSES)
    - (1 << PROTOCOL_OPTION_I2C_GENERAL_CALL)

    For more information, see the "Set protocol optons"
    command in the Motoron user's guide.

    \sa enable_crc(), disable_crc(),
      enable_crc_for_commands(), disable_crc_for_commands(),
      enable_crc_for_responses(), disable_crc_for_responses(),
      enable_i2c_general_call(), disable_i2c_general_call()
    """
    self.protocol_options = options
    cmd = [
      Motoron.CMD_SET_PROTOCOL_OPTIONS,
      options & 0x7F,
      ~options & 0x7F
    ]
    self.__send_command_core(cmd, True)

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
      | (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_COMMANDS)
      | (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def disable_crc(self):
    """
     Disables CRC for commands and responses.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << Motoron.PROTOCOL_OPTION_CRC_FOR_COMMANDS)
      & ~(1 << Motoron.PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def enable_crc_for_commands(self):
    """
    Enables CRC for commands.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      | (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_COMMANDS))

  def disable_crc_for_commands(self):
    """
    Disables CRC for commands.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << Motoron.PROTOCOL_OPTION_CRC_FOR_COMMANDS))

  def enable_crc_for_responses(self):
    """
    Enables CRC for responses.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      | (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def disable_crc_for_responses(self):
    """
    Disables CRC for responses.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << Motoron.PROTOCOL_OPTION_CRC_FOR_RESPONSES))

  def enable_i2c_general_call(self):
    """
    Enables the I2C general call address.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      | (1 << Motoron.PROTOCOL_OPTION_I2C_GENERAL_CALL))

  def disable_i2c_general_call(self):
    """
    Disables the I2C general call address.  See set_protocol_options().
    """
    self.set_protocol_options(self.protocol_options
      & ~(1 << Motoron.PROTOCOL_OPTION_I2C_GENERAL_CALL))

  def read_eeprom(self, offset, length):
    """
    Reads the specified bytes from the Motoron's EEPROM memory.

    For more information, see the "Read EEPROM" command in the
    Motoron user's guide.
    """
    cmd = [
      Motoron.CMD_READ_EEPROM,
      offset & 0x7F,
      length & 0x7F,
    ]
    return self.__send_command_and_read_response(cmd, length)

  def read_eeprom_device_number(self):
    """
    Reads the EEPROM device number from the device.
    This is the I2C address that the device uses if it detects that JMP1
    is shorted to GND when it starts up.  It is stored in non-volatile
    EEPROM memory.
    """
    return self.read_eeprom(Motoron.SETTING_DEVICE_NUMBER, 1)

  def write_eeprom(self, offset, value):
    """
    Writes a value to one byte in the Motoron's EEPROM memory.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron’s microcontroller is only rated for
    100,000 erase/write cycles.**

    For more information, see the "Write EEPROM" command in the
    Motoron user's guide.
    """
    cmd = [
      Motoron.CMD_WRITE_EEPROM,
      offset & 0x7F,
      value & 0x7F,
      (value >> 7) & 1,
    ]
    cmd += [
      cmd[1] ^ 0x7F,
      cmd[2] ^ 0x7F,
      cmd[3] ^ 0x7F,
    ]
    self.__send_command(cmd)
    time.sleep(0.006)

  def write_eeprom_device_number(self, number):
    """
    Writes to the EEPROM device number, changing it to the specified value.

    **Warning: Be careful not to write to the EEPROM in a fast loop. The
    EEPROM memory of the Motoron’s microcontroller is only rated for
    100,000 erase/write cycles.**

    For more information, see the "Write EEPROM" command in the
    Motoron user's guide.  Also, see the WriteEEPROM example that comes with
    this library for an example of how to use this method.
    """
    self.write_eeprom(Motoron.SETTING_DEVICE_NUMBER, number)

  def reinitialize(self):
    """
    Sends a "Reinitialize" command to the Motoron, which resets most of the
    Motoron's variables to their default state.

    For more information, see the "Reinitialize" command in the Motoron
    user's guide.

    \sa reset()
    """
    # Always send the reset command with a CRC byte to make it more reliable.
    cmd = [Motoron.CMD_REINITIALIZE]
    self.__send_command_core(cmd, True)
    self.protocol_options = MotoronI2C.DEFAULT_PROTOCOL_OPTIONS

  def reset(self):
    """
    Sends a "Reset" command to the Motoron, which does a full hardware reset.

    This command is equivalent to briefly driving the Motoron's RST pin low.
    The Motoron's RST is briefly driven low by the Motoron itself as a
    result of this command.

    After running this command, we recommend waiting for at least 5
    milliseconds before you try to communicate with the Motoron.

    \sa reinitialize()
    """
    cmd = [Motoron.CMD_RESET]
    self.__send_command_core(cmd, True)
    self.protocol_options = MotoronI2C.DEFAULT_PROTOCOL_OPTIONS

  def get_variables(self, motor, offset, length):
    """
    Reads information from the Motoron using a "Get variables" command.

    This library has helper methods to read every variable, but this method
    is useful if you want to get the raw bytes, or if you want to read
    multiple consecutive variables at the same time for efficiency.

    \param motor 0 to read general variables, or a motor number to read
      motor-specific variables.
    \param offset The location of the first byte to read.
    \param length How many bytes to read.
    \param buffer A pointer to an array to store the bytes read
      from the controller.
    """
    cmd = [
      Motoron.CMD_GET_VARIABLES,
      motor & 0x7F,
      offset & 0x7F,
      length & 0x7F,
    ]
    return self.__send_command_and_read_response(cmd, length)

  def get_var_u8(self, motor, offset):
    """
    Reads one byte from the Motoron using a "Get variables" command
    and returns the result as an unsigned 8-bit integer.

    \param motor 0 to read a general variable, or a motor number to read
      a motor-specific variable.
    \param offset The location of the byte to read.
    """
    return self.get_variables(motor, offset, 1)[0]

  def get_var_u16(self, motor, offset):
    """
    Reads two bytes from the Motoron using a "Get variables" command
    and returns the result as an unsigned 16-bit integer.

    \param motor 0 to read general variables, or a motor number to read
      motor-specific variables.
    \param offset The location of the first byte to read.
    """
    buffer = self.get_variables(motor, offset, 2)
    return int.from_bytes(buffer, byteorder="little", signed=False) # equivalent to `struct.unpack("<H", ...)`

  def get_var_s16(self, motor, offset):
    """
    Reads two bytes from the Motoron using a "Get variables" command
    and returns the result as a signed 16-bit integer.

    \param motor 0 to read general variables, or a motor number to read
      motor-specific variables.
    \param offset The location of the first byte to read.
    """
    buffer = self.get_variables(motor, offset, 2)
    return int.from_bytes(buffer, byteorder="little", signed=True) # equivalent to `struct.unpack("<h", ...)`

  def get_status_flags(self):
    """
    Reads the "Status flags" variable from the Motoron.

    The bits in this variable are defined by the STATUS_FLAGS_*
    macros:

    - STATUS_FLAG_PROTOCOL_ERROR
    - STATUS_FLAG_CRC_ERROR
    - STATUS_FLAG_COMMAND_TIMEOUT_LATCHED
    - STATUS_FLAG_MOTOR_FAULT_LATCHED
    - STATUS_FLAG_NO_POWER_LATCHED
    - STATUS_FLAG_RESET
    - STATUS_FLAG_COMMAND_TIMEOUT
    - STATUS_FLAG_MOTOR_FAULTING
    - STATUS_FLAG_NO_POWER
    - STATUS_FLAG_ERROR_ACTIVE
    - STATUS_FLAG_MOTOR_OUTPUT_ENABLED
    - STATUS_FLAG_MOTOR_DRIVING

    Here is some example code that uses bitwise operators to check
    whether there is currently a motor fault or a lack of power:

    ```{.py}
    mask = (1 << Motoron.STATUS_FLAG_NO_POWER) | \
      (1 << Motoron.STATUS_FLAG_MOTOR_FAULTING)
    if get_status_flags() & mask: # do something
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
    return self.get_var_u16(0, Motoron.VAR_STATUS_FLAGS)

  def get_protocol_error_flag(self):
    """
    Returns the "Protocol error" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_PROTOCOL_ERROR))

  def get_crc_error_flag(self):
    """
    Returns the "CRC error" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_CRC_ERROR))

  def get_command_timeout_latched_flag(self):
    """
    Returns the "Command timeout latched" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_COMMAND_TIMEOUT_LATCHED))

  def get_motor_fault_latched_flag(self):
    """
    Returns the "Motor fault latched" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_MOTOR_FAULT_LATCHED))

  def get_no_power_latched_flag(self):
    """
    Returns the "No power latched" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_NO_POWER_LATCHED))

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
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_RESET))

  def get_motor_faulting_flag(self):
    """
    Returns the "Motor faulting" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_MOTOR_FAULTING))

  def get_no_power_flag(self):
    """
    Returns the "No power" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_NO_POWER))

  def get_error_active_flag(self):
    """
    Returns the "Error active" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_ERROR_ACTIVE))

  def get_motor_output_enabled_flag(self):
    """
    Returns the "Motor output enabled" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_MOTOR_OUTPUT_ENABLED))

  def get_motor_driving_flag(self):
    """
    Returns the "Motor driving" bit from get_status_flags().

    For more information, see the "Status flags" variable in the Motoron
    user's guide.
    """
    return bool(self.get_status_flags() & (1 << Motoron.STATUS_FLAG_MOTOR_DRIVING))

  def get_vin_voltage(self):
    """
    Reads voltage on the Motoron's VIN pin, in raw device units.

    For more information, see the "VIN voltage" variable in the Motoron
    user's guide.

    \sa get_vin_voltage_mv()
    """
    return self.get_var_u16(0, Motoron.VAR_VIN_VOLTAGE)

  def get_vin_voltage_mv(self, reference_mv):
    """
    Reads the voltage on the Motoron's VIN pin and converts it to millivolts.

    For more information, see the "VIN voltage" variable in the Motoron
    user's guide.

    \param reference_mv The reference voltage (IOREF), in millivolts.
      For example, use 3300 for a 3.3 V system or 5000 for a 5 V system.

    \sa get_vin_voltage()
    """
    return self.get_vin_voltage() * reference_mv / 1024 * 1047 / 47

  def get_command_timeout_milliseconds(self):
    """
    Reads the "Command timeout" variable and converts it to milliseconds.

    For more information, see the "Command timeout" variable in the Motoron
    user's guide.

    \sa set_command_timeout_milliseconds()
    """
    return self.get_var_u16(0, Motoron.VAR_COMMAND_TIMEOUT) * 4

  def get_error_response(self):
    """
    Reads the "Error response" variable, which defines how the Motoron will
    stop its motors when an error is happening.

    For more information, see the "Error response" variable in the Motoron
    user's guide.

    \sa set_error_response()
    """
    return self.get_var_u8(0, Motoron.VAR_ERROR_RESPONSE)

  def get_error_mask(self):
    """
    Reads the "Error mask" variable, which defines which status flags are
    considered to be errors.

    For more information, see the "Error mask" variable in the Motoron
    user's guide.

    \sa set_error_mask()
    """
    return self.get_var_u16(0, Motoron.VAR_ERROR_MASK)

  def get_jumper_state(self):
    """
    Reads the "Jumper state" variable.

    For more information, see the "Jumper state" variable in the Motoron
    user's guide
    """
    return self.get_var_u8(0, Motoron.VAR_JUMPER_STATE)

  def get_target_speed(self, motor):
    """
    Reads the target speed of the specified motor, which is the speed at
    which the motor has been commanded to move.

    For more information, see the "Target speed" variable in the Motoron
    user's guide.

    \sa set_speed(), set_all_speeds(), set_all_speeds_using_buffers()
    """
    return self.get_var_s16(motor, Motoron.MVAR_TARGET_SPEED)

  def get_target_brake_amount(self, motor):
    """
    Reads the target brake amount for the specified motor.

    For more information, see the "Target speed" variable in the Motoron
    user's guide.

    \sa set_target_brake_amount()
    """
    return self.get_var_u16(motor, Motoron.MVAR_TARGET_BRAKE_AMOUNT)

  def get_current_speed(self, motor):
    """
    Reads the current speed of the specified motor, which is the speed that
    the Motoron is currently trying to apply to the motor.

    For more information, see the "Target speed" variable in the Motoron
    user's guide.

    \sa set_speed_now(), set_all_speeds_now(), set_all_speeds_now_using_buffers()
    """
    return self.get_var_s16(motor, Motoron.MVAR_CURRENT_SPEED)

  def get_buffered_speed(self, motor):
    """
    Reads the buffered speed of the specified motor.

    For more information, see the "Buffered speed" variable in the Motoron
    user's guide.

    \sa set_buffered_speed(), set_all_buffered_speeds()
    """
    return self.get_var_s16(motor, Motoron.MVAR_BUFFERED_SPEED)

  def get_pwm_mode(self, motor):
    """
    Reads the PWM mode of the specified motor.

    For more information, see the "PWM mode" variable in the Motoron
    user's guide.

    \sa set_pwm_mode()
    """
    return self.get_var_u8(motor, Motoron.MVAR_PWM_MODE)

  def get_max_acceleration_forward(self, motor):
    """
    Reads the maximum acceleration of the specified motor for the forward
    direction.

    For more information, see the "Max acceleration forward" variable in the
    Motoron user's guide.

    \sa set_max_acceleration(), set_max_acceleration_forward()
    """
    return self.get_var_u16(motor, Motoron.MVAR_MAX_ACCEL_FORWARD)

  def get_max_acceleration_reverse(self, motor):
    """
    Reads the maximum acceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max acceleration reverse" variable in the
    Motoron user's guide.

    \sa set_max_acceleration(), set_max_acceleration_reverse()
    """
    return self.get_var_u16(motor, Motoron.MVAR_MAX_ACCEL_REVERSE)

  def get_max_deceleration_forward(self, motor):
    """
    Reads the maximum deceleration of the specified motor for the forward
    direction.

    For more information, see the "Max deceleration forward" variable in the
    Motoron user's guide.

    \sa set_max_deceleration(), set_max_deceleration_forward()
    """
    return self.get_var_u16(motor, Motoron.MVAR_MAX_DECEL_FORWARD)

  def get_max_deceleration_reverse(self, motor):
    """
    Reads the maximum deceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max deceleration reverse" variable in the
    Motoron user's guide.

    \sa set_max_deceleration(), set_max_deceleration_reverse()
    """
    return self.get_var_u16(motor, Motoron.MVAR_MAX_DECEL_REVERSE)


# \cond

  # This function is used by Pololu for testing.
  def get_max_deceleration_temporary(self, motor):
    return self.get_var_u16(motor, Motoron.MVAR_MAX_DECEL_TMP)

# \endcond

  def get_starting_speed_forward(self, motor):
    """
    Reads the starting speed for the specified motor in the forward direction.

    For more information, see the "Starting speed forward" variable in the
    Motoron user's guide.

    \sa set_starting_speed(), set_starting_speed_forward()
    """
    return self.get_var_u16(motor, Motoron.MVAR_STARTING_SPEED_FORWARD)

  def get_starting_speed_reverse(self, motor):
    """
    Reads the starting speed for the specified motor in the reverse direction.

    For more information, see the "Starting speed reverse" variable in the
    Motoron user's guide.

    \sa set_starting_speed(), set_starting_speed_reverse()
    """
    return self.get_var_u16(motor, Motoron.MVAR_STARTING_SPEED_REVERSE)

  def get_direction_change_delay_forward(self, motor):
    """
    Reads the direction change delay for the specified motor in the
    forward direction.

    For more information, see the "Direction change delay forward" variable
    in the Motoron user's guide.

    \sa set_direction_change_delay(), set_direction_change_delay_forward()
    """
    return self.get_var_u8(motor, Motoron.MVAR_DIRECTION_CHANGE_DELAY_FORWARD)

  def get_direction_change_delay_reverse(self, motor):
    """
    Reads the direction change delay for the specified motor in the
    reverse direction.

    For more information, see the "Direction change delay reverse" variable
    in the Motoron user's guide.

    \sa set_direction_change_delay(), set_direction_change_delay_reverse()
    """
    return self.get_var_u8(motor, Motoron.MVAR_DIRECTION_CHANGE_DELAY_REVERSE)

  def set_variable(self, motor, offset, value):
    """
    Configures the Motoron using a "Set variable" command.

    This library has helper methods to set every variable, so you should
    not need to call this function directly.

    \param motor 0 to set a general variable, or a motor number to set
      motor-specific variables.
    \param offset The address of the variable to set (only certain offsets
      are allowed).
    \param value The value to set the variable to.

    \sa get_variables()
    """
    if value > 0x3FFF: value = 0x3FFF
    cmd = [
      Motoron.CMD_SET_VARIABLE,
      motor & 0x1F,
      offset & 0x7F,
      value & 0x7F,
      (value >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

  def set_command_timeout_milliseconds(self, ms):
    """
    Sets the command timeout period, in milliseconds.

    For more information, see the "Command timeout" variable
    in the Motoron user's guide.

    \sa disable_command_timeout(), get_command_timeout_milliseconds()
    """
    # Divide by 4, but round up.
    timeout = math.ceil(ms / 4)
    self.set_variable(0, Motoron.VAR_COMMAND_TIMEOUT, timeout)

  def set_error_response(self, response):
    """
    Sets the error response, which defines how the Motoron will
    stop its motors when an error is happening.

    The response parameter should be one of:

    - ERROR_RESPONSE_COAST
    - ERROR_RESPONSE_BRAKE
    - ERROR_RESPONSE_COAST_NOW
    - ERROR_RESPONSE_BRAKE_NOW

    For more information, see the "Error response" variable in the Motoron
    user's guide.

    \sa get_error_response()
    """
    self.set_variable(0, Motoron.VAR_ERROR_RESPONSE, response)

  def set_error_mask(self, mask):
    """
    Sets the "Error mask" variable, which defines which status flags are
    considered to be errors.

    For more information, see the "Error mask" variable in the Motoron
    user's guide.

    \sa get_error_mask(), get_status_flags()
    """
    self.set_variable(0, Motoron.VAR_ERROR_MASK, mask)

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

    \sa set_command_timeout_milliseconds(), set_error_mask()
    """
    self.set_error_mask(MotoronI2C.DEFAULT_ERROR_MASK & ~(1 << Motoron.STATUS_FLAG_COMMAND_TIMEOUT))

  def set_pwm_mode(self, motor, mode):
    """
    Sets the PWM mode for the specified motor.

    The mode parameter should be one of the following:

    - PWM_MODE_DEFAULT (20 kHz)
    - PWM_MODE_1_KHZ 1
    - PWM_MODE_2_KHZ 2
    - PWM_MODE_4_KHZ 3
    - PWM_MODE_5_KHZ 4
    - PWM_MODE_10_KHZ 5
    - PWM_MODE_20_KHZ 6
    - PWM_MODE_40_KHZ 7
    - PWM_MODE_80_KHZ 8

    For more information, see the "PWM mode" variable in the Motoron user's
    guide.

    \sa get_pwm_mode(self)
    """
    self.set_variable(motor, Motoron.MVAR_PWM_MODE, mode)

  def set_max_acceleration_forward(self, motor, accel):
    """
    Sets the maximum acceleration of the specified motor for the forward
    direction.

    For more information, see the "Max acceleration forward" variable in the
    Motoron user's guide.

    \sa set_max_acceleration(), get_max_acceleration_forward()
    """
    self.set_variable(motor, Motoron.MVAR_MAX_ACCEL_FORWARD, accel)

  def set_max_acceleration_reverse(self, motor, accel):
    """
    Sets the maximum acceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max acceleration reverse" variable in the
    Motoron user's guide.

    \sa set_max_acceleration(), get_max_acceleration_reverse()
    """
    self.set_variable(motor, Motoron.MVAR_MAX_ACCEL_REVERSE, accel)

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

    \sa set_max_deceleration(), get_max_deceleration_forward()
    """
    self.set_variable(motor, Motoron.MVAR_MAX_DECEL_FORWARD, decel)

  def set_max_deceleration_reverse(self, motor, decel):
    """
    Sets the maximum deceleration of the specified motor for the reverse
    direction.

    For more information, see the "Max deceleration reverse" variable in the
    Motoron user's guide.

    \sa set_max_deceleration(), get_max_deceleration_reverse()
    """
    self.set_variable(motor, Motoron.MVAR_MAX_DECEL_REVERSE, decel)

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

    \sa set_starting_speed(), get_starting_speed_forward()
    """
    self.set_variable(motor, Motoron.MVAR_STARTING_SPEED_FORWARD, speed)

  def set_starting_speed_reverse(self, motor, speed):
    """
    Sets the starting speed of the specified motor for the reverse
    direction.

    For more information, see the "Starting speed reverse" variable in the
    Motoron user's guide.

    \sa set_starting_speed(), get_starting_speed_reverse()
    """
    self.set_variable(motor, Motoron.MVAR_STARTING_SPEED_REVERSE, speed)

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

    \sa set_direction_change_delay(), get_direction_change_delay_forward()
    """
    self.set_variable(motor, Motoron.MVAR_DIRECTION_CHANGE_DELAY_FORWARD, duration)

  def set_direction_change_delay_reverse(self, motor, duration):
    """
    Sets the direction change delay of the specified motor for the reverse
    direction, in units of 10 ms.

    For more information, see the "Direction change delay reverse" variable
    in the Motoron user's guide.

    \sa set_direction_change_delay(), get_direction_change_delay_reverse()
    """
    self.set_variable(motor, Motoron.MVAR_DIRECTION_CHANGE_DELAY_REVERSE, duration)

  def set_direction_change_delay(self, motor, duration):
    """
    Sets the direction change delay of the specified motor (both directions),
    in units of 10 ms.

    If this function succeeds, it is equivalent to calling
    set_direction_change_delay_forward() and set_direction_change_delay_reverse().
    """
    self.set_direction_change_delay_forward(motor, duration)
    self.set_direction_change_delay_reverse(motor, duration)

  def coast_now(self):
    """
    Sends a "Coast now" command to the Motoron, causing all of the motors to
    immediately start coasting.

    For more information, see the "Coast now" command in the Motoron
    user's guide.
    """
    cmd = [Motoron.CMD_COAST_NOW]
    self.__send_command(cmd)

  def clear_motor_fault(self, flags=0):
    """
    Sends a "Clear motor fault" command to the Motoron.

    If any of the Motoron's motors chips are currently experiencing a
    fault (error), or bit 0 of the flags argument is 1, this command makes
    the Motoron attempt to recover from the faults.

    For more information, see the "Clear motor fault" command in the Motoron
    user's guide.

    \sa clear_motor_fault_unconditional(), get_motor_faulting_flag()
    """
    cmd = [ Motoron.CMD_CLEAR_MOTOR_FAULT, (flags & 0x7F) ]
    self.__send_command(cmd)

  def clear_motor_fault_unconditional(self):
    """
    Sends a "Clear motor fault" command to the Motoron with the
    "unconditional" flag set, so the Motoron will attempt to recover
    from any motor faults even if no fault is currently occurring.

    This is a more robust version of clear_motor_fault().
    """
    self.clear_motor_fault(1 << Motoron.CLEAR_MOTOR_FAULT_UNCONDITIONAL)

  def clear_latched_status_flags(self, flags):
    """
    Clears the specified flags in get_status_flags().

    For each bit in the flags argument that is 1, this command clears the
    corresponding bit in the "Status flags" variable, setting it to 0.

    For more information, see the "Clear latched status flags" command in the
    Motoron user's guide.

    \sa get_status_flags(), set_latched_status_flags()
    """
    cmd = [
      Motoron.CMD_CLEAR_LATCHED_STATUS_FLAGS,
      flags & 0x7F,
      (flags >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

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

    \sa clear_latched_status_flags()
    """
    self.clear_latched_status_flags(1 << Motoron.STATUS_FLAG_RESET)

  def set_latched_status_flags(self, flags):
    """
    Sets the specified flags in get_status_flags().

    For each bit in the flags argument that is 1, this command sets the
    corresponding bit in the "Status flags" variable to 1.

    For more information, see the "Set latched status flags" command in the
    Motoron user's guide.

    \sa get_status_flags(), set_latched_status_flags()
    """
    cmd = [
      Motoron.CMD_SET_LATCHED_STATUS_FLAGS,
      flags & 0x7F,
      (flags >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

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

    \sa set_speed_now(), set_all_speeds()
    """
    cmd = [
      Motoron.CMD_SET_SPEED,
      motor & 0x7F,
      speed & 0x7F,
      (speed >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

  def set_speed_now(self, motor, speed):
    """
    Sets the target and current speed of the specified motor, ignoring
    any acceleration and deceleration limits.

    For more information, see the "Set speed" command in the Motoron
    user's guide.

    \sa set_speed(), set_all_speeds_now()
    """
    cmd = [
      Motoron.CMD_SET_SPEED_NOW,
      motor & 0x7F,
      speed & 0x7F,
      (speed >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

  def set_buffered_speed(self, motor, speed):
    """
    Sets the buffered speed of the specified motor.

    This command does not immediately cause any change to the motor: it
    stores a speed for the specified motor in the Motoron so it can be
    used by later commands.

    For more information, see the "Set speed" command in the Motoron
    user's guide.

    \sa set_speed(), set_all_buffered_speeds(),
      set_all_speeds_using_buffers(), set_all_speeds_now_using_buffers()
    """
    cmd = [
      Motoron.CMD_SET_BUFFERED_SPEED,
      motor & 0x7F,
      speed & 0x7F,
      (speed >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

  def set_all_speeds(self, *speeds):
    """
    Sets the target speeds of all motors at the same time.

    This is equivalent to calling set_speed() once for each motor, but it is
    more efficient because all of the speeds are sent in the same command.

    For more information, see the "Set all speeds" command in the Motoron
    user's guide.

    \sa set_speed(), set_all_speeds_now(), set_all_buffered_speeds()
    """
    cmd = [Motoron.CMD_SET_ALL_SPEEDS]
    for speed in speeds:
      cmd += [
        speed & 0x7F,
        (speed >> 7) & 0x7F,
      ]
    self.__send_command(cmd)

  def set_all_speeds_now(self, *speeds):
    """
    Sets the target and currents speeds of all motors at the same time.

    This is equivalent to calling set_speed_now() once for each motor, but it is
    more efficient because all of the speeds are sent in the same command.

    For more information, see the "Set all speeds" command in the Motoron
    user's guide.

    \sa set_speed(), set_speed_now(), set_all_speeds()
    """
    cmd = [Motoron.CMD_SET_ALL_SPEEDS_NOW]
    for speed in speeds:
      cmd += [
        speed & 0x7F,
        (speed >> 7) & 0x7F,
      ]
    self.__send_command(cmd)

  def set_all_buffered_speeds(self, *speeds):
    """
    Sets the buffered speeds of all motors.

    This command does not immediately cause any change to the motors: it
    stores speed for each motor in the Motoron so they can be used by later
    commands.

    For more information, see the "Set all speeds" command in the Motoron
    user's guide.

    \sa set_speed(), set_buffered_speed(), set_all_speeds(),
      set_all_speeds_using_buffers(), set_all_speeds_now_using_buffers()
    """
    cmd = [Motoron.CMD_SET_ALL_BUFFERED_SPEEDS]
    for speed in speeds:
      cmd += [
        speed & 0x7F,
        (speed >> 7) & 0x7F,
      ]
    self.__send_command(cmd)

  def set_all_speeds_using_buffers(self):
    """
    Sets each motor's target speed equal to the buffered speed.

    This command is the same as set_all_speeds() except that the speeds are
    provided ahead of time using set_buffered_speed() or set_all_buffered_speeds().

    \sa set_all_speeds_now_using_buffers(), set_buffered_speed(),
      set_all_buffered_speeds()
    """
    cmd = [Motoron.CMD_SET_ALL_SPEEDS_USING_BUFFERS]
    self.__send_command(cmd)

  def set_all_speeds_now_using_buffers(self):
    """
    Sets each motor's target speed and current speed equal to the buffered
    speed.

    This command is the same as set_all_speeds_now() except that the speeds are
    provided ahead of time using set_buffered_speed() or set_all_buffered_speeds().

    \sa set_all_speeds_using_buffers(), set_buffered_speed(),
      set_all_buffered_speeds()
    """
    cmd = [Motoron.CMD_SET_ALL_SPEEDS_NOW_USING_BUFFERS]
    self.__send_command(cmd)

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

    \sa set_braking_now(), get_target_brake_amount()
    """
    cmd = [
      Motoron.CMD_SET_BRAKING,
      motor & 0x7F,
      amount & 0x7F,
      (amount >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

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

    \sa set_braking(), get_target_brake_amount()
    """
    cmd = [
      Motoron.CMD_SET_BRAKING_NOW,
      motor & 0x7F,
      amount & 0x7F,
      (amount >> 7) & 0x7F,
    ]
    self.__send_command(cmd)

  def reset_command_timeout(self):
    """
    Resets the command timeout.

    This prevents the command timeout status flags from getting set for some
    time.  (The command timeout is also reset by every other Motoron command,
    as long as its parameters are valid.)

    For more information, see the "Reset command timeout" command in the
    Motoron user's guide.

    \sa disable_command_timeout(), set_command_timeout_milliseconds()
    """
    cmd = [Motoron.CMD_RESET_COMMAND_TIMEOUT]
    self.__send_command(cmd)

  def __send_command_core(self, cmd, send_crc):
    if send_crc:
      write = i2c_msg.write(self.address, cmd + [Motoron.calculate_crc(cmd)])
    else:
      write = i2c_msg.write(self.address, cmd)
    self.bus.i2c_rdwr(write)

  def __send_command(self, cmd):
    send_crc = bool(self.protocol_options & (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_COMMANDS))
    self.__send_command_core(cmd, send_crc)

  def __read_response(self, length):
    crc_enabled = bool(self.protocol_options & (1 << Motoron.PROTOCOL_OPTION_CRC_FOR_RESPONSES))
    read = i2c_msg.read(self.address, length + crc_enabled)
    self.bus.i2c_rdwr(read)
    response = list(read)
    if crc_enabled:
      crc = response.pop()
      if crc != Motoron.calculate_crc(response):
        raise IOError("CRC check failed")
    return response

  def __send_command_and_read_response(self, cmd, response_length):
    self.__send_command(cmd)
    return self.__read_response(response_length)