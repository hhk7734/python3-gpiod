'''
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
'''
from ctypes import CDLL, \
    c_bool, c_char, c_int, c_uint, c_long, c_char_p, \
    POINTER, pointer, \
    Structure

libgpiod = CDLL("libgpiod.so")


def wrap_libgpiod_func(name: str, argtypes: list, restype):
    func = libgpiod[name]
    func.argtypes = argtypes
    func.restype = restype
    return func


gpiod_version_string = wrap_libgpiod_func(
    "gpiod_version_string",
    None,
    c_char_p
)


__version__ = tuple(int(x) for x in gpiod_version_string().split(b'.'))

GPIOD_LINE_BULK_MAX_LINES = 64


class line_fd_handle(Structure):
    pass


class timespec(Structure):
    pass


class gpiod_chip(Structure):
    pass


class gpiod_line(Structure):
    pass


class gpiod_line_bulk(Structure):
    pass


class gpiod_line_request_config(Structure):
    pass


class gpiod_line_event(Structure):
    pass


line_fd_handle._fields_ = [
    ("fd", c_int),
    ("refcount", c_int),
]

timespec._fields_ = [
    ("tv_sec", c_long),
    ("tv_nsec", c_long),
]

gpiod_chip._fields_ = [
    ("lines", POINTER(POINTER(gpiod_line))),
    ("num_lines", c_uint),

    ("fd", c_int),

    ("name", c_char * 32),
    ("label", c_char * 32),
]

gpiod_line._fields_ = [
    ("offset", c_uint),
    ("direction", c_int),
    ("active_state", c_int),
    ("used", c_bool),
    ("open_source", c_bool),
    ("open_drain", c_bool),

    ("state", c_int),
    ("up_to_date", c_bool),

    ("chip", POINTER(line_fd_handle)),
    ("e_fd_handle", POINTER(gpiod_chip)),

    ("name", c_char * 32),
    ("consumer", c_char * 32),
]

gpiod_line_bulk._fields_ = [
    ("lines", POINTER(gpiod_line) * GPIOD_LINE_BULK_MAX_LINES),
    ("num_lines", c_uint),
]

gpiod_line_request_config._fields_ = [
    ("consumer", c_char_p),
    ("request_type", c_int),
    ("flags", c_int),
]

gpiod_line_event._fields_ = [
    ("ts", timespec),
    ("event_type", c_int),
]
