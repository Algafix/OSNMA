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
from osnma.cryptographic.gst_class import GST
from osnma.utils.config import Config

from bitstring import BitArray
from typing import List, Dict, Tuple, Optional, Union

import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


ADKD0 = 0
ADKD4 = 4
ADKD12 = 12
ADKD5 = 5

WORDS_PER_ADKD = {0: [1, 2, 3, 4, 5],
                  12: [1, 2, 3, 4, 5],
                  4: [6, 10],
                  5: []}


class AuthenticatedData:

    auth_message = 'AUTHENTICATED: ADKD {adkd:02} - Satellite {satellite:02} {iod} ' \
                   '\n\t\t GST SF {gst_start}  to  GST SF {gst_last} ' \
                   '\n\t\t {words} \n'

    def __init__(self, tag: TagAndInfo):
        self.acc_length = len(tag.tag_value)
        self.start_gst = tag.gst_subframe
        self.last_gst = self.start_gst
        self.iod = tag.nav_data.iod if tag.adkd.uint != 4 else None
        self.new_tags = True
        self.log_message = self._generate_message(tag.adkd.uint, tag.prn_d.uint, self.iod)
        self.prn_d = tag.prn_d.uint
        self.adkd = tag.adkd.uint

    def _generate_message(self, adkd: int, prn_d: int, iod: BitArray) -> str:
        if iod is None:
            iod_message = ""
        else:
            iod_message = f"- IOD {self.iod}"

        words_message = "Words "
        for word in WORDS_PER_ADKD[adkd]:
            words_message += f"{word}, "
        words_message = words_message[:-2]

        auth_message = self.auth_message.format(adkd=adkd, satellite=prn_d,
                                                iod=iod_message, words=words_message,
                                                gst_start='{gst_start}', gst_last='{gst_last}')
        return auth_message

    def add_tag(self, tag: TagAndInfo):
        self.acc_length += len(tag.tag_value)
        self.last_gst = tag.gst_subframe
        self.new_tags = True

    def log_authenticated(self):
        gst_start = f"{self.start_gst}"
        gst_last = f"{self.last_gst}"
        logger.info(self.log_message.format(gst_start=gst_start, gst_last=gst_last))

    def __repr__(self):
        return f"{{acc_length: {self.acc_length}, start_gst: {self.start_gst}, " \
               f"last_gst: {self.last_gst}, iod: {self.iod}, new_tags: {self.new_tags}}}"


class ADKDDataManager:
    ADKD_MASKS = adkd_masks

    def __init__(self, adkd: int, svid: int):
        self.adkd = adkd
        self.svid = svid

    def _get_adkd_data_from_word(self, full_page: BitArray, word_type: int):
        data_mask = self.ADKD_MASKS[self.adkd]['adkd'][word_type]['bits']

        adkd_word_data = BitArray()
        for bit_block in data_mask:
            adkd_word_data.append(full_page[bit_block[0]: bit_block[1]])

        return adkd_word_data

    def add_word(self, word_type: int, data: BitArray, gst_page: GST):
        pass

    def get_nav_data(self, tag: TagAndInfo):
        pass


