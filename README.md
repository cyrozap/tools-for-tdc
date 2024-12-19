# Tools for TDC

This project is an effort to reverse engineer and document the `.tdc` capture file format used by [Total Phase Data Center][tpdc].
Total Phase Data Center (TPDC) is proprietary software needed to use Total Phase's protocol analyzer products, including their Beagle USB 5000 SuperSpeed Protocol Analyzer.

The goal of this project is to understand enough of the `.tdc` capture file format to write a tool to be able to convert them to [PCAP-NG][pcapng] format, to enable users of Beagle USB protocol analyzers to take advantage of Wireshark's wide array of protocol dissectors and plugin ecosystem.

This project was started in large part because Total Phase has a webpage that "explains" [how to export USB captures to PCAP][wireshark-export], but their "explanation" leaves the writing of the code to do the conversion [as an exercise to the reader][draw-the-rest-of-the-owl].


## Disclaimer

This project is not affiliated with, sponsored by, endorsed by, or in any way associated with Total Phase, Inc., the developer of Total Phase Data Center and associated protocol analyzer products.
This project makes no claim to ownership of the proprietary rights (including patents, trademarks, copyrights, trade secrets, etc.) of Total Phase, Inc. and its products or software.


## Project Status

The header format of the `.tdc` files is partially understood and documented with [Kaitai Struct][kaitai] in [doc/tdc.ksy](doc/tdc.ksy).
The format of the compressed capture data in `.tdc` files is (nearly) completely understood, and can be correctly decompressed using the algorithm described in [doc/Compression.md](doc/Compression.md).

To do:

- [ ] Reverse engineer the format of the decompressed capture data.
- [ ] Write a tool to parse a `.tdc` file and generate a `.pcapng` file from it.


## License

Except where stated otherwise:

* All software in this repository is made available under the [GNU General Public License, version 3 or later][gpl].
* All copyrightable content that is not software (e.g., reverse engineering notes, this README file, etc.) is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].


[tpdc]: https://web.archive.org/web/20241204022830/https://www.totalphase.com/products/data-center/
[pcapng]: https://datatracker.ietf.org/doc/draft-ietf-opsawg-pcapng/
[wireshark-export]: https://web.archive.org/web/20241204023125/https://www.totalphase.com/solutions/apps/exporting-captures-wireshark/
[draw-the-rest-of-the-owl]: https://web.archive.org/web/20101028033817if_/http://29.media.tumblr.com/tumblr_l7iwzq98rU1qa1c9eo1_500.jpg
[kaitai]: https://kaitai.io/
[gpl]: COPYING.txt
[cc-by-sa]: https://creativecommons.org/licenses/by-sa/4.0/
