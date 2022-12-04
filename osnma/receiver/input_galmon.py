import socket
import traceback

from bitstring import BitArray
from osnma.receiver.input import DataFormat
import osnma.receiver.navmon_pb2 as navmon_pb2


class GALMON:

    VALID_SV = [11, 12, 19, 18, 14, 26, 24, 30, 7, 8, 9, 1, 2, 3, 4, 5, 21, 25, 27, 31, 36, 13, 15, 33, 34, 10]

    def __init__(self, host='86.82.68.237', port=10000):

        self.index = -1
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))

        self.newest_tow = 0
        self.sv_list = []

    def __iter__(self):
        return self

    def __next__(self):

        data_format = None
        self.index += 1

        while True:
            sync = self.s.recv(4)
            if sync == b'bert':

                size = int.from_bytes(self.s.recv(2), 'big')
                message = self.s.recv(size, socket.MSG_WAITALL)

                try:
                    nmm = navmon_pb2.NavMonMessage()
                    nmm.ParseFromString(message)

                    # if nmm.sourceID != 200:
                    #     continue

                    # Check if it is Galileo signal from EB1
                    if nmm.type != 3 or nmm.gi.sigid != 1:
                        continue

                    data_bits = BitArray(nmm.gi.contents)
                    osnma_bits = BitArray(nmm.gi.reserved1)
                    word = data_bits[:6].uint
                    sv = nmm.gi.gnssSV
                    tow = nmm.gi.gnssTOW
                    wn = nmm.gi.gnssWN

                    # Update TOW and reset everything
                    if tow > self.newest_tow:
                        self.newest_tow = tow
                        self.sv_list = []
                    elif tow < self.newest_tow:
                        continue

                    # Only valid SVIDs
                    if sv not in self.VALID_SV:
                        continue

                    # Only receivers that transmit OSNMA bits
                    if osnma_bits == b'':
                        continue

                    # Only if we hadn't read that SVIDs
                    if sv in self.sv_list:
                        continue
                    else:
                        self.sv_list.append(sv)
                        long_page = BitArray(240)
                        long_page[2:114] = data_bits[:112]
                        long_page[122:138] = data_bits[112:]
                        long_page[138:178] = osnma_bits
                        data_format = DataFormat(sv, wn, tow, long_page)
                        break

                except Exception as e:
                    traceback.print_exc()

        if data_format is None:
            raise StopIteration

        return self.index, data_format

