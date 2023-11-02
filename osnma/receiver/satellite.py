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
from typing import List, Optional

from osnma.input_formats.base_classes import DataFormat


class Satellite:

    def __init__(self, svid=0):
        self.svid: int = svid
        self.hkroot_subframe: List[Optional[BitArray]] = [None for _ in range(15)]
        self.mack_subframe: List[Optional[BitArray]] = [None for _ in range(15)]
        self.osnma_subframe: bool = False
        self.subframe_start_gst: int = 0

    def _load_osnma(self, page: DataFormat, page_number: int):
        if page.has_osnma:
            page_hkroot, page_mack = page.get_osnma()
            self.hkroot_subframe[page_number] = page_hkroot
            self.mack_subframe[page_number] = page_mack

    def _new_subframe(self, page: DataFormat, page_number: int):

        self.hkroot_subframe = [None for _ in range(15)]
        self.mack_subframe = [None for _ in range(15)]

        if page.has_osnma:
            self.osnma_subframe = True
            self._load_osnma(page, page_number)
        else:
            self.osnma_subframe = False

    def _check_sync(self, gst_page: int):
        return True if self.subframe_start_gst + 30 > gst_page else False

    def _update_sync(self, gst_uint: int, page_number: int):
        gst_page_start = gst_uint - (page_number * 2)
        self.subframe_start_gst = gst_page_start

    def subframe_with_osnma(self) -> bool:
        return self.osnma_subframe

    def new_page(self, page: DataFormat, gst_uint: int):

        page_number = (gst_uint % 30) // 2

        if not self._check_sync(gst_uint):
            # New subframe, update sync and save
            self._update_sync(gst_uint, page_number)
            self._new_subframe(page, page_number)
        elif self.osnma_subframe:
            # Current subframe, save
            self._load_osnma(page, page_number)

    def get_mack_subframe(self) -> List[Optional[BitArray]]:
        return self.mack_subframe

    def get_hkroot_subframe(self) -> List[Optional[BitArray]]:
        return self.hkroot_subframe
