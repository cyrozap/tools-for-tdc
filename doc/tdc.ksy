meta:
  id: tdc
  file-extension: tdc
  title: Total Phase Data Center Capture File
  application: Total Phase Data Center
  license: CC0-1.0
  endian: le
seq:
  - id: magic
    contents: "TPDC"
  - id: header_version
    type: u2
  - id: data_offset
    type: u4
  - id: header
    type:
      switch-on: header_version
      cases:
        0x0100: header_v1
        0x0200: header_v2
        0x0300: header_v3
instances:
  blocks:
    pos: data_offset
    type: compressed_block
    repeat: eos
    doc: "Blocks of compressed data."
types:
  thing:
    seq:
      - id: lower
        type: u2
      - id: upper
        type: u2
  header_v1:
    seq:
      - id: unk0
        type: u2
      - id: unk1
        type: u2
      - id: capture_save_time
        type: u4
        doc: "The time at which the capture was saved, in seconds since the Unix epoch."
      - id: data_version
        type: u2
        doc: "The version number for the decompressed data."
      - id: unk3
        type: u4
      - id: unk4
        type: u4
      - id: unk5
        type: u4
      - id: num_thing
        type: u2
      - id: thing
        type: thing
        repeat: expr
        repeat-expr: num_thing
  header_v2:
    seq:
      - id: unk0
        type: u2
      - id: unk1
        type: u4
      - id: capture_save_time
        type: u4
        doc: "The time at which the capture was saved, in seconds since the Unix epoch."
      - id: data_version
        type: u2
        doc: "The version number for the decompressed data."
      - id: unk3
        type: u4
      - id: unk4
        type: u4
      - id: unk5
        type: u4
      - id: num_thing
        type: u2
      - id: thing
        type: thing
        repeat: expr
        repeat-expr: num_thing
  header_v3:
    seq:
      - id: unk0
        type: u2
      - id: unk1
        type: u4
      - id: capture_save_time
        type: u4
        doc: "The time at which the capture was saved, in seconds since the Unix epoch."
      - id: data_version
        type: u2
        doc: "The version number for the decompressed data."
      - id: unk3
        type: u4
      - id: unk4
        type: u4
      - id: unk5
        type: u8
      - id: num_thing
        type: u2
      - id: thing
        type: thing
        repeat: expr
        repeat-expr: num_thing
  compressed_block:
    seq:
      - id: length_info
        type: u4
        doc: "24-bit length and 8-bit unknown value. 8-bit unknown value seems to always be zero."
      - id: crc32
        type: u4
        doc: "The CRC-32/BZIP2 of the decompressed data."
      - id: data
        size: length_info >> 8
        doc: "Compressed data."
