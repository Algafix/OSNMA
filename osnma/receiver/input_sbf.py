
import socket

from bitstring import BitArray

from osnma.receiver.input import DataFormat

SYNC = b'$@'

TIME_STAMP = slice(8, 14)
SVID = 14
CRC = 15
SOURCE = 17
NAV_START = 20

TOW_DNU = 4294967295
WNc_DNU = 65535

GALRawINAV_NAV_BYTES = 8
NAV_REAL_SIZE = 234

SIGNAL_MASK = 0x1f

signal_type = {
    17: 'GAL_L1BC',
    19: 'GAL_E6BC',
    20: 'GAL_E5a',
    21: 'GAL_E5b',
    22: 'GAL_E4_AltBOC'
}

CRC16_XMODEM_TABLE = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
]


def crc_calculation(data, crc=0):

    for byte in data:
        crc = ((crc << 8) & 0xff00) ^ CRC16_XMODEM_TABLE[((crc >> 8) & 0xff) ^ byte]
    return crc & 0xffff


def parse_header(header):
    """Parses the header into crc, id, length and id into block
    number and block revision.

    :param header: Bytes object with the 8 byte header.
    :return: Tuple with the values (bytes) crc, (int) id, (int) length, (int) block_num, (int) rev_num.

    """

    crc = int.from_bytes(header[2:4], "little")
    id = int.from_bytes(header[4:6], "little")
    length = int.from_bytes(header[6:8], "little")

    block_num = id & 0xdfff
    rev_num = id >> 13

    return crc, id, length, block_num, rev_num


def parse_tow_wn(buffer):
    tow = int.from_bytes(buffer[:4], 'little')
    wn_c = int.from_bytes(buffer[4:], 'little')

    if tow == TOW_DNU:
        tow = 'DNU'
    if wn_c == WNc_DNU:
        wn_c = 'DNU'

    return tow, wn_c


def parse_SVID(svid):
    if svid == 0:
        svid = 'DNU'
    elif 1 <= svid <= 37:
        pass
    elif 38 <= svid <= 61:
        svid = svid - 37
    elif svid == 62:
        svid = 'GLONASS not known'
    elif 63 <= svid <= 68:
        svid = svid - 38
    elif 71 <= svid <= 106:
        svid = svid - 70
    elif 107 <= svid <= 119:
        pass
    elif 120 <= svid <= 140:
        pass
    elif 141 <= svid <= 180:
        svid = svid - 140
    elif 181 <= svid <= 187:
        svid = svid - 180
    elif 191 <= svid <= 197:
        svid = svid - 190
    elif 198 <= svid <= 215:
        svid = svid - 57
    elif 216 <= svid <= 222:
        svid = svid - 208
    elif 223 <= svid <= 245:
        svid = svid - 182
    else:
        svid = 'Not known'

    return svid


def parse_nav_bits(nav_bits):

    return [nav_bits[i:i + 4][::-1].hex() for i in range(0, len(nav_bits), 4)]


def parse_GALRawINAV(block):

    tow, wn_c = parse_tow_wn(block[TIME_STAMP])
    svid = parse_SVID(block[SVID])
    crc_passed = bool(block[CRC])
    source = signal_type[block[SOURCE] & SIGNAL_MASK]
    nav_bits_hex = parse_nav_bits(block[NAV_START:NAV_START + 4 * GALRawINAV_NAV_BYTES])

    # print_nav_page_block(tow, wn_c, svid, crc_passed, viterbi_errors, source, rx_channel, nav_bits_hex)
    # return csv_nav_page_block(tow, wn_c, svid, crc_passed, viterbi_errors, source, rx_channel, nav_bits_hex)
    return tow, wn_c, svid, crc_passed, source, nav_bits_hex


class SBF:

    def __init__(self, path, use_satellites_list=False):

        self.file = open(path, 'br')
        self.file_pos = self.file.tell()
        self.use_satellites_list = use_satellites_list

    def __iter__(self):
        return self

    def __next__(self):

        data_format = None

        while header := self.file.read(8):
            if header[:2] == SYNC:
                # Possible block header detected
                crc, block_id, length, block_num, rev_num = parse_header(header)

                if length % 4 != 0:
                    # Not a block, advance one byte
                    self.file_pos += 1
                    self.file.seek(self.file_pos)
                    continue

                block = header + self.file.read(length - 8)
                calculated_crc = crc_calculation(block[4:])

                if calculated_crc != crc:
                    # Not a block, advance one byte
                    self.file_pos += 1
                    self.file.seek(self.file_pos)
                    continue

                if block_id == 4023:
                    # We have a block and its a gal raw nav block
                    tow, wn_c, svid, crc_passed, band, nav_bits_hex = parse_GALRawINAV(block)

                    if self.use_satellites_list and svid not in self.use_satellites_list:
                        self.file_pos = self.file.tell()
                        continue

                    if band == 'GAL_L1BC' and tow != 'DNU' and wn_c != 'DNU':
                        # print(f"WN: {wn_c} TOW: {tow} SVID: {svid} BAND: {band} CRC: {crc_passed}")
                        tow = tow // 1000 - 2
                        wn = wn_c - 1024
                        nav_bits = BitArray(hex="".join(nav_bits_hex))[:234]
                        nav_bits.insert('0b000000', 114)
                        data_format = DataFormat(svid, wn, tow, nav_bits, band, crc_passed)
                        self.file_pos = self.file.tell()
                        break

                # It was a valid block, update descriptor and continue
                self.file_pos = self.file.tell()
            else:
                self.file_pos += 1
                self.file.seek(self.file_pos)

        if data_format is None:
            raise StopIteration

        return data_format


class SBFLive:

    def __init__(self, host, port):

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))

    def __iter__(self):
        return self

    def __next__(self):

        data_format = None

        while sync := self.s.recv(2):
            if sync == SYNC:
                header = sync + self.s.recv(6)
                crc, block_id, length, block_num, rev_num = parse_header(header)

                if length % 4 != 0:
                    continue

                block = header + self.s.recv(length - 8)
                calculated_crc = crc_calculation(block[4:])

                if calculated_crc != crc:
                    continue

                if block_id == 4023:
                    tow, wn_c, svid, crc_passed, band, nav_bits_hex = parse_GALRawINAV(block)
                    if band == 'GAL_L1BC' and tow != 'DNU' and wn_c != 'DNU':
                        tow = tow // 1000 - 2
                        wn = wn_c - 1024
                        nav_bits = BitArray(hex="".join(nav_bits_hex))[:234]
                        nav_bits.insert('0b000000', 114)
                        data_format = DataFormat(svid, wn, tow, nav_bits, band, crc_passed)
                        break

        if data_format is None:
            raise StopIteration

        return data_format
