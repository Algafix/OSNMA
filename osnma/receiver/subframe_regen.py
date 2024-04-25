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
from typing import List, Optional, Union, Dict, Tuple

######## imports ########
from bitstring import BitArray
from osnma.structures.fields_information import NB_DK_lt, NB_DP_lt
from osnma.cryptographic.gst_class import GST

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)


DSM_HEADER = 1
DSM_NUMBER_OF_BLOCKS_PAGE = 2
DSM_NUMBER_OF_BLOCKS_FIELD = slice(0, 4)
DSM_BLOCK_ID = slice(4, 8)
DSM_ID = slice(0, 4)


class SubFrameRegenerator:

    def __init__(self):
        self.dsm_id: Optional[int] = None
        self.bid_ref: Optional[int] = None
        self.svid_ref: Optional[int] = None
        self.gst_ref: Optional[GST] = None
        self.num_blocks: Optional[int] = None
        self.num_blocks_lookup_table: List[Union[str, int]] = []
        self.block_dict: Dict[int, List[BitArray]] = {}

    def _get_dsm_lookup_table(self, dsm_id: int):
        return NB_DK_lt if dsm_id < 12 else NB_DP_lt

    def _is_block_complete(self, block: List[BitArray]):
        full_block = BitArray().join([array for array in block if array is not None])
        return full_block if len(full_block) == 120 else False

    def _save_block(self, new_block: List[BitArray], bid: int):
        saved_block = self.block_dict.get(bid)
        if saved_block is None:
            self.block_dict[bid] = new_block
        else:
            for index, (new_page, saved_page) in enumerate(zip(new_block, saved_block)):
                if saved_page is None and new_page is not None:
                    saved_block[index] = new_page

    def _update_references(self, dsm_id, block_id, gst_subframe: GST, svid):
        self.dsm_id = dsm_id
        self.bid_ref = block_id
        self.svid_ref = svid
        self.gst_ref = gst_subframe
        self.num_blocks_lookup_table = self._get_dsm_lookup_table(dsm_id)
        self.num_blocks = None
        self.block_dict = {}

    def get_regenerated_blocks(self) -> List[Tuple[BitArray, int]]:
        complete_blocks = []
        for bid, block in dict(self.block_dict).items():
            if full_block := self._is_block_complete(block):
                complete_blocks.append((full_block, bid))
                self.block_dict.pop(bid)
        return complete_blocks

    def load_dsm_block(self, hkroot_subframe: List[Optional[BitArray]], gst_subframe: GST, svid: int) -> Union[BitArray, bool]:

        block_id: Optional[int] = None
        # Get block_id from DSM Header
        if hkroot_subframe[DSM_HEADER] is not None:
            block_id = hkroot_subframe[DSM_HEADER][DSM_BLOCK_ID].uint
            dsm_id = hkroot_subframe[DSM_HEADER][DSM_ID].uint
            if dsm_id != self.dsm_id:
                self._update_references(dsm_id, block_id, gst_subframe, svid)
        # Get block_id from inferring
        # TODO

        # Get the number of blocks for the DSM message if the block id is 0 and it has the third page
        # TODO: do it after reconstructing
        if block_id == 0 and hkroot_subframe[DSM_NUMBER_OF_BLOCKS_PAGE] is not None:
            #logger.warning(hkroot_subframe)
            raw_number_of_blocs = hkroot_subframe[DSM_NUMBER_OF_BLOCKS_PAGE][DSM_NUMBER_OF_BLOCKS_FIELD].uint
            self.num_blocks = self.num_blocks_lookup_table[raw_number_of_blocs]

        complete_block = self._is_block_complete(hkroot_subframe)
        if not complete_block and block_id is not None:
            self._save_block(hkroot_subframe, block_id)

        return complete_block
