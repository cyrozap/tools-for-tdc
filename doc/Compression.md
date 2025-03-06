# TDC File Data Compression

The data in Total Phase Data Center capture files (ending in `.tdc`) is split into one or more compressed blocks (see [tdc.ksy](tdc.ksy) for details on how to parse the file header and scan for blocks).
The compression algorithm is similar to [LZ77][lz77], since it involves segments of literal data as well as commands to copy data that already exists in the decompression buffer ("backreferences").
An explanation of the compressed data format and algorithm used to decompress each block follows.

> [!NOTE]
> Several months after reverse engineering this format, I discovered that this is an open source compression algorithm called [FastLZ][fastlz].


## Overview

The fundamental principle of this format / algorithm is that the compressed data block is made up entirely of control bytes followed by either literal data or "backreferences", which are commands to copy ranges of data at arbitrary locations in the decompressed output and append it to the end the decompressed output.
Each control byte indicates whether what follows is literal data to be directly appended to the decompressed output, or lookback commands to copy M bytes from a position starting N bytes back from the end of the decompressed output.
The exception to this is the first control byte in the block, the header byte, which indicates the version or type of the format of the compressed data block and is always followed by literal data.


## Control Bytes

Each control byte can be split into two parts--the high three bits, and the low five bits.


### High Three Bits

The meaning of these bits changes depending on whether or not this control byte is the header byte.

In the header byte, the high three bits represent the version / type of the decompression algorithm being used.
A `0b000` (0) value indicates that this block is a "type zero" compressed block, while `0b001` (1) indicates this is a "type one" compressed block.
All other values are undefined.
The details of the compressed block types will be explained later in this document.

In all other control bytes, the high three bits indicate whether the data that follows is literal data or metadata for a backreference copy.
If the high three bit are `0b000` (0), then the bytes that follow are literal data.
All other values (1-7, inclusive) indicate that this is a backreference, and the value is the base copy length of the backreference.


### Low Five Bits

The meaning of these bytes changes depending on if this control byte is for a literal data segment or a backreference.

For a literal data segment, these bits indicate one fewer than the number of literal bytes that follow it.
So when this value is zero, that means one byte of literal data follows.
When it's one, two bytes follow.
Etc.

For a backreference segment, these bits make up the upper eight bits of the base lookback offset ("distance" in [LZ77][lz77] terms).


## Data Segments

Following each control byte is a "data segment".
A data segment can be either a literal data segment or a backreference segment.


### Literal Data Segments

For literal data segments, the bytes that follow the control byte are copied directly and appended to the decompressed output.
The number of literal bytes is indicated by the low five bits in the control byte.


### Backreference Segments

Compared to literal data segments, backreference segments are much more complicated:

- The high three bits of the control byte specify how many bytes should be copied using a backreference (copy length).
  - If the copy length is `0b111` (7), it indicates that the actual copy length is extended by reading one or more additional bytes.
    - If this is a "type zero" compressed block, the first byte following the control byte is added to the copy length (7).
    - If this is a "type one" compressed block, each byte following the control byte is added to the copy length (7) until a byte with a value less than `0xFF` (255) is encountered.
      The byte with the value less than `0xFF` (255) is added to the copy length.
  - A constant value two is added to the copy length.
- The low five bits of the control byte make up the upper eight bits of the base lookback offset ("distance" in [LZ77][lz77] terms).
  - The byte following the last copy length byte (if any) is the lower eight bits of the base lookback offset.
  - If this is a "type one" compressed block and the base lookback offset is `0x1FFF` (8191), it indicates that the offset is extended by reading the next two bytes as a big-endian integer and adding them to the base offset.
    - e.g., if the base offset is `0x1FFF` (8191) and the next two bytes are `0x0001`, then the new offset should be `0x2000` (8192).
  - A constant value one is added to the lookback offset.
- When a backreference copies more data than exists in the decompression buffer at the specified offset, it means that the data will begin to repeat as long as necessary to satisfy the copy length.
  - e.g., if the decompressed data buffer contains the text "abcde" (hex: `6162636465`) and the backreference segment specifies to lookback two bytes and copy five, the contents of the decompressed data buffer will become "abcdededed" (hex: `61626364656465646564`)


## Examples

- `0000e0ff00`
  - Segments
    - `0000`: Header literal data segment
      - `00`: Header byte
        - High three bits: `0b000` (0)
          - Block type zero
        - Low five bits: `0b00000` (0)
          - Literal data length: 1
      - `00`: Literal data
    - `e0ff00`: Backreference segment
      - `e0`: Control byte
        - High three bits: `0b111` (7)
          - Base copy length: 7
        - Low five bits: `0b00000` (0)
          - High byte of the base lookback offset: 0
      - `ff`: Copy length extension
        - Copy length: 7 + 0xff (255) + 2 (constant) = 264
      - `00`: Low byte of the base lookback offset
        - Lookback offset: (0 << 8) + 0 + 1 (constant) = 1
  - Output: 265 zero bytes
    - 1 byte of literal data + 264 copies of that byte

See [../tools/test\_compression.py](../tools/test_compression.py) for examples of compressed data blocks with their decompressed outputs.


[lz77]: https://en.wikipedia.org/wiki/LZ77_and_LZ78#LZ77
[fastlz]: https://github.com/ariya/FastLZ
