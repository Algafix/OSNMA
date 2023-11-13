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
import copy

from osnma.structures.adkd import adkd_masks
from osnma.structures.mack_structures import TagAndInfo

from bitstring import BitArray
from typing import List, Dict, Tuple, Optional

from osnma.utils.config import Config
import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


ADKD0 = 0
ADKD4 = 4
ADKD12 = 12
ADKD5 = 5


class TagAccumulation:

    words_per_adkd = {0: [1, 2, 3, 4, 5],
                      12: [1, 2, 3, 4, 5],
                      4: [6, 10],
                      5: []}

    auth_message = 'AUTHENTICATED: ADKD {adkd} - Satellite {satellite} {iod} ' \
                   '\n\t\t GST SF {gst_start}  to  GST SF {gst_last} ' \
                   '\n\t\t {words} \n'

    def __init__(self, tag: TagAndInfo, iod: Optional[BitArray] = None):
        self.acc_length = len(tag.tag_value)
        self.start_gst = (tag.gst_subframe[:12].uint, tag.gst_subframe[12:].uint)
        self.last_gst = self.start_gst
        self.iod = iod
        self.new_tags = True
        self.log_message = self._generate_message(tag.adkd.uint, tag.prn_d.uint, iod)
        self.prn_d = tag.prn_d.uint
        self.adkd = tag.adkd.uint

    def _generate_message(self, adkd: int, prn_d: int, iod: BitArray) -> str:
        if iod is None:
            iod_message = ""
        else:
            iod_message = f"- IOD {self.iod}"

        satellite_message = prn_d if prn_d != 255 else "Any"

        words_message = "Words "
        for word in self.words_per_adkd[adkd]:
            words_message += f"{word}, "
        words_message = words_message[:-2]

        auth_message = self.auth_message.format(adkd=adkd, satellite=satellite_message,
                                                iod=iod_message, words=words_message,
                                                gst_start='{gst_start}', gst_last='{gst_last}')
        return auth_message

    def add_tag(self, tag: TagAndInfo):
        self.acc_length += len(tag.tag_value)
        self.last_gst = (tag.gst_subframe[:12].uint, tag.gst_subframe[12:].uint)
        self.new_tags = True

    def log_authenticated(self):
        gst_start = f"{self.start_gst[0]}-{self.start_gst[1]}"
        gst_last = f"{self.last_gst[0]}-{self.last_gst[1]}"
        logger.info(self.log_message.format(gst_start=gst_start, gst_last=gst_last))

    def __repr__(self):
        return f"{{acc_length: {self.acc_length}, start_gst: [{self.start_gst[0]}, {self.start_gst[1]}], " \
               f"last_gst: [{self.last_gst[0]}, {self.last_gst[1]}], iod: {self.iod}, new_tags: {self.new_tags}}}"


class ADKDDataManager:
    ADKD_MASKS = adkd_masks

    def __init__(self, adkd: int):
        self.adkd = adkd

    def _get_adkd_data_from_word(self, full_page: BitArray, word_type: int):
        data_mask = self.ADKD_MASKS[self.adkd]['adkd'][word_type]['bits']

        adkd_word_data = BitArray()
        for bit_block in data_mask:
            adkd_word_data.append(full_page[bit_block[0]: bit_block[1]])

        return adkd_word_data

    def add_word(self, word_type: int, data: BitArray, gst_page: BitArray):
        pass

    def tag_has_data(self, tag: TagAndInfo) -> bool:
        pass

    def get_nav_data(self, tag: TagAndInfo):
        pass


