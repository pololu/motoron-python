# Motoron Motor Controller library for Python/MicroPython

[www.pololu.com](https://www.pololu.com/)

## Summary

This is a Python 3 library that helps interface with
[Motoron motor controllers][motoron] using I&sup2;C or UART serial.

It supports the following Motoron controllers:

- [Motoron M1T550 Single I&sup2;C Motor Controller][M1T550]
- [Motoron M1U550 Single Serial Motor Controller][M1U550]
- [Motoron M2T550 Dual I&sup2;C Motor Controller][M2T550]
- [Motoron M2U550 Dual Serial Motor Controller][M2U550]
- [Motoron M3S550 Triple Motor Controller Shield for Arduino][M3S550]
- [Motoron M3H550 Triple Motor Controller for Raspberry Pi][M3H550]
- [Motoron M1T256 Single I&sup2;C Motor Controller][M1T256]
- [Motoron M1U256 Single Serial Motor Controller][M1U256]
- [Motoron M2T256 Dual I&sup2;C Motor Controller][M2T256]
- [Motoron M2U256 Dual Serial Motor Controller][M2U256]
- [Motoron M3S256 Triple Motor Controller Shield for Arduino][M3S256]
- [Motoron M3H256 Triple Motor Controller for Raspberry Pi][M3H256]
- [Motoron M2S Dual High-Power Motor Controllers for Arduino][M2S] (M2S18v20, M2S18v18, M2S24v16, M2S24v14)
- [Motoron M2H Dual High-Power Motor Controllers for Raspberry Pi][M2H] (M2H18v20, M2H18v18, M2H24v16, M2H24v14)

## Supported platforms

This library is designed to run on any Python 3 or MicroPython interpeter
that has a working (including access to compatible hardware)
version of one of the following Python libraries:

- [smbus2]
- [pySerial]
- [machine.I2C]
- [machine.UART]

We have mainly tested this library on Raspberry Pi single-board Linux computers
and MicroPython-compatible RP2040 development boards such as the
Raspberry Pi Pico.

## Installation

First, install Git, Python 3, and the Python 3 venv module by following the
appropriate instructions for your operating system.
On Debian-based operating systems, for example, you can run:

    sudo apt install git python3-venv

In a shell, run this command to create a Python virtual environment to
hold this library and its dependencies.

    python3 -m venv ~/myvenv

Run the following command to add the venv to your PATH so you can easily run the
`python3` and `pip3` commands for this virtual environment.  You will need to
do this every time to start a new shell.

    export PATH=~/myvenv/bin/:$PATH

(You can test that this worked by running `which pip3`.)

Download this library, and install it along with its dependencies in the
virtual environment:

    git clone https://github.com/pololu/motoron-python
    cd motoron-python
    pip3 install .

Now you should be able to run `python3` in your shell to start a Python 3 REPL
from the virtual environment.  In that REPL, run `import motoron`, and
make sure it does not print any error messages.  If so, you have successfully
installed the library.


## Alternative installation without a virtual environment

On Debian-based operating systems such as Ubuntu and Raspberry Pi OS, you can
install the library in a simpler way without needing to make a virtual
environment or run `pip3`.  Run the following command:

    sudo apt install python3 python3-smbus2 python3-serial

Now you can simply copy `motoron.py` and `motoron_protocol.py` into the same
directory as your Python code that uses the Motoron.


## Getting started on Raspberry Pi OS using I&sup2;C

To successfully run this library on Raspberry Pi OS using I&sup2;C,
you will need to enable I&sup2;C, figure out which I&sup2;C bus to use,
set up the I&sup2;C device permissions properly
(so you do not have to use `sudo`), and connect the Motoron to your
Raspberry Pi's I&sup2;C bus.  If you are not sure how to do those things,
see the "Getting started" sections of the [Motoron user's guide][guide].

The examples relevant to this setup are named `i2c_*.py`.
Run `python3 ./i2c_simple_example.py` inside the library directory to
execute the simplest example.


## Getting started on Raspberry Pi OS using UART serial

You will need to make sure that your machine has a serial port that
pySerial can connect to.  This is typically an integrated serial port that is
part of your computer or a USB-to-serial adapter.

On the Raspberry Pi, we recommend using `/dev/serial0`.  You can check if it
exists by running `ls -l /dev/serial*`.
If it does not exist, you should enable it by running
`sudo raspi-config nonint do_serial 2` and rebooting.
You should also add yourself to the `dialout` group by running
`sudo usermod -a -G dialout $(whoami)`, logging out, and logging back in again.

The examples relevant to this setup are named `serial_*.py`.
Run `./serial_simple_example.py` inside the library directory to execute the
simplest example.

## Getting started on MicroPython

The examples that work with MicroPython have names starting with `mpy_`.
You can run one of these examples by renaming it to `main.py`,
copying it to your board, and then rebooting your board.
The files `motoron.py` and `motoron_protocol.py` also need to be copied
to the board.

## Troubleshooting

### I&sup2;C bus not found

> FileNotFoundError: [Errno 2] No such file or directory: '/dev/i2c-1'

The error message above indicates that I&sup2;C bus 1 was not found.
For most users, the solution is to run `sudo raspi-config nonint do_i2c 0`
to enable I&sup2;C bus 1 and then reboot.
You can see which I&sup2;C busses are enabled by running `ls /dev/i2c*`.
If you have connected your Motoron to a different I&sup2;C bus, you should
specify the bus number when creating the MotoronI2C object.  For example:

    mc = motoron.MotoronI2C(bus=123)

### Serial port permission denied

> serial.serialutil.SerialException: [Errno 13] could not open port /dev/serial0: [Errno 13] Permission denied: '/dev/serial0'

The error message above indicates that your user does not have permission to
access `/dev/serial0`.  On a Raspberry Pi, you can fix this by running
`sudo usermod -a -G dialout $(whoami)`, logging out, and logging back in again.

> serial.serialutil.SerialException: could not open port 'COM8': PermissionError(13, 'Access is denied.', None, 5)

The error message above occurs on Windows if another program is using the
serial port you are trying to open.

## Files

The essential code for the library is in just two files: `motoron.py` and
`motoron_protocol.py`.

Several example programs come with the library.  They are single-file
Python programs that have names ending with `_example.py`.

## Classes

The main classes provided by this library are motoron.MotoronI2C and
motoron.MotoronSerial.  Each of these is a subclass of motoron.MotoronBase.

## Documentation

For complete documentation of this library, see
[the motoron-python documentation][doc].
If you are already on that page, then click the links in the "Classes" section
above.

## Command timeout

By default, the Motoron will turn off its motors if it has not received a valid
command in the last 1.5 seconds.  You can change the amount of time it
takes for the Motoron to time out using
motoron.MotoronBase.set_command_timeout_milliseconds or you can disable the
feature using motoron.MotoronBase.disable_command_timeout.

## Version history

* 2.0.0 (2023-06-09):
  - Changed the repository name from motoron-rpi to motoron-python.
  - Added MicroPython support and examples for the RP2040.
  - The `read_eeprom` and `get_variables` methods now return `bytes`
    objects instead of a list of integers, which allows the return
    value to be used with `int.from_bytes` and `struct.unpack` in MicroPython.
    Pass the return value to `list()` if you want a list.
  - Added support for the new 550 class Motorons.
  - The `get_vin_voltage_mv` method now takes an optional `type` parameter to
    specify what scaling to apply.
* 1.2.0 (2022-12-23): Added support for the [M2T256] and [M2U256] motorons.
  This version also supports the later-released [M1T256] and [M1U256].
* 1.1.0 (2022-08-05): Added support for the [M2S] and [M2H] Motorons.
* 1.0.0 (2022-05-13): Original release.

[motoron]: https://pololu.com/motoron
[M1T550]: https://www.pololu.com/product/5075
[M1U550]: https://www.pololu.com/product/5077
[M2T550]: https://www.pololu.com/product/5079
[M2U550]: https://www.pololu.com/product/5081
[M3S550]: https://www.pololu.com/category/304
[M3H550]: https://www.pololu.com/category/305
[M1T256]: https://www.pololu.com/product/5061
[M1U256]: https://www.pololu.com/product/5063
[M2T256]: https://www.pololu.com/product/5065
[M2U256]: https://www.pololu.com/product/5067
[M3S256]: https://www.pololu.com/category/290
[M3H256]: https://www.pololu.com/category/292
[M2S]: https://www.pololu.com/category/291
[M2H]: https://www.pololu.com/category/293
[doc]: https://pololu.github.io/motoron-python/
[guide]: https://www.pololu.com/docs/0J84
[smbus2]: https://github.com/kplindegaard/smbus2
[pySerial]: https://github.com/pyserial/pyserial/
[machine.I2C]: https://docs.micropython.org/en/latest/library/machine.I2C.html
[machine.UART]: https://docs.micropython.org/en/latest/library/machine.UART.html
[MSYS2]: https://www.msys2.org/
