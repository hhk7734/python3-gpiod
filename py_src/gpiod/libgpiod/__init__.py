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
from ctypes import memmove, memset, pointer, set_errno, sizeof
from datetime import datetime, timedelta
from errno import EBUSY, EINVAL, EIO, ENODEV, ENOENT, ENOTTY, EPERM
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
    read as os_read,
    R_OK,
    scandir,
)
from os.path import basename
import select
from select import POLLIN, POLLNVAL, POLLPRI
from stat import S_ISCHR
from typing import Iterator, List, Optional, Union

from .gpiod_h import *
from ..kernel import *

# core.c

_LINE_FREE = 0
_LINE_REQUESTED_VALUES = 1
_LINE_REQUESTED_EVENTS = 2


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
    # correspond to the ones in the dev attribute in sysfs.
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


def gpiod_chip_open(path: str) -> Optional[gpiod_chip]:
    """
    @brief Open a gpiochip by path.

    @param path: Path to the gpiochip device file.

    @return GPIO chip handle or None if an error occurred.
    """
    info = gpiochip_info()

    try:
        fd = os_open(path, O_RDWR | O_CLOEXEC)
    except FileNotFoundError:
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

    if info.label[0] == "\0":
        label = "unknown"
    else:
        label = info.label.decode()

    return gpiod_chip(
        num_lines=info.lines, fd=fd, name=info.name.decode(), label=label
    )


def gpiod_chip_close(chip: gpiod_chip):
    """
    @brief Close a GPIO chip handle and release all allocated resources.

    @param chip: The GPIO chip object.
    """
    if len(chip.lines) > 0:
        for i in range(chip.num_lines):
            line = chip.lines[i]
            if line is not None:
                gpiod_line_release(line)

    os_close(chip.fd)
    # How to free the chip object?
    del chip


def gpiod_chip_get_line(chip: gpiod_chip, offset: int) -> Optional[gpiod_line]:
    """
    @brief Get the handle to the GPIO line at given offset.

    @param chip:   The GPIO chip object.
    @param offset: The offset of the GPIO line.

    @return The GPIO line handle or None if an error occured.
    """
    if offset < 0 or offset >= chip.num_lines:
        set_errno(EINVAL)
        return None

    if chip.lines[offset] is None:
        line = gpiod_line(chip)
        line.fd_handle = None
        line.offset = offset

        chip.lines[offset] = line

    status = gpiod_line_update(chip.lines[offset])
    if status < 0:
        return None

    return chip.lines[offset]


def gpiod_line_bias(line: gpiod_line) -> int:
    """
    @brief Read the GPIO line bias setting.

    @param line GPIO line object.

    @return Returns GPIOD_LINE_BIAS_PULL_UP, GPIOD_LINE_BIAS_PULL_DOWN,
            GPIOD_LINE_BIAS_DISABLE or GPIOD_LINE_BIAS_AS_IS.
    """
    if line.info_flags & GPIOLINE_FLAG_BIAS_DISABLE:
        return GPIOD_LINE_BIAS_DISABLE
    if line.info_flags & GPIOLINE_FLAG_BIAS_PULL_UP:
        return GPIOD_LINE_BIAS_PULL_UP
    if line.info_flags & GPIOLINE_FLAG_BIAS_PULL_DOWN:
        return GPIOD_LINE_BIAS_PULL_DOWN

    return GPIOD_LINE_BIAS_AS_IS


def gpiod_line_is_used(line: gpiod_line) -> bool:
    """
    @brief Check if the line is currently in use.

    @param line GPIO line object.

    @return True if the line is in use, false otherwise.

    The user space can't know exactly why a line is busy. It may have been
    requested by another process or hogged by the kernel. It only matters that
    the line is used and we can't request it.
    """
    return bool(line.info_flags & GPIOLINE_FLAG_KERNEL)


def gpiod_line_is_open_drain(line: gpiod_line) -> bool:
    """
    @brief Check if the line is an open-drain GPIO.

    @param line GPIO line object.

    @return True if the line is an open-drain GPIO, false otherwise.
    """
    return bool(line.info_flags & GPIOLINE_FLAG_OPEN_DRAIN)


