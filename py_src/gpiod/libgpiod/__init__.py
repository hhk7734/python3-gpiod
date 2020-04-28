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
from ctypes import set_errno
from errno import ENODEV, ENOENT, ENOTTY
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
    scandir,
)
from os.path import basename
from stat import S_ISCHR

from .time_h import timespec
from .gpio_h import gpiochip_info, GPIO_GET_CHIPINFO_IOCTL

# pylint: disable=too-few-public-methods


# Forward declaration
class gpiod_chip:
    pass


# Forward declaration
class gpiod_line:
    pass


# Forward declaration
class gpiod_line_bulk:
    pass


GPIOD_LINE_BULK_MAX_LINES = 64


class gpiod_line_bulk:
    # pylint: disable=function-redefined
    def __init__(self):
        # GPIOD_LINE_BULK_MAX_LINES
        self.lines = []
        self.num_lines = 0


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
        self.ts = timespec()
        self.event_type = 0


# core.c

LINE_FREE = 0
LINE_REQUESTED_VALUES = 1
LINE_REQUESTED_EVENTS = 2


class line_fd_handle:
    def __init__(self):
        self.fd = 0
        self.refcount = 0


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
        self.fd_handle = line_fd_handle()
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
    def num_lines(self):
        # ::gpiod_chip_num_lines(chip)
        return self._num_lines

    @property
    def fd(self):
        return self._fd

    @property
    def name(self):
        # ::gpiod_chip_name(chip)
        return self._name

    @property
    def label(self):
        # ::gpiod_chip_label(chip)
        return self._label


# Function

# core.c


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


def gpiod_chip_open(path: str) -> gpiod_chip:
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


def gpiod_chip_get_line(chip: gpiod_chip, offset: int) -> gpiod_line:
    pass


def gpiod_line_request(
    line: gpiod_line, config: gpiod_line_request_config, default_val: int
) -> int:
    pass


def gpiod_line_release(line: gpiod_line):
    pass


def gpiod_line_is_requested(line: gpiod_line) -> bool:
    """
    @brief Check if the calling user has ownership of this line.

    @param line: GPIO line object.

    @return True if given line was requested, false otherwise.
    """
    return (
        line.state == LINE_REQUESTED_VALUES
        or line.state == LINE_REQUESTED_EVENTS
    )


def gpiod_line_get_value(line: gpiod_line) -> int:
    pass


def gpiod_line_set_value(line: gpiod_line, value: int) -> int:
    pass


def gpiod_line_event_wait(line: gpiod_line, timeout: timespec) -> int:
    pass


def gpiod_line_event_wait_bulk(
    bulk: gpiod_line_bulk, timeout: timespec, event_bulk: gpiod_line_bulk
) -> int:
    pass


def gpiod_line_event_read(line: gpiod_line, event: gpiod_line_event) -> int:
    pass


def gpiod_line_event_get_fd(line: gpiod_line) -> int:
    pass


# helpers.c


def gpiod_chip_open_by_name(name: str) -> gpiod_chip:
    """
    @brief Open a gpiochip by name.

    @param name: Name of the gpiochip to open.

    @return GPIO chip handle or None if an error occurred.
    """
    return gpiod_chip_open("/dev/" + str(name))


def gpiod_chip_open_by_number(num: int) -> gpiod_chip:
    """
    @brief Open a gpiochip by number.

    @param num: Number of the gpiochip.

    @return GPIO chip handle or None if an error occurred.
    """
    return gpiod_chip_open("/dev/gpiochip" + str(num))


def gpiod_chip_open_by_label(label: str) -> gpiod_chip:
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


def gpiod_chip_open_lookup(descr) -> gpiod_chip:
    """
    @brief Open a gpiochip based on the best guess what the path is.

    @param descr: String describing the gpiochip.

    @return GPIO chip handle or None if an error occurred.

    This routine tries to figure out whether the user passed it the path to the
    GPIO chip, its name, label or number as a string. Then it tries to open it
    using one of the gpiod_chip_open** variants.
    """
    try:
        num = int(descr)
        return gpiod_chip_open_by_number(num)
    except ValueError:
        pass

    chip = gpiod_chip_open_by_label(descr)

    if not bool(chip):
        if descr[:5] != "/dev/":
            return gpiod_chip_open_by_name(descr)

        return gpiod_chip_open(descr)

    return chip


def gpiod_chip_find_line(chip: gpiod_chip, name: str) -> gpiod_line:
    pass


# iter.c


class gpiod_chip_iter:
    def __init__(self):
        self.chips = []
        self.offset = 0

    def __iter__(self):
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

    def __next__(self):
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

        # gpiod_chip_iter_next_noclose
        if self.offset < len(self.chips):
            index = self.offset
            self.offset += 1
            return self.chips[index]

        raise StopIteration
