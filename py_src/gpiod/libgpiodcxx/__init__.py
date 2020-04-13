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
from .. import libgpiod

from ctypes import POINTER, \
    get_errno
from datetime import datetime
from os import strerror
from typing import List


class chip:
    OPEN_LOOKUP = 1
    OPEN_BY_PATH = 2
    OPEN_BY_NAME = 3
    OPEN_BY_LABEL = 4
    OPEN_BY_NUMBER = 5


class line:
    pass


class line_bulk:
    pass


class line_event:
    pass


class line_request:
    pass


open_funcs = {
    chip.OPEN_LOOKUP: libgpiod.gpiod_chip_open_lookup,
    chip.OPEN_BY_PATH: libgpiod.gpiod_chip_open,
    chip.OPEN_BY_NAME: libgpiod.gpiod_chip_open_by_name,
    chip.OPEN_BY_LABEL: libgpiod.gpiod_chip_open_by_label,
    chip.OPEN_BY_NUMBER: libgpiod.gpiod_chip_open_by_number,
}


def chip_deleter(chip_p: POINTER(libgpiod.gpiod_chip)):
    libgpiod.gpiod_chip_close(chip_p)


class shared_chip:
    def __init__(self,
                 chip_p: POINTER(libgpiod.gpiod_chip) = None):
        self._chip_p = chip_p

    def get(self):
        return self._chip_p

    def __del__(self):
        if bool(self._chip_p):
            chip_deleter(self._chip_p)


class chip:
    def __init__(self, device=None, how: int = chip.OPEN_LOOKUP):
        self._m_chip = shared_chip()
        if(device is not None):
            self.open(device, how)

    def __del__(self):
        pass

    def open(self, device, how: int = chip.OPEN_LOOKUP):
        if(how == chip.OPEN_BY_NUMBER):
            device = int(device)
        else:
            device = str(device).encode()

        func = open_funcs[how]

        chip_p = func(device)
        if not bool(chip_p):
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "cannot open GPIO device {}".format(device))

        self._m_chip = shared_chip(chip_p)

    def reset(self):
        self._m_chip = shared_chip()

    @property
    def name(self) -> str:
        self._throw_if_noref()

        return self._m_chip.get()[0].name.decode()

    @property
    def label(self) -> str:
        self._throw_if_noref()

        return self._m_chip.get()[0].label.decode()

    @property
    def num_lines(self) -> int:
        self._throw_if_noref()

        return self._m_chip.get()[0].num_lines

    def get_line(self, offset: int) -> line:
        self._throw_if_noref()

        if offset >= self.num_lines or offset < 0:
            raise IndexError("line offset out of range")

        line_p = libgpiod.gpiod_chip_get_line(self._m_chip.get(), offset)
        if not bool(line_p):
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "error getting GPIO line from chip")

        return line(line_p, self)

    def find_line(self, name: str) -> line:
        pass

    def get_lines(self, offsets: List[int]) -> line_bulk:
        lines = line_bulk()

        for it in offsets:
            lines.append(self.get_line(it))

        return lines

    def get_all_lines(self) -> line_bulk:
        lines = line_bulk()

        for i in range(self.num_lines):
            lines.append(self.get_line(i))

        return lines

    def find_lines(self, names: List[str]) -> line_bulk:
        pass

    def __eq__(self, other: chip) -> bool:
        return self._m_chip.get() == other._m_chip.get()

    def __ne__(self, other: chip) -> bool:
        return self._m_chip.get() != other._m_chip.get()

    def __bool__(self) -> bool:
        return bool(self._m_chip.get())

    OPEN_LOOKUP = 1
    OPEN_BY_PATH = 2
    OPEN_BY_NAME = 3
    OPEN_BY_LABEL = 4
    OPEN_BY_NUMBER = 5

    def _throw_if_noref(self):
        if not bool(self._m_chip.get()):
            raise RuntimeError("object not associated with an open GPIO chip")