class ADKD0DataBlock:

    def __init__(self, gst_start: BitArray):
        self.gst_start = gst_start
        self.iod: Optional[BitArray] = None
        self.words: Dict[int, BitArray] = {}
        self.nav_data_stream: Optional[BitArray] = None
        self.gst_limit = BitArray('0xffffffff')
        self.last_gst_updated = gst_start
        self.gst_completed = BitArray()

    def __repr__(self):

        gst_completed_msg = ''
        if self.gst_completed:
            gst_completed_msg = f" gst_completed: {self.gst_completed[:12].uint} - {self.gst_completed[12:].uint},"

        msg = f"gst_start: {self.gst_start[:12].uint} - {self.gst_start[12:].uint}, iod: {self.iod}," \
               f" words: {self.words}\n\t last_gst_updated: {self.last_gst_updated[:12].uint} - " \
               f"{self.last_gst_updated[12:].uint},{gst_completed_msg} gst_limit: {self.gst_limit}\n\t"

        return msg

    def add_word(self, word_type: int, data: BitArray, gst_page: BitArray):
        self.last_gst_updated = gst_page
        if word_type != 5:
            self.iod = data[:10]
        self.words[word_type] = data
        if not self.gst_completed and len(self.words) == 5:
            self.gst_completed = gst_page

    def get_word(self, word_type: int) -> Optional[BitArray]:
        return self.words.get(word_type)

    def _compute_data_stream(self):
        data_stream = BitArray()
        for i in range(1, 6):
            data_stream.append(self.words[i])
        self.nav_data_stream = data_stream

    def get_nav_data(self) -> Optional['ADKD0DataBlock']:
        if len(self.words) != 5:
            return None
        else:
            self._compute_data_stream()
        return self


class ADKD0DataManager(ADKDDataManager):

    def __init__(self, svid: int):
        super().__init__(ADKD0)
        self.svid = svid
        self.adkd0_data_blocks: List[ADKD0DataBlock] = []

    def __repr__(self):
        return f"\n\t{self.adkd0_data_blocks}\n"

    def _iod_unambiguous(self, gst_page: BitArray) -> bool:
        """
        Checks if we have received a Word Type with IOD during this subframe so the Word Type 5 can be linked.
        self.adkd0_data_blocks must not be empty
        """
        last_adkd0_block = self.adkd0_data_blocks[-1]
        if last_adkd0_block.last_gst_updated.uint - gst_page.uint < 30:
            return True
        return False

    def _is_new_adkd0_data_block(self, iod: BitArray) -> bool:
        return len(self.adkd0_data_blocks) == 0 or self.adkd0_data_blocks[-1].iod != iod

    def _clean_old_data(self):
        """
        If a data block has no gst_completed value and there is new data in the list, we can delete the old data because
        it will never complete.
        """
        previous_block_not_complete = False
        for idx, data_block in enumerate(list(self.adkd0_data_blocks)):
            if previous_block_not_complete:
                self.adkd0_data_blocks.pop(idx-1)
            if not data_block.gst_completed:
                previous_block_not_complete = True


    def _handle_word_type_5(self, word_5_data: BitArray, gst_page: BitArray):
        if len(self.adkd0_data_blocks) == 0:
            # Not initialized, cant link WT5
            return

        if not self._iod_unambiguous(gst_page):
            # Cant ensure WT5 belongs to this data IOD
            return

        last_adkd0_block = self.adkd0_data_blocks[-1]
        last_word_type_5 = last_adkd0_block.get_word(5)

        if last_word_type_5 is None:
            self.adkd0_data_blocks[-1].add_word(5, word_5_data, gst_page)
        elif last_word_type_5 != word_5_data:
            # Create new ADKD0Data block with updated GST
            # For some reason o this case its assumed the next subframe
            new_adkd0data_block = copy.deepcopy(last_adkd0_block)
            new_adkd0data_block.gst_start = BitArray(uint=gst_page.uint + 5, length=32)
            new_adkd0data_block.add_word(5, word_5_data, gst_page)
            self.adkd0_data_blocks.append(new_adkd0data_block)

    def add_word(self, word_type: int, page: BitArray, gst_page: BitArray):

        adkd_data = self._get_adkd_data_from_word(page, word_type)

        if word_type != 5:
            iod = adkd_data[:10]
            if self._is_new_adkd0_data_block(iod):
                new_adkd0 = ADKD0DataBlock(gst_page)
                new_adkd0.add_word(word_type, adkd_data, gst_page)
                self.adkd0_data_blocks.append(new_adkd0)
            else:
                self.adkd0_data_blocks[-1].add_word(word_type, adkd_data, gst_page)
        else:
            self._handle_word_type_5(adkd_data, gst_page)

        self._clean_old_data()

    def tag_has_data(self, tag: TagAndInfo) -> bool:
        tag_has_data = False
        gst_tag = tag.gst_subframe

        for nav_data in self.adkd0_data_blocks:
            if nav_data.gst_start.uint < gst_tag.uint:
                tag_has_data = True
                break
        return tag_has_data

    def get_nav_data(self, tag: TagAndInfo) -> Optional[ADKD0DataBlock]:
        data = None
        gst_tag = tag.gst_subframe
        gst_start_tesla_key = tag.tesla_key.gst_start

        for nav_data in self.adkd0_data_blocks:
            if nav_data.gst_completed and nav_data.gst_start.uint < gst_tag.uint:
                if nav_data.gst_completed.uint < gst_start_tesla_key.uint - Config.TL:
                    tmp_data = nav_data.get_nav_data()
                else:
                    tmp_data = None
                data = None if nav_data.gst_limit.uint < gst_tag.uint else tmp_data
            else:
                break
        return data

    def get_complete_iod(self, tag: TagAndInfo) -> Optional[BitArray]:
        gst_tag = tag.gst_subframe
        iod = None
        for nav_data in self.adkd0_data_blocks:
            if nav_data.gst_start.uint < gst_tag.uint:
                iod = nav_data.iod
            else:
                break

        if iod[-3:] != tag.iod_tag[-3:]:
            raise ValueError(f"IOD from tag {tag.id} and data don't match: Tag {tag.iod_tag[-3:]} - Data {iod[-3:]}.")
            # print(f"Warning: IOD from tag {tag.id} and data don't match: Tag {tag.iod_tag[-3:]} - Data {iod[-3:]}.")
        return iod


