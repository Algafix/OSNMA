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
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from osnma.osnma_core.tesla_chain import TESLAChain

######## imports ########
from ..structures.mack_structures import MACKMessage, Tag0AndSeq, TagAndInfo, TESLAKey
from ..structures.fields_information import field_info
from ..utils.config import Config
from osnma.cryptographic.gst_class import GST

from bitstring import BitArray

######## logger ########
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

    def __init__(self, tesla_chain: 'TESLAChain'):
        self.tesla_chain = tesla_chain
        self.chain_id = self.tesla_chain.chain_id
        self.key_size = self.tesla_chain.key_size
        self.tag_size = self.tesla_chain.tag_size
        self.num_tags = (MACK_MSG_SIZE - self.key_size) // (self.tag_size + TAG_INFO_SIZE)
        self.full_tag_size = self.tag_size + TAG_INFO_SIZE
        self.tesla_key_gst_start_offset = ((self.full_tag_size * self.num_tags) // MACK_PAGE_SIZE)*2+1
        self.nma_status = None

        self.gst_sf_reconstructed_tesla = GST()
        self.pages_reconstructed_tesla = []
        self.sf_with_TK_reconstructed = False

    def _get_pages_and_slice(self, global_bit_start, size):

        page_start = global_bit_start // MACK_PAGE_SIZE
        page_bit_start = global_bit_start % MACK_PAGE_SIZE

        global_bit_end = global_bit_start + size
        page_end = global_bit_end // MACK_PAGE_SIZE
        if global_bit_end % MACK_PAGE_SIZE == 0:
            page_end = page_end - 1
        page_bit_end = page_bit_start + size

        return slice(page_start, page_end+1), slice(page_bit_start, page_bit_end)

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

    def extract_from_mack_message(self, key_pages):
        key_pages_bits = BitArray()
        missing_key_pages = False
        for key_page in key_pages:
            if key_page is None:
                missing_key_pages = True
                break
            key_pages_bits.append(key_page)
        return key_pages_bits, missing_key_pages

    def parse_mack_message(self, mack_message: list[BitArray], gst_sf: GST, prn_a: int,
                           nma_status: BitArray) -> MACKMessage:

        self.nma_status = nma_status
        prn_a = BitArray(uint=prn_a, length=8)

        mack_msg_parsed = MACKMessage(gst_sf, self.chain_id, prn_a, self.num_tags)

        # TAGS
        for nr_tag in range(self.num_tags):

            tag_pages_slice, tag_bit_slice = self._get_pages_and_slice(nr_tag*self.full_tag_size, self.full_tag_size)
            page_bits, missing_pages = self.extract_from_mack_message(mack_message[tag_pages_slice])

            if missing_pages:
                mack_msg_parsed.add_tag(None)
                continue
            complete_tag_bits = page_bits[tag_bit_slice]

            if nr_tag == 0:
                complete_tag = self.parse_mack_header(complete_tag_bits, gst_sf, prn_a)
                mack_msg_parsed.add_tag0(complete_tag)
            else:
                complete_tag = self.parse_complete_tag(complete_tag_bits, gst_sf, prn_a, nr_tag)
                mack_msg_parsed.add_tag(complete_tag)

        # TESLA KEY
        reconstructed = False
        key_pages_slice, key_bit_slice = self._get_pages_and_slice(self.full_tag_size * self.num_tags, self.key_size)

        key_pages_bits, missing_key_pages = self.extract_from_mack_message(mack_message[key_pages_slice])
        if missing_key_pages and Config.DO_TESLA_KEY_REGEN:
            if gst_sf != self.gst_sf_reconstructed_tesla:
                # Start new saved key
                self.gst_sf_reconstructed_tesla = gst_sf
                self.pages_reconstructed_tesla = mack_message[key_pages_slice]
                self.sf_with_TK_reconstructed = False
            elif not self.sf_with_TK_reconstructed:
                # Update saved list
                for i, (saved_page, new_page) in enumerate(zip(self.pages_reconstructed_tesla, mack_message[key_pages_slice])):
                    if saved_page is None and new_page is not None:
                        self.pages_reconstructed_tesla[i] = new_page
                # Check again if we are complete
                key_pages_bits, missing_key_pages = self.extract_from_mack_message(self.pages_reconstructed_tesla)
                reconstructed = True
                self.sf_with_TK_reconstructed = not missing_key_pages

        if not missing_key_pages:
            tesla_key_bits = key_pages_bits[key_bit_slice]
            tesla_key_gst_page_start = gst_sf + self.tesla_key_gst_start_offset
            tesla_key = TESLAKey(gst_sf, tesla_key_bits, prn_a.uint, gst_start=tesla_key_gst_page_start, reconstructed=reconstructed)
            mack_msg_parsed.add_key(tesla_key)

        return mack_msg_parsed
