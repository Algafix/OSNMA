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
from typing import TYPE_CHECKING, List, Optional, Dict, Tuple
if TYPE_CHECKING:
    from osnma.osnma_core.tesla_chain import TESLAChain
from osnma.structures.mack_structures import MACKMessage, TagAndInfo, MACSeqObject
from osnma.osnma_core.nav_data_manager import NavigationDataManager

######## imports ########
from osnma.structures.maclt import mac_lookup_table
from osnma.cryptographic.gst_class import GST
from osnma.utils.config import Config

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

    def verify_tag(self, tag: TagAndInfo):
        if tag.authenticate(self.tesla_chain.mac_function):
            logger.info(f"Tag AUTHENTICATED\n\t{tag.get_log()}")
            if not tag.is_dummy:
                self.nav_data_m.new_tag_verified(tag)
        else:
            logger.error(f"Tag FAILED\n\t{tag.get_log()}")
        self.tags_awaiting_key.remove(tag)

    def verify_macseq(self, macseq: MACSeqObject):
        if macseq.authenticate(self.tesla_chain.mac_function):
            self.set_key_index_to_tags(macseq.flex_list)
            self.tags_awaiting_key.extend(macseq.flex_list)
            logger.info(f"MACSEQ AUTHENTICATED\n\t{macseq.get_log()}")
        else:
            logger.error(f"MACSEQ FAILED\n\t{macseq.get_log()}")
        self.macseq_awaiting_key.remove(macseq)

    def set_key_index_to_tags(self, tag_list: List[TagAndInfo]):
        for tag in tag_list:
            if tag.adkd.uint != 12:
                tag.key_id = self.tesla_chain.get_key_index(tag.gst_subframe) + 1
            else:
                tag.key_id = self.tesla_chain.get_key_index(tag.gst_subframe) + 11

    def set_key_index_to_macseq(self, macseq: MACSeqObject):
        macseq.key_id = self.tesla_chain.get_key_index(macseq.gst) + 1

    def verify_maclt(self, mack_message: MACKMessage) \
            -> Tuple[List[TagAndInfo], List[TagAndInfo], MACSeqObject, bool, List[Optional[Dict]]]:

        tag_list = []
        flex_list = []
        tags_log = []

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
                    tag.is_flx = True
                    flex_list.append(tag)
            tags_log.append(tag if tag is None else tag.get_json())

        macseq_object = mack_message.get_macseq(flex_list)
        return tag_list, flex_list, macseq_object, is_flx_tag_missing, tags_log

    def _add_tags_waiting_key(self, tag_list: List[TagAndInfo]):
        """
        Adds the tags to the waiting for key list if the tag has an active ADKD and authenticates data of one of the
        valid satellites. The list of valid PRN_D is currently 1-36.
        """
        for tag in tag_list:
            if tag.adkd.uint not in Config.ACTIVE_ADKD:
                continue
            prn_d = tag.prn_d.uint
            if prn_d not in range(1, Config.NS+1):
                logger.warning(f"Tag {tag} authenticating a PRN_D not implemented.")
                continue
            self.tags_awaiting_key.append(tag)

    def _filter_tag_by_TL(self, tag) -> bool:
        """
        Filter a tag based on the TL value. If TL is greater than 30s, only ADKD12 can be verified. If TL is greater
        than 330s, no tag can be verified.
        """
        if Config.TL > 330:
            return True
        elif Config.TL > 30 and tag.adkd.uint != 12:
            return True
        else:
            return False

    def update_tag_lists(self, gst_subframe: GST):
        """
        Should be called every time a new TESLA key is provided.

        Authenticates the MACSEQ of that key and adds the tags to the list. Then authenticates all tags that have
        a valid TESLA key and for which data has been received. If no data has been received, delete the tag.

        Then informs the NavigationDataManager that new data might be authentic.
        """

        # Check for MACSEQ key to update tag list
        for macseq in list(self.macseq_awaiting_key):
            if self.tesla_chain.key_check(macseq):
                self.verify_macseq(macseq)

        # Check if any tags has key and data
        logger.info("Tag verification:\n")
        for tag in list(self.tags_awaiting_key):

            if self._filter_tag_by_TL(tag):
                self.tags_awaiting_key.remove(tag)
                continue

            if self.tesla_chain.key_check(tag):
                # Has a verified key
                tag.nav_data  = self.nav_data_m.get_data(tag)
                if tag.nav_data is not None:
                    self.verify_tag(tag)
                else:
                    # The key has arrived but no data: discard tag
                    self.tags_awaiting_key.remove(tag)

        # Check if any data can be authenticated
        self.nav_data_m.check_authenticated_data(gst_subframe)

    def load_mack_message(self, mack_message: MACKMessage) -> List[Optional[Dict]]:
        tag_list, flex_list, macseq, is_flx_tag_missing, tags_log = self.verify_maclt(mack_message)
        self.set_key_index_to_tags(tag_list)
        if macseq and not is_flx_tag_missing:
            self.set_key_index_to_macseq(macseq)
            self.macseq_awaiting_key.append(macseq)
        logger.info(f"Non-FLX tags in MACK:\t{tag_list}\n")
        logger.info(f"FLX tags in MACK:\t{flex_list}\n")
        self._add_tags_waiting_key(tag_list)
        return tags_log
