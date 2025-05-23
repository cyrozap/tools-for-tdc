# SPDX-License-Identifier: GPL-3.0-or-later

# tdc_data.py - A library for parsing decompressed TPDC capture data
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


import struct
from datetime import datetime, timezone
from typing import NamedTuple


class ParserError(Exception):
    pass

class Data:
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
            raise ParserError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), 1, self.get_remaining()))

        value: int = self._data[self.get_index()]
        self.inc_index()
        return value

    def take_two_le(self) -> int:
        if self.get_remaining() < 2:
            raise ParserError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), 2, self.get_remaining()))

        value: int = self.take_one()
        value += self.take_one() << 8
        return value

    def take_three_le(self) -> int:
        if self.get_remaining() < 3:
            raise ParserError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), 3, self.get_remaining()))

        value: int = self.take_one()
        value += self.take_one() << 8
        value += self.take_one() << 16
        return value

    def take_four_le(self) -> int:
        if self.get_remaining() < 4:
            raise ParserError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), 4, self.get_remaining()))

        value: int = self.take_two_le()
        value += self.take_two_le() << 16
        return value

    def take_eight_le(self) -> int:
        if self.get_remaining() < 8:
            raise ParserError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), 8, self.get_remaining()))

        value: int = self.take_four_le()
        value += self.take_four_le() << 32
        return value

    def take_n_bytes(self, count: int) -> bytes:
        if count < 0:
            raise ParserError("Cannot request {} bytes--length must be positive".format(count))

        if self.get_remaining() < count:
            raise ParserError("Compressed data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), count, self.get_remaining()))

        value: bytes = self._data[self.get_index():self.get_index()+count]
        self.inc_index(count)
        return value

    def take_remaining_bytes(self) -> bytes:
        count: int = self.get_remaining()
        value: bytes = self._data[self.get_index():self.get_index()+count]
        self.inc_index(count)
        return value

class TVRecord(NamedTuple):
    tag: int
    value: bytes


def format_timestamp(nanoseconds: int) -> str:
    # Convert nanoseconds to total seconds
    total_seconds: int = nanoseconds // 1_000_000_000

    # Calculate hours, minutes, and seconds
    hours: int = total_seconds // 3600
    minutes: int = (total_seconds % 3600) // 60
    seconds: int = total_seconds % 60

    # Calculate remaining nanoseconds after extracting seconds
    remaining_ns: int = nanoseconds % 1_000_000_000

    # Extract milliseconds, microseconds, and remaining nanoseconds
    milliseconds: int = remaining_ns // 1_000_000
    microseconds: int = (remaining_ns % 1_000_000) // 1_000
    nanos: int = remaining_ns % 1_000

    # Format the time string
    formatted_time: str = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}.{microseconds:03}.{nanos:03}"

    return formatted_time

def handle_block_0(version: int, sample_rate_sps: int | None, data_bytes: bytes) -> None:
    data = Data(data_bytes)

    index: int = data.take_four_le()
    unk2: int = data.take_two_le()

    records: list[TVRecord] = []
    while data.get_remaining():
        tag: int = data.take_two_le()
        size: int = data.take_four_le() - 6
        value: bytes = data.take_n_bytes(size)
        records.append(TVRecord(tag, value))

    remaining: bytes = data.take_remaining_bytes()
    assert len(remaining) == 0

    info: str = "Block 0"
    info += f": Index: {index}"
    info += f", Unk2: {unk2:#06x}"
    info += ", Records: ["
    for i, record in enumerate(records):
        info += f"(Tag: {record.tag:#06x}"
        if record.value:
            info += ", Value: "
            if record.tag == 0x0000:
                assert len(record.value) == 14
                unk5, timestamp_samples, length_samples = struct.unpack("<HQI", record.value)
                info += f"(Unk5: {unk5:#06x}"
                if sample_rate_sps is not None:
                    timestamp_ns: int = (timestamp_samples * 1_000_000_000) // sample_rate_sps
                    length_ns: int = (length_samples * 1_000_000_000) // sample_rate_sps
                    info += f", Timestamp: {format_timestamp(timestamp_ns)}"
                    info += f", Length: {format_timestamp(length_ns)}"
                else:
                    info += ", Timestamp: Unknown"
                    info += ", Length: Unknown"
                info += ")"
            else:
                info += record.value.hex()
        info += ")"
        if i < len(records) - 1:
            info += ", "
    info += "]"

    print(info)

