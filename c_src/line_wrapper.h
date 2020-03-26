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

void set_line_class(py::module &m) {
    py::class_<gpiod::line> line(m, "line");

    line.doc()
        = "/**\n"
          " * @brief Represents a single GPIO line.\n"
          " *\n"
          " * Internally this class holds a raw pointer to a GPIO line "
          "descriptor and a\n"
          " * reference to the parent chip. All line resources are freed when "
          "the last\n"
          " * reference to the parent chip is dropped.\n"
          " */";

    line.def(py::init<>(),
             "/**\n"
             " * @brief Default constructor. Creates an empty line object.\n"
             " */")
        .def("offset",
             &gpiod::line::offset,
             "/**\n"
             " * @brief Get the offset of this line.\n"
             " * @return Offet of this line.\n"
             " */")
        .def("name",
             &gpiod::line::name,
             "/**\n"
             " * @brief Get the name of this line (if any).\n"
             " * @return Name of this line or an empty string if it is "
             "unnamed.\n"
             " */")
        .def("consumer",
             &gpiod::line::consumer,
             "/**\n"
             " * @brief Get the consumer of this line (if any).\n"
             " * @return Name of the consumer of this line or an empty string "
             "if it\n"
             " *         is unused.\n"
             " */")
        .def("direction",
             &gpiod::line::direction,
             "/**\n"
             " * @brief Get current direction of this line.\n"
             " * @return Current direction setting.\n"
             " */")
        .def("active_state",
             &gpiod::line::active_state,
             "/**\n"
             " * @brief Get current active state of this line.\n"
             " * @return Current active state setting.\n"
             " */")
#if LIBGPIODCXX_VERSION_CODE >= LIBGPIODCXX_VERSION(1, 5)
        .def("bias", &gpiod::line::bias)
#endif
        .def("is_used", &gpiod::line::is_used)
        .def("is_open_drain", &gpiod::line::is_open_drain)
        .def("is_open_source", &gpiod::line::is_open_source)
        .def("request",
             &gpiod::line::request,
             py::arg("config"),
             py::arg("default_val") = 0,
             "/**\n"
             " * @brief Request this line.\n"
             " * @param config Request config (see gpiod::line_request).\n"
             " * @param default_val Default value - only matters for OUTPUT "
             "direction.\n"
             " */")
        .def("release",
             &gpiod::line::release,
             "/**\n"
             " * @brief Release the line if it was previously requested.\n"
             " */")
        .def("is_requested", &gpiod::line::is_requested)
        .def("get_value",
             &gpiod::line::get_value,
             "/**\n"
             " * @brief Read the line value.\n"
             " * @return Current value (0 or 1).\n"
             " */")
        .def("set_value",
             &gpiod::line::set_value,
             py::arg("value"),
             "/**\n"
             " * @brief Set the value of this line.\n"
             " * @param val New value (0 or 1).\n"
             " */")
#if LIBGPIODCXX_VERSION_CODE >= LIBGPIODCXX_VERSION(1, 5)
        .def("set_config",
             &gpiod::line::set_config,
             py::arg("direction"),
             py::arg("flags"),
             py::arg("value") = 0)
        .def("set_flags", &gpiod::line::set_flags, py::arg("flags"))
        .def("set_direction_input", &gpiod::line::set_direction_input)
        .def("set_direction_output",
             &gpiod::line::set_direction_output,
             py::arg("value") = 0)
#endif
        .def("event_wait",
             &gpiod::line::event_wait,
             py::arg("timeout"),
             "/**\n"
             " * @brief Wait for an event on this line.\n"
             " * @param timeout Time to wait before returning if no event "
             "occurred.\n"
             " * @return True if an event occurred and can be read, false if "
             "the wait\n"
             " *         timed out.\n"
             " */")
        .def("event_read",
             &gpiod::line::event_read,
             "/**\n"
             " * @brief Read a line event.\n"
             " * @return Line event object.\n"
             " */")
#if LIBGPIODCXX_VERSION_CODE >= LIBGPIODCXX_VERSION(1, 5)
        .def("event_read_multiple", &gpiod::line::event_read_multiple)
#endif
        .def("event_get_fd", &gpiod::line::event_get_fd)
        .def("get_chip", &gpiod::line::get_chip)
#if LIBGPIODCXX_VERSION_CODE >= LIBGPIODCXX_VERSION(1, 5)
        .def("update", &gpiod::line::update)
#endif
        .def("reset", &gpiod::line::reset)
        .def(py::self == py::self)
        .def(py::self != py::self)
        .def(! py::self);

    line.def_property_readonly_static(
            "DIRECTION_INPUT",
            [](py::object) { return int(gpiod::line::DIRECTION_INPUT); })
        .def_property_readonly_static(
            "DIRECTION_OUTPUT",
            [](py::object) { return int(gpiod::line::DIRECTION_OUTPUT); })
        .def_property_readonly_static(
            "ACTIVE_LOW",
            [](py::object) { return int(gpiod::line::ACTIVE_LOW); })
        .def_property_readonly_static("ACTIVE_HIGH", [](py::object) {
            return int(gpiod::line::ACTIVE_HIGH);
        });

#if LIBGPIODCXX_VERSION_CODE >= LIBGPIODCXX_VERSION(1, 5)
    line.def_property_readonly_static(
            "BIAS_AS_IS",
            [](py::object) { return int(gpiod::line::BIAS_AS_IS); })
        .def_property_readonly_static(
            "BIAS_DISABLE",
            [](py::object) { return int(gpiod::line::BIAS_DISABLE); })
        .def_property_readonly_static(
            "BIAS_PULL_UP",
            [](py::object) { return int(gpiod::line::BIAS_PULL_UP); })
        .def_property_readonly_static("BIAS_PULL_DOWN", [](py::object) {
            return int(gpiod::line::BIAS_PULL_DOWN);
        });
#endif
}