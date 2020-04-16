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

from ctypes import POINTER, pointer, \
    c_int, \
    get_errno
from datetime import timedelta, datetime
from errno import ENOENT
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

    def __bool__(self):
        return bool(self._chip_p)


class chip:
    def __init__(self, device=None, how: int = chip.OPEN_LOOKUP,
                 chip_p: POINTER(libgpiod.gpiod_chip) = None):
        if(bool(chip_p)):
            self._m_chip = chip_p
            return

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
        # Act like shared_ptr::reset()
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

        # Failed to deepcopy due to pointer of ctypes
        return line(line_p, chip(chip_p=self._m_chip))

    def find_line(self, name: str) -> line:
        self._throw_if_noref()

        line_p = libgpiod.gpiod_chip_find_line(
            self._m_chip.get(), name.encode())
        errno = get_errno()
        if not bool(line_p) and errno != ENOENT:
            raise OSError(errno,
                          strerror(errno),
                          "error looking up GPIO line by name")

        # Failed to deepcopy due to pointer of ctypes
        return line(line_p, chip(chip_p=self._m_chip)) \
            if bool(line_p) else line()

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
        lines = line_bulk()

        for it in names:
            a_line = self.find_line(it)
            if not a_line:
                lines.clear()
                return lines

            lines.append(a_line)

        return lines

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


reqtype_mapping = {
    line_request.DIRECTION_AS_IS: libgpiod.GPIOD_LINE_REQUEST_DIRECTION_AS_IS,
    line_request.DIRECTION_INPUT: libgpiod.GPIOD_LINE_REQUEST_DIRECTION_INPUT,
    line_request.DIRECTION_OUTPUT: libgpiod.GPIOD_LINE_REQUEST_DIRECTION_OUTPUT,
    line_request.EVENT_FALLING_EDGE:
        libgpiod.GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE,
    line_request.EVENT_RISING_EDGE:
        libgpiod.GPIOD_LINE_REQUEST_EVENT_RISING_EDGE,
    line_request.EVENT_BOTH_EDGES:
        libgpiod.GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES,
}

reqflag_mapping = {
    line_request.FLAG_ACTIVE_LOW: libgpiod.GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW,
    line_request.FLAG_OPEN_DRAIN: libgpiod.GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN,
    line_request.FLAG_OPEN_SOURCE: libgpiod.GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE,
}


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
        self._throw_if_null()

        conf = libgpiod.gpiod_line_request_config()
        conf.consumer = config.consumer.encode()
        conf.request_type = reqtype_mapping[config.request_type]
        conf.flags = 0

        rv = libgpiod.gpiod_line_request(
            self._m_line, pointer(conf), default_val)
        if rv:
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "error requesting GPIO line")

    def release(self):
        self._throw_if_null()

        libgpiod.gpiod_line_release(self._m_line)

    @property
    def is_requested(self) -> bool:
        self._throw_if_null()

        return self._m_line[0].state == libgpiod._LINE_REQUESTED_VALUES \
            or self._m_line[0].state == libgpiod._LINE_REQUESTED_EVENTS

    def get_value(self) -> int:
        self._throw_if_null()

        rv = libgpiod.gpiod_line_get_value(self._m_line)
        if rv == -1:
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "error reading GPIO line value")

        return rv

    def set_value(self, val: int):
        self._throw_if_null()

        rv = libgpiod.gpiod_line_set_value(self._m_line, val)
        if rv:
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "error setting GPIO line value")

    def event_wait(self, timeout: timedelta) -> bool:
        self._throw_if_null()

        ts = libgpiod.timespec()
        ts.tv_sec = (timeout.days * 86400) + timeout.seconds
        ts.tv_nsec = timeout.microseconds * 1000

        rv = libgpiod.gpiod_line_event_wait(self._m_line, pointer(ts))
        if rv < 0:
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "error polling for events")

        return bool(rv)

    def event_read(self) -> line_event:
        self._throw_if_null()

        event_buf = libgpiod.gpiod_line_event()
        event = line_event()

        rv = libgpiod.gpiod_line_event_read(self._m_line, pointer(event_buf))
        if rv < 0:
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "error reading line event")

        if event_buf.event_type == libgpiod.GPIOD_LINE_EVENT_RISING_EDGE:
            event.event_type = line_event.RISING_EDGE
        elif event_buf.event_type == libgpiod.GPIOD_LINE_EVENT_FALLING_EDGE:
            event.event_type = line_event.FALLING_EDGE

        event.timestamp = datetime(year=1970, month=1, day=1) \
            + timedelta(
            days=event_buf.ts.tv_sec // 86400,
            seconds=event_buf.ts.tv_sec % 86400,
            microseconds=event_buf.ts.tv_nsec // 1000)

        event.source = self

        return event

    def event_get_fd(self) -> int:
        self._throw_if_null()

        ret = libgpiod.gpiod_line_event_get_fd(self._m_line)

        if ret < 0:
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "unable to get the line event file descriptor")

        return ret

    def get_chip(self) -> chip:
        return self._m_chip

    def reset(self):
        self._m_line = None
        self._m_chip.reset()

    def __eq__(self, other: line) -> bool:
        return self._m_line == other._m_line

    def __ne__(self, other: line) -> bool:
        return self._m_line != other._m_line

    def __bool__(self) -> bool:
        return bool(self._m_line)

    DIRECTION_INPUT = 1
    DIRECTION_OUTPUT = 2

    ACTIVE_LOW = 1
    ACTIVE_HIGH = 2

    def _throw_if_null(self):
        if not bool(self._m_line):
            raise RuntimeError("object not holding a GPIO line handle")