def gpiod_line_is_open_source(line: gpiod_line) -> bool:
    """
    @brief Check if the line is an open-source GPIO.

    @param line GPIO line object.

    @return True if the line is an open-source GPIO, false otherwise.
    """
    return bool(line.info_flags & GPIOLINE_FLAG_OPEN_SOURCE)


def gpiod_line_update(line: gpiod_line) -> int:
    """
    @brief Re-read the line info.

    @param line: GPIO line object.

    @return 0 if the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.

    The line info is initially retrieved from the kernel by
    gpiod_chip_get_line() and is later re-read after every successful request.
    Users can use this function to manually re-read the line info when needed.

    We currently have no mechanism provided by the kernel for keeping the line
    info synchronized and for the sake of speed and simplicity of this low-level
    library we don't want to re-read the line info automatically everytime
    a property is retrieved. Any daemon using this library must track the state
    of lines on its own and call this routine if needed.

    The state of requested lines is kept synchronized (or rather cannot be
    changed by external agents while the ownership of the line is taken) so
    there's no need to call this function in that case.
    """
    info = gpioline_info()

    info.line_offset = line.offset

    status = ioctl(line.chip.fd, GPIO_GET_LINEINFO_IOCTL, info)
    if status < 0:
        return -1

    line.direction = (
        GPIOD_LINE_DIRECTION_OUTPUT
        if info.flags & GPIOLINE_FLAG_IS_OUT
        else GPIOD_LINE_DIRECTION_INPUT
    )
    line.active_state = (
        GPIOD_LINE_ACTIVE_STATE_LOW
        if info.flags & GPIOLINE_FLAG_ACTIVE_LOW
        else GPIOD_LINE_ACTIVE_STATE_HIGH
    )
    line.info_flags = info.flags

    line.name = info.name.decode()
    line.consumer = info.consumer.decode()

    return 0


def _line_bulk_same_chip(bulk: gpiod_line_bulk) -> bool:
    if bulk.num_lines == 1:
        return True

    first_chip = bulk[0].chip

    for it in bulk:
        if it.chip != first_chip:
            set_errno(EINVAL)
            return False

    return True


def _line_bulk_all_requested(bulk: gpiod_line_bulk) -> bool:
    for it in bulk:
        if not gpiod_line_is_requested(it):
            set_errno(EPERM)
            return False

    return True


def _line_bulk_all_free(bulk: gpiod_line_bulk) -> bool:
    for it in bulk:
        if not gpiod_line_is_free(it):
            set_errno(EBUSY)
            return False

    return True


def _line_request_direction_is_valid(direction: int) -> bool:
    if (
        direction == GPIOD_LINE_REQUEST_DIRECTION_AS_IS
        or direction == GPIOD_LINE_REQUEST_DIRECTION_INPUT
        or direction == GPIOD_LINE_REQUEST_DIRECTION_OUTPUT
    ):
        return True

    set_errno(EINVAL)
    return False


def _line_request_direction_to_gpio_handleflag(direction: int) -> int:
    if direction == GPIOD_LINE_REQUEST_DIRECTION_INPUT:
        return GPIOHANDLE_REQUEST_INPUT
    if direction == GPIOD_LINE_REQUEST_DIRECTION_OUTPUT:
        return GPIOHANDLE_REQUEST_OUTPUT

    return 0


def _line_request_flag_to_gpio_handleflag(flags: int) -> int:
    hflags = 0

    if flags & GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN:
        hflags |= GPIOHANDLE_REQUEST_OPEN_DRAIN
    if flags & GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE:
        hflags |= GPIOHANDLE_REQUEST_OPEN_SOURCE
    if flags & GPIOD_LINE_REQUEST_FLAG_ACTIVE_LOW:
        hflags |= GPIOHANDLE_REQUEST_ACTIVE_LOW
    if flags & GPIOD_LINE_REQUEST_FLAG_BIAS_DISABLE:
        hflags |= GPIOHANDLE_REQUEST_BIAS_DISABLE
    if flags & GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_DOWN:
        hflags |= GPIOHANDLE_REQUEST_BIAS_PULL_DOWN
    if flags & GPIOD_LINE_REQUEST_FLAG_BIAS_PULL_UP:
        hflags |= GPIOHANDLE_REQUEST_BIAS_PULL_UP

    return hflags


