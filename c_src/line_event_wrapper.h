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

#pragma once

#include "common.h"

void set_line_event_class(py::module &m) {
    py::class_<gpiod::line_event> line_event(m, "line_event");

    line_event.doc()
        = "/**\n"
          " * @brief Describes a single GPIO line event.\n"
          " */";

    line_event
        .def_property_readonly_static(
            "RISING_EDGE",
            [](py::object) { return int(gpiod::line_event::RISING_EDGE); })
        .def_property_readonly_static("FALLING_EDGE", [](py::object) {
            return int(gpiod::line_event::FALLING_EDGE);
        });

    line_event.def(py::init<>())
        .def_readwrite("timestamp", &gpiod::line_event::timestamp)
        .def_readwrite("event_type", &gpiod::line_event::event_type)
        .def_readwrite("source", &gpiod::line_event::source);
}