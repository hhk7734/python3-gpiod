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

#include <bitset>
#include <pybind11/pybind11.h>

namespace pybind11 {
namespace detail {
    template<>
    struct type_caster<std::bitset<32>> {
    public:
        /**
         * This macro establishes the name 'std::bitset<32>' in
         * function signatures and declares a local variable
         * 'value' of type std::bitset<32>
         */
        PYBIND11_TYPE_CASTER(std::bitset<32>, _("std::bitset<32>"));

        /**
         * Conversion part 1 (Python->C++): convert a PyObject into
         * a std::bitset<32> instance or return false upon failure.
         * The second argument indicates whether implicit conversions
         * should be applied.
         */
        bool load(handle src, bool) {
            /* Extract PyObject from handle */
            PyObject *source = src.ptr();
            /* Try converting into a Python integer value */
            PyObject *tmp = PyNumber_Long(source);
            if(! tmp) return false;
            /* Now try to convert into a C++ std::bitset<32> */
            value = PyLong_AsUnsignedLong(tmp);
            Py_DECREF(tmp);
            /* Ensure return code was OK (to avoid out-of-range errors etc) */
            return ! (value == -1 && ! PyErr_Occurred());
        }

        /**
         * Conversion part 2 (C++ -> Python): convert an std::bitset<32>
         * instance into a Python object. The second and third arguments
         * are used to indicate the return value policy and parent object
         * (for ``return_value_policy::reference_internal``) and are
         * generally ignored by implicit casters.
         */
        static handle cast(std::bitset<32> src,
                           return_value_policy /* policy */,
                           handle /* parent */) {
            return PyLong_FromUnsignedLong(src.to_ulong());
        }
    };
}    // namespace detail
}    // namespace pybind11