def _line_request_values(
    bulk: gpiod_line_bulk,
    config: gpiod_line_request_config,
    default_vals: List[int],
) -> int:
    if config.request_type != GPIOD_LINE_REQUEST_DIRECTION_OUTPUT and (
        config.flags
        & (
            GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN
            | GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE
        )
    ):
        set_errno(EINVAL)
        return -1

    if (config.flags & GPIOD_LINE_REQUEST_FLAG_OPEN_DRAIN) and (
        config.flags & GPIOD_LINE_REQUEST_FLAG_OPEN_SOURCE
    ):
        set_errno(EINVAL)
        return -1

    # pylint: disable=no-member
    req = gpiohandle_request()

    req.lines = bulk.num_lines
    req.flags = _line_request_flag_to_gpio_handleflag(config.flags)

    if config.request_type == GPIOD_LINE_REQUEST_DIRECTION_INPUT:
        req.flags |= GPIOHANDLE_REQUEST_INPUT
    elif config.request_type == GPIOD_LINE_REQUEST_DIRECTION_OUTPUT:
        req.flags |= GPIOHANDLE_REQUEST_OUTPUT

    for i in range(bulk.num_lines):
        req.lineoffsets[i] = bulk[i].offset
        if (
            config.request_type == GPIOD_LINE_REQUEST_DIRECTION_OUTPUT
            and default_vals
        ):
            req.default_values[i] = 1 if default_vals[i] else 0

    if config.consumer:
        req.consumer_label = config.consumer[:32].encode()

    fd = bulk[0].chip.fd

    status = ioctl(fd, GPIO_GET_LINEHANDLE_IOCTL, req)
    if status < 0:
        return -1

    # line_fd = line_make_fd_handle(req.fd)
    line_fd = line_fd_handle(req.fd)

    for i, line in enumerate(bulk):
        line.state = _LINE_REQUESTED_VALUES
        line.req_flags = config.flags
        if config.request_type == GPIOD_LINE_REQUEST_DIRECTION_OUTPUT:
            line.output_value = req.default_values[i]
        # line_set_fd(line, line_fd)
        line.fd_handle = line_fd

        rv = gpiod_line_update(line)
        if rv:
            gpiod_line_release_bulk(bulk)
            return rv

    return 0


def _line_request_event_single(
    line: gpiod_line, config: gpiod_line_request_config
) -> int:
    # pylint: disable=no-member
    req = gpioevent_request()
    if config.consumer:
        req.consumer_label = config.consumer[:32].encode()

    req.lineoffset = line.offset
    req.handleflags = _line_request_flag_to_gpio_handleflag(config.flags)
    req.handleflags |= GPIOHANDLE_REQUEST_INPUT

    if config.request_type == GPIOD_LINE_REQUEST_EVENT_RISING_EDGE:
        req.eventflags |= GPIOEVENT_REQUEST_RISING_EDGE
    elif config.request_type == GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE:
        req.eventflags |= GPIOEVENT_REQUEST_FALLING_EDGE
    elif config.request_type == GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES:
        req.eventflags |= GPIOEVENT_REQUEST_BOTH_EDGES

    status = ioctl(line.chip.fd, GPIO_GET_LINEEVENT_IOCTL, req)
    if status < 0:
        return -1

    line_fd = line_fd_handle(req.fd)

    line.state = _LINE_REQUESTED_EVENTS
    line.req_flags = config.flags
    # line_set_fd(line, line_fd)
    line.fd_handle = line_fd

    rv = gpiod_line_update(line)
    if rv:
        gpiod_line_release(line)
        return rv

    return 0


def _line_request_events(
    bulk: gpiod_line_bulk, config: gpiod_line_request_config
) -> int:
    for i in range(bulk.num_lines):
        status = _line_request_event_single(bulk[i], config)
        if status < 0:
            for j in range(i):
                gpiod_line_release(bulk[j])

            return -1

    return 0


