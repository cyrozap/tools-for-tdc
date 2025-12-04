#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

# unpack.py - A tool for unpacking TPDC capture files into a directory
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

from crc32_bzip2 import crc32
from fastlz import decompress
from tdc import Tdc


def main() -> None:
    parser = argparse.ArgumentParser(description="Unpack a .tdc file into a directory.")
    parser.add_argument("file", type=str, help="The .tdc file to unpack")
    parser.add_argument("-o", "--output", type=str, help="Output directory name")
    args = parser.parse_args()

    input_path: Path = Path(args.file)
    if not input_path.exists():
        print(f"Error: File '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    output_dir: Path = Path(args.output) if args.output else input_path.with_name(f"{input_path.name}.unpacked")
    output_dir.mkdir(parents=True, exist_ok=False)

    try:
        tdc_file = Tdc.from_file(args.file)
    except Exception as e:
        print(f"Error parsing .tdc file: {e}", file=sys.stderr)
        sys.exit(1)

    # Write metadata.json
    metadata_path: Path = output_dir / "metadata.json"
    metadata = {
        "header_version": tdc_file.header_version,
        "data_offset": tdc_file.data_offset,
        "header": {},
    }
    if hasattr(tdc_file, "header"):
        header = tdc_file.header
        metadata["header"].update({
            "unk0": header.unk0,
            "unk1": header.unk1,
            "capture_save_time": header.capture_save_time,
            "data_version": header.data_version,
            "unk3": header.unk3,
            "unk4": header.unk4,
            "unk5": header.unk5,
            "num_thing": header.num_thing,
            "thing": [
                {
                    "lower": item.lower,
                    "upper": item.upper,
                }
                for item in header.thing
            ],
        })
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Write each decompressed block
    for i, block in enumerate(tdc_file.blocks):
        compressed: bytes = block.data
        decompressed: bytes = decompress(compressed)
        expected_crc: int = block.crc32
        actual_crc: int = crc32(decompressed)
        if expected_crc != actual_crc:
            raise ValueError(f"CRC mismatch for block {i}: expected 0x{expected_crc:08X}, got 0x{actual_crc:08X}")

        block_path: Path = output_dir / f"block_{i}.bin"
        with open(block_path, "wb") as f:
            f.write(decompressed)

        print(f"Wrote {len(decompressed)} bytes to {block_path}", file=sys.stderr)

    print(f"Unpacked {len(tdc_file.blocks)} blocks into {output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
