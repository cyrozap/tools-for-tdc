# Tools


## [crc32\_bzip2.py](crc32_bzip2.py)

An implementation of the CRC-32/BZIP2 algorithm, which is used in the `.tdc` format to verify decompressed data.


## [fastlz.py](fastlz.py)

A library containing an implementation of the decompression algorithm ([FastLZ][fastlz]) described in [../doc/Compression.md](../doc/Compression.md).


## [process.py](process.py)

A demo program to process `.tdc` files. Currently, it only decompressed the data contained in the selected `.tdc` file and writes it to a new file.
It does not yet parse the decompressed data.


## [tdc\_data.py](tdc_data.py)

A library for parsing the decompressed data in `.tdc` files.


## [test\_crc32.py](test_crc32.py) and [test\_fastlz.py](test_fastlz.py)

Unit tests for the implementations of the CRC-32/BZIP2 algorithm and the [FastLZ][fastlz] decompression algorithm, respectively.


[fastlz]: https://github.com/ariya/FastLZ
