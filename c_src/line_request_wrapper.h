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

void set_line_request_class(py::module &m) {
    py::class_<gpiod::line_request> line_request(m, "line_request");

    line_request.doc()
        = "/**\n"
          " * @brief Stores the configuration for line requests.\n"
          " */";

    line_request
        .def_property_readonly_static(
            "DIRECTION_AS_IS",
            [](py::object) {
                return int(gpiod::line_request::DIRECTION_AS_IS);
            })
        .def_property_readonly_static(
            "DIRECTION_INPUT",
            [](py::object) {
                return int(gpiod::line_request::DIRECTION_INPUT);
            })
        .def_property_readonly_static(
            "DIRECTION_OUTPUT",
            [](py::object) {
                return int(gpiod::line_request::DIRECTION_OUTPUT);
            })
        .def_property_readonly_static(
            "EVENT_FALLING_EDGE",
            [](py::object) {
                return int(gpiod::line_request::EVENT_FALLING_EDGE);
            })
        .def_property_readonly_static(
            "EVENT_RISING_EDGE",
            [](py::object) {
                return int(gpiod::line_request::EVENT_RISING_EDGE);
            })
        .def_property_readonly_static("EVENT_BOTH_EDGES", [](py::object) {
            return int(gpiod::line_request::EVENT_BOTH_EDGES);
        });

    line_request.def(py::init<>())
        .def_readwrite("consumer", &gpiod::line_request::consumer)
        .def_readwrite("request_type", &gpiod::line_request::request_type)
        .def_readwrite("flags", &gpiod::line_request::flags);
}