"""
MIT License

Copyright (c) 2020 Hyeonki Hong <hhk7734@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from ctypes import c_char, c_uint8, c_uint32, c_uint64, c_int, Structure
from .ioctl_h import _IOR, _IOWR

# pylint: disable=too-few-public-methods


class gpiochip_info(Structure):
    _fields_ = [
        ("name", c_char * 32),
        ("label", c_char * 32),
        ("lines", c_uint32),
    ]


GPIOLINE_FLAG_KERNEL = 0b0_0001
GPIOLINE_FLAG_IS_OUT = 0b0_0010
GPIOLINE_FLAG_ACTIVE_LOW = 0b0_0100
GPIOLINE_FLAG_OPEN_DRAIN = 0b0_1000
GPIOLINE_FLAG_OPEN_SOURCE = 0b1_0000


class gpioline_info(Structure):
    _fields_ = [
        ("line_offset", c_uint32),
        ("flags", c_uint32),
        ("name", c_char * 32),
        ("consumer", c_char * 32),
    ]


GPIOHANDLES_MAX = 64

GPIOHANDLE_REQUEST_INPUT = 0b0_0001
GPIOHANDLE_REQUEST_OUTPUT = 0b0_0010
GPIOHANDLE_REQUEST_ACTIVE_LOW = 0b0_0100
GPIOHANDLE_REQUEST_OPEN_DRAIN = 0b0_1000
GPIOHANDLE_REQUEST_OPEN_SOURCE = 0b1_0000


class gpiohandle_request(Structure):
    _fields_ = [
        ("lineoffsets", c_uint32 * GPIOHANDLES_MAX),
        ("flags", c_uint32),
        ("default_values", c_uint8 * GPIOHANDLES_MAX),
        ("consumer_label", c_char * 32),
        ("lines", c_uint32),
        ("fd", c_int),
    ]


class gpiohandle_data(Structure):
    _fields_ = [
        ("values", c_uint8 * GPIOHANDLES_MAX),
    ]


GPIOHANDLE_GET_LINE_VALUES_IOCTL = _IOWR(0xB4, 0x08, gpiohandle_data)
GPIOHANDLE_SET_LINE_VALUES_IOCTL = _IOWR(0xB4, 0x09, gpiohandle_data)


GPIOEVENT_REQUEST_RISING_EDGE = 0b01
GPIOEVENT_REQUEST_FALLING_EDGE = 0b10
GPIOEVENT_REQUEST_BOTH_EDGES = (
    GPIOEVENT_REQUEST_RISING_EDGE | GPIOEVENT_REQUEST_FALLING_EDGE
)


class gpioevent_request(Structure):
    _fields_ = [
        ("lineoffset", c_uint32),
        ("handleflags", c_uint32),
        ("eventflags", c_uint32),
        ("consumer_label", c_char * 32),
        ("fd", c_int),
    ]


GPIOEVENT_EVENT_RISING_EDGE = 0b01
GPIOEVENT_EVENT_FALLING_EDGE = 0b10


class gpioevent_data(Structure):
    _fields_ = [
        ("timestamp", c_uint64),
        ("id", c_uint32),
    ]


GPIO_GET_CHIPINFO_IOCTL = _IOR(0xB4, 0x01, gpiochip_info)
GPIO_GET_LINEINFO_IOCTL = _IOWR(0xB4, 0x02, gpioline_info)
GPIO_GET_LINEHANDLE_IOCTL = _IOWR(0xB4, 0x03, gpiohandle_request)
GPIO_GET_LINEEVENT_IOCTL = _IOWR(0xB4, 0x04, gpioevent_request)
