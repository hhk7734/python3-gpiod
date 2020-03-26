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

void set_chip_class(py::module &m) {
    py::class_<gpiod::chip> chip(m, "chip");

    chip.doc()
        = "/**\n"
          " * @brief Represents a GPIO chip.\n"
          " *\n"
          " * Internally this class holds a smart pointer to an open GPIO "
          "chip descriptor.\n"
          " * Multiple objects of this class can reference the same chip. "
          "The chip is\n"
          " * closed and all resources freed when the last reference is "
          "dropped.\n"
          " */";

    chip.def(py::init<>(),
             "/**\n"
             " * @brief Default constructor. Creates an empty GPIO chip "
             "object.\n"
             " */")
        .def(py::init<const std::string &, int>(),
             py::arg("device"),
             py::arg("how") = int(gpiod::chip::OPEN_LOOKUP),
             "/**\n"
             " * @brief Constructor. Opens the chip using chip::open.\n"
             " * @param device String describing the GPIO chip.\n"
             " * @param how Indicates how the chip should be opened.\n"
             " */")
        .def("open",
             &gpiod::chip::open,
             py::arg("device"),
             py::arg("how") = int(gpiod::chip::OPEN_LOOKUP),
             "/**\n"
             " * @brief Open a GPIO chip.\n"
             " * @param device String describing the GPIO chip.\n"
             " * @param how Indicates how the chip should be opened.\n"
             " *\n"
             " * If the object already holds a reference to an open chip, it "
             "will be\n"
             " * closed and the reference reset.\n"
             " */")
        .def(
            "reset",
            &gpiod::chip::reset,
            "/**\n"
            " * @brief Reset the internal smart pointer owned by this object.\n"
            " */")
        .def("name",
             &gpiod::chip::name,
             "/**\n"
             " * @brief Return the name of the chip held by this object.\n"
             " * @return Name of the GPIO chip.\n"
             " */")
        .def("label",
             &gpiod::chip::label,
             "/**\n"
             " * @brief Return the label of the chip held by this object.\n"
             " * @return Label of the GPIO chip.\n"
             " */")
        .def("num_lines",
             &gpiod::chip::num_lines,
             "/**\n"
             " * @brief Return the number of lines exposed by this chip.\n"
             " * @return Number of lines.\n"
             " */")
        .def("get_line",
             &gpiod::chip::get_line,
             py::arg("offset"),
             "/**\n"
             " * @brief Get the line exposed by this chip at given offset.\n"
             " * @param offset Offset of the line.\n"
             " * @return Line object.\n"
             " */")
        .def("find_line",
             &gpiod::chip::find_line,
             py::arg("name"),
             "/**\n"
             " * @brief Get the line exposed by this chip by name.\n"
             " * @param name Line name.\n"
             " * @return Line object.\n"
             " */")
        .def("get_lines",
             &gpiod::chip::get_lines,
             py::arg("offsets"),
             "/**\n"
             " * @brief Get a set of lines exposed by this chip at given "
             "offsets.\n"
             " * @param offsets Vector of line offsets.\n"
             " * @return Set of lines held by a line_bulk object.\n"
             " */")
        .def("get_all_lines", &gpiod::chip::get_all_lines)
        .def("find_lines", &gpiod::chip::find_lines, py::arg("names"))
        .def(py::self == py::self)
        .def(py::self != py::self)
        .def(! py::self);

    chip.def_property_readonly_static(
            "OPEN_LOOKUP",
            [](py::object) { return int(gpiod::chip::OPEN_LOOKUP); })
        .def_property_readonly_static(
            "OPEN_BY_PATH",
            [](py::object) { return int(gpiod::chip::OPEN_BY_PATH); })
        .def_property_readonly_static(
            "OPEN_BY_NAME",
            [](py::object) { return int(gpiod::chip::OPEN_BY_NAME); })
        .def_property_readonly_static(
            "OPEN_BY_LABEL",
            [](py::object) { return int(gpiod::chip::OPEN_BY_LABEL); })
        .def_property_readonly_static("OPEN_BY_NUMBER", [](py::object) {
            return int(gpiod::chip::OPEN_BY_NUMBER);
        });
}