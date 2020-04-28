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
from ctypes import get_errno
from datetime import timedelta, datetime
from errno import ENOENT
from os import strerror
from typing import List

from .. import libgpiod


class chip:
    # pylint: disable=too-few-public-methods
    OPEN_LOOKUP = 1
    OPEN_BY_PATH = 2
    OPEN_BY_NAME = 3
    OPEN_BY_LABEL = 4
    OPEN_BY_NUMBER = 5


class line:
    # pylint: disable=too-few-public-methods
    pass


class line_bulk:
    # pylint: disable=too-few-public-methods
    pass


class line_event:
    # pylint: disable=too-few-public-methods
    pass


class line_request:
    # pylint: disable=too-few-public-methods
    pass


open_funcs = {
    chip.OPEN_LOOKUP: libgpiod.gpiod_chip_open_lookup,
    chip.OPEN_BY_PATH: libgpiod.gpiod_chip_open,
    chip.OPEN_BY_NAME: libgpiod.gpiod_chip_open_by_name,
    chip.OPEN_BY_LABEL: libgpiod.gpiod_chip_open_by_label,
    chip.OPEN_BY_NUMBER: libgpiod.gpiod_chip_open_by_number,
}


def chip_deleter(chip_struct: libgpiod.gpiod_chip):
    # pylint: disable=missing-function-docstring
    libgpiod.gpiod_chip_close(chip_struct)


class shared_chip:
    # pylint: disable=missing-function-docstring, bad-whitespace
    def __init__(self, chip_struct: libgpiod.gpiod_chip = None):
        self._chip_struct = chip_struct

    def get(self):
        return self._chip_struct

    def __del__(self):
        if self._chip_struct is not None:
            chip_deleter(self._chip_struct)

    def __bool__(self):
        return self._chip_struct is not None


