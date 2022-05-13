#!/usr/bin/python

from bitstring import BitArray

SYNC = b'$@'

TIME_STAMP = slice(8,14)
SVID = 14
CRC = 15
VITERBI_CNT = 16
SOURCE = 17
FREQ_NR = 18
RX_CHANNEL = 19
NAV_START = 20

TOW_DNU = 4294967295
WNc_DNU = 65535

GALRawINAV_NAV_BYTES = 8
GPSRawCA_NAV_BYTES = 10

SIGNAL_MASK = 0x1f
CONCAT_MASK = 0b00100000

signal_type = {
    0: 'L1CA - GPS',
    17: 'E1 (L1BC) - Galileo'
}

def le2be(uint):
    return uint[::-1]

def crc_calculation(block):

    #polynomial = BitArray('0b10001000000100001')
    #poly_size=len(polynomial)
    block = BitArray('0b11010011101100')
    polynomial = BitArray('0b1011')
    poly_size = len(polynomial)

    poly_position = 0

    # block_size = len(block * 8)
    block_size = len(block)
    # block = BitArray(block) + BitArray('0x0000')
    block = BitArray(block) + BitArray('0b000')

    while True:
        
        block.overwrite(block[:poly_size] ^ polynomial, 0)

        if pos := block.find('0b1'):
            pos = pos[0]
            block = block[pos:]
            poly_position += pos
            if poly_position >= block_size:
                break
        else:
            break

    print(f"CRC {block.uint}")


def print_nav_page_block(
    tow, wn_c, svid, crc_passed, viterbi, source, rx_channel, nav_bits):

    print(f"ToW ms: {tow}, ToW s {tow//1000}, WN: {wn_c}")
    print(f"SVId:\t\t{svid}")
    print(f"CRC:\t\t{crc_passed}")
    print(f"Viterbi:\t{viterbi}")
    print(f"Signal type:\t{source[0]}")
    print(f"Rx Channel:\t{rx_channel}")
    print(f"Navigation bits in hex: \n {nav_bits}")

# PARSE SECTIONS #

def parse_header(header):
    """Parses the header into crc, id, length and id into block
    number and block revision.

    :param header: Bytes object with the 8 byte header.
    :return: Tuple with the values (bytes) crc, (int) id, (int) length, (int) block_num, (int) rev_num. 

    """
    
    crc = int.from_bytes(header[2:4], "little")
    id = int.from_bytes(header[4:6], "little")
    length = int.from_bytes(header[6:8], "little")

    block_num = id & 0xefffffff
    rev_num = id >> 13

    return crc, id, length, block_num, rev_num

def parse_tow_wn(buffer):
    
    tow = int.from_bytes(buffer[:4],'little')
    wn_c = int.from_bytes(buffer[4:], 'little')

    if tow == TOW_DNU:
        tow = 'DNU'
    if wn_c == WNc_DNU:
        wn_c = 'DNU'

    return tow, wn_c

def parse_SVID(svid):

    if svid == 0:
        svid = 'DNU'
    elif svid >= 1 and svid <= 37:
        pass
    elif svid >= 38 and svid <= 61:
        svid = svid - 37
    elif svid == 62:
        svid = 'GLONASS not known'
    elif svid >= 63 and svid <= 68:
        svid = svid - 38
    elif svid >= 71 and svid <= 106:
        svid = svid - 70
    elif svid >= 107 and svid <= 119:
        pass
    elif svid >= 120 and svid <= 140:
        pass
    elif svid >= 141 and svid <= 180:
        svid = svid - 140
    elif svid >= 181 and svid <= 187:
        svid = svid - 180
    elif svid >= 191 and svid <= 197:
        svid = svid - 190
    elif svid >= 198 and svid <= 215:
        svid = svid - 57
    elif svid >= 216 and svid <= 222:
        svid = svid - 208
    elif svid >= 223 and svid <= 245:
        svid = svid - 182
    else:
        svid = 'Not known'
    
    return svid

def parse_CRC(crc):
    return bool(crc)

def parse_viterbi_cnt(viterbi_cnt):
    return viterbi_cnt

def parse_rx_channel(rx_channel):
    return rx_channel

def parse_nav_bits(nav_bits):
    return [nav_bits[i:i+4].hex() for i in range(0, len(nav_bits), 4)]

## PARSE GENERAL BLOCKS ##

def parse_nav_page_block(block, parse_source, nav_len):

    tow, wn_c = parse_tow_wn(block[TIME_STAMP])
    svid = parse_SVID(block[SVID])
    crc_passed = parse_CRC(block[CRC])
    viterbi_errors = parse_viterbi_cnt(block[VITERBI_CNT])
    source = parse_source(block[SOURCE])
    # FreqNr
    rx_channel = parse_rx_channel(block[RX_CHANNEL])
    nav_bits_hex = parse_nav_bits(block[NAV_START:NAV_START+4*nav_len])

    print_nav_page_block(tow, wn_c, svid, crc_passed, viterbi_errors, 
    source, rx_channel, nav_bits_hex)

### PARSE SPECIFIC BLOCK NUMBERS ###

def parse_GALRawINAV(block):
    print("GAL Raw Block\n")

    def parse_source(source):
        signal = signal_type[source & SIGNAL_MASK]
        concat = source & CONCAT_MASK

        return signal, concat
    
    parse_nav_page_block(block, parse_source, GALRawINAV_NAV_BYTES)

def parse_GPSRawCA(block):
    print("GPS Raw Block\n")

    def parse_source(source):
        signal = signal_type[source & SIGNAL_MASK]
        return (signal,None)
    
    parse_nav_page_block(block, parse_source, GPSRawCA_NAV_BYTES)

switch_block = {
    4017: parse_GPSRawCA,
    4023: parse_GALRawINAV,
}


#### MAIN READING LOOP ####

if __name__ == '__main__':

    sbf_file = open("utils/gps_gal_raw.sbf", 'br')

    while header := sbf_file.read(8):

        if header[:2] == SYNC:
            
            fake_block = False

            crc, id, length, block_num, rev_num = parse_header(header)

            block = header + sbf_file.read(length-8)

            crc_calculation(block)

            print('\nBlock detected!')
            print(f"\tcrc {crc}\n\tid {id}\n\tlength {length}\n\tnum {block_num}, rev {rev_num}\n")

            switch_block[id](block)

            exit(3)

        else:
            print(f"Out of sync!")

    sbf_file.close()