def gpiod_line_request(
    line: gpiod_line, config: gpiod_line_request_config, default_val: int
) -> int:
    """
    @brief Reserve a single line.

    @param line:        GPIO line object.
    @param config:      Request options.
    @param default_val: Initial line value - only relevant if we're setting
                        the direction to output.

    @return 0 if the line was properly reserved. In case of an error this
    routine returns -1 and sets the last error number.

    If this routine succeeds, the caller takes ownership of the GPIO line until
    it's released.
    """
    bulk = gpiod_line_bulk()

    bulk.add(line)

    return gpiod_line_request_bulk(bulk, config, [default_val])


def _line_request_is_direction(request: int) -> bool:
    return request in [
        GPIOD_LINE_REQUEST_DIRECTION_AS_IS,
        GPIOD_LINE_REQUEST_DIRECTION_INPUT,
        GPIOD_LINE_REQUEST_DIRECTION_OUTPUT,
    ]


def _line_request_is_events(request: int) -> bool:
    return request in [
        GPIOD_LINE_REQUEST_EVENT_FALLING_EDGE,
        GPIOD_LINE_REQUEST_EVENT_RISING_EDGE,
        GPIOD_LINE_REQUEST_EVENT_BOTH_EDGES,
    ]


def gpiod_line_request_bulk(
    bulk: gpiod_line_bulk,
    config: gpiod_line_request_config,
    default_vals: List[int],
) -> int:
    """
    @brief Reserve a set of GPIO lines.

    @param bulk:         Set of GPIO lines to reserve.
    @param config:       Request options.
    @param default_vals: Initial line values - only relevant if we're setting
                         the direction to output.

    @return 0 if the all lines were properly requested. In case of an error
            this routine returns -1 and sets the last error number.

    If this routine succeeds, the caller takes ownership of the GPIO lines
    until they're released. All the requested lines must be prodivided by the
    same gpiochip.
    """
    if not _line_bulk_same_chip(bulk) or not _line_bulk_all_free(bulk):
        return -1

    if _line_request_is_direction(config.request_type):
        return _line_request_values(bulk, config, default_vals)
    if _line_request_is_events(config.request_type):
        return _line_request_events(bulk, config)

    set_errno(EINVAL)
    return -1


def gpiod_line_release(line: gpiod_line):
    """
    @brief Release a previously reserved line.

    @param line: GPIO line object.
    """
    bulk = gpiod_line_bulk()

    bulk.add(line)

    gpiod_line_release_bulk(bulk)


def gpiod_line_release_bulk(bulk: gpiod_line_bulk):
    """
    @brief Release a set of previously reserved lines.

    @param bulk: Set of GPIO lines to release.

    If the lines were not previously requested together, the behavior is
    undefined.
    """
    for it in bulk:
        # line_fd_decref(line)
        it.fd_handle = None
        it.state = _LINE_FREE


def gpiod_line_is_requested(line: gpiod_line) -> bool:
    """
    @brief Check if the calling user has ownership of this line.

    @param line: GPIO line object.

    @return True if given line was requested, false otherwise.
    """
    return (
        line.state == _LINE_REQUESTED_VALUES
        or line.state == _LINE_REQUESTED_EVENTS
    )


def gpiod_line_is_free(line: gpiod_line) -> bool:
    """
    @brief Check if the calling user has neither requested ownership of this
           line nor configured any event notifications.

    @param line: GPIO line object.

    @return True if given line is free, false otherwise.
    """
    return line.state == _LINE_FREE


def gpiod_line_get_value(line: gpiod_line) -> int:
    """
    @brief Read current value of a single GPIO line.

    @param line: GPIO line object.

    @return 0 or 1 if the operation succeeds. On error this routine returns -1
            and sets the last error number.
    """
    bulk = gpiod_line_bulk()
    value = [0]

    bulk.add(line)

    status = gpiod_line_get_value_bulk(bulk, value)
    if status < 0:
        return -1

    return value[0]


