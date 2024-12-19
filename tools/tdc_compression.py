# SPDX-License-Identifier: GPL-3.0-or-later

# tdc_compression.py - A library for decompressing TPDC capture data
# Copyright (C) 2024  Forest Crossman <cyrozap@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import logging
import tempfile
from math import ceil
from pathlib import Path


LOG = logging.getLogger(__name__)


class CompressedStream:
    def __init__(self, data: bytes) -> None:
        self._data: bytes = data
        self._index: int = 0

    def __bytes__(self) -> bytes:
        return self._data

    def get_index(self) -> int:
        return self._index

    def inc_index(self, count: int = 1) -> None:
        self._index += count

    def get_remaining(self) -> int:
        return len(self._data) - self.get_index()

    def take_one(self) -> int:
        if self.get_remaining() < 1:
            raise DecompressionError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), 1, self.get_remaining()))

        value: int = self._data[self.get_index()]
        self.inc_index()
        return value

    def take_two_be(self) -> int:
        if self.get_remaining() < 2:
            raise DecompressionError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), 2, self.get_remaining()))

        value: int = self.take_one() << 8
        value += self.take_one()
        return value

    def take_n_bytes(self, count: int) -> bytes:
        if self.get_remaining() < count:
            raise DecompressionError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), count, self.get_remaining()))

        value: bytes = self._data[self.get_index():self.get_index()+count]
        self.inc_index(count)
        return value

class DecompressedStream:
    def __init__(self) -> None:
        self._data: bytearray = bytearray()

    def __len__(self) -> int:
        return len(self._data)

    def __bytes__(self) -> bytes:
        return bytes(self._data)

    def extend(self, data: bytes) -> None:
        self._data.extend(data)

    def lookback_n_take_m_bytes(self, lookback: int, count: int) -> None:
        if lookback > len(self):
            raise DecompressionError("Decompressed data of length {} is not long enough to look back {} bytes".format(len(self), lookback))

        lookback_data: bytes = self._data[-lookback:]

        if lookback < count:
            extra: int = count - lookback
            repeats: int = ceil(extra / lookback)
            lookback_data = lookback_data * (1 + repeats)

        lookback_data = lookback_data[:count]
        self.extend(lookback_data)

class DecompressionError(Exception):
    pass


def dump(compressed: CompressedStream, decompressed: DecompressedStream) -> None:
    """Dump the current state of the compressed and decompressed data to temporary files."""
    with tempfile.TemporaryDirectory(prefix="tdc-decompression-error-", delete=False) as temp_dir:
        temp_path: Path = Path(temp_dir)

        compressed_filename: Path = temp_path.joinpath("compressed.bad_decompress.bin")
        with open(compressed_filename, "wb") as f:
            f.write(bytes(compressed))
        LOG.warning("Dumped compressed data to \"{}\"".format(compressed_filename))

        decompressed_filename: Path = temp_path.joinpath("decompressed.bad_decompress.bin")
        with open(decompressed_filename, "wb") as f:
            f.write(bytes(decompressed))
        LOG.warning("Dumped decompressed data to \"{}\"".format(decompressed_filename))

def extract_bits(value: int) -> tuple[int, int]:
    assert value >> 8 == 0

    high_three_bits: int = value >> 5
    low_five_bits: int = value & 0x1F

    return (high_three_bits, low_five_bits)

def decompress(compressed_bytes: bytes) -> bytes:
    compressed: CompressedStream = CompressedStream(compressed_bytes)
    decompressed: DecompressedStream = DecompressedStream()

    try:
        header_type: int | None = None

        while compressed.get_remaining() > 0:
            # Read the next control byte
            control_byte: int = compressed.take_one()

            # Extract parts from the control byte
            copy_length: int
            length_minus_one_or_offset_high: int
            copy_length, length_minus_one_or_offset_high = extract_bits(control_byte)

            if header_type is None:
                # This is the header byte, so get the type from the high three bits
                header_type = copy_length

                if header_type not in (0b000, 0b001):
                    # Raise an error if the header byte is unsupported
                    raise DecompressionError("Unsupported header byte: {:#04x} at index {}".format(control_byte, compressed.get_index()))

                # Header is always a literal, not a backreference
                copy_length = 0

            if copy_length == 0:
                # Get literal length from control byte
                literal_length: int = length_minus_one_or_offset_high + 1

                # Copy literal bytes from the compressed data
                decompressed.extend(compressed.take_n_bytes(literal_length))

                # Go to the next control byte
                continue

            elif copy_length == 7:
                # Handle extended backreference copy length
                if header_type == 0b000:
                    # Add the next byte to the copy length
                    copy_length += compressed.take_one()

                elif header_type == 0b001:
                    # Add subsequent bytes, stopping when the first non-0xFF byte is reached
                    value: int = 0xFF
                    while value == 0xFF:
                        value = compressed.take_one()
                        copy_length += value

            # Calculate the full offset for the backreference
            lookback_offset: int = (length_minus_one_or_offset_high << 8) | compressed.take_one()

            if header_type == 0b001:
                # Handle extended offset for the backreference
                if lookback_offset == 0x1FFF:
                    lookback_offset += compressed.take_two_be()

            # Append bytes from the decompressed data to the end of the decompressed data
            decompressed.lookback_n_take_m_bytes(1 + lookback_offset, 2 + copy_length)

    except Exception as exc:
        dump(compressed, decompressed)
        raise DecompressionError("Encountered error at compressed index {}: {}".format(compressed.get_index(), exc))

    return bytes(decompressed)
