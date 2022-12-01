# Motoron Motor Controller Python library for Raspberry Pi

[www.pololu.com](https://www.pololu.com/)

## Summary

This is a Python 3 library that helps interface with
[Motoron motor controllers][motoron] using I&sup2;C.

It supports the following Motorons that were designed for the Raspberry Pi:

- [Motoron M3H256 Triple Motor Controller for Raspberry Pi][M3H256]
- [Motoron M2H Dual High-Power Motor Controllers for Raspberry Pi][M2H] (M2H18v20, M2H18v18, M2H24v16, M2H24v14)

It also supports these Motoron controllers:

- [Motoron M3S256 Triple Motor Controller Shield for Arduino][M3S256]
- [Motoron M2S Dual High-Power Motor Controllers for Arduino][M2S] (M2S18v20, M2S18v18, M2S24v16, M2S24v14)

This library is designed to run on a Raspberry Pi but should also work on
other computers as long as they have Python 3, I&sup2;C and the [smbus2] library.
This library does **not** support Python 2.

## Getting started

To use this library, you will also need to enable I&sup2;C, figure out
which I2C bus to use, set up the I&sup2;C device permissions properly
(so you do not have to use `sudo`), and connect the Motoron to your
Raspberry Pi's I&sup2;C bus.  If you are not sure how to do those things,
see the "Getting started" sections of the [Motoron user's guide][guide].

This library depends on Python 3 and the easiest way to download the library
is to use git.  To install these programs on Raspberry Pi OS, run:

    sudo apt-get install git python3-dev python3-pip

This library depends on [smbus2], which you can install by running:

    sudo pip3 install smbus2

Finally, to download and install the library, run:

    git clone https://github.com/pololu/motoron-rpi.git
    cd motoron-rpi
    sudo python3 setup.py install

## Examples

Several example programs come with the library.  They are single-file
Python programs that have names ending with `_example.py`.

You can run an example program by typing the path to the example.  For example,
if you are in the `motoron-rpi` directory, type `./i2c_simple_example.py`
to run that example.

## Troubleshooting

    FileNotFoundError: [Errno 2] No such file or directory: '/dev/i2c-1'

The error message above indicates that I&sup2;C bus 1 was not found.
For most users, the solution is to run `sudo raspi-config nonint do_i2c 0`
to enable I&sup2;C bus 1 and then reboot.
You can see which I&sup2;C busses are enabled by running `ls /dev/i2c*`.
If you have connected your Motoron to a different I2C bus, you should specify
the bus number when creating the MotoronI2C object.  For example:

    mc = motoron.MotoronI2C(bus=123)

## Classes

The main class provided by this library is motoron.MotoronI2C.

## Documentation

For complete documentation of this library, see
[the motoron-rpi documentation][doc].
If you are already on that page, then click the links in the "Classes" section
above.

## Command timeout

By default, the Motoron will turn off its motors if it has not received a valid
command in the last 1.5 seconds.  You can change the amount of time it
takes for the Motoron to time out using
motoron.MotoronI2C.set_command_timeout_milliseconds or you can disable the
feature using motoron.MotoronI2C.disable_command_timeout.

## Version history

* 1.1.0 (2022-08-05): Added support for the [M2S] and [M2H] Motorons.
* 1.0.0 (2022-05-13): Original release.

[motoron]: https://pololu.com/motoron
[M3S256]: https://www.pololu.com/category/290
[M3H256]: https://www.pololu.com/category/292
[M2S]: https://www.pololu.com/category/291
[M2H]: https://www.pololu.com/category/293
[doc]: https://pololu.github.io/motoron-rpi/
[guide]: https://www.pololu.com/docs/0J84
[smbus2]: https://pypi.org/project/smbus2/
