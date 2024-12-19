#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

# process.py - A tool for parsing TPDC USB capture files
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


import argparse
import sys
import tempfile
from pathlib import Path

from crc32_bzip2 import crc32
from tdc_compression import decompress

try:
    from tdc import Tdc
except ModuleNotFoundError:
    print("Error: Failed to import \"tdc.py\". Please run \"make\" in this directory to generate that file, then try running this script again.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process a file.")
    parser.add_argument("-o", "--output", type=str, default="", help="The output file.")
    parser.add_argument("file", type=str, help="The file to process")
    args = parser.parse_args()

    output_filename: str = args.output
    if not output_filename:
        output_filename = str(Path(tempfile.mkdtemp(prefix="tdc-decompressed-file-")).joinpath(Path(args.file).name + ".decompressed.bin"))

    compressed_len_total: int = 0
    decompressed_len_total: int = 0

    with open(output_filename, "wb") as output:
        tdc_file: Tdc = Tdc.from_file(args.file)
        for block in tdc_file.blocks:
            compressed: bytes = block.data
            compressed_len_total += len(compressed)

            decompressed: bytes = decompress(compressed)
            decompressed_len_total += len(decompressed)

            decompressed_crc: int = crc32(decompressed)
            match: bool = block.crc32 == decompressed_crc
            if not match:
                raise ValueError("CRCs don't match! Expcted 0x{:08x}, got 0x{:08x}".format(block.crc32, decompressed_crc))

            output.write(decompressed)
            print("Wrote {} decompressed bytes to \"{}\"".format(len(decompressed), output_filename), file=sys.stderr)

        print("Finished writing {} decompressed bytes to \"{}\"".format(decompressed_len_total, output_filename), file=sys.stderr)

    print("Decompressed {} bytes from {} compressed bytes (compression ratio: {:.02f}%)".format(decompressed_len_total, compressed_len_total, (compressed_len_total*100)/decompressed_len_total), file=sys.stderr)


if __name__ == "__main__":
    main()