class line_request:
    DIRECTION_AS_IS = 1
    DIRECTION_INPUT = 2
    DIRECTION_OUTPUT = 3
    EVENT_FALLING_EDGE = 4
    EVENT_RISING_EDGE = 5
    EVENT_BOTH_EDGES = 6

    FLAG_ACTIVE_LOW = 0b001
    FLAG_OPEN_SOURCE = 0b010
    FLAG_OPEN_DRAIN = 0b100

    def __init__(self):
        self.consumer = ""
        self.request_type = 0
        self.flags = 0


class line:
    def __init__(self,
                 line_p: POINTER(libgpiod.gpiod_line) = None,
                 owner: chip = chip()):
        self._m_line = line_p
        self._m_chip = owner

    def __del__(self):
        pass

    @property
    def offset(self) -> int:
        self._throw_if_null()

        return self._m_line[0].offset

    @property
    def name(self) -> str:
        self._throw_if_null()

        return self._m_line[0].name.decode()

    @property
    def consumer(self) -> str:
        self._throw_if_null()

        return self._m_line[0].consumer.decode()

    @property
    def direction(self) -> int:
        self._throw_if_null()

        return self.DIRECTION_INPUT \
            if self._m_line[0].direction \
            == libgpiod.GPIOD_LINE_DIRECTION_INPUT \
            else self.DIRECTION_OUTPUT

    @property
    def active_state(self) -> int:
        self._throw_if_null()

        return self.ACTIVE_HIGH \
            if self._m_line[0].active_state \
            == libgpiod.GPIOD_LINE_ACTIVE_STATE_HIGH \
            else self.ACTIVE_LOW

    @property
    def is_used(self) -> bool:
        self._throw_if_null()

        return self._m_line[0].used

    @property
    def is_open_drain(self) -> bool:
        self._throw_if_null()

        return self._m_line[0].open_drain

    @property
    def is_open_source(self) -> bool:
        self._throw_if_null()

        return self._m_line[0].open_source

    def request(self, config: line_request, default_val: int = 0):
        pass

    def release(self):
        pass

    @property
    def is_requested(self) -> bool:
        self._throw_if_null()

        return self._m_line[0].state == libgpiod._LINE_REQUESTED_VALUES \
            or self._m_line[0].state == libgpiod._LINE_REQUESTED_EVENTS

    def get_value(self) -> int:
        pass

    def set_value(self, val: int):
        pass

    def event_wait(self, timeout: datetime) -> bool:
        pass

    def event_read(self) -> line_event:
        pass

    def event_get_fd(self) -> int:
        pass

    def get_chip(self) -> chip:
        pass

    def reset(self):
        pass

    def __eq__(self, other: line) -> bool:
        pass

    def __ne__(self, other: line) -> bool:
        pass

    def __bool__(self) -> bool:
        pass

    DIRECTION_INPUT = 1
    DIRECTION_OUTPUT = 2

    ACTIVE_LOW = 1
    ACTIVE_HIGH = 2

    def _throw_if_null(self):
        if not bool(self._m_line):
            raise RuntimeError("object not holding a GPIO line handle")


class line_event:
    RISING_EDGE = None
    FALLING_EDGE = None

    def __init__(self):
        self.timestamp = None
        self.event_type = None
        self.source = None


class line_bulk:
    def __init__(self, lines: List[line] = []):
        pass

    def __del__(self):
        pass

    def append(self, new_line: line):
        pass

    def get(self, offset: int) -> line:
        pass

    def __getitem__(self, index: int) -> line:
        pass

    def size(self) -> int:
        pass

    def empty(self) -> bool:
        pass

    def clear(self):
        pass

    def request(self, config: line_request, default_vals: List[int]):
        pass

    def release(self):
        pass

    def get_values(self) -> List[int]:
        pass

    def set_values(self, values: List[int]):
        pass

    def event_wait(self, timeout: datetime) -> line_bulk:
        pass

    def __bool__(self) -> bool:
        pass

    MAX_LINES = None

    def __iter__(self):
        pass

    def __next__(self) -> line:
        pass
