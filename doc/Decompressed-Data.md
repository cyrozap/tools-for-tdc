# TDC Decompressed Data Format


## Overview

The decompressed data is a sequence of blocks.
Each block has a header byte which defines the type of the block, followed by the data bytes in that block.
The number of bytes of data in each block depends on the type of the block, so unlike with TLV data it is not possible to scan through all the blocks if a block with an unknown type is present.

So far, only block types 0, 5, and 6 are understood.


## Header Byte

Each block begins with a header byte.

The header byte is split into two nybbles:

- The purpose of the high nybble is unknown.
- The low nybble is the block type.


## Block Types


### Block Type 0

This block contains the captured data.

The fields in this block are as follows:

- `3B`: The 24-bit (little-endian) block size.
  This is the size of the entire block, including the header byte and size bytes.
  Must be 10 or greater.
- `<I`: The block index (starts at zero and increments by one for each type-0 block).
- `<H`: Unknown data.
- Block size minus 10 bytes: Zero or more records of TLV data.

Each record of TLV data is formatted as follows:

- `<H`: Tag
- `<I`: Record length (including the length of the tag (2), length of the record length (4), and the length of the value).
  Must be 6 or greater.
- Record length minus 6 bytes: Value


#### Record Tag 0x0000

- `<H`: Unknown data.
- `<Q`: Timestamp samples.
  Divide by the sample rate to get the timestamp of this capture block in seconds since the start of the capture.
- `<I`: Length samples.
  Divide by the sample rate to get the length / duration of this capture block in seconds.


### Block Type 5

This block contains metadata about the capture.

This block will typically occur first in the block sequence.

The number of fields in this block varies according to the data version in the `.tdc` file (outside this decompressed capture data).

The fields in this block are as follows:

- `<I`: Unknown data.
- `<I`: Unknown data.
- `<I`: Capture start time, in seconds since the Unix epoch.
- `<I`: Capture end time, in seconds since the Unix epoch.
- `<Q`: The total number of samples taken during the capture.
- `<I`: The sample rate, in samples per second.
- `B`: Unknown data.
- `<I`: Unknown data.
- `<I`: Unknown data.
- `<I`: Unknown data. Only present in data version 0x0103 and later.
- `B`: Unknown data. Only present in data version 0x0104 and later.
- `B`: Unknown data. Only present in data version 0x0108 and later.
- `B`: Unknown data. Only present in data version 0x010A and later.


### Block Type 6

This block contains metadata about the bus, including the protocol type of the bus.
For USB, this also includes enumeration info for devices on the bus.

This block will typically occur last in the block sequence.

The first four bytes after the header byte identify the protocol of the bus:

- 1: I2C
- 2: SPI
- 3: USB
- 4: CAN
- 5: eSPI
- 6: USB-PD

The exact meaning of the remaining bytes is currently unknown.
