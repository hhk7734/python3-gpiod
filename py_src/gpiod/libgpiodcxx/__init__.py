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

from datetime import datetime
from typing import List


class chip:
    pass


class line:
    pass


class line_bulk:
    pass


class line_event:
    pass


class line_request:
    pass


class chip:
    def __init__(self, device, how: int):
        pass

    def __del__(self):
        pass

    def open(self, device, how: int):
        pass

    def reset(self):
        pass

    def name(self) -> str:
        pass

    def label(self) -> str:
        pass

    def num_lines(self) -> int:
        pass

    def get_line(self, offset: int) -> line:
        pass

    def find_line(self, name: str) -> line:
        pass

    def get_lines(self, offsets: List[int]) -> line_bulk:
        pass

    def get_all_lines(self) -> line_bulk:
        pass

    def find_lines(self, names: List[str]) -> line_bulk:
        pass

    def __eq__(self, other: chip) -> bool:
        pass

    def __ne__(self, other: chip) -> bool:
        pass

    def __bool__(self) -> bool:
        pass

    OPEN_LOOKUP = None
    OPEN_BY_PATH = None
    OPEN_BY_NAME = None
    OPEN_BY_LABEL = None
    OPEN_BY_NUMBER = None


class line_request:
    DIRECTION_AS_IS = None
    DIRECTION_INPUT = None
    DIRECTION_OUTPUT = None
    EVENT_FALLING_EDGE = None
    EVENT_RISING_EDGE = None
    EVENT_BOTH_EDGES = None

    FLAG_ACTIVE_LOW = None
    FLAG_OPEN_SOURCE = None
    FLAG_OPEN_DRAIN = None

    def __init__(self):
        self.consumer = None
        self.flags = None


class line:
    def __init__(self, line, owner: chip):
        pass

    def __del__(self):
        pass

    def offset(self) -> int:
        pass

    def name(self) -> str:
        pass

    def consumer(self) -> str:
        pass

    def direction(self) -> int:
        pass

    def active_state(self) -> int:
        pass

    def is_used(self) -> bool:
        pass

    def is_open_drain(self) -> bool:
        pass

    def is_open_source(self) -> bool:
        pass

    def request(self, config: line_request, default_val: int = 0):
        pass

    def release(self):
        pass

    def is_requested(self) -> bool:
        pass

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

    DIRECTION_INPUT = None
    DIRECTION_OUTPUT = None

    ACTIVE_LOW = None
    ACTIVE_HIGH = None


class line_event:
    RISING_EDGE = None
    FALLING_EDGE = None

    def __init__(self):
        self.timestamp = None
        self.event_type = None
        self.source = None


class line_bulk:
    def __init__(self, lines: List[line]):
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
