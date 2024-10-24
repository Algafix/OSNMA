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

######## type annotations ########
from typing import List, Optional, Dict
from bitstring import BitArray
from osnma.input_formats.base_classes import DataFormat, GAL_BAND


class Satellite:

    def __init__(self, svid: int = 0):
        """
        The satellite class encapsulates a Galileo satellite regarding OSNMA data. From each page received during a
        subframe stores the HKROOT and MACK message. At the end of a subframe, the HKROOT list is requested by
        the subframe regenerator and the MACK message is processed (partially if crc extraction is on).
        """
        self.svid = svid
        self.hkroot_subframe: List[Optional[BitArray]] = [None for _ in range(15)]
        self.mack_subframe: List[Optional[BitArray]] = [None for _ in range(15)]
        self.osnma_subframe: bool = False
        self.active_on_this_subframe: bool = False
        self.already_processed: bool = False
        self.pages_bits_log: Dict[GAL_BAND, List[Optional[str]]] = {
            GAL_BAND.E1B: [None for _ in range(15)],
            GAL_BAND.E5b: [None for _ in range(15)]
        }

    def _load_osnma(self, page: DataFormat, page_number: int):
        page_hkroot, page_mack = page.get_osnma()
        self.hkroot_subframe[page_number] = page_hkroot
        self.mack_subframe[page_number] = page_mack

    def reset(self):
        self.hkroot_subframe = [None for _ in range(15)]
        self.mack_subframe = [None for _ in range(15)]
        self.osnma_subframe = False
        self.active_on_this_subframe = False
        self.already_processed = False
        self.pages_bits_log = {
            GAL_BAND.E1B: [None for _ in range(15)],
            GAL_BAND.E5b: [None for _ in range(15)]
        }

    def is_already_processed(self):
        return self.already_processed

    def set_already_processed(self):
        self.already_processed = True

    def subframe_with_osnma(self) -> bool:
        return self.osnma_subframe

    def is_active(self) -> bool:
        return self.active_on_this_subframe

    def new_page(self, page: DataFormat):
        self.active_on_this_subframe = True
        self.osnma_subframe |= page.has_osnma

        gst_page = page.gst_page
        page_number = (gst_page.tow % 30) // 2
        if page.has_osnma:
            self._load_osnma(page, page_number)
        self.pages_bits_log[page.band][page_number] = page.nav_bits.hex

    def get_mack_subframe(self) -> List[Optional[BitArray]]:
        return self.mack_subframe

    def get_hkroot_subframe(self) -> List[Optional[BitArray]]:
        return self.hkroot_subframe
