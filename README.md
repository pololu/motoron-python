# Motoron Motor Controller Python library for Raspberry Pi

[www.pololu.com](https://www.pololu.com/)

## Summary

This is a Python 3 library that helps interface with
[Motoron motor controllers][motoron] using I&sup2;C or UART serial.

It supports the following Motoron controllers:

- [Motoron M2T256 Dual I&sup2;C Motor Controller][M2T256]
- [Motoron M2U256 Dual Serial Motor Controller][M2U256]
- [Motoron M3S256 Triple Motor Controller Shield for Arduino][M3S256]
- [Motoron M3H256 Triple Motor Controller for Raspberry Pi][M3H256]
- [Motoron M2S Dual High-Power Motor Controllers for Arduino][M2S] (M2S18v20, M2S18v18, M2S24v16, M2S24v14)
- [Motoron M2H Dual High-Power Motor Controllers for Raspberry Pi][M2H] (M2H18v20, M2H18v18, M2H24v16, M2H24v14)

## Supported platforms

This library is designed to run on a Raspberry Pi and also works on
other systems as long as they have Python 3 and either the
[smbus2] library (for I&sup2;C) or the [pySerial] library (for UART serial).
The smbus2 library generally only works on single-board Linux machines with
an I&sup;C bus.  The pySerial library works on a wide variety of platforms.

This library does **not** support Python 2.

## Getting started

This library depends on Python 3 and the easiest way to download the library
is to use git.

To install these programs on Raspberry Pi OS, run:

    sudo apt-get install git python3-dev python3-pip

To install these programs on [MSYS2], run:

    pacman -S git $MINGW_PACKAGE_PREFIX-python3

To download and install the library, run:

    git clone https://github.com/pololu/motoron-rpi.git
    cd motoron-rpi
    sudo python3 setup.py install

(Omit the `sudo` if you are using MSYS2.)

### Getting started with I&sup2;C

If you want to use I&sup2;C, you will need to install [smbus2]:

    sudo pip3 install smbus2

You will also need to enable I&sup2;C, figure out which I&sup2;C bus to use,
set up the I&sup2;C device permissions properly
(so you do not have to use `sudo`), and connect the Motoron to your
Raspberry Pi's I&sup2;C bus.  If you are not sure how to do those things,
see the "Getting started" sections of the [Motoron user's guide][guide].

### Getting started with serial

If you want to use UART serial, you will need to install [pySerial].
You can typically install this with the following command:

    sudo pip3 install pyserial

On MSYS2, the command above probably will not work, but you can install the
pySerial package provided by MSYS2 instead:

    pacman -S $MINGW_PACKAGE_PREFIX-python-pyserial

You will need to make sure that your machine has a serial port that
pySerial can connect to.  This is typically an integrated serial port that is
part of your computer or a USB-to-serial adapter.

On the Raspberry Pi, we recommend using `/dev/serial0`.  You can check if it
exists by running `ls -l /dev/serial*`.
If it does not exist, you should enable it by running
`sudo raspi-config nonint do_serial 2` and rebooting.
You should also add yourself to the `dialout` group by running
`sudo usermod -a -G dialout $(whoami)`, logging out, and logging back in again.

## Examples

Several example programs come with the library.  They are single-file
Python programs that have names ending with `_example.py`.

You can run an example program by typing the path to the example.  For example,
if you are in the `motoron-rpi` directory, type `./i2c_simple_example.py`
to run that example.

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

## Classes

The main classes provided by this library are motoron.MotoronI2C and
motoron.MotoronSerial.  Each of these is a subclass of motoron.MotoronBase.

## Documentation

For complete documentation of this library, see
[the motoron-rpi documentation][doc].
If you are already on that page, then click the links in the "Classes" section
above.

## Command timeout

By default, the Motoron will turn off its motors if it has not received a valid
command in the last 1.5 seconds.  You can change the amount of time it
takes for the Motoron to time out using
motoron.MotoronBase.set_command_timeout_milliseconds or you can disable the
feature using motoron.MotoronBase.disable_command_timeout.

## Version history

* 1.2.0 (2022-12-23): Added support for the [M2T256] and [M2U256] motorons.
* 1.1.0 (2022-08-05): Added support for the [M2S] and [M2H] Motorons.
* 1.0.0 (2022-05-13): Original release.

[motoron]: https://pololu.com/motoron
[M3S256]: https://www.pololu.com/category/290
[M3H256]: https://www.pololu.com/category/292
[M2S]: https://www.pololu.com/category/291
[M2H]: https://www.pololu.com/category/293
[M2T256]: https://www.pololu.com/product/5065
[M2U256]: https://www.pololu.com/product/5067
[doc]: https://pololu.github.io/motoron-rpi/
[guide]: https://www.pololu.com/docs/0J84
[smbus2]: https://github.com/kplindegaard/smbus2
[pySerial]: https://github.com/pyserial/pyserial/
[MSYS2]: https://www.msys2.org/