def gpiod_line_get_value_bulk(bulk: gpiod_line_bulk, values: List[int]) -> int:
    """
    @brief Read current values of a set of GPIO lines.

    @param bulk:   Set of GPIO lines to reserve.
    @param values: An array big enough to hold line_bulk->num_lines values.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.

    If succeeds, this routine fills the values array with a set of values in
    the same order, the lines are added to line_bulk. If the lines were not
    previously requested together, the behavior is undefined.
    """
    data = gpiohandle_data()

    if not _line_bulk_same_chip(bulk) or not _line_bulk_all_requested(bulk):
        return -1

    fd = bulk[0].fd_handle.fd

    status = ioctl(fd, GPIOHANDLE_GET_LINE_VALUES_IOCTL, data)
    if status < 0:
        return -1

    for i in range(bulk.num_lines):
        values[i] = data.values[i]

    return 0


def gpiod_line_set_value(line: gpiod_line, value: int) -> int:
    """
    @brief Set the value of a single GPIO line.

    @param line:  GPIO line object.
    @param value: New value.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.
    """
    bulk = gpiod_line_bulk()

    bulk.add(line)

    return gpiod_line_set_value_bulk(bulk, [value])


def gpiod_line_set_value_bulk(
    bulk: gpiod_line_bulk, values: Optional[List[int]] = None
) -> int:
    """
    @brief Set the values of a set of GPIO lines.

    @param bulk:   Set of GPIO lines to reserve.
    @param values: An array holding line_bulk->num_lines new values for lines.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.

    If the lines were not previously requested together, the behavior is
    undefined.
    """
    data = gpiohandle_data()

    if not _line_bulk_same_chip(bulk) or not _line_bulk_all_requested(bulk):
        return -1

    memset(pointer(data), 0, sizeof(data))

    if values is not None:
        for i in range(bulk.num_lines):
            data.values[i] = 1 if values[i] else 0

    fd = bulk[0].fd_handle.fd

    status = ioctl(fd, GPIOHANDLE_SET_LINE_VALUES_IOCTL, data)
    if status < 0:
        return -1

    for i, line in enumerate(bulk):
        line.output_value = data.values[i]

    return 0


def gpiod_line_set_config(
    line: gpiod_line, direction: int, flags: int, value: int
) -> int:
    """
    @brief Update the configuration of a single GPIO line.

    @param line:      GPIO line object.
    @param direction: Updated direction which may be one of
                      GPIOD_LINE_REQUEST_DIRECTION_AS_IS,
                      GPIOD_LINE_REQUEST_DIRECTION_INPUT, or
                      GPIOD_LINE_REQUEST_DIRECTION_OUTPUT.
    @param flags:     Replacement flags.
    @param value:     The new output value for the line when direction is
                      GPIOD_LINE_REQUEST_DIRECTION_OUTPUT.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.
    """
    bulk = gpiod_line_bulk()

    bulk.add(line)

    return gpiod_line_set_config_bulk(bulk, direction, flags, [value])


def gpiod_line_set_config_bulk(
    bulk: gpiod_line_bulk,
    direction: int,
    flags: int,
    values: Optional[List[int]],
) -> int:
    """
    @brief Update the configuration of a set of GPIO lines.

    @param bulk:      Set of GPIO lines.
    @param direction: Updated direction which may be one of
                      GPIOD_LINE_REQUEST_DIRECTION_AS_IS,
                      GPIOD_LINE_REQUEST_DIRECTION_INPUT, or
                      GPIOD_LINE_REQUEST_DIRECTION_OUTPUT.
    @param flags:     Replacement flags.
    @param values:    An array holding line_bulk->num_lines new logical values
                      for lines when direction is
                      GPIOD_LINE_REQUEST_DIRECTION_OUTPUT.
                      A NULL pointer is interpreted as a logical low for all
                      lines.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.

    If the lines were not previously requested together, the behavior is
    undefined.
    """
    hcfg = gpiohandle_config()

    if not _line_bulk_same_chip(bulk) or not _line_bulk_all_requested(bulk):
        return -1

    if not _line_request_direction_is_valid(direction):
        return -1

    memset(pointer(hcfg), 0, sizeof(hcfg))

    hcfg.flags = _line_request_flag_to_gpio_handleflag(flags)
    hcfg.flags |= _line_request_direction_to_gpio_handleflag(direction)
    if direction == GPIOD_LINE_REQUEST_DIRECTION_OUTPUT and values is not None:
        for i in range(bulk.num_lines):
            hcfg.default_values[i] = 1 if values[i] else 0

    fd = bulk[0].fd_handle.fd

    status = ioctl(fd, GPIOHANDLE_SET_CONFIG_IOCTL, hcfg)
    if status < 0:
        return -1

    for i, line in enumerate(bulk):
        line.req_flags = flags
        if direction == GPIOD_LINE_REQUEST_DIRECTION_OUTPUT:
            line.output_value = hcfg.default_values[i]

        rv = gpiod_line_update(line)
        if rv < 0:
            return rv

    return 0


