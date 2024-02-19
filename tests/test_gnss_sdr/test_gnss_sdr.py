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
from google.protobuf.message import DecodeError
import nav_message_pb2 as gnss_sdr_protobuf

host = '127.0.0.1'
port = 1234

def _recv_exact(s, size) -> bytes:
    message = bytes()
    while len(message) < size:
        recv_buff = s.recv(size - len(message))
        message += recv_buff
    return message

def _get_socket():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((host, port))
    except OSError as e:
        print(f"Binding error {e}")
        exit()
    return s

def _parse_message(message):
    prn = message.prn
    page_tow = message.tow_at_current_symbol_ms // 1000
    page_bits = BitArray(bin=message.nav_message)
    is_even = not page_bits[0]
    return prn, page_tow, page_bits, is_even


def get_gst(gst_wn, gst_tow, page_tow, full_page_bits: BitArray):

    word_type = full_page_bits[2:8].uint
    if word_type in [0, 5]:
        if word_type == 0:
            nav_wn = full_page_bits[98:110].uint
            nav_tow = (full_page_bits[110:114] + full_page_bits[122:138]).uint
        else:
            nav_wn = full_page_bits[75:87].uint
            nav_tow = full_page_bits[87:107].uint
        if nav_tow != page_tow:
            print(f"Error: Nav data ToW {nav_tow} doesn't match ToW reported by receiver {page_tow}")

        if gst_wn == 0:
            gst_wn = nav_wn
        elif nav_wn == gst_wn + 1:
            gst_wn = nav_wn
        elif nav_wn < gst_wn:
            print(f"Error: Nav data WN {nav_wn} is lesser than the previously reported WN {gst_wn}")

    if page_tow > gst_tow:
        gst_tow = page_tow
    elif page_tow < gst_tow:
        print(f"Error: Receiver ToW {page_tow} is lesser than the previously reported ToW {gst_tow}")

    return gst_wn, gst_tow

s = _get_socket()

print(f"Binded {s}")
f = open("decoding2.txt", 'rb')

svid_pages_dict = {}
gst_wn = 0
gst_tow = 0

while True:
    try:
        #data = s.recv(1024)
        data = f.readline()
        if data == b'':
            break
        data = b'\n' + data.rstrip()
        #print(data)

        message = gnss_sdr_protobuf.navMsg()
        message.ParseFromString(data)

        if message.system != 'E' or message.signal != '1B':
            continue
        if 'tow_at_current_symbol_ms' not in [field.name for field, value in message.ListFields()]:
            #print(f"Page with no tow\n{message}")
            continue

        prn, page_tow, page_bits, is_even = _parse_message(message)

        if is_even:
            svid_pages_dict[prn] = (page_tow, page_bits)
            continue
        else:
            if prn not in svid_pages_dict:
                continue
            even_page_tow, even_page_bits = svid_pages_dict.pop(prn)
            if even_page_tow != page_tow-1:
                continue
            full_page_bits = even_page_bits + page_bits
            page_tow = page_tow - 3

            gst_wn, gst_tow = get_gst(gst_wn, gst_tow, page_tow, full_page_bits)

            print(f"{prn:02d} {gst_wn} {gst_tow}\t{full_page_bits}")


    except DecodeError as e:
        print(f"GNSS SDR decoding failed:\t")
        # traceback.print_exc()
        continue
    except Exception as e:
        print(f"Unhandled exception in GNSS SDR input module:")
        traceback.print_exc()
        continue

