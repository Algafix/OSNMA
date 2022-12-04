import socket
import navmon_pb2
import traceback

from bitstring import BitArray

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("86.82.68.237", 10000))

# Valid satellites according to www.gsc-europa.eu/system-service-status/constellation-information
valid_sv = [11, 12, 19, 18, 14, 26, 24, 30, 7, 8, 9, 1, 2, 3, 4, 5, 21, 25, 27, 31, 36, 13, 15, 33, 34, 10]

newest_tow = 0
sv_list = []

while True:
    sync = s.recv(4)
    if sync == b'bert':
        size = int.from_bytes(s.recv(2), 'big')
        message = s.recv(size, socket.MSG_WAITALL)

        try:
            nmm = navmon_pb2.NavMonMessage()
            nmm.ParseFromString(message)

            if nmm.sourceID != 200:
                continue

            # Check if it is Galileo signal from EB1
            if nmm.type != 3 or nmm.gi.sigid != 1:
                continue

            data_bits = BitArray(nmm.gi.contents)
            osnma_bits = BitArray(nmm.gi.reserved1)
            word = data_bits[:6].uint
            sID = nmm.sourceID
            sv = nmm.gi.gnssSV
            tow = nmm.gi.gnssTOW

            # Update TOW and reset everything
            if tow > newest_tow:
                newest_tow = tow
                sv_list = []
                print(f"\n\n==============================")
                print(f"New TOW: {newest_tow}")
                print(f"==============================\n")
            elif tow < newest_tow:
                continue

            # Only valid SVIDs
            if sv not in valid_sv:
                continue

            # Only receivers that transmit OSNMA bits
            if osnma_bits == b'':
                continue

            # Only if we hadn't read that SVIDs
            if sv in sv_list:
                continue
            else:
                sv_list.append(sv)
                print(f"{sv}\t{tow}")
                print(f'\tWord {word}\t{data_bits}')
                print(f'\t{osnma_bits}')
                long_page = BitArray(240)
                long_page[2:114] = data_bits[:112]
                long_page[122:138] = data_bits[112:]
                long_page[138:178] = osnma_bits
                print(f"\t\t{long_page}")

        except Exception as e:
            traceback.print_exc()
            pass