def handle_block_5(version: int, data_bytes: bytes) -> int:
    data = Data(data_bytes)

    unk1: int = data.take_four_le()
    unk2: int = data.take_four_le()
    capture_start_time: int = data.take_four_le()
    capture_end_time: int = data.take_four_le()
    capture_samples: int = data.take_eight_le()
    sample_rate_sps: int = data.take_four_le()
    unk7: int = data.take_one()
    unk8: int = data.take_four_le()
    unk9: int = data.take_four_le()

    info: str = "Block 5"
    info += f": Unk1: {unk1:#010x}"
    info += f", Unk2: {unk2:#010x}"
    info += f", CaptureStartTime: {datetime.fromtimestamp(capture_start_time, timezone.utc).astimezone().isoformat()}"
    info += f", CaptureEndTime: {datetime.fromtimestamp(capture_end_time, timezone.utc).astimezone().isoformat()}"
    info += f", CaptureSamples: {capture_samples}"
    info += f", SampleRateSps: {sample_rate_sps}"
    info += f", Unk7: {unk7:#04x}"
    info += f", Unk8: {unk8:#010x}"
    info += f", Unk9: {unk9:#010x}"

    if version >= 0x0103:
        unk10 = data.take_four_le()
        info += f", Unk10: {unk10:#010x}"
    if version >= 0x0104:
        unk11 = data.take_one()
        info += f", Unk11: {unk11:#04x}"
    if version >= 0x0108:
        unk12 = data.take_one()
        info += f", Unk12: {unk12:#04x}"
    if version >= 0x010A:
        unk13 = data.take_one()
        info += f", Unk13: {unk13:#04x}"

    remaining_bytes = data.take_remaining_bytes()
    assert len(remaining_bytes) == 0

    print(info)

    return sample_rate_sps

def handle_block_6(protocol: int, data_bytes: bytes) -> None:
    protocol_enum = {
        1: "I2C",
        2: "SPI",
        3: "USB",
        4: "CAN",
        5: "eSPI",
        6: "USB-PD"
    }

    info: str = "Block 6"
    info += f": Protocol: {protocol_enum.get(protocol, "unknown")} ({protocol})"

    # TODO: Process the rest of the data in this block.

    print(info)

def parse(version: int, data_bytes: bytes) -> None:
    sample_rate_sps: int | None = None
    data = Data(data_bytes)
    while data.get_remaining() > 0:
        header: int = data.take_one()
        # unk: int = header >> 4
        block_type: int = header & 0x0F

        if block_type == 0:
            b0_size: int = data.take_three_le()
            b0_block_data: bytes = data.take_n_bytes(b0_size - 4)
            handle_block_0(version, sample_rate_sps, b0_block_data)
        elif block_type == 5:
            b5_block_data: bytes = data.take_n_bytes(37)
            if version >= 0x0103:
                b5_block_data += data.take_n_bytes(4)
            if version >= 0x0104:
                b5_block_data += data.take_n_bytes(1)
            if version >= 0x0108:
                b5_block_data += data.take_n_bytes(1)
            if version >= 0x010A:
                b5_block_data += data.take_n_bytes(1)
            sample_rate_sps = handle_block_5(version, b5_block_data)
        elif block_type == 6:
            protocol: int = data.take_four_le()
            b6_size: int = data.take_four_le()
            b6_block_data: bytes = data.take_n_bytes(b6_size)
            handle_block_6(protocol, b6_block_data)
        else:
            raise ParserError("Unsupported block type: {:#03x} at index {}".format(block_type, data.get_index()))