def gpiod_line_set_flags(line: gpiod_line, flags: int) -> int:
    """
    @brief Update the configuration flags of a single GPIO line.

    @param line:  GPIO line object.
    @param flags: Replacement flags.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.
    """
    bulk = gpiod_line_bulk()

    bulk.add(line)

    return gpiod_line_set_flags_bulk(bulk, flags)


def gpiod_line_set_flags_bulk(bulk: gpiod_line_bulk, flags: int) -> int:
    """
    @brief Update the configuration flags of a set of GPIO lines.

    @param bulk:  Set of GPIO lines.
    @param flags: Replacement flags.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.

    If the lines were not previously requested together, the behavior is
    undefined.
    """
    line = bulk[0]
    values = []
    direction: int

    if line.direction == GPIOD_LINE_DIRECTION_OUTPUT:
        for line in bulk:
            values.append(line.output_value)

        direction = GPIOD_LINE_REQUEST_DIRECTION_OUTPUT
    else:
        direction = GPIOD_LINE_REQUEST_DIRECTION_INPUT

    return gpiod_line_set_config_bulk(bulk, direction, flags, values)


def gpiod_line_set_direction_input(line: gpiod_line) -> int:
    """
    @brief Set the direction of a single GPIO line to input.

    @param line: GPIO line object.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.
    """
    return gpiod_line_set_config(
        line, GPIOD_LINE_REQUEST_DIRECTION_INPUT, line.req_flags, 0
    )


def gpiod_line_set_direction_input_bulk(bulk: gpiod_line_bulk) -> int:
    """
    @brief Set the direction of a set of GPIO lines to input.

    @param bulk: Set of GPIO lines.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.

    If the lines were not previously requested together, the behavior is
    undefined.
    """
    line = bulk[0]

    return gpiod_line_set_config_bulk(
        bulk, GPIOD_LINE_REQUEST_DIRECTION_INPUT, line.req_flags, None
    )


def gpiod_line_set_direction_output(line: gpiod_line, value: int) -> int:
    """
    @brief Set the direction of a single GPIO line to output.

    @param line:  GPIO line object.
    @param value: The logical value output on the line.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.
    """
    return gpiod_line_set_config(
        line, GPIOD_LINE_REQUEST_DIRECTION_OUTPUT, line.req_flags, value
    )


def gpiod_line_set_direction_output_bulk(
    bulk: gpiod_line_bulk, values: Optional[List[int]]
) -> int:
    """
    @brief Set the direction of a set of GPIO lines to output.

    @param bulk:   Set of GPIO lines.
    @param values: An array holding line_bulk->num_lines new logical values
                for lines.  A NULL pointer is interpreted as a logical low
                for all lines.

    @return 0 is the operation succeeds. In case of an error this routine
            returns -1 and sets the last error number.

    If the lines were not previously requested together, the behavior is
    undefined.
    """
    line = bulk[0]
    return gpiod_line_set_config_bulk(
        bulk, GPIOD_LINE_REQUEST_DIRECTION_OUTPUT, line.req_flags, values
    )


def gpiod_line_event_wait(line: gpiod_line, timeout: timedelta) -> int:
    """
    @brief Wait for an event on a single line.

    @param line:    GPIO line object.
    @param timeout: Wait time limit.

    @return 0 if wait timed out, -1 if an error occurred, 1 if an event
            occurred.
    """
    bulk = gpiod_line_bulk()

    bulk.add(line)

    return gpiod_line_event_wait_bulk(bulk, timeout, None)


