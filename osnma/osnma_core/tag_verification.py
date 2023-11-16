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
from typing import TYPE_CHECKING, List, Union
if TYPE_CHECKING:
    from osnma.osnma_core.tesla_chain import TESLAChain
from osnma.structures.mack_structures import MACKMessage, TagAndInfo, MACSeqObject
from osnma.osnma_core.nav_data_manager import NavigationDataManager, ADKD0DataBlock, ADKD4DataBlock

######## imports ########
from osnma.structures.maclt import mac_lookup_table
from osnma.cryptographic.gst_class import GST
from osnma.utils.config import Config

from bitstring import BitArray

######## logger ########
import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


def verify_maclt_slot(tag: TagAndInfo, slot: str):
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

    def __init__(self, tesla_chain: 'TESLAChain', nav_data_m: NavigationDataManager):
        self.tesla_chain = tesla_chain
        self.nav_data_m = nav_data_m
        self.maclt_dict = mac_lookup_table[tesla_chain.maclt]
        self.macseq_awaiting_key: List[MACSeqObject] = []
        self.tags_awaiting_key: List[TagAndInfo] = []

    def _check_deprecated_data(self, tag: TagAndInfo, nav_data_block: Union[ADKD0DataBlock, ADKD4DataBlock]):
        # In case a satellite leaves sight but we still have data and receive cross-tags
        # If a tag fails the cross-authentication and the data is more than one subframe old, probably the data
        # has changed since our last recording from that satellite and therefore should not be used for future tags
        if tag.adkd.uint == 0 or tag.adkd.uint == 12:
            data_gst_sf = nav_data_block.last_gst_updated // 30 * 30
            if tag.gst_subframe > data_gst_sf + 30:
                nav_data_block.gst_limit = tag.gst_subframe - 30
                return True
        return False

    def verify_tag(self, tag: TagAndInfo, nav_data_block: Union[ADKD0DataBlock, ADKD4DataBlock]):
        nav_data = nav_data_block.nav_data_stream
        if tag.is_tag0:
            auth_data = tag.prn_a + tag.gst_subframe.bitarray + BitArray(uint=tag.ctr, length=8) + tag.nma_status + nav_data
        else:
            auth_data = tag.prn_d + tag.prn_a + tag.gst_subframe.bitarray + BitArray(uint=tag.ctr, length=8) + tag.nma_status + nav_data

        mac = self.tesla_chain.mac_function(tag.tesla_key.key, auth_data)
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
        auth_data = macseq.svid + macseq.gst.bitarray
        for tag in macseq.flex_list:
            auth_data.append(tag.prn_d + tag.adkd + tag.cop)

        computed_macseq = self.tesla_chain.mac_function(tesla_key.key, auth_data)[:12]
        if computed_macseq == macseq.macseq_value:
            self.set_tag_keys(macseq.flex_list)
            self.tags_awaiting_key.extend(macseq.flex_list)
            logger.info(f"MACSEQ AUTHENTICATED\n\t{macseq.get_log()}")
        else:
            logger.error(f"MACSEQ FAILED\n\t{macseq.get_log()}")

        self.macseq_awaiting_key.remove(macseq)

    def set_tag_keys(self, tag_list: List[TagAndInfo]):

        for tag in tag_list:
            if tag.adkd.uint != 12:
                tag.key_id = self.tesla_chain.get_key_index(tag.gst_subframe) + 1
            else:
                subframe_id = self.tesla_chain.get_key_index(tag.gst_subframe)
                tag.key_id = subframe_id + 10 * self.tesla_chain.nmack + 1

    def set_macseq_key(self, macseq: MACSeqObject):
        macseq.key_id = self.tesla_chain.get_key_index(macseq.gst) + 1

    def verify_maclt(self, mack_message: MACKMessage) -> (List[TagAndInfo], MACSeqObject, bool):

        tag_list = []
        flex_list = []

        if self.maclt_dict['sections'] == 1:
            sequence = self.maclt_dict["sequence"]
        elif self.maclt_dict['sections'] == 2:
            sf_index = 1 if mack_message.gst_sf.tow % 60 else 0
            sequence = self.maclt_dict["sequence"][sf_index]
        else:
            raise ValueError(f"MACLT {self.tesla_chain.maclt} sections not 1 nor 2: {self.maclt_dict['sections']}")

        if self.maclt_dict['NMACK'] != 1:
            logger.critical(f"MACLT number {self.maclt_dict['ID']} NOT SUPPORTED. With the new ICD only 1 MACK block"
                            f"per MACK message is supported")
            exit(1)

        is_flx_tag_missing = False

        for tag, slot in zip(mack_message.tags, sequence):
            if slot != 'FLX':
                if tag is not None:
                    if verify_maclt_slot(tag, slot):
                        tag_list.append(tag)
                    else:
                        logger.error(f"TAG - MACLT ERROR:\n\t{slot}\t{tag}\n")
            else:
                if tag is None:
                    is_flx_tag_missing = True
                else:
                    flex_list.append(tag)

        macseq_object = mack_message.get_macseq(flex_list)

        return tag_list, macseq_object, is_flx_tag_missing

    def add_tags_waiting_key(self, tag_list: List[TagAndInfo]):
        """
        Adds the tags to the waiting for key list if the tag has an active ADKD and authenticates data of one of the
        valid satellites. The list of valid PRN_D is currently 1-36 and 255 for ADKD4 (this changes in ICD-1.0).
        """
        logger.info(f"Non-FLX tags in MACK:\t{tag_list}\n")
        for tag in tag_list:
            if tag.adkd.uint not in Config.ACTIVE_ADKD:
                continue
            prn_d = tag.prn_d.uint
            if prn_d != 255 and prn_d not in range(1, Config.NS+1):
                logger.warning(f"Tag {tag} authenticating a PRN_D not implemented.")
                continue
            self.tags_awaiting_key.append(tag)

    def update_tag_lists(self, gst_subframe: GST):

        # Check for MACSEQ key to update tag list
        for macseq in list(self.macseq_awaiting_key):
            if self.tesla_chain.key_check(macseq):
                self.verify_macseq(macseq)

        # Check if any tags has key and data
        logger.info("Tag verification:\n")
        for tag in list(self.tags_awaiting_key):
            if self.tesla_chain.key_check(tag):
                # Has a verified key
                nav_data_block = self.nav_data_m.get_data(tag)
                if nav_data_block is not None:
                    self.verify_tag(tag, nav_data_block)
                else:
                    # The key has arrived but no data: discard tag
                    # logger.critical(f"No data when key arrive: {tag}")
                    self.tags_awaiting_key.remove(tag)

        # Check if any data can be authenticated
        logger.info(f"Data authenticated:\n")
        self.nav_data_m.authenticated_data(gst_subframe)

    def load_mack_message(self, mack_message: MACKMessage):

        tag_list, macseq, is_flx_tag_missing = self.verify_maclt(mack_message)
        self.set_tag_keys(tag_list)
        if macseq and not is_flx_tag_missing:
            self.set_macseq_key(macseq)
            self.macseq_awaiting_key.append(macseq)
        self.add_tags_waiting_key(tag_list)
