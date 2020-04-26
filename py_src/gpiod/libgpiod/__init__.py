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
from ctypes import (
    CDLL,
    c_bool,
    c_char,
    c_int,
    c_uint,
    c_long,
    c_char_p,
    POINTER,
    pointer,
    set_errno,
    Structure,
)
from errno import ENODEV, ENOTTY
from fcntl import ioctl
from os import (
    access,
    close as os_close,
    lstat,
    major,
    minor,
    open as os_open,
    O_CLOEXEC,
    O_RDWR,
    R_OK,
)
from os.path import basename
from stat import S_ISCHR

from .time_h import timespec
from .gpio_h import gpiochip_info, GPIO_GET_CHIPINFO_IOCTL

SO_CANDIDATE = (
    "libgpiod.so",
    "libgpiod.so.2",
    "libgpiod.so.1",
)
libgpiod = None

for so in SO_CANDIDATE:
    try:
        libgpiod = CDLL(so, use_errno=True)
        break
    except OSError:
        pass
    except BaseException as error:
        raise error

if libgpiod is None:
    raise FileNotFoundError("Failed to find any of {}".format(SO_CANDIDATE))


def wrap_libgpiod_func(name: str, argtypes: list, restype):
    # pylint: disable=missing-function-docstring
    func = libgpiod[name]
    func.argtypes = argtypes
    func.restype = restype
    return func


gpiod_version_string = wrap_libgpiod_func(
    "gpiod_version_string", None, c_char_p
)


__version__ = tuple(int(x) for x in gpiod_version_string().split(b"."))

if __version__ < (1, 1):
    ENUM_BASE = 0
else:
    ENUM_BASE = 1


# pylint: disable=too-few-public-methods


# Forward declaration
class gpiod_chip(Structure):
    pass


# Forward declaration
class gpiod_line(Structure):
    pass


# Forward declaration
class gpiod_line_bulk(Structure):
    pass


GPIOD_LINE_BULK_MAX_LINES = 64


class gpiod_line_bulk(Structure):
    # pylint: disable=function-redefined
    _fields_ = [
        ("lines", POINTER(gpiod_line) * GPIOD_LINE_BULK_MAX_LINES),
        ("num_lines", c_uint),
    ]


GPIOD_LINE_DIRECTION_INPUT = ENUM_BASE
GPIOD_LINE_DIRECTION_OUTPUT = ENUM_BASE + 1

GPIOD_LINE_ACTIVE_STATE_HIGH = ENUM_BASE
GPIOD_LINE_ACTIVE_STATE_LOW = ENUM_BASE + 1

GPIOD_LINE_REQUEST_DIRECTION_AS_IS = ENUM_BASE
GPIOD_LINE_REQUEST_DIRECTION_INPUT = ENUM_BASE + 1
GPIOD_LINE_REQUEST_DIRECTION_OUTPUT = ENUM_BASE + 2
GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE = ENUM_BASE + 3
GPIOD_LINE_REQUEST_EVENT_RISING_EDGE = ENUM_BASE + 4
GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES = ENUM_BASE + 5

GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN = 0b001
GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE = 0b010
GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW = 0b100


class gpiod_line_request_config(Structure):
    _fields_ = [
        ("consumer", c_char_p),
        ("request_type", c_int),
        ("flags", c_int),
    ]


GPIOD_LINE_EVENT_RISING_EDGE = ENUM_BASE
GPIOD_LINE_EVENT_FALLING_EDGE = ENUM_BASE + 1


class gpiod_line_event(Structure):
    _fields_ = [
        ("ts", timespec),
        ("event_type", c_int),
    ]


# core.c

LINE_FREE = 0
LINE_REQUESTED_VALUES = 1
LINE_REQUESTED_EVENTS = 2

