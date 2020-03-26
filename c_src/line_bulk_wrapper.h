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

void set_line_bulk_class(py::module &m) {
    py::class_<gpiod::line_bulk> line_bulk(m, "line_bulk");

    line_bulk.def(py::init<>())
        .def(py::init<const std::vector<gpiod::line> &>())
        .def("append", &gpiod::line_bulk::append, py::arg("new_line"))
        .def("get", &gpiod::line_bulk::get, py::arg("offset"))
        .def("size", &gpiod::line_bulk::size)
        .def("empty", &gpiod::line_bulk::empty)
        .def("clear", &gpiod::line_bulk::clear)
        .def("request",
             &gpiod::line_bulk::request,
             py::arg("config"),
             py::arg("default_vals") = std::vector<int>())
        .def("release", &gpiod::line_bulk::release)
        .def("get_values", &gpiod::line_bulk::get_values)
        .def("set_values", &gpiod::line_bulk::set_values, py::arg("values"))
        .def("event_wait", &gpiod::line_bulk::event_wait, py::arg("timeout"))
        .def(! py::self);

    line_bulk.def_property_readonly_static(
        "MAX_LINES", [](py::object) { return gpiod::line_bulk::MAX_LINES; });

    py::class_<gpiod::line_bulk::iterator> iterator(line_bulk, "iterator");

    iterator.def(py::init<>())
        .def(py::self == py::self)
        .def(py::self != py::self);

    line_bulk.def("begin", &gpiod::line_bulk::begin)
        .def("end", &gpiod::line_bulk::end);
}