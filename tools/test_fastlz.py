# SPDX-License-Identifier: 0BSD

# Copyright (C) 2024-2025 by Forest Crossman <cyrozap@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.


import pytest

from fastlz import DecompressionError, compress, decompress


def test_decompress_0_a() -> None:
    assert decompress(bytes.fromhex("1f000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")) == bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")

def test_decompress_0_b() -> None:
    assert decompress(bytes.fromhex("000102030405060708090a0b0c0d")) == bytes.fromhex("010304050708090a0b0c0d")

def test_decompress_0_c() -> None:
    assert decompress(bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d")) == bytes.fromhex("010304050708090a0b0c0d0f101112131415161718191a1b1c1d1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d")

def test_decompress_0_d() -> None:
    assert decompress(bytes.fromhex("0000e0ff00")) == bytes([0] * 265)

def test_decompress_0_e() -> None:
    import os
    random_data: bytes = os.urandom(16384)
    random_data_copy: bytes = random_data
    compressed_data: bytes = bytes.fromhex("1f")
    compressed_data += random_data[:32]
    random_data = random_data[32:]
    while len(random_data) > 0:
        compressed_data += bytes.fromhex("1f") + random_data[:32]
        random_data = random_data[32:]
    compressed_data += bytes.fromhex("ffffff")
    expected_data = random_data_copy + random_data_copy[-8192:-8192+264]
    assert decompress(compressed_data) == expected_data

def test_decompress_1_a() -> None:
    assert decompress(bytes.fromhex("3f000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")) == bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")

def test_decompress_1_b() -> None:
    assert decompress(bytes.fromhex("2000000000000000")) == bytes.fromhex("00000000")

def test_decompress_1_c() -> None:
    assert decompress(bytes.fromhex("2000200020002000")) == bytes.fromhex("00000000000000000000")

def test_decompress_1_d() -> None:
    assert decompress(bytes.fromhex("2000e0ffffffff0000")) == bytes([0] * 1030)

def test_decompress_1_e() -> None:
    assert decompress(b"\x24abcde\xe0\x01\x04") == b"abcdeabcdeabcde"

def test_decompress_1_f() -> None:
    assert decompress(bytes.fromhex("20aae0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe003fff0102")) == bytes([0xaa] * 8682)
    assert decompress(bytes.fromhex("20aae0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe00fffeff0102")) == bytes([0xaa] * 8942)

def test_decompress_1_g() -> None:
    import os
    random_data: bytes = os.urandom(16384)
    random_data_copy: bytes = random_data
    compressed_data: bytes = bytes.fromhex("3f")
    compressed_data += random_data[:32]
    random_data = random_data[32:]
    while len(random_data) > 0:
        compressed_data += bytes.fromhex("1f") + random_data[:32]
        random_data = random_data[32:]
    compressed_data += bytes.fromhex("fffffeff0102")
    expected_data = random_data_copy + random_data_copy[-8450:-8450+518]
    assert decompress(compressed_data) == expected_data

def test_decompress_error_a() -> None:
    """Unsupported header byte"""
    with pytest.raises(DecompressionError):
        decompress(bytes.fromhex("e000"))

def test_decompress_error_b() -> None:
    """take_n_bytes"""
    with pytest.raises(DecompressionError):
        decompress(bytes.fromhex("00"))

def test_decompress_error_c() -> None:
    """take_one"""
    with pytest.raises(DecompressionError):
        decompress(bytes.fromhex("000020"))

def test_decompress_error_d() -> None:
    """take_two_be"""
    with pytest.raises(DecompressionError):
        decompress(bytes.fromhex("20003fff"))

def test_decompress_error_e() -> None:
    """lookback_n_take_m_bytes"""
    with pytest.raises(DecompressionError):
        decompress(bytes.fromhex("00002001"))

def test_compress() -> None:
    import os
    random_data: bytes = os.urandom(16384)
    compressed_data: bytes = compress(random_data)
    decompressed_data: bytes = decompress(compressed_data)
    assert random_data == decompressed_data