class ADKD0DataBlock:

    def __init__(self, gst_start: GST):
        self.gst_start = gst_start
        self.iod: Optional[BitArray] = None
        self.words: Dict[int, BitArray] = {}
        self.nav_data_stream: Optional[BitArray] = None
        self.last_gst_updated = gst_start
        self.gst_completed = GST()
        self.last_cop = 0
        self.last_cop_gst = GST(wn=0, tow=0)

    def __repr__(self):

        gst_completed_msg = ''
        if self.gst_completed:
            gst_completed_msg = f" gst_completed: {self.gst_completed},"

        msg = f"gst_start: {self.gst_start}, iod: {self.iod}, words: {self.words}\n\t" \
              f"last_gst_updated: {self.last_gst_updated},{gst_completed_msg} last_cop: {self.last_cop} {self.last_cop_gst}\n\t"

        return msg

    def add_word(self, word_type: int, data: BitArray, gst_page: GST):
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
        super().__init__(ADKD0, svid)
        self.adkd0_data_blocks: List[ADKD0DataBlock] = []

    def __repr__(self):
        return f"\n\t{self.adkd0_data_blocks}\n"

    def _iod_unambiguous(self, gst_page: GST) -> bool:
        """
        Checks if we have received a Word Type with IOD during this subframe so the Word Type 5 can be linked.
        self.adkd0_data_blocks must not be empty
        """
        last_adkd0_block = self.adkd0_data_blocks[-1]
        if last_adkd0_block.last_gst_updated - gst_page < 30:
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

    def _handle_word_type_5(self, word_5_data: BitArray, gst_page: GST):
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
            # Due to a bug in DV bits, this is to the next subframe
            new_adkd0data_block = copy.deepcopy(last_adkd0_block)
            new_adkd0data_block.gst_start = gst_page + 30 - (gst_page.tow % 30)  # Next subframe
            new_adkd0data_block.last_cop = 0
            new_adkd0data_block.last_cop_gst = GST(wn=0, tow=0)
            new_adkd0data_block.add_word(5, word_5_data, gst_page)
            self.adkd0_data_blocks.append(new_adkd0data_block)

    def add_word(self, word_type: int, page: BitArray, gst_page: GST):

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

    def get_nav_data(self, tag: TagAndInfo) -> Optional[ADKD0DataBlock]:
        data = None
        tag_data_gst_sf_limit = tag.gst_subframe-30*tag.cop.uint
        gst_start_tesla_key = tag.tesla_key.gst_start

        for nav_data in self.adkd0_data_blocks:
            if tag_data_gst_sf_limit <= nav_data.gst_start < tag.gst_subframe:
                # Data received inside COP range, check TL and proceed
                data = nav_data.get_nav_data()
                if data.gst_completed and data.gst_completed > gst_start_tesla_key - Config.TL:
                    # Completed after TL, do not use
                    data = None
                break
            elif nav_data.gst_start < tag_data_gst_sf_limit < nav_data.last_gst_updated:
                    # Case with COP saturated at 15 and data from the satellite still updated in COP limit
                    data = nav_data.get_nav_data()
                    break

        if data is None and tag.prn_a != tag.prn_d and len(self.adkd0_data_blocks) >= 1:
            # Last check: cross-auth tag for a satellite we lost view but the data may still be valid
            last_data_block = self.adkd0_data_blocks[-1]
            if tag.cop.uint >= last_data_block.last_cop and last_data_block.last_cop_gst > tag.gst_subframe - last_data_block.last_cop*30:
                # Only if the COP is equal or higher (no reset in data) AND
                # we are sure there's not enough time to get to the same COP with new data.
                data = last_data_block

        return data

    def get_complete_iod(self, tag: TagAndInfo) -> Optional[BitArray]:
        gst_tag = tag.gst_subframe
        iod = None
        for nav_data in self.adkd0_data_blocks:
            if nav_data.gst_start < gst_tag:
                iod = nav_data.iod
            else:
                break

        return iod


class ADKD4WordData:

    def __init__(self, gst_start: GST, data: BitArray):
        self.gst_start = gst_start
        self.data = data

    def __repr__(self):
        return f"GST {self.gst_start}"

    def get_nav_data(self):
        return self.data


class ADKD4DataBlock:
    def __init__(self, gst_start: GST, nav_data_stream: BitArray):
        self.gst_start = gst_start
        self.nav_data_stream = nav_data_stream


class ADKD4DataManager(ADKDDataManager):

    def __init__(self, svid: int):
        super().__init__(ADKD4, svid)
        self.word_lists: Dict[int, List[ADKD4WordData]] = {6: [], 10: []}

    def __repr__(self):
        return f"{self.word_lists}"

    def _is_new_data(self, word_list: List[ADKD4WordData], data: BitArray):
        for word in word_list:
            if word.data == data:
                return False
        return True

    def add_word(self, word_type: int, full_page: BitArray, gst_page: GST):

        adkd_data = self._get_adkd_data_from_word(full_page, word_type)
        word_list = self.word_lists[word_type]

        if not word_list or self._is_new_data(word_list, adkd_data):
            word_data = ADKD4WordData(gst_page, adkd_data)
            word_list.append(word_data)

    def get_nav_data(self, tag: TagAndInfo):

        nav_data = {6: False, 10: False}
        gst_tag = tag.gst_subframe

        # Search for the newest word6 and word10 when the tag was received
        for word_type, word_list in self.word_lists.items():
            for word in word_list:
                if word.gst_start < gst_tag:
                    nav_data[word_type] = BitArray(word.data)

        if nav_data[6] and nav_data[10]:
            return ADKD4DataBlock(gst_tag, nav_data[6] + nav_data[10])
        else:
            return None


