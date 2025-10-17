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

######## imports ########
from enum import Enum, IntEnum
from bitstring import BitArray

from osnma.structures.fields_information import NB_DK_lt, NB_DP_lt

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)


class HKROOT(IntEnum):
    NMA_HEADER_END = 8
    DSM_ID_START = 8
    DSM_ID_END = 12
    BID_START = 12
    BID_END = 16
    DATA_START = 16
    NB_START = 16
    NB_END = 20

class DSMType(Enum):
    DSM_PKR = 0
    DSM_KROOT = 1


class DigitalSignatureMessage:

    def __init__(self, dsm_id: int):
        self.blocks_received: dict[int, BitArray] = {}
        self.total_of_blocks: int | None = None
        self.dsm_id = dsm_id
        self.dsm_type = DSMType.DSM_KROOT if dsm_id < 12 else DSMType.DSM_PKR
        self.blocks_lt = NB_DK_lt if self.dsm_id < 12 else NB_DP_lt

    def load_dsm_subframe(self, dsm_subframe: BitArray):

        bid = dsm_subframe[HKROOT.BID_START:HKROOT.BID_END].uint
        self.blocks_received[bid] = dsm_subframe[HKROOT.DATA_START:]

        if bid == 0:
            number_of_blocks_field = dsm_subframe[HKROOT.NB_START:HKROOT.NB_END].uint
            self.total_of_blocks = self.blocks_lt[number_of_blocks_field]

        logger.info(f"Received block {bid} for DSM ID {self.dsm_id}.")
        logger.info(f"DSM ID {self.dsm_id} blocks "
                    f"({len(self.blocks_received)}/{'?' if self.total_of_blocks is None else self.total_of_blocks}): "
                    f"{sorted(self.blocks_received.keys())}\n")

    def is_complete(self) -> bool:
        return len(self.blocks_received) == self.total_of_blocks

    def reset_dsm(self):
        self.blocks_received = {}
        self.total_of_blocks = None

    def get_message(self) -> BitArray:
        hkroot_data = BitArray()
        for i in range(self.total_of_blocks):
            hkroot_data += self.blocks_received[i]
        self.reset_dsm()
        return hkroot_data

class DigitalSignatureMessageManager:

    def __init__(self):
        self.dsm_messages: dict[int, DigitalSignatureMessage] = {i:DigitalSignatureMessage(i) for i in range(16)}
        self.last_dsm_kroot_ids = []
        self.last_dsm_pkr_ids = []

    def _purge_old_dsm(self, dsm_id: int):
        if dsm_id < 12:
            last_dsm_ids = self.last_dsm_kroot_ids
        else:
            last_dsm_ids = self.last_dsm_pkr_ids

        if dsm_id not in last_dsm_ids:
            last_dsm_ids.append(dsm_id)

        if len(last_dsm_ids) > 2:
            reset_index = last_dsm_ids.pop(0)
            self.dsm_messages[reset_index].reset_dsm()

    def new_dsm_subframe(self, hkroot_sf: BitArray):
        nma_header = hkroot_sf[:HKROOT.NMA_HEADER_END]
        dsm_id = hkroot_sf[HKROOT.DSM_ID_START:HKROOT.DSM_ID_END].uint
        self._purge_old_dsm(dsm_id)

        dsm = self.dsm_messages[dsm_id]
        dsm.load_dsm_subframe(hkroot_sf)

        return nma_header, dsm