class chip:
    # pylint: disable=function-redefined, bad-whitespace
    def __init__(
        self,
        device=None,
        how: int = chip.OPEN_LOOKUP,
        chip_shared: shared_chip = None,
    ):
        """
        @brief Constructor. Creates an empty GPIO chip object or opens the chip
                using chip.open.

        @param device: String describing the GPIO chip.
        @param how:    Indicates how the chip should be opened.

        Usage:
            c = chip()
            c = chip("gpiochip0")
            c = chip("/dev/gpiochip0", chip.OPEN_BY_PATH)
        """
        if bool(chip_shared):
            self._m_chip = chip_shared
            return

        self._m_chip = shared_chip()
        if device is not None:
            self.open(device, how)

    def __del__(self):
        """
        @brief Destructor

        Usage:
            del chip
        """

    def open(self, device, how: int = chip.OPEN_LOOKUP):
        """
        @brief Open a GPIO chip.

        @param device: String or int describing the GPIO chip.
        @param how:    Indicates how the chip should be opened.

        If the object already holds a reference to an open chip, it will be
        closed and the reference reset.

        Usage:
            chip.open("/dev/gpiochip0")
            chip.open(0, chip.OPEN_BY_NUMBER)
        """
        if how == chip.OPEN_BY_NUMBER:
            device = int(device)
        else:
            device = str(device)

        func = open_funcs[how]

        chip_struct = func(device)
        if chip_struct is None:
            errno = get_errno()
            raise OSError(
                errno,
                strerror(errno),
                "cannot open GPIO device {}".format(device),
            )

        self._m_chip = shared_chip(chip_struct)

    def reset(self):
        """
        @brief Reset the internal smart pointer owned by this object.

        Usage:
            chip.reset()
        """
        # Act like shared_ptr::reset()
        self._m_chip = shared_chip()

    @property
    def name(self) -> str:
        """
        @brief Return the name of the chip held by this object.

        @return Name of the GPIO chip.

        Usage:
            print(chip.name)
        """
        self._throw_if_noref()

        return self._m_chip.get().name

    @property
    def label(self) -> str:
        """
        @brief Return the label of the chip held by this object.

        @return Label of the GPIO chip.

        Usage:
            print(chip.label)
        """
        self._throw_if_noref()

        return self._m_chip.get().label

    @property
    def num_lines(self) -> int:
        """
        @brief Return the number of lines exposed by this chip.

        @return Number of lines.

        Usage:
            print(chip.num_lines)
        """
        self._throw_if_noref()

        return self._m_chip.get().num_lines

    def get_line(self, offset: int) -> line:
        """
        @brief Get the line exposed by this chip at given offset.

        @param offset: Offset of the line.

        @return Line object

        Usage:
            l = chip.get_line(0)
        """
        self._throw_if_noref()

        if offset >= self.num_lines or offset < 0:
            raise IndexError("line offset out of range")

        line_struct = libgpiod.gpiod_chip_get_line(self._m_chip.get(), offset)
        if line_struct is None:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error getting GPIO line from chip"
            )

        # Failed to deepcopy due to pointer of ctypes
        return line(line_struct, chip(chip_shared=self._m_chip))

    def find_line(self, name: str) -> line:
        """
        @brief Get the line exposed by this chip by name.

        @param name: Line name.

        @return Line object.

        Usage:
            l = chip.find_line("PIN_0")
        """
        self._throw_if_noref()

        line_struct = libgpiod.gpiod_chip_find_line(self._m_chip.get(), name)
        errno = get_errno()
        if line_struct is None and errno != ENOENT:
            raise OSError(
                errno, strerror(errno), "error looking up GPIO line by name"
            )

        # Failed to deepcopy due to pointer of ctypes
        return (
            line(line_struct, chip(chip_shared=self._m_chip))
            if bool(line_struct)
            else line()
        )

    def get_lines(self, offsets: List[int]) -> line_bulk:
        """
        @brief Get a set of lines exposed by this chip at given offsets.

        @param offsets: List of line offsets.

        @return Set of lines held by a line_bulk object.

        Usage:
            lb = chip.get_lines([0, 1, 2])
        """
        lines = line_bulk()

        for it in offsets:
            lines.append(self.get_line(it))

        return lines

    def get_all_lines(self) -> line_bulk:
        """
        @brief Get all lines exposed by this chip.

        @return All lines exposed by this chip held by a line_bulk object.

        Usage:
            lb = chip.get_all_lines()
        """
        lines = line_bulk()

        for i in range(self.num_lines):
            lines.append(self.get_line(i))

        return lines

    def find_lines(self, names: List[str]) -> line_bulk:
        """
        @brief Get a set of lines exposed by this chip by their names.

        @param names: List of line names.

        @return Set of lines held by a line_bulk object.

        Usage:
            lb = chip.find_lines(["PIN_0", "PIN_1", "PIN_2"])
        """
        lines = line_bulk()

        for it in names:
            a_line = self.find_line(it)
            if not a_line:
                lines.clear()
                return lines

            lines.append(a_line)

        return lines

    def __eq__(self, rhs: chip) -> bool:
        """
        @brief Equality operator.

        @param rhs: Right-hand side of the equation.

        @return True if rhs references the same chip. False otherwise.

        Usage:
            print(chip1 == chip2)
        """
        return self._m_chip.get() == rhs._m_chip.get()

    def __ne__(self, rhs: chip) -> bool:
        """
        @brief Inequality operator.

        @param rhs: Right-hand side of the equation.

        @return False if rhs references the same chip. True otherwise.

        Usage:
            print(chip1 != chip2)
        """
        return self._m_chip.get() != rhs._m_chip.get()

    def __bool__(self) -> bool:
        """
        @brief Check if this object holds a reference to a GPIO chip.

        @return True if this object references a GPIO chip, false otherwise.

        Usage:
            print(bool(chip))
            print(not chip)
        """
        return self._m_chip.get() is not None

    OPEN_LOOKUP = 1
    OPEN_BY_PATH = 2
    OPEN_BY_NAME = 3
    OPEN_BY_LABEL = 4
    OPEN_BY_NUMBER = 5

    def _throw_if_noref(self):
        if not bool(self._m_chip.get()):
            raise RuntimeError("object not associated with an open GPIO chip")


