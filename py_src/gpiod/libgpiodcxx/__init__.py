"""
MIT License

Copyright (c) 2020-2021 Hyeonki Hong <hhk7734@gmail.com>

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
from __future__ import annotations

from copy import copy
from ctypes import get_errno
from datetime import timedelta
from errno import ENOENT
from os import strerror
from typing import Iterator, List, Optional, Union

from .. import libgpiod

# pylint: disable=too-many-lines

_CHIP_OPEN_LOOKUP = 1
_CHIP_OPEN_BY_PATH = 2
_CHIP_OPEN_BY_NAME = 3
_CHIP_OPEN_BY_LABEL = 4
_CHIP_OPEN_BY_NUMBER = 5

_LINE_BIAS_AS_IS = 1
_LINE_BIAS_DISABLE = 2
_LINE_BIAS_PULL_UP = 3
_LINE_BIAS_PULL_DOWN = 4


open_funcs = {
    _CHIP_OPEN_LOOKUP: libgpiod.gpiod_chip_open_lookup,
    _CHIP_OPEN_BY_PATH: libgpiod.gpiod_chip_open,
    _CHIP_OPEN_BY_NAME: libgpiod.gpiod_chip_open_by_name,
    _CHIP_OPEN_BY_LABEL: libgpiod.gpiod_chip_open_by_label,
    _CHIP_OPEN_BY_NUMBER: libgpiod.gpiod_chip_open_by_number,
}


def chip_deleter(chip_struct: libgpiod.gpiod_chip):
    # pylint: disable=missing-function-docstring
    libgpiod.gpiod_chip_close(chip_struct)


class shared_chip:
    # pylint: disable=missing-function-docstring
    def __init__(self, chip_struct: Optional[libgpiod.gpiod_chip] = None):
        self._chip_struct = chip_struct

    def get(self) -> Optional[libgpiod.gpiod_chip]:
        return self._chip_struct

    def __del__(self) -> None:
        if self._chip_struct is not None:
            chip_deleter(self._chip_struct)

    def __bool__(self) -> bool:
        return self._chip_struct is not None


class chip:
    # pylint: disable=function-redefined
    def __init__(
        self,
        device: Optional[Union[int, str]] = None,
        how: int = _CHIP_OPEN_LOOKUP,
        chip_shared: Optional[shared_chip] = None,
    ) -> None:
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
        if chip_shared is not None and bool(chip_shared):
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

    def open(
        self, device: Union[int, str], how: int = _CHIP_OPEN_LOOKUP
    ) -> None:
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
        return self._throw_if_noref_and_get_m_chip().name

    @property
    def label(self) -> str:
        """
        @brief Return the label of the chip held by this object.

        @return Label of the GPIO chip.

        Usage:
            print(chip.label)
        """
        return self._throw_if_noref_and_get_m_chip().label

    @property
    def num_lines(self) -> int:
        """
        @brief Return the number of lines exposed by this chip.

        @return Number of lines.

        Usage:
            print(chip.num_lines)
        """
        return self._throw_if_noref_and_get_m_chip().num_lines

    def get_line(self, offset: int) -> line:
        """
        @brief Get the line exposed by this chip at given offset.

        @param offset: Offset of the line.

        @return Line object

        Usage:
            l = chip.get_line(0)
        """
        if offset >= self.num_lines or offset < 0:
            raise IndexError("line offset out of range")

        line_struct = libgpiod.gpiod_chip_get_line(
            self._throw_if_noref_and_get_m_chip(), offset
        )
        if line_struct is None:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error getting GPIO line from chip"
            )

        return line(line_struct, copy(self))

    def find_line(self, name: str) -> line:
        """
        @brief Get the line exposed by this chip by name.

        @param name: Line name.

        @return Line object.

        Usage:
            l = chip.find_line("PIN_0")
        """
        line_struct = libgpiod.gpiod_chip_find_line(
            self._throw_if_noref_and_get_m_chip(), name
        )
        errno = get_errno()
        if line_struct is None and errno != ENOENT:
            raise OSError(
                errno, strerror(errno), "error looking up GPIO line by name"
            )

        return line(line_struct, copy(self)) if bool(line_struct) else line()

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

    OPEN_LOOKUP = _CHIP_OPEN_LOOKUP
    OPEN_BY_PATH = _CHIP_OPEN_BY_PATH
    OPEN_BY_NAME = _CHIP_OPEN_BY_NAME
    OPEN_BY_LABEL = _CHIP_OPEN_BY_LABEL
    OPEN_BY_NUMBER = _CHIP_OPEN_BY_NUMBER

    def _throw_if_noref_and_get_m_chip(self) -> libgpiod.gpiod_chip:
        _m_chip_get = self._m_chip.get()
        if _m_chip_get is None or not bool(_m_chip_get):
            raise RuntimeError("object not associated with an open GPIO chip")
        return _m_chip_get


class line_request:
    # pylint: disable=function-redefined
    # pylint: disable=too-few-public-methods
    DIRECTION_AS_IS = 1
    DIRECTION_INPUT = 2
    DIRECTION_OUTPUT = 3
    EVENT_FALLING_EDGE = 4
    EVENT_RISING_EDGE = 5
    EVENT_BOTH_EDGES = 6

    FLAG_ACTIVE_LOW = libgpiod.GPIOD_BIT(0)
    FLAG_OPEN_SOURCE = libgpiod.GPIOD_BIT(1)
    FLAG_OPEN_DRAIN = libgpiod.GPIOD_BIT(2)
    FLAG_BIAS_DISABLE = libgpiod.GPIOD_BIT(3)
    FLAG_BIAS_PULL_DOWN = libgpiod.GPIOD_BIT(4)
    FLAG_BIAS_PULL_UP = libgpiod.GPIOD_BIT(5)

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
    # pylint: disable=line-too-long
    line_request.FLAG_ACTIVE_LOW: libgpiod.GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW,
    line_request.FLAG_OPEN_DRAIN: libgpiod.GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN,
    line_request.FLAG_OPEN_SOURCE: libgpiod.GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE,
    line_request.FLAG_BIAS_DISABLE: libgpiod.GPIOD_LINE_REQUEST_FLAG_BIAS_DISABLE,
    line_request.FLAG_BIAS_PULL_DOWN: libgpiod.GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_DOWN,
    line_request.FLAG_BIAS_PULL_UP: libgpiod.GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP,
}

bias_mapping = {
    libgpiod.GPIOD_LINE_BIAS_PULL_UP: _LINE_BIAS_PULL_UP,
    libgpiod.GPIOD_LINE_BIAS_PULL_DOWN: _LINE_BIAS_PULL_DOWN,
    libgpiod.GPIOD_LINE_BIAS_DISABLE: _LINE_BIAS_DISABLE,
    libgpiod.GPIOD_LINE_BIAS_AS_IS: _LINE_BIAS_AS_IS,
}


class line:
    # pylint: disable=function-redefined
    def __init__(
        self,
        line_struct: Optional[libgpiod.gpiod_line] = None,
        owner: chip = chip(),
    ) -> None:
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
        return self._throw_if_null_and_get_m_line().offset

    @property
    def name(self) -> str:
        """
        @brief Get the name of this line (if any).

        @return Name of this line or an empty string if it is unnamed.

        Usage:
            print(line.name)
        """
        return self._throw_if_null_and_get_m_line().name

    @property
    def consumer(self) -> str:
        """
        @brief Get the consumer of this line (if any).

        @return Name of the consumer of this line or an empty string if it
                is unused.

        Usage:
            print(line.consumer)
        """
        return self._throw_if_null_and_get_m_line().consumer

    @property
    def direction(self) -> int:
        """
        @brief Get current direction of this line.

        @return Current direction setting.

        Usage:
            print(line.direction == line.DIRECTION_INPUT)
        """
        return (
            self.DIRECTION_INPUT
            if self._throw_if_null_and_get_m_line().direction
            == libgpiod.GPIOD_LINE_DIRECTION_INPUT
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
        return (
            self.ACTIVE_HIGH
            if self._throw_if_null_and_get_m_line().active_state
            == libgpiod.GPIOD_LINE_ACTIVE_STATE_HIGH
            else self.ACTIVE_LOW
        )

    @property
    def bias(self) -> int:
        """
        @brief Get current bias of this line.

        @return Current bias setting.

        Usage:
            print(line.bias == line.BIAS_PULL_UP)
        """
        return bias_mapping[
            libgpiod.gpiod_line_bias(self._throw_if_null_and_get_m_line())
        ]

    def is_used(self) -> bool:
        """
        @brief Check if this line is used by the kernel or other user space
               process.

        @return True if this line is in use, false otherwise.

        Usage:
            print(line.is_used())
        """
        return libgpiod.gpiod_line_is_used(self._throw_if_null_and_get_m_line())

    def is_open_drain(self) -> bool:
        """
        @brief Check if this line represents an open-drain GPIO.

        @return True if the line is an open-drain GPIO, false otherwise.

        Usage:
            print(line.is_open_drain())
        """
        return libgpiod.gpiod_line_is_open_drain(
            self._throw_if_null_and_get_m_line()
        )

    def is_open_source(self) -> bool:
        """
        @brief Check if this line represents an open-source GPIO.

        @return True if the line is an open-source GPIO, false otherwise.

        Usage:
            print(line.is_open_source())
        """
        return libgpiod.gpiod_line_is_open_source(
            self._throw_if_null_and_get_m_line()
        )

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
        _m_line = self._throw_if_null_and_get_m_line()

        conf = libgpiod.gpiod_line_request_config()
        conf.consumer = config.consumer
        conf.request_type = reqtype_mapping[config.request_type]
        conf.flags = 0

        for k, v in reqflag_mapping.items():
            if config.flags & k:
                conf.flags |= v

        rv = libgpiod.gpiod_line_request(_m_line, conf, default_val)
        if rv:
            errno = get_errno()
            raise OSError(errno, strerror(errno), "error requesting GPIO line")

    def release(self):
        """
        @brief Release the line if it was previously requested.

        Usage:
            line.release()
        """
        libgpiod.gpiod_line_release(self._throw_if_null_and_get_m_line())

    def is_requested(self) -> bool:
        """
        @brief Check if this user has ownership of this line.

        @return True if the user has ownership of this line, false otherwise.

        Usage:
            print(line.is_requested())
        """
        return libgpiod.gpiod_line_is_requested(
            self._throw_if_null_and_get_m_line()
        )

    def get_value(self) -> int:
        """
        @brief Read the line value.

        @return Current value (0 or 1).

        Usage:
            val = line.get_value()
        """
        rv = libgpiod.gpiod_line_get_value(self._throw_if_null_and_get_m_line())
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
        rv = libgpiod.gpiod_line_set_value(
            self._throw_if_null_and_get_m_line(), val
        )
        if rv:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error setting GPIO line value"
            )

    def set_config(self, direction: int, flags: int, value: int = 0):
        """
        @brief Set configuration of this line.

        @param direction: New direction.
        @param flags:     Replacement flags.
        @param value:     New value (0 or 1) - only matters for OUTPUT
                          direction.
        """
        self._throw_if_null()

        bulk = line_bulk([self])

        bulk.set_config(direction, flags, [value])

    def set_flags(self, flags: int):
        """
        @brief Set configuration flags of this line.

        @param flags: Replacement flags.
        """
        self._throw_if_null()

        bulk = line_bulk([self])

        bulk.set_flags(flags)

    def set_direction_input(self):
        """
        @brief Change the direction this line to input.
        """
        self._throw_if_null()

        bulk = line_bulk([self])

        bulk.set_direction_input()

    def set_direction_output(self, value: int = 0):
        """
        @brief Change the direction this lines to output.

        @param value: New value (0 or 1).
        """
        self._throw_if_null()

        bulk = line_bulk([self])

        bulk.set_direction_output([value])

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
        rv = libgpiod.gpiod_line_event_wait(
            self._throw_if_null_and_get_m_line(), timeout
        )
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
        _m_line = self._throw_if_null_and_get_m_line()

        event_buf = libgpiod.gpiod_line_event()
        event = line_event()

        rv = libgpiod.gpiod_line_event_read(_m_line, event_buf)
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
        ret = libgpiod.gpiod_line_event_get_fd(
            self._throw_if_null_and_get_m_line()
        )

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

    def update(self) -> None:
        """
        @brief Re-read the line info from the kernel.

        Usage:
            line.update()
        """
        ret = libgpiod.gpiod_line_update(self._throw_if_null_and_get_m_line())

        if ret < 0:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "unable to update the line info"
            )

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

    BIAS_AS_IS = 1
    BIAS_DISABLE = 2
    BIAS_PULL_UP = 3
    BIAS_PULL_DOWN = 4

    def _throw_if_null(self) -> None:
        if self._m_line is None:
            raise RuntimeError("object not holding a GPIO line handle")

    def _throw_if_null_and_get_m_line(self) -> libgpiod.gpiod_line:
        if self._m_line is None:
            raise RuntimeError("object not holding a GPIO line handle")
        return self._m_line


class line_event:
    # pylint: disable=function-redefined
    # pylint: disable=too-few-public-methods
    RISING_EDGE = 1
    FALLING_EDGE = 2

    def __init__(self):
        self.timestamp = None
        self.event_type = 0
        self.source = line()


class line_bulk:
    # pylint: disable=function-redefined
    # pylint: disable=missing-function-docstring
    def __init__(self, lines: Optional[List[line]] = None) -> None:
        """
        @brief Constructor. Creates a empty line_bulk or from a list of lines.

        @param lines: List of gpiod::line objects.

        @note All lines must be owned by the same GPIO chip.

        Usage:
            bulk = line_bulk()
            bulk = line_bulk([line1, line2])
        """
        self._m_bulk = lines if lines is not None else []

    def __del__(self) -> None:
        """
        @brief Destructor

        Usage:
            del bulk
        """

    def append(self, new_line: line) -> None:
        """
        @brief Add a line to this line_bulk object.

        @param new_line: Line to add.

        @note The new line must be owned by the same chip as all the other
              lines already held by this line_bulk object.

        Usage:
            bulk.append(line1)
        """
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
        """
        @brief Get the line at given offset.

        @param offset: Offset of the line to get.

        @return Reference to the line object.

        Usage:
            line1 = bulk.get(1)
        """
        return self._m_bulk[offset]

    def __getitem__(self, offset: int) -> line:
        """
        @brief Get the line at given offset.

        @param offset: Offset of the line to get.

        @return Reference to the line object.

        Usage:
            line1 = bulk[1]
        """
        return self._m_bulk[offset]

    @property
    def size(self) -> int:
        """
        @brief Get the number of lines currently held by this object.

        @return Number of elements in this line_bulk.

        Usage:
            print(bulk.size)
        """
        return len(self._m_bulk)

    def __len__(self) -> int:
        """
        @brief Get the number of lines currently held by this object.

        @return Number of elements in this line_bulk.

        Usage:
            print(len(bulk))
        """
        return len(self._m_bulk)

    @property
    def empty(self) -> bool:
        """
        @brief Check if this line_bulk doesn't hold any lines.

        @return True if this object is empty, false otherwise.

        Usage:
            print(bulk.empty)
        """
        return len(self._m_bulk) == 0

    def clear(self):
        """
        @brief Remove all lines from this object.

        Usage:
            bulk.clear()
        """
        self._m_bulk.clear()

    def request(
        self, config: line_request, default_vals: Optional[List[int]] = None
    ) -> None:
        """
        @brief Request all lines held by this object.

        @param config:       Request config (see gpiod::line_request).
        @param default_vals: List of default values. Only relevant for output
                             direction requests.

        Usage:
            config = line_request()
            config.consumer = "Application"
            config.request_type = line_request.DIRECTION_OUTPUT

            # bulk.request(config)
            bulk.request(config, [1] * bulk.size)
        """
        self._throw_if_empty()

        if default_vals is None:
            default_vals = [0] * self.size

        if self.size != len(default_vals):
            raise ValueError(
                "the number of default values must correspond "
                "to the number of lines"
            )

        try:
            for i in range(self.size):
                self._m_bulk[i].request(config, default_vals[i])
        except OSError as error:
            self.release()
            raise error

    def release(self) -> None:
        """
        @brief Release all lines held by this object.

        Usage:
            bulk.release()
        """
        self._throw_if_empty()

        for it in self._m_bulk:
            it.release()

    def get_values(self) -> List[int]:
        """
        @brief Read values from all lines held by this object.

        @return List containing line values the order of which corresponds
                to the order of lines in the internal array.

        Usage:
            ret = bulk.get_values()
        """
        self._throw_if_empty()

        values = []
        for it in self._m_bulk:
            values.append(it.get_value())

        return values

    def set_values(self, values: List[int]) -> None:
        """
        @brief Set values of all lines held by this object.

        @param values: List of values to set. Must be the same size as the
               number of lines held by this line_bulk.

        Usage:
            bulk.set)_blaues([1] * bulk.size)
        """
        self._throw_if_empty()

        if self.size != len(values):
            raise ValueError(
                "the size of values array must correspond to "
                "the number of lines"
            )

        for i in range(self.size):
            self._m_bulk[i].set_value(values[i])

    def set_config(
        self, direction: int, flags: int, values: Optional[List[int]] = None
    ):
        """
        @brief Set configuration of all lines held by this object.

        @param direction: New direction.
        @param flags:     Replacement flags.

        @param List of values to set. Must be the same size as the number of
               lines held by this line_bulk.
               Only relevant for output direction requests.
        """
        self._throw_if_empty()

        if values is not None and self.size != len(values):
            raise ValueError(
                "the size of values array must correspond to "
                "the number of lines"
            )

        gflags = 0

        for first, second in reqflag_mapping.items():
            if first & flags:
                gflags |= second

        bulk = libgpiod.gpiod_line_bulk()

        self._to_line_bulk(bulk)

        rv = libgpiod.gpiod_line_set_config_bulk(
            bulk, direction, gflags, values
        )
        if rv < 0:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error setting GPIO line config"
            )

    def set_flags(self, flags: int):
        """
        @brief Set configuration flags of all lines held by this object.

        @param flags: Replacement flags.
        """
        self._throw_if_empty()

        bulk = libgpiod.gpiod_line_bulk()

        self._to_line_bulk(bulk)

        gflags = 0

        for first, second in reqflag_mapping.items():
            if first & flags:
                gflags |= second

        rv = libgpiod.gpiod_line_set_flags_bulk(bulk, gflags)
        if rv < 0:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error setting GPIO line flags"
            )

    def set_direction_input(self):
        """
        @brief Change the direction all lines held by this object to input.
        """
        self._throw_if_empty()

        bulk = libgpiod.gpiod_line_bulk()

        self._to_line_bulk(bulk)

        rv = libgpiod.gpiod_line_set_direction_input_bulk(bulk)
        if rv < 0:
            errno = get_errno()
            raise OSError(
                errno,
                strerror(errno),
                "error setting GPIO line direction to input",
            )

    def set_direction_output(self, values: Optional[List[int]] = None):
        """
        @brief Change the direction this lines to output.

        @param values: Vector of values to set. Must be the same size as the
                       number of lines held by this line_bulk.
        """
        self._throw_if_empty()

        if values is not None and self.size != len(values):
            raise ValueError(
                "the size of values array must correspond to "
                "the number of lines"
            )

        bulk = libgpiod.gpiod_line_bulk()

        self._to_line_bulk(bulk)

        rv = libgpiod.gpiod_line_set_direction_output_bulk(bulk, values)
        if rv < 0:
            errno = get_errno()
            raise OSError(
                errno,
                strerror(errno),
                "error setting GPIO line direction to output",
            )

    def event_wait(self, timeout: timedelta) -> line_bulk:
        """
        @brief Poll the set of lines for line events.

        @param timeout: timedelta to wait before returning an empty line_bulk.

        @return Returns a line_bulk object containing lines on which events
                occurred.

        Usage:
            ebulk = bulk.event_wait(timedelta(microseconds=20000))
        """
        self._throw_if_empty()

        bulk = libgpiod.gpiod_line_bulk()
        event_bulk = libgpiod.gpiod_line_bulk()
        ret = line_bulk()

        self._to_line_bulk(bulk)

        rv = libgpiod.gpiod_line_event_wait_bulk(bulk, timeout, event_bulk)
        if rv < 0:
            errno = get_errno()
            raise OSError(errno, strerror(errno), "error polling for events")

        if rv > 0:
            for i in range(event_bulk.num_lines):
                ret.append(line(event_bulk[i], self._m_bulk[i].get_chip()))

        return ret

    def __bool__(self) -> bool:
        """
        @brief Check if this object holds any lines.

        @return True if this line_bulk holds at least one line, false otherwise.

        Usage:
            print(bool(bulk))
            print(not bulk)
        """
        return not self.empty

    @property
    def MAX_LINES(self) -> int:
        """
        @brief Max number of lines that this object can hold.
        """
        return libgpiod.GPIOD_LINE_BULK_MAX_LINES

    def __iter__(self) -> Iterator[line]:
        """
        @brief Iterator for iterating over lines held by line_bulk.

        Usage:
            for l in bulk:
                print(l.name)
        """
        return self._m_bulk.__iter__()

    def _throw_if_empty(self):
        if self.empty:
            raise RuntimeError("line_bulk not holding any GPIO lines")

    def _to_line_bulk(self, bulk: libgpiod.gpiod_line_bulk) -> None:
        for it in self._m_bulk:
            # pylint: disable=protected-access
            bulk.add(it._m_line)


class chip_iter:
    """
    @brief Allows to iterate over all GPIO chips present on the system.

    Usage:
        for c in chip_iter():
            print(c.name)
    """

    def __init__(self):
        self._iter = None

    def __iter__(self):
        self._iter = libgpiod.gpiod_chip_iter().__iter__()
        if self._iter is None:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error creating GPIO chip iterator"
            )

        return self

    def __next__(self) -> chip:
        _next = self._iter.next_noclose()
        return chip(chip_shared=shared_chip(_next))


class line_iter:
    """
    @brief Allows to iterate over all lines owned by a GPIO chip.

    @param owner: Chip owning the GPIO lines over which we want to iterate.

    Usage:
        for l in line_iter(chip):
            print("{}: {}".format(l.offset, l.name))
    """

    def __init__(self, owner: chip) -> None:
        self._chip = owner

        self._iter = None

    def __iter__(self) -> Iterator[libgpiod.gpiod_line]:
        self._iter = iter(libgpiod.gpiod_line_iter(self._chip._m_chip.get()))
        if self._iter is None:
            errno = get_errno()
            raise OSError(
                errno, strerror(errno), "error creating GPIO line iterator"
            )

        return self

    def __next__(self) -> line:
        if self._iter is not None:
            return line(next(self._iter), self._chip)

        raise StopIteration
