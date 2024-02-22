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
import osnma.input_formats.nav_message_pb2 as gnss_sdr_protobuf


class GNSS_SDR(PageIterator):
    def __init__(self, host='127.0.0.1', port=1234, wn=None):
        super().__init__()
        self.host = host
        self.port = port
        self.s = self._get_socket()

        self.gst_wn = 0 if wn is None else wn
        self.gst_tow = 0
        self.svid_pages_dict = {}

    def _get_socket(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((self.host, self.port))
        except OSError as e:
            print(f"Binding error {e}")
            exit()
        return s

    def _parse_message(self, message):
        prn = message.prn
        page_tow = message.tow_at_current_symbol_ms // 1000
        page_bits = BitArray(bin=message.nav_message)
        is_even = not page_bits[0]
        return prn, page_tow, page_bits, is_even

    def _get_wn_and_tow_from_nav_data(self, word_type, full_page_bits: BitArray):
        if word_type == 0:
            nav_wn = full_page_bits[98:110].uint
            nav_tow = (full_page_bits[110:114] + full_page_bits[122:138]).uint
        else:
            nav_wn = full_page_bits[75:87].uint
            nav_tow = full_page_bits[87:107].uint
        return nav_wn, nav_tow

    def update_gst(self, page_tow, full_page_bits: BitArray):

        # Update ToW
        if page_tow > self.gst_tow:
            self.gst_tow = page_tow
        elif page_tow < self.gst_tow:
            self.gst_tow = page_tow
            self.gst_wn = self.gst_wn + 1

        # Update WN
        word_type = full_page_bits[2:8].uint
        if word_type in [0, 5]:
            nav_wn, nav_tow = self._get_wn_and_tow_from_nav_data(word_type, full_page_bits)

            if nav_tow != page_tow:
                print(f"Error: Nav data ToW {nav_tow} doesn't match ToW reported by receiver {page_tow}")

            if self.gst_wn == 0:  # Not initialized
                self.gst_wn = nav_wn
            elif nav_wn == self.gst_wn + 1:
                print(f"Error: WN has increased ({nav_wn} vs {self.gst_wn}) without a ToW rollover.")
            elif nav_wn < self.gst_wn:
                print(f"Error: Nav data WN {nav_wn} is lesser than the previously reported WN {self.gst_wn}")

    def __next__(self):
        data_format = None
        while True:
            try:
                data = self.s.recv(1024)
                message = gnss_sdr_protobuf.navMsg()
                message.ParseFromString(data)

                if message.system != 'E' or message.signal != '1B':
                    continue
                if 'tow_at_current_symbol_ms' not in [field.name for field, value in message.ListFields()]:
                    continue

                prn, page_tow, page_bits, is_even = self._parse_message(message)

                if is_even:
                    self.svid_pages_dict[prn] = (page_tow, page_bits)
                    continue
                else:
                    if prn not in self.svid_pages_dict:
                        continue
                    even_page_tow, even_page_bits = self.svid_pages_dict.pop(prn)
                    if even_page_tow != page_tow - 1:
                        continue
                    full_page_bits = even_page_bits + page_bits
                    page_tow = page_tow - 3

                    self.update_gst(page_tow, full_page_bits)

                    #print(f"{prn:02d} {self.gst_wn} {self.gst_tow}\t{full_page_bits}")

                    if self.gst_wn == 0:
                        continue

                    data_format = DataFormat(prn, self.gst_wn, self.gst_tow, full_page_bits)
                    break

            except DecodeError as e:
                print(f"GNSS SDR decoding failed:\t")
                # traceback.print_exc()
                continue
            except Exception as e:
                print(f"Unhandled exception in GNSS SDR input module:")
                traceback.print_exc()
                continue

        if data_format is None:
            raise StopIteration

        return data_format
