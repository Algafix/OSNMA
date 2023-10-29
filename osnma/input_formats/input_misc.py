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

from osnma.input_formats.base_classes import DataFormat, PageIterator


class ICDTestVectors(PageIterator):

    def __init__(self, path):
        super().__init__()
        self.path = path

        # Load dataframe
        nav_msg_header = ['TOW', 'WN', 'SVID', 'NAVBits']
        nav_msg = pd.read_csv(self.path, header=None, names=nav_msg_header)

        # Adapt column types
        nav_msg.TOW = nav_msg.TOW.astype(int)
        nav_msg.WN = nav_msg.WN.astype(int)
        nav_msg.SVID = nav_msg.SVID.astype(int)

        self.data_iter = nav_msg.iterrows()

    def __next__(self) -> DataFormat:
        index, row = next(self.data_iter)
        nav_bits = BitArray(hex=row["NAVBits"])

        data = DataFormat(row['SVID'], row['WN'], row['TOW'], nav_bits)

        return data


class QascomTestOne(PageIterator):

    def __init__(self, path, svid):
        super().__init__()
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

    def __next__(self) -> (int, DataFormat):
        index, row = next(self.data_iter)
        data = DataFormat(row['SVID'], row['WN'], row['TOW'], BitArray(hex=row['NavMessage']))

        return data


class QascomTest(PageIterator):

    def __init__(self, path):
        super().__init__()
        self.path = path

        nav_msg_header = ['Date', 'Time', 'GNSS', 'SVID', 'WN', 'TOW', 'NavMessage']
        nav_msg = pd.read_csv(self.path, header=None, names=nav_msg_header)

        gnss_is_galileo = nav_msg.GNSS == 0
        nav_msg = nav_msg[gnss_is_galileo]
        nav_msg = nav_msg.reset_index(drop=True)

        self.data_iter = nav_msg.iterrows()

    def __next__(self) -> (int, DataFormat):
        index, row = next(self.data_iter)
        data = DataFormat(row['SVID'], row['WN'], row['TOW'], BitArray(hex=row['NavMessage']))

        return data
