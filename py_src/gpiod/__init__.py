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
from . import libgpiodcxx


class chip(libgpiodcxx.chip):
    pass


class line(libgpiodcxx.line):
    pass


class line_bulk(libgpiodcxx.line_bulk):
    pass


def find_line(name: str) -> line:
    """
    @brief Find a GPIO line by name. Search all GPIO chips present on the
           system.

    @param name: Name of the line.

    @return A line object - empty if the line was not found.
    """
    for c in chip_iter():
        ret = c.find_line(name)
        if bool(ret):
            return ret

    return ret


class line_event(libgpiodcxx.line_event):
    # pylint: disable=too-few-public-methods
    pass


class line_request(libgpiodcxx.line_request):
    # pylint: disable=too-few-public-methods
    pass


class chip_iter(libgpiodcxx.chip_iter):
    # pylint: disable=too-few-public-methods
    pass


def make_chip_iter() -> chip_iter:
    """
    @brief Create a new chip_iter.

    @return New chip iterator object pointing to the first GPIO chip on the
            system.

    Usage:
        for c in make_chip_iter():
            print(c.label)
    """
    return chip_iter().__iter__()


class line_iter(libgpiodcxx.line_iter):
    # pylint: disable=too-few-public-methods
    pass
