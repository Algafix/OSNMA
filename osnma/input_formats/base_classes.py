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

from bitstring import BitArray


class DataFormat:
    """
    Object that encapsulates an I/NAV full page together with the GNSS time of transmission and the SVID of the satellite.
    """
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
        "240 bits of the full page (even and odd concatenated)"
        self.svid = svid
        "Space Vehicle (Satellite) ID"
        self.wn = wn
        "Week number in Galileo Time"
        self.tow = tow
        "Time of week of transmission"
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


class PageIterator:
    """
    Abstract class to be implemented by any input format
    """
    def __init__(self):
        pass

    def __iter__(self) -> 'PageIterator':
        return self

    def __next__(self) -> 'DataFormat':
        pass
