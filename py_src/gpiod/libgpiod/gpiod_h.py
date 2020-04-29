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
from os import close as os_close

# pylint: disable=too-few-public-methods

# Forward declaration
class gpiod_chip:
    pass


# Forward declaration
class gpiod_line:
    pass


GPIOD_LINE_BULK_MAX_LINES = 64


class gpiod_line_bulk:
    # pylint: disable=function-redefined
    def __init__(self):
        # gpiod_line_bulk_init(bulk)
        self._lines = []

    # pylint: disable=missing-function-docstring

    def add(self, line: gpiod_line):
        # gpiod_line_bulk_add(bulk, line)
        if self.num_lines < GPIOD_LINE_BULK_MAX_LINES:
            self._lines.append(line)

    @property
    def num_lines(self) -> int:
        # gpiod_line_bulk_num_lines(bulk)
        return len(self._lines)

    def __getitem__(self, offset):
        # gpiod_line_bulk_get_line(bulk, offset)
        return self._lines[offset]

    def __iter__(self):
        return iter(self._lines)


GPIOD_LINE_DIRECTION_INPUT = 1
GPIOD_LINE_DIRECTION_OUTPUT = 2

GPIOD_LINE_ACTIVE_STATE_HIGH = 1
GPIOD_LINE_ACTIVE_STATE_LOW = 2

GPIOD_LINE_REQUEST_DIRECTION_AS_IS = 1
GPIOD_LINE_REQUEST_DIRECTION_INPUT = 2
GPIOD_LINE_REQUEST_DIRECTION_OUTPUT = 3
GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE = 4
GPIOD_LINE_REQUEST_EVENT_RISING_EDGE = 5
GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES = 6

GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN = 0b001
GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE = 0b010
GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW = 0b100


class gpiod_line_request_config:
    def __init__(self):
        self.consumer = ""
        self.request_type = 0
        self.flags = 0


GPIOD_LINE_EVENT_RISING_EDGE = 1
GPIOD_LINE_EVENT_FALLING_EDGE = 2


class gpiod_line_event:
    def __init__(self):
        self.ts = None
        self.event_type = 0


# core.c

# _LINE_FREE = 0
# _LINE_REQUESTED_VALUES = 1
# _LINE_REQUESTED_EVENTS = 2


class line_fd_handle:
    def __init__(self, fd):
        self.fd = fd

    def __del__(self):
        # line_fd_decref(line)
        os_close(self.fd)


class gpiod_line:
    # pylint: disable=function-redefined, too-many-instance-attributes
    def __init__(self, chip: gpiod_chip):
        self.offset = 0
        self.direction = 0
        self.active_state = 0
        self.used = False
        self.open_source = False
        self.open_drain = False
        self.state = 0
        self.up_to_date = False
        self.chip = chip
        self.fd_handle = None
        # size 32
        self.name = ""
        # size 32
        self.consumer = ""


class gpiod_chip:
    # pylint: disable=function-redefined
    def __init__(self, num_lines: int, fd: int, name: str, label: str):
        self.lines = [None] * num_lines
        self._num_lines = num_lines
        self._fd = fd
        # size 32
        self._name = name
        # size 32
        self._label = label

    # pylint: disable=missing-function-docstring

    @property
    def num_lines(self) -> int:
        # ::gpiod_chip_num_lines(chip)
        return self._num_lines

    @property
    def fd(self) -> int:
        return self._fd

    @property
    def name(self) -> str:
        # ::gpiod_chip_name(chip)
        return self._name

    @property
    def label(self) -> str:
        # ::gpiod_chip_label(chip)
        return self._label
