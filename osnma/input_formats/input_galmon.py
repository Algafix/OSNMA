#
# Copyright © European Union 2022
#
# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the Licence for the specific language governing permissions and limitations under the Licence.
#

import socket
import time
import traceback

from bitstring import BitArray
from osnma.input_formats.base_classes import DataFormat, PageIterator
from google.protobuf.message import DecodeError
import osnma.input_formats.navmon_pb2 as navmon_pb2


class GALMON(PageIterator):

    VALID_SV = [11, 12, 19, 18, 14, 26, 24, 30, 7, 8, 9, 1, 2, 3, 4, 5, 21, 25, 27, 31, 36, 13, 15, 33, 34, 10]

    def __init__(self, host='86.82.68.237', port=10000):
        super().__init__()
        self.host = host
        self.port = port
        self.s = self._get_socket()

        self.newest_tow = 0
        self.sv_list = []

    def _get_socket(self):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(30)
                s.connect((self.host, self.port))
            except ConnectionRefusedError as e:
                print("Galmon refusing connection, retrying in 10 seconds")
                time.sleep(10)
            else:
                break
        return s

    def __next__(self):
        data_format = None
        while True:
            try:
                sync = self.s.recv(4)
                if len(sync) == 0:
                    raise TimeoutError("Galmon closed connection")
                if sync == b'bert':
                    size = int.from_bytes(self.s.recv(2), 'big')
                    message = self.s.recv(size)

                    nmm = navmon_pb2.NavMonMessage()
                    nmm.ParseFromString(message)
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
            except TimeoutError as e:
                print(f"Unexpected read from Galmon: {e}")
                self.s.close()
                self.s = self._get_socket()
            except DecodeError as e:
                # print(f"Failed:\n{nmm}")
                # traceback.print_exc()
                continue
            except Exception as e:
                print(f"Unhandled exception in galmon input module:")
                traceback.print_exc()
                continue

        if data_format is None:
            raise StopIteration

        return data_format