class NavigationDataManager:

    def __init__(self):
        """
        The NavigationDataManager is instantiated as part of the receiver. For each page received, it is called to
        extract the relevant navigation data of the page and store it depending on which ADKD authenticates it.

        When a tag requires data, it is called to provide it. When a tag is authenticated, that information is
        transmitted to the NavigationDataManager to mark that data block as authentic.

        It also has a function to log the updated status of the data.
        """
        self.auth_sats_svid: List[int] = []
        self.authenticated_data_dict: Dict[Tuple[int, BitArray], AuthenticatedData] = {}

        self.adkd0_data_managers: Dict[int, ADKD0DataManager] = {}
        self.adkd4_data_managers: Dict[int, ADKD4DataManager] = {}
        for i in range(1, Config.NS+1):
            self.adkd0_data_managers[i] = ADKD0DataManager(i)
            self.adkd4_data_managers[i] = ADKD4DataManager(i)

        self.active_words = set()
        for adkd, words in WORDS_PER_ADKD.items():
            if adkd in Config.ACTIVE_ADKD:
                self.active_words.update(words)

    def _get_dummy_data(self, tag: TagAndInfo) -> Union[ADKD0DataBlock, ADKD4DataBlock]:
        """
        For dummy tags, the navigation data has to a zero array of the ADKD size.
        """
        adkd = tag.adkd.uint
        nav_data_len = adkd_masks[adkd]['len']
        if adkd == 4:
            nav_data = ADKD4DataBlock(GST(), BitArray(nav_data_len))
        elif adkd == 0 or adkd == 12:
            nav_data = ADKD0DataBlock(GST())
            nav_data.nav_data_stream = BitArray(nav_data_len)
        else:
            logger.warning(f"Dummy tag {tag} for a not implemented ADKD")
            nav_data = None

        return nav_data

    def get_data(self, tag: TagAndInfo):
        svid = tag.prn_d.uint
        adkd = tag.adkd.uint
        nav_data = None

        if tag.is_dummy:
            return self._get_dummy_data(tag)

        try:
            if adkd == 0 or adkd == 12:
                nav_data = self.adkd0_data_managers[svid].get_nav_data(tag)
            elif adkd == 4:
                nav_data = self.adkd4_data_managers[svid].get_nav_data(tag)
        except KeyError as e:
            msg = f"Tag {tag.id} authenticating a satellite with PRN_D {e} is not implemented."
            logger.warning(msg)
            nav_data = None
        return nav_data

    def new_tag_verified(self, tag: TagAndInfo):
        if tag.data_id in self.authenticated_data_dict:
            self.authenticated_data_dict[tag.data_id].add_tag(tag)
        else:
            self.authenticated_data_dict[tag.data_id] = AuthenticatedData(tag)

    def load_page(self, page: BitArray, gst_page: GST, svid: int):
        word_type = page[2:8].uint
        if word_type not in self.active_words:
            return
        if word_type in WORDS_PER_ADKD[ADKD0]:
            self.adkd0_data_managers[svid].add_word(word_type, page, gst_page)
        else:
            self.adkd4_data_managers[svid].add_word(word_type, page, gst_page)

    def get_authenticated_data(self, gst_subframe: GST):
        """
        Called every time a MACK message with a new TESLA key is received after verifying all possible tags.
        Authenticates any data blocks possible (according to tag length)
        """

        for auth_data in self.authenticated_data_dict.values():
            if auth_data.acc_length >= Config.TAG_LENGTH and auth_data.new_tags:
                auth_data.log_authenticated()
                auth_data.new_tags = False
                # TODO: Eliminar quan les dades deixen de ser valides:
                #       Tinc noves dades al complert I no hi ha cap tag esperant key apuntant a elles
                #       O han passat 4h(?)

                # TTFAF Calculation
                if auth_data.adkd != 4 and auth_data.prn_d not in self.auth_sats_svid:
                    self.auth_sats_svid.append(auth_data.prn_d)
                    if len(self.auth_sats_svid) == 4:
                        # Everything is checked at the end of the SF, so add 30 seconds to the gst of the subframe
                        # Also, OSNMAlib works with pages timestamped with the GST of leading edge of the first page,
                        # but to receive the data of a page we have to wait until the page ends, hence +1 second.
                        gst_subframe_data_end = gst_subframe+30+1
                        logger.info(f"First Authenticated Fix at GST {gst_subframe_data_end}")
                        logger.info(f"First GST {Config.FIRST_GST}")
                        logger.info(f"TTFAF {(gst_subframe_data_end - Config.FIRST_GST).tow} seconds\n")
                        if Config.STOP_AT_FAF:
                            raise Exception("Stopped by FAF")
