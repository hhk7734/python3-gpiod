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

    line_bulk.doc()
        = "/**\n"
          " * @brief Represents a set of GPIO lines.\n"
          " *\n"
          " * Internally an object of this class stores an array of line "
          "objects\n"
          " * owned by a single chip.\n"
          " */";

    line_bulk
        .def(py::init<>(),
             "/**\n"
             " * @brief Default constructor. Creates an empty line_bulk "
             "object.\n"
             " */")
        .def(py::init<const std::vector<gpiod::line> &>())
        .def("append", &gpiod::line_bulk::append, py::arg("new_line"))
        .def("get", &gpiod::line_bulk::get, py::arg("offset"))
        .def(
            "size",
            &gpiod::line_bulk::size,
            "/**\n"
            " * @brief Get the number of lines currently held by this object.\n"
            " * @return Number of elements in this line_bulk.\n"
            " */")
        .def("empty", &gpiod::line_bulk::empty)
        .def("clear", &gpiod::line_bulk::clear)
        .def("request",
             &gpiod::line_bulk::request,
             py::arg("config"),
             py::arg("default_vals") = std::vector<int>(),
             "/**\n"
             " * @brief Request all lines held by this object.\n"
             " * @param config Request config (see gpiod::line_request).\n"
             " * @param default_vals Vector of default values. Only relevant "
             "for\n"
             " *                     output direction requests.\n"
             " */")
        .def("release",
             &gpiod::line_bulk::release,
             "/**\n"
             " * @brief Release all lines held by this object.\n"
             " */")
        .def("get_values", &gpiod::line_bulk::get_values)
        .def("set_values",
             &gpiod::line_bulk::set_values,
             py::arg("values"),
             "/**\n"
             " * @brief Set values of all lines held by this object.\n"
             " * @param values Vector of values to set. Must be the same size "
             "as the\n"
             " *               number of lines held by this line_bulk.\n"
             " */")
        .def("event_wait", &gpiod::line_bulk::event_wait, py::arg("timeout"))
        .def(! py::self);

    line_bulk.def_property_readonly_static(
        "MAX_LINES", [](py::object) { return gpiod::line_bulk::MAX_LINES; });

    line_bulk.def(
        "__iter__",
        [](gpiod::line_bulk &self) {
            return py::make_iterator(self.begin(), self.end());
        },
        py::keep_alive<0, 1>(), /* Essential: keep object alive while iterator
                                   exists */
        "/**\n"
        " * @brief Iterator for iterating over lines held by line_bulk.\n"
        " */");
}