if __version__ < (1, 0, 1):

    class gpiod_line(Structure):
        # pylint: disable=function-redefined
        _fields_ = [
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

    class line_fd_handle(Structure):
        _fields_ = [
            ("fd", c_int),
            ("refcount", c_int),
        ]

    class gpiod_line(Structure):
        # pylint: disable=function-redefined
        _fields_ = [
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


class gpiod_chip(Structure):
    # pylint: disable=function-redefined
    _fields_ = [
        ("lines", POINTER(POINTER(gpiod_line))),
        ("num_lines", c_uint),
        ("fd", c_int),
        ("name", c_char * 32),
        ("label", c_char * 32),
    ]


# Function


def _is_gpiochip_cdev(path: str) -> bool:
    try:
        statbuf = lstat(path)
    except FileNotFoundError:
        return False

    # Is it a character device?
    if not S_ISCHR(statbuf.st_mode):
        # Passing a file descriptor not associated with a character
        # device to ioctl() makes it set errno to ENOTTY. Let's do
        # the same in order to stay compatible with the versions of
        # libgpiod from before the introduction of this routine.
        set_errno(ENOTTY)
        return False

    # Do we have a corresponding sysfs attribute?
    name = basename(path)
    sysfsp = "/sys/bus/gpio/devices/{}/dev".format(name)
    if not access(sysfsp, R_OK):
        # This is a character device but not the one we're after.
        # Before the introduction of this function, we'd fail with
        # ENOTTY on the first GPIO ioctl() call for this file
        # descriptor. Let's stay compatible here and keep returning
        # the same error code.
        set_errno(ENOTTY)
        return False

    # Make sure the major and minor numbers of the character device
    # correspond with the ones in the dev attribute in sysfs.
    devstr = "{}:{}".format(major(statbuf.st_rdev), minor(statbuf.st_rdev))

    try:
        with open(sysfsp, "r") as fd:
            sysfsdev = fd.read(len(devstr))
    except FileNotFoundError:
        return False

    if sysfsdev != devstr:
        set_errno(ENODEV)
        return False

    return True


def gpiod_chip_open(path: c_char_p) -> POINTER(gpiod_chip):
    """
    @brief Open a gpiochip by path.

    @param path Path to the gpiochip device file.

    @return GPIO chip handle or NULL if an error occurred.
    """
    info = gpiochip_info()
    chip = pointer(gpiod_chip())

    fd = os_open(path, O_RDWR | O_CLOEXEC)
    if fd < 0:
        return None

    # We were able to open the file but is it really a gpiochip character
    # device?
    if not _is_gpiochip_cdev(path):
        os_close(fd)
        return None

    status = ioctl(fd, GPIO_GET_CHIPINFO_IOCTL, info)
    if status < 0:
        os_close(fd)
        return None

    chip[0].fd = fd
    chip[0].num_lines = info.lines
    chip[0].name = info.name

    if info.label[0] == "\0":
        chip[0].label = b"unknown"
    else:
        chip[0].label = info.label

    return chip


gpiod_chip_open_by_name = wrap_libgpiod_func(
    "gpiod_chip_open_by_name", [c_char_p,], POINTER(gpiod_chip)
)

gpiod_chip_open_by_number = wrap_libgpiod_func(
    "gpiod_chip_open_by_number", [c_uint,], POINTER(gpiod_chip)
)

gpiod_chip_open_by_label = wrap_libgpiod_func(
    "gpiod_chip_open_by_label", [c_char_p,], POINTER(gpiod_chip)
)

gpiod_chip_open_lookup = wrap_libgpiod_func(
    "gpiod_chip_open_lookup", [c_char_p,], POINTER(gpiod_chip)
)

gpiod_chip_close = wrap_libgpiod_func(
    "gpiod_chip_close", [POINTER(gpiod_chip),], None
)

gpiod_chip_get_line = wrap_libgpiod_func(
    "gpiod_chip_get_line", [POINTER(gpiod_chip), c_uint,], POINTER(gpiod_line)
)

gpiod_chip_find_line = wrap_libgpiod_func(
    "gpiod_chip_find_line",
    [POINTER(gpiod_chip), c_char_p,],
    POINTER(gpiod_line),
)

gpiod_line_request = wrap_libgpiod_func(
    "gpiod_line_request",
    [POINTER(gpiod_line), POINTER(gpiod_line_request_config), c_int,],
    c_int,
)

gpiod_line_release = wrap_libgpiod_func(
    "gpiod_line_release", [POINTER(gpiod_line),], None
)


def gpiod_line_is_requested(line: POINTER(gpiod_line)) -> bool:
    """
    @brief Check if the calling user has ownership of this line.

    @param line: GPIO line object.

    @return True if given line was requested, false otherwise.
    """
    return (
        line[0].state == LINE_REQUESTED_VALUES
        or line[0].state == LINE_REQUESTED_EVENTS
    )


gpiod_line_get_value = wrap_libgpiod_func(
    "gpiod_line_get_value", [POINTER(gpiod_line),], c_int
)

gpiod_line_set_value = wrap_libgpiod_func(
    "gpiod_line_set_value", [POINTER(gpiod_line), c_int,], c_int
)

gpiod_line_event_wait = wrap_libgpiod_func(
    "gpiod_line_event_wait", [POINTER(gpiod_line), POINTER(timespec),], c_int
)

gpiod_line_event_read = wrap_libgpiod_func(
    "gpiod_line_event_read",
    [POINTER(gpiod_line), POINTER(gpiod_line_event),],
    c_int,
)

gpiod_line_event_wait_bulk = wrap_libgpiod_func(
    "gpiod_line_event_wait_bulk",
    [POINTER(gpiod_line_bulk), POINTER(timespec), POINTER(gpiod_line_bulk),],
    c_int,
)

gpiod_line_event_get_fd = wrap_libgpiod_func(
    "gpiod_line_event_get_fd", [POINTER(gpiod_line),], c_int
)
