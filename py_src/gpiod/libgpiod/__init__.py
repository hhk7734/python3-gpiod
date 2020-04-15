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

libgpiod = CDLL("libgpiod.so", use_errno=True)


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

if __version__ < (1, 1):
    enum_base = 0
else:
    enum_base = 1

GPIOD_LINE_BULK_MAX_LINES = 64

GPIOD_LINE_DIRECTION_INPUT = enum_base
GPIOD_LINE_DIRECTION_OUTPUT = enum_base + 1

GPIOD_LINE_ACTIVE_STATE_HIGH = enum_base
GPIOD_LINE_ACTIVE_STATE_LOW = enum_base + 1

_LINE_FREE = 0
_LINE_REQUESTED_VALUES = 1
_LINE_REQUESTED_EVENTS = 2

GPIOD_LINE_REQUEST_DIRECTION_AS_IS = enum_base
GPIOD_LINE_REQUEST_DIRECTION_INPUT = enum_base + 1
GPIOD_LINE_REQUEST_DIRECTION_OUTPUT = enum_base + 2
GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE = enum_base + 3
GPIOD_LINE_REQUEST_EVENT_RISING_EDGE = enum_base + 4
GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES = enum_base + 5

GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN = 0b001
GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE = 0b010
GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW = 0b100

GPIOD_LINE_EVENT_RISING_EDGE = enum_base
GPIOD_LINE_EVENT_FALLING_EDGE = enum_base + 1


class timespec(Structure):
    pass


class line_fd_handle(Structure):
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


timespec._fields_ = [
    ("tv_sec", c_long),
    ("tv_nsec", c_long),
]

line_fd_handle._fields_ = [
    ("fd", c_int),
    ("refcount", c_int),
]

gpiod_chip._fields_ = [
    ("lines", POINTER(POINTER(gpiod_line))),
    ("num_lines", c_uint),

    ("fd", c_int),

    ("name", c_char * 32),
    ("label", c_char * 32),
]

if __version__ < (1, 0, 1):
    gpiod_line._fields_ = [
        ("offset", c_uint),
        ("direction", c_int),
        ("active_state", c_int),
        ("used", c_bool),
        ("open_source", c_bool),
        ("open_drain", c_bool),

        ("state", c_int),
        ("up_to_date", c_bool),

        ("chip", POINTER(gpiod_chip)),
        ("fd", c_int),

        ("name", c_char * 32),
        ("consumer", c_char * 32),
    ]
else:
    gpiod_line._fields_ = [
        ("offset", c_uint),
        ("direction", c_int),
        ("active_state", c_int),
        ("used", c_bool),
        ("open_source", c_bool),
        ("open_drain", c_bool),

        ("state", c_int),
        ("up_to_date", c_bool),

        ("chip", POINTER(gpiod_chip)),
        ("fd_handle", POINTER(line_fd_handle)),

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

# Function

gpiod_chip_open = wrap_libgpiod_func(
    "gpiod_chip_open",
    [c_char_p, ],
    POINTER(gpiod_chip)
)

gpiod_chip_open_by_name = wrap_libgpiod_func(
    "gpiod_chip_open_by_name",
    [c_char_p, ],
    POINTER(gpiod_chip)
)

gpiod_chip_open_by_number = wrap_libgpiod_func(
    "gpiod_chip_open_by_number",
    [c_uint, ],
    POINTER(gpiod_chip)
)

gpiod_chip_open_by_label = wrap_libgpiod_func(
    "gpiod_chip_open_by_label",
    [c_char_p, ],
    POINTER(gpiod_chip)
)

gpiod_chip_open_lookup = wrap_libgpiod_func(
    "gpiod_chip_open_lookup",
    [c_char_p, ],
    POINTER(gpiod_chip)
)

gpiod_chip_close = wrap_libgpiod_func(
    "gpiod_chip_close",
    [POINTER(gpiod_chip), ],
    None
)

gpiod_chip_get_line = wrap_libgpiod_func(
    "gpiod_chip_get_line",
    [POINTER(gpiod_chip), c_uint, ],
    POINTER(gpiod_line)
)

gpiod_chip_find_line = wrap_libgpiod_func(
    "gpiod_chip_find_line",
    [POINTER(gpiod_chip), c_char_p, ],
    POINTER(gpiod_line)
)

gpiod_line_request = wrap_libgpiod_func(
    "gpiod_line_request",
    [POINTER(gpiod_line), POINTER(gpiod_line_request_config), c_int, ],
    c_int
)

gpiod_line_release = wrap_libgpiod_func(
    "gpiod_line_release",
    [POINTER(gpiod_line), ],
    None
)

gpiod_line_get_value = wrap_libgpiod_func(
    "gpiod_line_get_value",
    [POINTER(gpiod_line), ],
    c_int
)

gpiod_line_set_value = wrap_libgpiod_func(
    "gpiod_line_set_value",
    [POINTER(gpiod_line), c_int, ],
    c_int
)

gpiod_line_event_wait = wrap_libgpiod_func(
    "gpiod_line_event_wait",
    [POINTER(gpiod_line), POINTER(timespec), ],
    c_int
)

gpiod_line_event_read = wrap_libgpiod_func(
    "gpiod_line_event_read",
    [POINTER(gpiod_line), POINTER(gpiod_line_event), ],
    c_int
)

gpiod_line_event_wait_bulk = wrap_libgpiod_func(
    "gpiod_line_event_wait_bulk",
    [POINTER(gpiod_line_bulk), POINTER(timespec), POINTER(gpiod_line_bulk), ],
    c_int
)

gpiod_line_event_get_fd = wrap_libgpiod_func(
    "gpiod_line_event_get_fd",
    [POINTER(gpiod_line), ],
    c_int
)
