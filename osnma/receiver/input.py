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

import pandas as pd
from bitstring import BitArray


class DataFormat:
    osnma_start = 138
    osnma_end = 178
    hkroot_start = 138
    hkroot_length = 8
    mack_start = 146
    mack_length = 32

    def __init__(self, svid: int, wn: int, tow: int, nav_bits: BitArray, band: str = 'GAL_L1BC', crc: bool = True):

        if len(nav_bits) != 240:
            raise ValueError(f"The DataFormat object accepts 1 nominal page (or double page) with 240 bits."
                             f" Current length {len(nav_bits)} bits.")
        self.nav_bits = nav_bits

        self.svid = svid
        self.wn = wn
        self.tow = tow
        self.band = band
        self.crc = crc

        self.dsm_id = None
        self.bid = None

        self.has_osnma = self.nav_bits[self.osnma_start:self.osnma_end].uint != 0

        if self.has_osnma:
            if tow % 30 == 2:
                self._dsm_header()

    def get_osnma(self):
        page_hkroot = self.nav_bits[self.hkroot_start:self.hkroot_start + self.hkroot_length]
        page_mack = self.nav_bits[self.mack_start:self.mack_start + self.mack_length]
        return page_hkroot, page_mack

    def _dsm_header(self):
        hkroot, _ = self.get_osnma()

        self.dsm_id = hkroot[:4]
        self.bid = hkroot[4:]


class QascomTestOne:

    def __init__(self, path, svid):
        self.path = path
        self.svid = svid

        nav_msg_header = ['Date', 'Time', 'GNSS', 'SVID', 'WN', 'TOW', 'NavMessage']
        nav_msg = pd.read_csv(self.path, header=None, names=nav_msg_header)

        gnss_is_galileo = nav_msg.GNSS == 0
        svid_is_one = nav_msg.SVID == self.svid
        all_filters = gnss_is_galileo & svid_is_one
        nav_msg = nav_msg[all_filters]
        nav_msg = nav_msg.reset_index(drop=True)

        self.data_iter = nav_msg.iterrows()

    def __iter__(self) -> 'QascomTestOne':
        return self

    def __next__(self) -> (int, DataFormat):
        index, row = next(self.data_iter)
        data = DataFormat(row['SVID'], row['WN'], row['TOW'], BitArray(hex=row['NavMessage']))

        return index, data


class QascomTest:

    def __init__(self, path):
        self.path = path

        nav_msg_header = ['Date', 'Time', 'GNSS', 'SVID', 'WN', 'TOW', 'NavMessage']
        nav_msg = pd.read_csv(self.path, header=None, names=nav_msg_header)

        gnss_is_galileo = nav_msg.GNSS == 0
        nav_msg = nav_msg[gnss_is_galileo]
        nav_msg = nav_msg.reset_index(drop=True)

        self.data_iter = nav_msg.iterrows()

    def __iter__(self) -> 'QascomTest':
        return self

    def __next__(self) -> (int, DataFormat):
        index, row = next(self.data_iter)
        data = DataFormat(row['SVID'], row['WN'], row['TOW'], BitArray(hex=row['NavMessage']))

        return index, data


class SBFAscii:

    def __init__(self, path, svid=None):
        self.path = path
        self.svid = svid
        self.real_size = 234

        # Load dataframe
        nav_msg_header = ['TOW', 'WN', 'SVID', 'CRCPassed', 'ViterbiCnt', 'signalType',
                          'concatenated', 'VITERBI_TYPE', 'RxChannel', 'NAVBits']
        nav_msg = pd.read_csv(self.path, header=None, names=nav_msg_header)

        # Filter the dataframe
        nav_msg.dropna(inplace=True)
        nav_msg.SVID = nav_msg.SVID.apply(lambda x: int(x[1:]))
        if self.svid is not None:
            mask = nav_msg['SVID'].values == self.svid
            nav_msg = nav_msg[mask]
        nav_msg.reset_index(inplace=True, drop=True)

        # Adapt column types
        nav_msg.TOW = nav_msg.TOW.astype(int)
        nav_msg.WN = nav_msg.WN.astype(int)
        nav_msg.NAVBits = nav_msg.NAVBits.apply(lambda x: x.replace(' ', ''))

        self.data_iter = nav_msg.iterrows()

    def __iter__(self) -> 'SBFAscii':
        return self

    def __next__(self) -> (int, DataFormat):
        index, row = next(self.data_iter)

        # Reconstruct double page 240 bits
        nav_bits = BitArray(hex=row["NAVBits"])[:self.real_size]
        nav_bits.insert('0b000000', 114)

        # WN counts from GPS WN 0, and TOW counts at the end of the SF
        wn = row['WN']-1024
        tow = row['TOW']-2
        band = row['signalType']
        crc = True if row['CRCPassed'] == 'Passed' else False
        data = DataFormat(row['SVID'], wn, tow, nav_bits, band=band, crc=crc)

        return index, data


class ICDTestVectors:

    def __init__(self, path,):
        self.path = path

        # Load dataframe
        nav_msg_header = ['TOW', 'WN', 'SVID', 'NAVBits']
        nav_msg = pd.read_csv(self.path, header=None, names=nav_msg_header)

        # Adapt column types
        nav_msg.TOW = nav_msg.TOW.astype(int)
        nav_msg.WN = nav_msg.WN.astype(int)
        nav_msg.SVID = nav_msg.SVID.astype(int)

        self.data_iter = nav_msg.iterrows()

    def __iter__(self) -> 'ICDTestVectors':
        return self

    def __next__(self) -> (int, DataFormat):
        index, row = next(self.data_iter)
        nav_bits = BitArray(hex=row["NAVBits"])

        data = DataFormat(row['SVID'], row['WN'], row['TOW'], nav_bits)

        return index, data


