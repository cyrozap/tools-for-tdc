#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

# pack.py - A tool for packing unpacked .tdc data back into a .tdc file
# Copyright (C) 2025  Forest Crossman <cyrozap@gmail.com>
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


import argparse
import json
import sys
from pathlib import Path
from typing import BinaryIO

from crc32_bzip2 import crc32
from fastlz import compress


def write_header(output_file: BinaryIO, header_version: int, data_offset: int, header_data: dict) -> None:
    """
    Write the header to the output file.

    :param output_file: The file object to write the header to.
    :param header_version: The version of the header to write.
    :param data_offset: The offset to the data section.
    :param header_data: A dictionary containing the header data to write.
    :return: None
    """
    output_file.write(b"TPDC")
    output_file.write(header_version.to_bytes(2, byteorder="little"))
    output_file.write(data_offset.to_bytes(4, byteorder="little"))

    unk1_size: int = {
        0x100: 2,
        0x200: 4,
        0x300: 4,
    }[header_version]

    unk5_size: int = {
        0x100: 4,
        0x200: 4,
        0x300: 8,
    }[header_version]

    output_file.write(header_data["unk0"].to_bytes(2, byteorder="little"))
    output_file.write(header_data["unk1"].to_bytes(unk1_size, byteorder="little"))
    output_file.write(header_data["capture_save_time"].to_bytes(4, byteorder="little"))
    output_file.write(header_data["data_version"].to_bytes(2, byteorder="little"))
    output_file.write(header_data["unk3"].to_bytes(4, byteorder="little"))
    output_file.write(header_data["unk4"].to_bytes(4, byteorder="little"))
    output_file.write(header_data["unk5"].to_bytes(unk5_size, byteorder="little"))
    output_file.write(header_data["num_thing"].to_bytes(2, byteorder="little"))

    for item in header_data["thing"]:
        output_file.write(item["lower"].to_bytes(2, byteorder="little"))
        output_file.write(item["upper"].to_bytes(2, byteorder="little"))

    header_len: int = output_file.tell()
    padding_len: int = data_offset - header_len
    assert padding_len >= 0
    output_file.write(bytes([0] * padding_len))

def main() -> None:
    parser = argparse.ArgumentParser(description="Pack unpacked .tdc data back into a .tdc file.")
    parser.add_argument("input_dir", type=str, help="The directory containing unpacked .tdc data.")
    parser.add_argument("-o", "--output", type=str, default="packed.tdc", help="The output .tdc file.")
    args = parser.parse_args()

    input_dir: Path = Path(args.input_dir)
    output_file: Path = Path(args.output)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Directory '{input_dir}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)

    metadata_path: Path = input_dir / "metadata.json"
    if not metadata_path.exists():
        print(f"Error: Missing metadata.json in '{input_dir}'.", file=sys.stderr)
        sys.exit(1)

    with open(metadata_path, "r") as f:
        metadata: dict = json.load(f)

    header_version: int = metadata["header_version"]
    data_offset: int = metadata["data_offset"]
    header_data: dict = metadata["header"]

    with open(output_file, "wb") as f:
        write_header(f, header_version, data_offset, header_data)

        # Write each block
        block_count: int = 0
        while True:
            block_path: Path = input_dir / f"block_{block_count}.bin"
            if not block_path.exists():
                break

            with open(block_path, "rb") as block_f:
                decompressed: bytes = block_f.read()
                compressed: bytes = compress(decompressed)
                f.write((len(compressed) << 8).to_bytes(4, byteorder="little"))
                f.write(crc32(decompressed).to_bytes(4, byteorder="little"))
                f.write(compressed)

            block_count += 1

        print(f"Packed {block_count} blocks into '{output_file}'.", file=sys.stderr)


if __name__ == "__main__":
    main()
