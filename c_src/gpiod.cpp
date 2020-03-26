/*
 * MIT License
 *
 * Copyright (c) 2020 Hyeonki Hong <hhk7734@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

// clang-format off
#include "common.h"
// clang-format on

#include "chip_iter_wrapper.h"
#include "chip_wrapper.h"
#include "line_bulk_wrapper.h"
#include "line_event_wrapper.h"
#include "line_iter_wrapper.h"
#include "line_request_wrapper.h"
#include "line_wrapper.h"

PYBIND11_MODULE(_gpiod, m) {
    set_chip_class(m);
    set_line_request_class(m);
    set_line_class(m);

    m.def("find_line", &gpiod::find_line, py::arg("name"));

    set_line_event_class(m);
    set_line_bulk_class(m);

    m.def("make_chip_iter", &gpiod::make_chip_iter)
        .def("begin",
             py::overload_cast<gpiod::chip_iter>(&gpiod::begin),
             py::arg("iter"))
        .def("end",
             py::overload_cast<const gpiod::chip_iter &>(&gpiod::end),
             py::arg("iter"));

    set_chip_iter_class(m);

    m.def("begin",
          py::overload_cast<gpiod::line_iter>(&gpiod::begin),
          py::arg("iter"))
        .def("end",
             py::overload_cast<const gpiod::line_iter &>(&gpiod::end),
             py::arg("iter"));

    set_line_iter_class(m);
}