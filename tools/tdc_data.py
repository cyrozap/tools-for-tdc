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

    def take_le(self, count: int) -> int:
        return int.from_bytes(self.take_bytes(count), byteorder="little")

    def take_bytes(self, count: int) -> bytes:
        if count < 0:
            raise ParserError("Cannot request {} bytes--length must be positive".format(count))

        if self.get_remaining() < count:
            raise ParserError("Data incomplete at index {}: Requested {}, but only {} remaining".format(self.get_index(), count, self.get_remaining()))

        value: bytes = self._data[self.get_index():self.get_index()+count]
        self.inc_index(count)
        return value

    def take_remaining_bytes(self) -> bytes:
        count: int = self.get_remaining()
        return self.take_bytes(count)

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

def format_time_samples(samples: int, sample_rate_sps: int | None) -> str:
    """
    Convert samples and sample rate to a timestamp/duration string.

    :param samples: The sample count you want to convert to a timestamp/duration.
    :param sample_rate_sps: The sample rate, in samples per second, or None.
    :return: The formatted timestamp/duration string, or "Unknown" if no sample rate was provided.
    """

    if sample_rate_sps is None:
        return "Unknown"

    ns = (samples * 1_000_000_000) // sample_rate_sps
    return format_timestamp(ns)

def handle_block_0(version: int, sample_rate_sps: int | None, data_bytes: bytes) -> None:
    data = Data(data_bytes)

    index: int = data.take_le(4)
    unk2: int = data.take_le(2)

    records: list[TVRecord] = []
    while data.get_remaining():
        tag: int = data.take_le(2)
        size: int = data.take_le(4) - 6
        value: bytes = data.take_bytes(size)
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
            match record.tag:
                case 0x0000:
                    assert len(record.value) == 14
                    unk5, timestamp_samples, length_samples = struct.unpack("<HQI", record.value)
                    info += f"(Unk5: {unk5:#06x}"
                    info += f", Timestamp: {format_time_samples(timestamp_samples, sample_rate_sps)}"
                    info += f", Length: {format_time_samples(length_samples, sample_rate_sps)}"
                    info += ")"
                case 0x0300:
                    unk_0300: int = struct.unpack("<I", record.value)[0]
                    info += f"{unk_0300:#010x}"
                    dir_down: bool = unk_0300 & 0x01 != 0
                    dir_up: bool = unk_0300 & 0x02 != 0
                    is_ss: bool = unk_0300 & 0x04 != 0
                    dir_str: str = ""
                    match (dir_up, dir_down):
                        case (False, True):
                            dir_str = "↓"
                        case (True, False):
                            dir_str = "↑"
                        case (True, True):
                            dir_str = "↕"
                        case _:
                            dir_str = ""
                    sp_str: str = "FS"
                    if is_ss:
                        sp_str = "SS"
                    if unk_0300 & 0b111:
                        info += f" ({sp_str + dir_str})"
                case _:
                    info += record.value.hex()
        info += ")"
        if i < len(records) - 1:
            info += ", "
    info += "]"

    print(info)

def handle_block_5(version: int, data_bytes: bytes) -> int:
    data = Data(data_bytes)

    unk1: int = data.take_le(4)
    unk2: int = data.take_le(4)
    capture_start_time: int = data.take_le(4)
    capture_end_time: int = data.take_le(4)
    capture_samples: int = data.take_le(8)
    sample_rate_sps: int = data.take_le(4)
    unk7: int = data.take_le(1)
    unk8: int = data.take_le(4)
    unk9: int = data.take_le(4)

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
        unk10 = data.take_le(4)
        info += f", Unk10: {unk10:#010x}"
    if version >= 0x0104:
        unk11 = data.take_le(1)
        info += f", Unk11: {unk11:#04x}"
    if version >= 0x0108:
        unk12 = data.take_le(1)
        info += f", Unk12: {unk12:#04x}"
    if version >= 0x010A:
        unk13 = data.take_le(1)
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
        header: int = data.take_le(1)
        # unk: int = header >> 4
        block_type: int = header & 0x0F

        match block_type:
            case 0:
                b0_size: int = data.take_le(3)
                b0_block_data: bytes = data.take_bytes(b0_size - 4)
                handle_block_0(version, sample_rate_sps, b0_block_data)
            case 5:
                b5_block_data: bytes = data.take_bytes(37)
                if version >= 0x0103:
                    b5_block_data += data.take_bytes(4)
                if version >= 0x0104:
                    b5_block_data += data.take_bytes(1)
                if version >= 0x0108:
                    b5_block_data += data.take_bytes(1)
                if version >= 0x010A:
                    b5_block_data += data.take_bytes(1)
                sample_rate_sps = handle_block_5(version, b5_block_data)
            case 6:
                protocol: int = data.take_le(4)
                b6_size: int = data.take_le(4)
                b6_block_data: bytes = data.take_bytes(b6_size)
                handle_block_6(protocol, b6_block_data)
            case _:
                raise ParserError("Unsupported block type: {:#03x} at index {}".format(block_type, data.get_index()))
