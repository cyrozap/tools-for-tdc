# SPDX-License-Identifier: 0BSD

# Copyright (C) 2024 by Forest Crossman <cyrozap@gmail.com>
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


from crc32_bzip2 import crc32


def test_crc32_a():
    assert crc32(bytes([i for i in range(256)])) == 0xb6b5ee95

def test_crc32_b():
    assert crc32(bytes.fromhex("c57198c7add891b93d3948dbf3d659b3")) == 0x67f0fed5

def test_crc32_c():
    assert crc32(bytes.fromhex("ec275b295d53743d43638984fb4b6772")) == 0x98b50d4c

def test_crc32_d():
    assert crc32(bytes.fromhex("40a97ee33dc971be93d50169b2d2635121e32d2f0553b2c5b4b2eb59ddacdb0b")) == 0x4b0a823e

def test_crc32_e():
    assert crc32(bytes([i for i in range(256)]) * 1023) == 0x00b06b15

def test_crc32_f():
    assert crc32(bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")) == 0x707e66af