class line_request:
    # pylint: disable=function-redefined
    # pylint: disable=too-few-public-methods
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
    # pylint: disable=line-too-long
    line_request.DIRECTION_AS_IS: libgpiod.GPIOD_LINE_REQUEST_DIRECTION_AS_IS,
    line_request.DIRECTION_INPUT: libgpiod.GPIOD_LINE_REQUEST_DIRECTION_INPUT,
    line_request.DIRECTION_OUTPUT: libgpiod.GPIOD_LINE_REQUEST_DIRECTION_OUTPUT,
    line_request.EVENT_FALLING_EDGE: libgpiod.GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE,
    line_request.EVENT_RISING_EDGE: libgpiod.GPIOD_LINE_REQUEST_EVENT_RISING_EDGE,
    line_request.EVENT_BOTH_EDGES: libgpiod.GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES,
}

reqflag_mapping = {
    line_request.FLAG_ACTIVE_LOW: libgpiod.GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW,
    line_request.FLAG_OPEN_DRAIN: libgpiod.GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN,
    line_request.FLAG_OPEN_SOURCE: libgpiod.GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE,
}


class line:
    # pylint: disable=function-redefined, bad-whitespace
    def __init__(
        self, line_struct: libgpiod.gpiod_line = None, owner: chip = chip()
    ):
        """
        @brief Constructor. Creates an empty line object.

        Usage:
            l = line()
        """
        self._m_line = line_struct
        self._m_chip = owner

    def __del__(self):
        """
        @brief Destructor

        Usage:
            del line
        """

    @property
    def offset(self) -> int:
        """
        @brief Get the offset of this line.

        @return Offet of this line.

        Usage:
            print(line.offset)
        """
        self._throw_if_null()

        return self._m_line.offset

    @property
    def name(self) -> str:
        """
        @brief Get the name of this line (if any).

        @return Name of this line or an empty string if it is unnamed.

        Usage:
            print(line.name)
        """
        self._throw_if_null()

        return self._m_line.name

    @property
    def consumer(self) -> str:
        """
        @brief Get the consumer of this line (if any).

        @return Name of the consumer of this line or an empty string if it
                is unused.

        Usage:
            print(line.consumer)
        """
        self._throw_if_null()

        return self._m_line.consumer

    @property
    def direction(self) -> int:
        """
        @brief Get current direction of this line.

        @return Current direction setting.

        Usage:
            print(line.direction == line.DIRECTION_INPUT)
        """
        self._throw_if_null()

        return (
            self.DIRECTION_INPUT
            if self._m_line.direction == libgpiod.GPIOD_LINE_DIRECTION_INPUT
            else self.DIRECTION_OUTPUT
        )

    @property
    def active_state(self) -> int:
        """
        @brief Get current active state of this line.

        @return Current active state setting.

        Usage:
            print(line.active_state == line.ACTIVE_HIGH)
        """
        self._throw_if_null()

        return (
            self.ACTIVE_HIGH
            if self._m_line.active_state
            == libgpiod.GPIOD_LINE_ACTIVE_STATE_HIGH
            else self.ACTIVE_LOW
        )

    @property
    def is_used(self) -> bool:
        """
        @brief Check if this line is used by the kernel or other user space
               process.

        @return True if this line is in use, false otherwise.

        Usage:
            print(line.is_used)
        """
        self._throw_if_null()

        return self._m_line.used

    @property
    def is_open_drain(self) -> bool:
        """
        @brief Check if this line represents an open-drain GPIO.

        @return True if the line is an open-drain GPIO, false otherwise.

        Usage:
            print(line.is_open_drain)
        """
        self._throw_if_null()

        return self._m_line.open_drain

    @property
    def is_open_source(self) -> bool:
        """
        @brief Check if this line represents an open-source GPIO.

        @return True if the line is an open-source GPIO, false otherwise.

        Usage:
            print(line.is_open_source)
        """
        self._throw_if_null()

        return self._m_line.open_source

    def request(self, config: line_request, default_val: int = 0):
        """
        @brief Request this line.

        @param config:      Request config (see gpiod.line_request).
        @param default_val: Default value - only matters for OUTPUT direction.

        Usage:
            config = line_request()
            config.consumer = "Application"
            config.request_type = line_request.DIRECTION_OUTPUT

            # line.request(config)
            line.request(config, 1)
        """
        self._throw_if_null()

        conf = libgpiod.gpiod_line_request_config()
        conf.consumer = config.consumer
        conf.request_type = reqtype_mapping[config.request_type]
        conf.flags = 0

        rv = libgpiod.gpiod_line_request(self._m_line, conf, default_val)
        if rv:
            errno = get_errno()
            raise OSError(errno, strerror(errno), "error requesting GPIO line")

    def release(self):
        """
        @brief Release the line if it was previously requested.

        Usage:
            line.release()
        """
        self._throw_if_null()

        libgpiod.gpiod_line_release(self._m_line)

    @property
    def is_requested(self) -> bool:
        """
        @brief Check if this user has ownership of this line.

        @return True if the user has ownership of this line, false otherwise.

        Usage:
            print(line.is_requested)
        """
        self._throw_if_null()

        return libgpiod.gpiod_line_is_requested(self._m_line)

    def get_value(self) -> int:
        """
        @brief Read the line value.

        @return Current value (0 or 1).

        Usage:
            val = line.get_value()
        """
        self._throw_if_null()

        rv = libgpiod.gpiod_line_get_value(self._m_line)
        if rv == -1:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error reading GPIO line value"
            )

        return rv

    def set_value(self, val: int):
        """
        @brief Set the value of this line.

        @param val: New value (0 or 1).

        Usage:
            line.set_value(1)
        """
        self._throw_if_null()

        rv = libgpiod.gpiod_line_set_value(self._m_line, val)
        if rv:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error setting GPIO line value"
            )

    def event_wait(self, timeout: timedelta) -> bool:
        """
        @brief Wait for an event on this line.

        @param timeout: Time to wait before returning if no event occurred.

        @return True if an event occurred and can be read, false if the wait
                timed out.

        Usage:
            if line.event_wait(timedelta(seconds=10)):
                print("An event occurred")
            else:
                print("Timeout")
        """
        self._throw_if_null()

        rv = libgpiod.gpiod_line_event_wait(self._m_line, timeout)
        if rv < 0:
            errno = get_errno()
            raise OSError(errno, strerror(errno), "error polling for events")

        return bool(rv)

    def event_read(self) -> line_event:
        """
        @brief Read a line event.

        @return Line event object.

        Usage:
            if line.event_wait(timedelta(seconds=10)):
                event = line.event_read()
                print(event.event_type == line_event.RISING_EDGE)
                print(event.timestamp)
            else:
                print("Timeout")
        """
        self._throw_if_null()

        event_buf = libgpiod.gpiod_line_event()
        event = line_event()

        rv = libgpiod.gpiod_line_event_read(self._m_line, event_buf)
        if rv < 0:
            errno = get_errno()
            raise OSError(errno, strerror(errno), "error reading line event")

        if event_buf.event_type == libgpiod.GPIOD_LINE_EVENT_RISING_EDGE:
            event.event_type = line_event.RISING_EDGE
        elif event_buf.event_type == libgpiod.GPIOD_LINE_EVENT_FALLING_EDGE:
            event.event_type = line_event.FALLING_EDGE

        event.timestamp = event_buf.ts

        event.source = self

        return event

    def event_get_fd(self) -> int:
        """
        @brief Get the event file descriptor associated with this line.

        @return File descriptor number

        Usage:
            fd = line.event_get_fd()
        """
        self._throw_if_null()

        ret = libgpiod.gpiod_line_event_get_fd(self._m_line)

        if ret < 0:
            errno = get_errno()
            raise OSError(
                errno,
                strerror(errno),
                "unable to get the line event file descriptor",
            )

        return ret

    def get_chip(self) -> chip:
        """
        @brief Get the reference to the parent chip.

        @return Reference to the parent chip object.

        Usage:
            c = line.get_chip()
        """
        return self._m_chip

    def reset(self):
        """
        @brief Reset the state of this object.

        This is useful when the user needs to e.g. keep the line_event object
        but wants to drop the reference to the GPIO chip indirectly held by
        the line being the source of the event.

        Usage:
            line.reset()
        """
        self._m_line = None
        self._m_chip.reset()

    def __eq__(self, rhs: line) -> bool:
        """
        @brief Check if two line objects reference the same GPIO line.

        @param rhs: Right-hand side of the equation.

        @return True if both objects reference the same line, fale otherwise.

        Usage:
            print(line1 == line2)
        """
        return self._m_line == rhs._m_line

    def __ne__(self, rhs: line) -> bool:
        """
        @brief Check if two line objects reference different GPIO lines.

        @param rhs: Right-hand side of the equation.

        @return False if both objects reference the same line, true otherwise.

        Usage:
            print(line1 != line2)
        """
        return self._m_line != rhs._m_line

    def __bool__(self) -> bool:
        """
        @brief Check if this object holds a reference to any GPIO line.

        @return True if this object references a GPIO line, false otherwise.

        Usage:
            print(bool(line))
            print(not line)
        """
        return self._m_line is not None

    DIRECTION_INPUT = 1
    DIRECTION_OUTPUT = 2

    ACTIVE_LOW = 1
    ACTIVE_HIGH = 2

    def _throw_if_null(self):
        if self._m_line is None:
            raise RuntimeError("object not holding a GPIO line handle")


