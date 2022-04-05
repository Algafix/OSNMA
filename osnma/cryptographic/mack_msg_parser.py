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

from ..structures.mack_structures import MACKMessage, MACKHeaderBlock, MACKBlock, Tag0AndSeq, TagAndInfo, TESLAKey
from ..structures.fields_information import field_info

from bitstring import BitArray

MACK_MSG_SIZE = field_info['MACK_MSG']['size']
TAG_INFO_SIZE = field_info['TAG_INFO']['size']
PRN_D_SIZE = field_info['PRN_D']['size']
ADKD_SIZE = field_info['ADKD']['size']
IOD_TAG_SIZE = field_info['IOD_TAG']['size']
MACSEQ_SIZE = field_info['MACSEQ']['size']


class MACKMessageParser:

    def __init__(self, tesla_chain):
        self.tesla_chain = tesla_chain
        self.chain_id = self.tesla_chain.chain_id
        self.key_size = self.tesla_chain.key_size
        self.tag_size = self.tesla_chain.tag_size
        self.num_mack = self.tesla_chain.nmack
        self.num_tags = ((MACK_MSG_SIZE//self.num_mack) - self.key_size) // (self.tag_size + TAG_INFO_SIZE)
        self.block_size = MACK_MSG_SIZE//self.num_mack
        self.nma_status = None

    def parse_mack_header(self, tag0_seq_msg, gst_sf, prn_a):
        tag0 = tag0_seq_msg[:self.tag_size]
        mac_seq = tag0_seq_msg[self.tag_size:self.tag_size + MACSEQ_SIZE]
        iod_tag = tag0_seq_msg[-IOD_TAG_SIZE:]
        tag0_seq = Tag0AndSeq(tag0, prn_a, iod_tag, gst_sf, mac_seq, self.nma_status)

        return tag0_seq

    def parse_complete_tag(self, complete_tag_message, gst_sf, prn_a, counter, mack_block):

        tag = complete_tag_message[:self.tag_size]
        info = complete_tag_message[self.tag_size:]
        prn_d = info[:PRN_D_SIZE]
        adkd = info[PRN_D_SIZE:PRN_D_SIZE+ADKD_SIZE]
        iod_tag = info[-IOD_TAG_SIZE:]

        tag_and_info = TagAndInfo(tag, prn_d, adkd, iod_tag, gst_sf, prn_a, counter, mack_block, self.nma_status)

        return tag_and_info

    def parse_first_block(self, mack_block_msg, gst_sf: BitArray, prn_a: int):

        # Return object
        mack_header_block = MACKHeaderBlock(self.num_tags)

        complete_tag_size = self.tag_size + TAG_INFO_SIZE
        total_tags_size = complete_tag_size*self.num_tags

        # Split messages
        mack_header_msg = mack_block_msg[:complete_tag_size]
        tags_info_msg = mack_block_msg[complete_tag_size: total_tags_size]
        key_msg = mack_block_msg[total_tags_size: total_tags_size + self.key_size]

        # Parse header tag
        tag0_seq = self.parse_mack_header(mack_header_msg, gst_sf, prn_a)
        mack_header_block.add_tag(tag0_seq)

        # Parse rest of tags. Range start in 0 and ends in value-1, but we already parsed the first tag so subtract 1.
        # The counter in the MAC starts at 1 so we have to increase it by 2 when calling the function.
        for i in range(self.num_tags-1):
            complete_tag_msg = tags_info_msg[i*complete_tag_size: (i+1)*complete_tag_size]
            tag_and_info = self.parse_complete_tag(complete_tag_msg, gst_sf, prn_a, i+2, 1)
            mack_header_block.add_tag(tag_and_info)

        # Parse key
        tesla_key = TESLAKey(gst_sf[:12], gst_sf[12:], key_msg, prn_a, 1)
        mack_header_block.add_key(tesla_key)

        return mack_header_block

    def parse_block(self, mack_block_msg, gst_sf, prn_a, block_index):
        # Return object
        mack_block = MACKBlock(block_index, self.num_tags)

        complete_tag_size = self.tag_size + TAG_INFO_SIZE
        total_tags_size = complete_tag_size * self.num_tags

        # Split messages
        tags_info_msg = mack_block_msg[:total_tags_size]
        key_msg = mack_block_msg[total_tags_size: total_tags_size + self.key_size]

        # Parse tags. Range start in 0 and ends in value-1,
        for i in range(self.num_tags):
            complete_tag_msg = tags_info_msg[i * complete_tag_size: (i + 1) * complete_tag_size]
            tag_and_info = self.parse_complete_tag(complete_tag_msg, gst_sf, prn_a, i + 1, block_index)
            mack_block.add_tag(tag_and_info)

        # Parse key
        tesla_key = TESLAKey(gst_sf[:12], gst_sf[12:], key_msg, prn_a, block_index)
        mack_block.add_key(tesla_key)

        return mack_block

    def parse_mack_message(self, mack_message: BitArray, gst_sf: BitArray, prn_a: int, nma_status: BitArray) \
            -> MACKMessage:

        self.nma_status = nma_status

        mack_msg_parsed = MACKMessage(gst_sf, self.chain_id, self.num_mack, prn_a)

        for block_index in range(1, self.num_mack+1):
            mack_block = mack_message[(block_index-1)*self.block_size: block_index*self.block_size]

            if block_index == 1:
                mack_block = self.parse_first_block(mack_block, gst_sf, prn_a)
            else:
                mack_block = self.parse_block(mack_block, gst_sf, prn_a, block_index)

            mack_msg_parsed.add_mack_block(mack_block)

        return mack_msg_parsed
