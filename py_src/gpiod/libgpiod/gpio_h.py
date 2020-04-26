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
from ctypes import c_char, c_uint32, c_int, Structure
from .ioctl_h import _IOR, _IOWR

# pylint: disable=too-few-public-methods


class gpiochip_info(Structure):
    _fields_ = [
        ("name", c_char * 32),
        ("label", c_char * 32),
        ("lines", c_uint32),
    ]


class gpioline_info(Structure):
    _fields_ = [
        ("line_offset", c_uint32),
        ("flags", c_uint32),
        ("name", c_char * 32),
        ("consumer", c_char * 32),
    ]


GPIOHANDLES_MAX = 64


class gpiohandle_request(Structure):
    _fields_ = [
        ("lineoffsets", c_uint32 * GPIOHANDLES_MAX),
        ("flags", c_uint32),
        ("default_values", c_uint32 * GPIOHANDLES_MAX),
        ("consumer_label", c_char * 32),
        ("lines", c_uint32),
        ("fd", c_int),
    ]


class gpioevent_request(Structure):
    _fields_ = [
        ("lineoffset", c_uint32),
        ("handleflags", c_uint32),
        ("eventflags", c_uint32),
        ("consumer_label", c_char * 32),
        ("fd", c_int),
    ]


GPIO_GET_CHIPINFO_IOCTL = _IOR(0xB4, 0x01, gpiochip_info)
GPIO_GET_LINEINFO_IOCTL = _IOWR(0xB4, 0x02, gpioline_info)
GPIO_GET_LINEHANDLE_IOCTL = _IOWR(0xB4, 0x03, gpiohandle_request)
GPIO_GET_LINEEVENT_IOCTL = _IOWR(0xB4, 0x04, gpioevent_request)
