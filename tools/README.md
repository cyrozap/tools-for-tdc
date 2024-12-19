# Tools


## [crc32\_bzip2.py](crc32_bzip2.py)

An implementation of the CRC-32/BZIP2 algorithm, which is used in the `.tdc` format to verify decompressed data.


## [process.py](process.py)

A demo program to process `.tdc` files. Currently, it only decompressed the data contained in the selected `.tdc` file and writes it to a new file.
It does not yet parse the decompressed data.


## [tdc\_compression.py](tdc_compression.py)

A library containing an implementation of the decompression algorithm described in [../doc/Compression.md](../doc/Compression.md).


## [test\_compression.py](test_compression.py) and [test\_crc32.py](test_crc32.py)

Unit tests for the implementations of the decompression algorithm and CRC-32/BZIP2 algorithm, respectively.
