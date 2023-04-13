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

from ..structures.mack_structures import MACKMessage, Tag0AndSeq, TagAndInfo, TESLAKey
from ..structures.fields_information import field_info

from typing import List
from bitstring import BitArray

import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)

MACK_MSG_SIZE = field_info['MACK_MSG']['size']
TAG_INFO_SIZE = field_info['TAG_INFO']['size']
PRN_D_SIZE = field_info['PRN_D']['size']
ADKD_SIZE = field_info['ADKD']['size']
IOD_TAG_SIZE = field_info['IOD_TAG']['size']
MACSEQ_SIZE = field_info['MACSEQ']['size']
MACK_PAGE_SIZE = 32


class MACKMessageParser:
    """
    Updated version. Now there is only 1 MACK block per MACK message.
    """

    def __init__(self, tesla_chain):
        self.tesla_chain = tesla_chain
        self.chain_id = self.tesla_chain.chain_id
        self.key_size = self.tesla_chain.key_size
        self.tag_size = self.tesla_chain.tag_size
        self.num_tags = (MACK_MSG_SIZE - self.key_size) // (self.tag_size + TAG_INFO_SIZE)
        self.full_tag_size = self.tag_size + TAG_INFO_SIZE
        self.nma_status = None

    def _get_pages_and_slice(self, global_bit_start, size):

        page_start = global_bit_start // MACK_PAGE_SIZE
        page_bit_start = global_bit_start % MACK_PAGE_SIZE

        global_bit_end = global_bit_start + size
        page_end = global_bit_end // MACK_PAGE_SIZE
        if global_bit_end % MACK_PAGE_SIZE == 0:
            page_end = page_end - 1
        page_bit_end = page_bit_start + size

        return list(range(page_start, page_end + 1)), slice(page_bit_start, page_bit_end)

    def parse_mack_header(self, tag0_seq_msg, gst_sf, prn_a) -> Tag0AndSeq:
        tag0 = tag0_seq_msg[:self.tag_size]
        mac_seq = tag0_seq_msg[self.tag_size:self.tag_size + MACSEQ_SIZE]
        iod_tag = tag0_seq_msg[-IOD_TAG_SIZE:]
        tag0_seq = Tag0AndSeq(tag0, prn_a, iod_tag, gst_sf, mac_seq, self.nma_status)

        return tag0_seq

    def parse_complete_tag(self, complete_tag_message, gst_sf, prn_a, counter) -> TagAndInfo:

        tag = complete_tag_message[:self.tag_size]
        info = complete_tag_message[self.tag_size:]
        prn_d = info[:PRN_D_SIZE]
        adkd = info[PRN_D_SIZE:PRN_D_SIZE + ADKD_SIZE]
        iod_tag = info[-IOD_TAG_SIZE:]

        tag_and_info = TagAndInfo(tag, prn_d, adkd, iod_tag, gst_sf, prn_a, counter + 1, self.nma_status)

        return tag_and_info

    def parse_mack_message(self, mack_message: List[BitArray], gst_sf: BitArray, prn_a: int,
                           nma_status: BitArray) -> MACKMessage:

        self.nma_status = nma_status
        prn_a = BitArray(uint=prn_a, length=8)

        mack_msg_parsed = MACKMessage(gst_sf, self.chain_id, prn_a, self.num_tags)

        # Extract tags if we have the pages
        for nr_tag in range(self.num_tags):

            tag_pages, tag_slice = self._get_pages_and_slice(nr_tag*self.full_tag_size, self.full_tag_size)
            page_bits = BitArray()
            missing_pages = False

            for tag_page in tag_pages:
                if mack_message[tag_page] is None:
                    missing_pages = True
                    break
                page_bits.append(mack_message[tag_page])

            if missing_pages:
                mack_msg_parsed.add_tag(None)
                continue

            complete_tag_bits = page_bits[tag_slice]

            if nr_tag == 0:
                complete_tag = self.parse_mack_header(complete_tag_bits, gst_sf, prn_a)
                mack_msg_parsed.add_tag0(complete_tag)
            else:
                complete_tag = self.parse_complete_tag(complete_tag_bits, gst_sf, prn_a, nr_tag)
                mack_msg_parsed.add_tag(complete_tag)

        # check pages for tesla key
        key_pages, key_slice = self._get_pages_and_slice(self.full_tag_size * self.num_tags, self.key_size)
        key_pages_bits = BitArray()
        missing_key_pages = False
        for key_page in key_pages:
            if mack_message[key_page] is None:
                missing_key_pages = True
                break
            key_pages_bits.append(mack_message[key_page])

        if missing_key_pages:
            logger.info(f"Missing a page from the TESLA key")  # TODO: log info to TESLA key regenerated, not if not
        else:
            tesla_key_bits = key_pages_bits[key_slice]
            tesla_key = TESLAKey(gst_sf[:12], gst_sf[12:], tesla_key_bits, prn_a.uint, 1)  # TODO: remove nrblock to 1
            mack_msg_parsed.add_key(tesla_key)

        return mack_msg_parsed
