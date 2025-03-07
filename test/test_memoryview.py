#!/usr/bin/env python
# coding: utf-8

import pytest
from array import array
from msgpack import packb, unpackb
import sys


pytestmark = pytest.mark.skipif(
    sys.version_info[0] < 3, reason="Only Python 3 supports buffer protocol"
)


def make_array(f, data):
    a = array(f)
    a.frombytes(data)
    return a


def _runtest(format, nbytes, expected_header, expected_prefix, use_bin_type):
    # create a new array
    original_array = array(format)
    original_array.fromlist([255] * (nbytes // original_array.itemsize))
    original_data = original_array.tobytes()
    view = memoryview(original_array)

    # pack, unpack, and reconstruct array
    packed = packb(view, use_bin_type=use_bin_type)
    unpacked = unpackb(packed, raw=(not use_bin_type))
    reconstructed_array = make_array(format, unpacked)

    # check that we got the right amount of data
    assert len(original_data) == nbytes
    # check packed header
    assert packed[:1] == expected_header
    # check packed length prefix, if any
    assert packed[1 : 1 + len(expected_prefix)] == expected_prefix
    # check packed data
    assert packed[1 + len(expected_prefix) :] == original_data
    # check array unpacked correctly
    assert original_array == reconstructed_array


def test_fixstr_from_byte():
    _runtest("B", 1, b"\xa1", b"", False)
    _runtest("B", 31, b"\xbf", b"", False)


def test_fixstr_from_float():
    _runtest("f", 4, b"\xa4", b"", False)
    _runtest("f", 28, b"\xbc", b"", False)


def test_str16_from_byte():
    _runtest("B", 2**8, b"\xda", b"\x01\x00", False)
    _runtest("B", 2**16 - 1, b"\xda", b"\xff\xff", False)


def test_str16_from_float():
    _runtest("f", 2**8, b"\xda", b"\x01\x00", False)
    _runtest("f", 2**16 - 4, b"\xda", b"\xff\xfc", False)


def test_str32_from_byte():
    _runtest("B", 2**16, b"\xdb", b"\x00\x01\x00\x00", False)


def test_str32_from_float():
    _runtest("f", 2**16, b"\xdb", b"\x00\x01\x00\x00", False)


def test_bin8_from_byte():
    _runtest("B", 1, b"\xc4", b"\x01", True)
    _runtest("B", 2**8 - 1, b"\xc4", b"\xff", True)


def test_bin8_from_float():
    _runtest("f", 4, b"\xc4", b"\x04", True)
    _runtest("f", 2**8 - 4, b"\xc4", b"\xfc", True)


def test_bin16_from_byte():
    _runtest("B", 2**8, b"\xc5", b"\x01\x00", True)
    _runtest("B", 2**16 - 1, b"\xc5", b"\xff\xff", True)


def test_bin16_from_float():
    _runtest("f", 2**8, b"\xc5", b"\x01\x00", True)
    _runtest("f", 2**16 - 4, b"\xc5", b"\xff\xfc", True)


def test_bin32_from_byte():
    _runtest("B", 2**16, b"\xc6", b"\x00\x01\x00\x00", True)


def test_bin32_from_float():
    _runtest("f", 2**16, b"\xc6", b"\x00\x01\x00\x00", True)


def test_multidim_memoryview():
    # See https://github.com/msgpack/msgpack-python/issues/526
    view = memoryview(b"\00" * 6)
    data = view.cast(view.format, (3, 2))
    packed = packb(data)
    assert packed == b'\xc4\x06\x00\x00\x00\x00\x00\x00'