def gpiod_line_event_wait_bulk(
    bulk: gpiod_line_bulk,
    timeout: timedelta,
    event_bulk: Optional[gpiod_line_bulk],
) -> int:
    """
    @brief Wait for events on a set of lines.

    @param bulk:       Set of GPIO lines to monitor.
    @param timeout:    Wait time limit.
    @param event_bulk: Bulk object in which to store the line handles on which
                       events occurred. Can be None.

    @return 0 if wait timed out, -1 if an error occurred, 1 if at least one
            event occurred.
    """
    if not _line_bulk_same_chip(bulk) or not _line_bulk_all_requested(bulk):
        return -1

    poll = select.poll()
    fd_to_line = {}

    for it in bulk:
        poll.register(it.fd_handle.fd, POLLIN | POLLPRI)
        fd_to_line[it.fd_handle.fd] = it

    timeout_ms = (
        (timeout.days * 86_400_000)
        + (timeout.seconds * 1_000)
        + (timeout.microseconds / 1000.0)
    )

    revents = poll.poll(timeout_ms)

    if revents is None:
        return -1
    if len(revents) == 0:
        return 0

    for it in revents:
        fd = it[0]
        revent = it[1]
        if revent:
            if revent & POLLNVAL:
                set_errno(EINVAL)
                return -1

            if event_bulk is not None:
                event_bulk.add(fd_to_line[fd])

    return 1


def gpiod_line_event_read(line: gpiod_line, event: gpiod_line_event) -> int:
    """
    @brief Read the last event from the GPIO line.

    @param line:  GPIO line object.
    @param event: Buffer to which the event data will be copied.

    @return 0 if the event was read correctly, -1 on error.

    @note This function will block if no event was queued for this line.
    """
    fd = gpiod_line_event_get_fd(line)
    if fd < 0:
        return -1

    return gpiod_line_event_read_fd(fd, event)


def gpiod_line_event_get_fd(line: gpiod_line) -> int:
    """
    @brief Get the event file descriptor.

    @param line: GPIO line object.

    @return Number of the event file descriptor or -1 if the user tries to
            retrieve the descriptor from a line that wasn't configured for
            event monitoring.

    Users may want to poll the event file descriptor on their own. This routine
    allows to access it.
    """
    if line.state != _LINE_REQUESTED_EVENTS:
        set_errno(EPERM)
        return -1

    return line.fd_handle.fd


def gpiod_line_event_read_fd(fd: int, event: gpiod_line_event) -> int:
    """
    @brief Read the last GPIO event directly from a file descriptor.

    @param fd:    File descriptor.
    @param event: Buffer in which the event data will be stored.

    @return 0 if the event was read correctly, -1 on error.

    Users who directly poll the file descriptor for incoming events can also
    directly read the event data from it using this routine. This function
    translates the kernel representation of the event to the libgpiod format.
    """
    evdata = gpioevent_data()

    try:
        rd = os_read(fd, sizeof(evdata))
    except OSError:
        return -1

    if len(rd) != sizeof(evdata):
        set_errno(EIO)
        return -1

    memmove(pointer(evdata), rd, sizeof(evdata))

    event.event_type = (
        GPIOD_LINE_EVENT_RISING_EDGE
        if evdata.id == GPIOEVENT_EVENT_RISING_EDGE
        else GPIOD_LINE_EVENT_FALLING_EDGE
    )

    sec = evdata.timestamp // 1_000_000_000
    event.ts = datetime(year=1970, month=1, day=1) + timedelta(
        days=sec // 86400,
        seconds=sec % 86400,
        microseconds=(evdata.timestamp % 1_000_000_000) // 1000,
    )

    return 0


# helpers.c


def gpiod_chip_open_by_name(name: str) -> Optional[gpiod_chip]:
    """
    @brief Open a gpiochip by name.

    @param name: Name of the gpiochip to open.

    @return GPIO chip handle or None if an error occurred.
    """
    return gpiod_chip_open("/dev/" + str(name))


def gpiod_chip_open_by_number(num: Union[int, str]) -> Optional[gpiod_chip]:
    """
    @brief Open a gpiochip by number.

    @param num: Number of the gpiochip.

    @return GPIO chip handle or None if an error occurred.
    """
    return gpiod_chip_open("/dev/gpiochip" + str(num))


