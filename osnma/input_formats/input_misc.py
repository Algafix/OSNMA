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
import datetime
from enum import Enum

from osnma.input_formats.base_classes import DataFormat, PageIterator, PAGE_TOW_E1B_LOOKUP_TABLE

class GnssChipset(Enum):
    BROADCOM = 1
    MEDIATEK = 2

class AndroidGNSSLog(PageIterator):

    NAV_PREFIX = 'Nav'
    GAL_INAV_TYPE = '1537'
    UTC_TIME_LOGS = ['Raw', 'Agc']  # I have only found raw and agc to be more or less reliable for timing
    GST_START_EPOCH = datetime.datetime(1999, 8, 22, 0, 0, 0)
    # Actually it was 13 seconds before that, but its only relevant for GNSS time. This is easier for WN and TOW
    LEAP_SECONDS = 18  # Could be extracted from raw or agc, but I have never seen that field populated

    def __init__(self, path, gnss_chipset='BROADCOM'):
        """
        :param path: Path to the log file
        :param gnss_chipset: String indicating the smartphone's GNSS chipset manufacturer (broadcom or mediatek)
        """
        super().__init__()
        self.file = open(path, 'r')
        self.tow = None
        self.wn = None
        self.gnss_chipset = GnssChipset[gnss_chipset.upper()]

    def line_is_gal_inav(self, line):
        if not line[0] == AndroidGNSSLog.NAV_PREFIX:
            return False
        if not line[2] == AndroidGNSSLog.GAL_INAV_TYPE:
            return False
        if not line[3] == '1':
            return False
        return True

    def _get_formatted_bits(self, inav_line):
        str_bits = inav_line[6:]
        raw_bits = BitArray()
        for byte in str_bits:
            raw_bits += BitArray(int=byte, length=8)
        if self.gnss_chipset == GnssChipset.BROADCOM:
            data_format_bits = raw_bits[4:118] + BitArray('0b000000') + raw_bits[118:] + BitArray('0b000000')
        elif self.gnss_chipset == GnssChipset.MEDIATEK:
            data_format_bits = raw_bits[:114] + BitArray('0b000000') + raw_bits[114:-4] + BitArray('0b000000')
        else:
            raise Exception(f'Chipset {self.gnss_chipset} not supported.')
        return data_format_bits

    def get_GST_from_utc(self, utcmillis):
        utcmillis = int(utcmillis)
        utc_timestamp = datetime.datetime.utcfromtimestamp(round(utcmillis / 1000) + AndroidGNSSLog.LEAP_SECONDS)
        time_diff = utc_timestamp - AndroidGNSSLog.GST_START_EPOCH
        wn = time_diff.days // 7
        week_days = time_diff - datetime.timedelta(days=wn*7)
        tow = int(week_days.total_seconds())

        return wn, tow

    def _fix_1_second_misalignment(self, page):
        current_tow_offset = (self.tow-2)%30
        possible_page_offsets = PAGE_TOW_E1B_LOOKUP_TABLE[page]
        for possible_offset in possible_page_offsets:
            misalignment = current_tow_offset - possible_offset
            if abs(misalignment) == 1:
                self.tow = self.tow - misalignment
                return True
        return False

    def __next__(self):

        data_format = None
        while line := self.file.readline():
            line = line.strip().split(',')

            if line[0] in AndroidGNSSLog.UTC_TIME_LOGS:
                if line[1] is '':
                    continue
                wn, tow = self.get_GST_from_utc(line[1])
                self.wn = wn
                self.tow = tow
                continue

            if self.line_is_gal_inav(line):
                if self.tow is None:
                    continue
                svid = int(line[1])
                page = int(line[5])
                if (self.tow-2)%2 == 0:
                    # Lazy check for 1 second misalignment using the page structure. If not possible, remove page.
                    if not self._fix_1_second_misalignment(page):
                        continue

                data_format_bits = self._get_formatted_bits(line)
                data_format = DataFormat(svid, self.wn, self.tow-2, data_format_bits)
                break

        if data_format is None:
            raise StopIteration

        return data_format

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
