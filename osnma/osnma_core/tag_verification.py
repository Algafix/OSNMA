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

from osnma.structures.mack_structures import MACKMessage, Tag0AndSeq, TagAndInfo, MACSeqObject
from osnma.structures.maclt import mac_lookup_table
from osnma.osnma_core.nav_data_manager import NavigationDataManager

from bitstring import BitArray

import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


def verify_maclt_slot(tag, slot):
    slot_adkd = int(slot[:2])
    slot_type = slot[2]

    slot_verified = False
    if slot_adkd == tag.adkd.uint:
        if slot_type == 'S' and tag.prn_a == tag.prn_d:
            slot_verified = True
        elif slot_type == 'E' and tag.prn_d.uint in range(1, 37):
            slot_verified = True
        elif slot_type in 'SE' and tag.prn_d.uint == 255:
            slot_verified = True
        elif slot_type == 'G' and tag.prn_d.uint in range(64, 96):
            slot_verified = True

    return slot_verified


class TagStateStructure:

    def __init__(self, tesla_chain, nav_data_m: NavigationDataManager):
        self.tesla_chain = tesla_chain
        self.nav_data_m = nav_data_m
        self.maclt_dict = mac_lookup_table[tesla_chain.maclt]
        self.macseq_awaiting_key = []
        self.tags_awaiting_key = []

    def _check_deprecated_data(self, tag, nav_data_block):
        # In case a satellite leaves sight but we still have data and receive cross-tags
        # If a tag fails the cross-authentication and the data is more than one subframe old, probably the data
        # has changed since our last recording from that satellite and therefore should not be used for future tags
        if tag.adkd.uint == 0 or tag.adkd.uint == 12:
            data_gst_sf = nav_data_block.last_gst_updated.uint//30 * 30
            if tag.gst_subframe.uint > data_gst_sf + 30:
                nav_data_block.gst_limit = BitArray(uint=tag.gst_subframe.uint-30, length=32)
                return True
        return False

    def verify_tag0(self, tag0: Tag0AndSeq, nav_data_block):

        nav_data = nav_data_block.nav_data_stream
        tesla_key = tag0.tesla_key
        auth_data = tag0.prn_a + tag0.gst_subframe + BitArray(uint=tag0.ctr, length=8) + tag0.nma_status + nav_data
        mac0 = self.tesla_chain.mac_function(tesla_key.key, auth_data)
        computed_tag0 = mac0[:self.tesla_chain.tag_size]

        if computed_tag0 == tag0.tag_value:
            logger.info(f"Tag AUTHENTICATED\n\t{tag0.get_log()}")
            self.nav_data_m.add_authenticated_tag(tag0)
        else:
            logger.error(f"Tag FAILED\n\t{tag0.get_log()}")

        self.tags_awaiting_key.remove(tag0)

    def verify_tag(self, tag: TagAndInfo, nav_data_block):

        # If PRN_D is 255, PRN_D is PRN_A for the formula.
        prn_d = tag.prn_a if tag.prn_d.uint == 255 else tag.prn_d

        nav_data = nav_data_block.nav_data_stream
        tesla_key = tag.tesla_key
        auth_data = prn_d + tag.prn_a + tag.gst_subframe + BitArray(uint=tag.ctr, length=8) + tag.nma_status \
            + nav_data
        mac = self.tesla_chain.mac_function(tesla_key.key, auth_data)
        computed_tag0 = mac[:self.tesla_chain.tag_size]

        if computed_tag0 == tag.tag_value:
            logger.info(f"Tag AUTHENTICATED\n\t{tag.get_log()}")
            self.nav_data_m.add_authenticated_tag(tag)
        else:
            if not self._check_deprecated_data(tag, nav_data_block):
                logger.error(f"Tag FAILED\n\t{tag.get_log()}")

        self.tags_awaiting_key.remove(tag)

    def verify_macseq(self, macseq: MACSeqObject):
        tesla_key = macseq.tesla_key
        auth_data = macseq.svid + macseq.gst
        for tag in macseq.flex_list:
            auth_data.append(tag.prn_d + tag.adkd + tag.iod_tag)

        computed_macseq = self.tesla_chain.mac_function(tesla_key.key, auth_data)[:12]
        if computed_macseq == macseq.macseq_value:
            self.set_tag_keys(macseq.flex_list)
            self.tags_awaiting_key.extend(macseq.flex_list)
            logger.info(f"MACSEQ AUTHENTICATED\n\t{macseq.get_log()}")
        else:
            logger.error(f"MACSEQ FAILED\n\t{macseq.get_log()}")

        self.macseq_awaiting_key.remove(macseq)

    def set_tag_keys(self, tag_list):

        for tag in tag_list:
            if tag.adkd.uint != 12:
                tag.key_id = self.tesla_chain.get_key_index(tag.gst_subframe, tag.mack_block) + 1
            else:
                subframe_id = self.tesla_chain.get_key_index(tag.gst_subframe, tag.mack_block)
                tag.key_id = subframe_id + 10 * self.tesla_chain.nmack + 1

    def set_macseq_key(self, macseq):
        macseq.key_id = self.tesla_chain.get_key_index(macseq.gst, 1) + 1

    def verify_maclt(self, mack_message: MACKMessage):
        # TODO: 2 functions for sections == 1 or 2

        tag_list = []
        flex_list = []

        if self.maclt_dict['sections'] == 1:
            sequence = self.maclt_dict["sequence"]
        elif self.maclt_dict['sections'] == 2:
            #sf_index = 1 if mack_message.gst_sf.uint % 60 else 0
            sf_index = 1 if mack_message.gst_sf[12:].uint % 60 else 0
            sequence = self.maclt_dict["sequence"][sf_index]
        else:
            raise ValueError(f"MACLT {self.tesla_chain.maclt} sections not 1 nor 2: {self.maclt_dict['sections']}")

        if self.maclt_dict['NMACK'] == 1:
            sequence = [sequence]

        for mack_block, maclt_block in zip(mack_message.mack_blocks, sequence):
            for tag, slot in zip(mack_block.tags, maclt_block):
                if slot != 'FLX':
                    if verify_maclt_slot(tag, slot):
                        tag_list.append(tag)
                    else:
                        logger.error(f"TAG - MACLT ERROR:\n\t{slot}\t{tag}\n")
                else:
                    flex_list.append(tag)

        macseq_object = mack_message.get_macseq(flex_list)

        return tag_list, macseq_object

    def add_tags_waiting_key(self, tag_list):

        for tag in tag_list:
            for tag_wait in list(self.tags_awaiting_key):
                if tag.id[:2] == tag_wait.id[:2] and (tag.id[2] != tag_wait.id[2] or tag.new_data):
                    # If the tag has data allocated but is waiting for the key, we keep it.
                    if self.nav_data_m.get_data(tag_wait.id, tag_wait.gst_subframe) is None:
                        self.tags_awaiting_key.remove(tag_wait)

            self.tags_awaiting_key.append(tag)

    def update_tag_lists(self):

        # Check for MACSEQ key to update tag list
        for macseq in list(self.macseq_awaiting_key):
            if self.tesla_chain.key_check(macseq):
                self.verify_macseq(macseq)

        # Check if any tags has key and data
        logger.info("Tag verification:\n")
        for tag in list(self.tags_awaiting_key):
            if self.tesla_chain.key_check(tag):
                # Has a verified key
                nav_data_block = self.nav_data_m.get_data(tag.id, tag.gst_subframe)
                if nav_data_block is not None:
                    if isinstance(tag, Tag0AndSeq):
                        self.verify_tag0(tag, nav_data_block)
                    else:
                        self.verify_tag(tag, nav_data_block)
                else:
                    # The key has arrived but no data: discard tag
                    self.tags_awaiting_key.remove(tag)

        # Check if any data can be authenticated
        logger.info(f"Data authenticated:\n")
        self.nav_data_m.authenticated_data()

    def load_mack_message(self, mack_message: MACKMessage):

        tag_list, macseq = self.verify_maclt(mack_message)
        self.set_tag_keys(tag_list)
        self.set_macseq_key(macseq)
        self.macseq_awaiting_key.append(macseq)
        self.add_tags_waiting_key(tag_list)