class ADKD4WordData:

    def __init__(self, gst_start: BitArray, data: BitArray):
        self.gst_start = gst_start
        self.data = data

    def __repr__(self):
        return f"GST {self.gst_start[:12].uint} - {self.gst_start[12:].uint}"

    def get_nav_data(self):
        return self.data


class ADKD4DataBlock:
    def __init__(self, gst_start: BitArray, nav_data_stream: BitArray):
        self.gst_start = gst_start
        self.nav_data_stream = nav_data_stream


class ADKD4DataManager(ADKDDataManager):

    def __init__(self):
        super().__init__(ADKD4)
        self.word_lists: Dict[int, List[ADKD4WordData]] = {6: [], 10: []}

    def __repr__(self):
        return f"{self.word_lists}"

    def _is_new_data(self, word_list: List[ADKD4WordData], data: BitArray):
        for word in word_list:
            if word.data == data:
                return False
        return True

    def add_word(self, word_type: int, page: BitArray, gst_page: BitArray):

        adkd_data = self._get_adkd_data_from_word(page, word_type)
        word_list = self.word_lists[word_type]

        if not word_list or self._is_new_data(word_list, adkd_data):
            word_data = ADKD4WordData(gst_page, adkd_data)
            word_list.append(word_data)

    def tag_has_data(self, tag: TagAndInfo) -> bool:
        """
        TODO
        Think of the case where only W6 or W10 are received and then the data changes, should not keep tags for
        the old words.
        """
        tag_has_data = False
        gst_tag = tag.gst_subframe

        for word in [word for word_list in self.word_lists.values() for word in word_list]:
            if word.gst_start.uint < gst_tag.uint:
                tag_has_data = True
                break

        return tag_has_data

    def get_nav_data(self, tag: TagAndInfo):

        nav_data = {6: False, 10: False}
        gst_tag = tag.gst_subframe

        # Search for the newest word6 and word10 when the tag was received
        for word_type, word_list in self.word_lists.items():
            for word in word_list:
                if word.gst_start.uint < gst_tag.uint:
                    nav_data[word_type] = BitArray(word.data)

        # Set the TOW to the previous subframe
        if nav_data[6] and nav_data[10]:
            tow_data = gst_tag[12:].uint - 25
            nav_data[6].append(BitArray(uint=tow_data, length=20))
            return ADKD4DataBlock(gst_tag, nav_data[6] + nav_data[10])
        else:
            return None