class line_event:
    # pylint: disable=function-redefined
    # pylint: disable=too-few-public-methods
    RISING_EDGE = 1
    FALLING_EDGE = 2

    def __init__(self):
        self.timestamp = datetime()
        self.event_type = 0
        self.source = line()


class line_bulk:
    # pylint: disable=function-redefined
    # pylint: disable=missing-function-docstring
    def __init__(self, lines: List[line] = None):
        self._m_bulk = lines if lines is not None else []

    def __del__(self):
        pass

    def append(self, new_line: line):
        if not new_line:
            raise ValueError("line_bulk cannot hold empty line objects")

        if len(self._m_bulk) >= self.MAX_LINES:
            raise IndexError("maximum number of lines reached")

        if (
            len(self._m_bulk) >= 1
            and self._m_bulk[0].get_chip() != new_line.get_chip()
        ):
            raise ValueError(
                "line_bulk cannot hold GPIO lines from different chips"
            )

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

    def request(self, config: line_request, default_vals: List[int] = None):
        self._throw_if_empty()

        if default_vals is None:
            default_vals = [0] * self.size

        if self.size != len(default_vals):
            raise ValueError(
                "the number of default values must correspond "
                "with the number of lines"
            )

        try:
            for i in range(self.size):
                self._m_bulk[i].request(config, default_vals[i])
        except OSError as error:
            self.release()
            raise error

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
            raise ValueError(
                "the size of values array must correspond with "
                "the number of lines"
            )

        for i in range(self.size):
            self._m_bulk[i].set_value(values[i])

    def event_wait(self, timeout: timedelta) -> line_bulk:
        self._throw_if_empty()

        bulk = libgpiod.gpiod_line_bulk()
        event_bulk = libgpiod.gpiod_line_bulk()
        ret = line_bulk()

        self._to_line_bulk(bulk)

        event_bulk.num_lines = 0

        rv = libgpiod.gpiod_line_event_wait_bulk(bulk, timeout, event_bulk)
        if rv < 0:
            errno = get_errno()
            raise OSError(errno, strerror(errno), "error polling for events")

        if rv > 0:
            for i in range(event_bulk.num_lines):
                ret.append(line(event_bulk[i], self._m_bulk[i].get_chip()))

        return ret

    def __bool__(self) -> bool:
        return not self.empty

    MAX_LINES = libgpiod.GPIOD_LINE_BULK_MAX_LINES

    def __iter__(self) -> [].__iter__():
        return self._m_bulk.__iter__()

    def _throw_if_empty(self):
        if self.empty:
            raise RuntimeError("line_bulk not holding any GPIO lines")

    def _to_line_bulk(self, bulk: libgpiod.gpiod_line_bulk):
        for it in self._m_bulk:
            # pylint: disable=protected-access
            bulk.add(it._m_line)