class line_event:
    RISING_EDGE = 1
    FALLING_EDGE = 2

    def __init__(self):
        self.timestamp = timedelta()
        self.event_type = 0
        self.source = line()


class line_bulk:
    def __init__(self, lines: List[line] = []):
        # If assigned lines by reference, when using line_bulk(), Changed lists
        # can be assigned, not empty lists.
        self._m_bulk = lines.copy()

    def __del__(self):
        pass

    def append(self, new_line: line):
        if not new_line:
            raise ValueError("line_bulk cannot hold empty line objects")

        if len(self._m_bulk) >= self.MAX_LINES:
            raise IndexError("maximum number of lines reached")

        if len(self._m_bulk) >= 1 and \
                self._m_bulk[0].get_chip() != new_line.get_chip():
            raise ValueError(
                "line_bulk cannot hold GPIO lines from different chips")

        self._m_bulk.append(new_line)

    def get(self, offset: int) -> line:
        return self._m_bulk[offset]

    def __getitem__(self, offset: int) -> line:
        return self._m_bulk[offset]

    @property
    def size(self) -> int:
        return len(self._m_bulk)

    def __len__(self) -> int:
        return len(self._m_bulk)

    @property
    def empty(self) -> bool:
        return len(self._m_bulk) == 0

    def clear(self):
        self._m_bulk = []

    def request(self, config: line_request, default_vals: List[int] = []):
        self._throw_if_empty()

        if not len(default_vals):
            default_vals = [0] * self.size

        if self.size != len(default_vals):
            raise ValueError("the number of default values must correspond "
                             "with the number of lines")

        try:
            for i in range(self.size):
                self._m_bulk[i].request(config, default_vals[i])
        except OSError as e:
            self.release()
            raise e

    def release(self):
        self._throw_if_empty()

        for it in self._m_bulk:
            it.release()

    def get_values(self) -> List[int]:
        self._throw_if_empty()

        values = []
        for it in self._m_bulk:
            values.append(it.get_value())

        return values

    def set_values(self, values: List[int]):
        self._throw_if_empty()

        if self.size != len(values):
            raise ValueError("the size of values array must correspond with "
                             "the number of lines")

        for i in range(self.size):
            self._m_bulk[i].set_value(values[i])

    def event_wait(self, timeout: timedelta) -> line_bulk:
        self._throw_if_empty()

        bulk = libgpiod.gpiod_line_bulk()
        event_bulk = libgpiod.gpiod_line_bulk()
        ts = libgpiod.timespec()
        ret = line_bulk()

        self._to_line_bulk(pointer(bulk))

        event_bulk.num_lines = 0

        ts.tv_sec = (timeout.days * 86400) + timeout.seconds
        ts.tv_nsec = timeout.microseconds * 1000

        rv = libgpiod.gpiod_line_event_wait_bulk(pointer(bulk),
                                                 pointer(ts),
                                                 pointer(event_bulk))
        if rv < 0:
            errno = get_errno()
            raise OSError(errno,
                          strerror(errno),
                          "error polling for events")
        elif rv > 0:
            for i in range(event_bulk.num_lines):
                ret.append(
                    line(event_bulk.lines[i], self._m_bulk[i].get_chip()))

        return ret

    def __bool__(self) -> bool:
        return not self.empty

    MAX_LINES = libgpiod.GPIOD_LINE_BULK_MAX_LINES

    def __iter__(self) -> [].__iter__():
        return self._m_bulk.__iter__()

    def _throw_if_empty(self):
        if self.empty:
            raise RuntimeError("line_bulk not holding any GPIO lines")

    def _to_line_bulk(self, bulk: POINTER(libgpiod.gpiod_line_bulk)):
        bulk[0].num_lines = 0
        for it in self._m_bulk:
            bulk[0].lines[bulk[0].num_lines] = it._m_line
            bulk[0].num_lines += 1