class NavigationDataManager:

    ACTIVE_ADKD = {0, 4, 12}

    words_per_adkd = {0: [1, 2, 3, 4, 5],
                      12: [1, 2, 3, 4, 5],
                      4: [6, 10],
                      5: []}

    def __init__(self):
        self.adkd_masks = adkd_masks
        self.tags_accumulated: Dict[Tuple[int, int, int], TagAccumulation] = {}
        self.adkd0_data_managers: Dict[int, ADKD0DataManager] = {}
        for i in range(1, Config.NS+1):
            self.adkd0_data_managers[i] = ADKD0DataManager(i)

        self.adkd4_data_manager = ADKD4DataManager()

        self.auth_sats_svid: List[int] = []

        self.active_words = set()
        for adkd, words in self.words_per_adkd.items():
            if adkd in self.ACTIVE_ADKD:
                self.active_words.update(words)

    def tag_has_data(self, tag: TagAndInfo):
        svid = tag.prn_d.uint
        adkd = tag.adkd.uint
        tag_has_data = False

        try:
            if adkd == 0 or adkd == 12:
                tag_has_data = self.adkd0_data_managers[svid].tag_has_data(tag)
            elif adkd == 4:
                tag_has_data = self.adkd4_data_manager.tag_has_data(tag)
        except KeyError as e:
            msg = f"Tag {tag.id} authenticating a satellite with PRN_D {e} is not implemented."
            if svid in range(64, 96):
                msg += " PRN_D 64 - 95 was used for GPS in previous OSNMA versions."
            logger.warning(msg)
        return tag_has_data


    def get_data(self, tag: TagAndInfo):
        svid = tag.prn_d.uint
        adkd = tag.adkd.uint
        nav_data = None

        try:
            if adkd == 0 or adkd == 12:
                nav_data = self.adkd0_data_managers[svid].get_nav_data(tag)
            elif adkd == 4:
                nav_data = self.adkd4_data_manager.get_nav_data(tag)
        except KeyError as e:
            msg = f"Tag {tag.id} authenticating a satellite with PRN_D {e} is not implemented."
            if svid in range(64, 96):
                msg += " PRN_D 64 - 95 was used for GPS in previous OSNMA versions."
            logger.warning(msg)
        return nav_data

    def add_authenticated_tag(self, tag: TagAndInfo):

        if tag.id in self.tags_accumulated:
            self.tags_accumulated[tag.id].add_tag(tag)
        else:
            complete_iod = None
            if tag.adkd.uint == ADKD0 or tag.adkd.uint == ADKD12:
                complete_iod = self.adkd0_data_managers[tag.prn_d.uint].get_complete_iod(tag)
            self.tags_accumulated[tag.id] = TagAccumulation(tag, iod=complete_iod)

    def load_page(self, page: BitArray, gst_page: BitArray, svid: int):
        word_type = page[2:8].uint
        if word_type not in self.active_words:
            return
        if word_type in self.words_per_adkd[ADKD0]:
            self.adkd0_data_managers[svid].add_word(word_type, page, gst_page)
        else:
            self.adkd4_data_manager.add_word(word_type, page, gst_page)

    def authenticated_data(self, gst_subframe: BitArray):

        for tag_id, tag in self.tags_accumulated.items():
            if tag.acc_length >= Config.TAG_LENGTH and tag.new_tags:
                tag.log_authenticated()
                tag.new_tags = False
                # TODO: Eliminar quan les dades deixen de ser valides:
                #       Tinc noves dades al complert I no hi ha cap tag esperant key apuntant a elles
                #       O han passat 4h(?)

                # TTFAF Calculation
                if tag.adkd != 4 and tag.prn_d not in self.auth_sats_svid:
                    self.auth_sats_svid.append(tag.prn_d)
                    if len(self.auth_sats_svid) == 4:
                        # Everything is checked at the end of the SF, so add 30 seconds to the gst of the subframe
                        # Also, OSNMAlib works with pages timestamped with the GST of leading edge of the first page,
                        # but to receive the data of a page we have to wait until the page ends, hence +1 second.
                        gst_subframe_data_end = BitArray(uint=gst_subframe.uint+30+1, length=32)
                        logger.info(f"FIRST AUTHENTICATED FIX {gst_subframe_data_end[:12].uint} {gst_subframe_data_end[12:].uint}")
                        logger.info(f"FIRST TOW {Config.FIRST_TOW}")
                        logger.info(f"TTFAF {gst_subframe_data_end[12:].uint - Config.FIRST_TOW}")
                        if Config.STOP_AT_FAF:
                            raise Exception("Stopped by FAF")