def gpiod_chip_open_by_label(label: str) -> Optional[gpiod_chip]:
    """
    @brief Open a gpiochip by label.

    @param label: Label of the gpiochip to open.

    @return GPIO chip handle or None if the chip with given label was not found
            or an error occured.

    @note If the chip cannot be found but no other error occurred, errno is set
          to ENOENT.
    """
    chip_iter = iter(gpiod_chip_iter())
    if chip_iter is None:
        return None

    for chip in chip_iter:
        if chip.label == label:
            # gpiod_chip_iter_free_noclose
            return chip

    set_errno(ENOENT)
    # gpiod_chip_iter_free

    return None


def gpiod_chip_open_lookup(descr: Union[int, str]) -> Optional[gpiod_chip]:
    """
    @brief Open a gpiochip based on the best guess what the path is.

    @param descr: String describing the gpiochip.

    @return GPIO chip handle or None if an error occurred.

    This routine tries to figure out whether the user passed it the path to the
    GPIO chip, its name, label or number as a string. Then it tries to open it
    using one of the gpiod_chip_open** variants.
    """
    if isinstance(descr, int):
        descr = str(descr)

    if descr.isdigit():
        return gpiod_chip_open_by_number(descr)

    chip = gpiod_chip_open_by_label(descr)

    if not bool(chip):
        if descr[:5] != "/dev/":
            return gpiod_chip_open_by_name(descr)

        return gpiod_chip_open(descr)

    return chip


def gpiod_chip_find_line(chip: gpiod_chip, name: str) -> Optional[gpiod_line]:
    """
    @brief Find a GPIO line by name among lines associated with given GPIO chip.

    @param chip: The GPIO chip object.
    @param name: The name of the GPIO line.

    @return The GPIO line handle or None if the line could not be found or an
            error occurred.

    @note In case a line with given name is not associated with given chip, the
          function sets errno to ENOENT.
    """
    line_iter = gpiod_line_iter(chip)
    if line_iter is None:
        return None

    for line in line_iter:
        if line.name and line.name == name:
            return line

    set_errno(ENOENT)

    return None


# iter.c


class gpiod_chip_iter:
    def __init__(self):
        self.chips = []
        self.offset = 0

    def __iter__(self) -> Iterator[gpiod_chip]:
        """
        gpiod_chip_iter_new()

        @brief Create a new gpiochip iterator.

        @return A new chip iterator object or None if an error occurred.
        """
        dirs = []
        for it in scandir("/dev"):
            if it.name[:8] == "gpiochip":
                dirs.append(it.path)

        if len(dirs) == 0:
            return None

        for it in dirs:
            chip = gpiod_chip_open(it)
            if chip is None:
                for c in self.chips:
                    gpiod_chip_close(c)
                self.chips.clear()
                return None

            self.chips.append(chip)

        return self

    def next_noclose(self) -> gpiod_chip:
        """
        gpiod_chip_iter_next_noclose()

        @brief Get the next gpiochip handle without closing the previous one.

        @return The next open gpiochip handle or raise StopIteration if no more
                chips are present in the system.

        @note This function works just like ::gpiod_chip_iter_next but doesn't
              close the most recently opened chip handle.
        """
        if self.offset < len(self.chips):
            index = self.offset
            self.offset += 1
            return self.chips[index]

        raise StopIteration

    def __next__(self) -> gpiod_chip:
        """
        gpiod_chip_iter_next()

        @brief Get the next gpiochip handle.

        @return The next open gpiochip handle or raise StopIteration if no more
                chips are present in the system.

        @note The previous chip handle will be closed.
        """
        if self.offset > 0:
            gpiod_chip_close(self.chips[self.offset - 1])
            self.chips[self.offset - 1] = None

        return self.next_noclose()


class gpiod_line_iter:
    # pylint: disable=too-few-public-methods
    def __init__(self, chip: gpiod_chip):
        self.chip = chip

        self.lines = []

    def __iter__(self) -> Iterator[gpiod_line]:
        # gpiod_line_iter_new(chip)
        for i in range(self.chip.num_lines):
            self.lines.append(gpiod_chip_get_line(self.chip, i))
            if self.lines[i] is None:
                del self.lines
                return iter([])

        return iter(self.lines)
