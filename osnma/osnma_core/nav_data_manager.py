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

from osnma.structures.adkd import adkd_masks
from osnma.structures.mack_structures import TagAndInfo

from bitstring import BitArray

import osnma.utils.config as config
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
                   '\n\t\t GST {gst_start}  to  GST {gst_last} ' \
                   '\n\t\t {words} \n'

    def __init__(self, tag: TagAndInfo, iod=None):
        self.acc_length = len(tag.tag_value)
        self.start_gst = (tag.gst_subframe[:12].uint, tag.gst_subframe[12:].uint)
        self.last_gst = self.start_gst
        self.iod = iod
        self.new_tags = False
        self.log_message = self._generate_message(tag.adkd.uint, tag.prn_d.uint, iod)

    def _generate_message(self, adkd, prn_d, iod):
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
               f"last_gst: [{self.last_gst[0]}, {self.last_gst[1]}], iod: {self.iod}}}"


class ADKD0DataBlock:

    def __init__(self, gst_start):
        self.gst_start = gst_start
        self.iod = None
        self.words = {}
        self.nav_data_stream = None
        self.gst_limit = BitArray('0xffffffff')
        self.last_gst_updated = gst_start

    def __repr__(self):
        return f"gst_start: {self.gst_start[:12].uint} - {self.gst_start[12:].uint}, iod: {self.iod}," \
               f" words: {self.words}\n\t"

    def add_word(self, word_type, data, gst_page):
        self.last_gst_updated = gst_page
        if word_type != 5:
            self.iod = data[:10]
        self.words[word_type] = data

    def get_word(self, word_type):
        return self.words.get(word_type)

    def _compute_data_stream(self):
        data_stream = BitArray()
        for i in range(1, 6):
            data_stream.append(self.words[i])
        self.nav_data_stream = data_stream

    def get_nav_data(self):
        if len(self.words) != 5:
            return None
        else:
            if self.nav_data_stream is None:
                self._compute_data_stream()
            return self


class ADKD0DataStructure:

    def __init__(self):
        self.adkd0_data_blocks = []

    def __repr__(self):
        return f"\n\t{self.adkd0_data_blocks}\n"

    def _missing_word5(self, gst_page):
        adkd0_blocks = self.adkd0_data_blocks
        if adkd0_blocks:
            last_adkd0_block = adkd0_blocks[-1]
            if not last_adkd0_block.get_word(5):
                if last_adkd0_block.last_gst_updated.uint - gst_page.uint < 30:
                    # Only if we can be sure that they belong to the same subframe
                    return True
        return False

    def _is_new_adkd0_data_block(self, iod):
        return len(self.adkd0_data_blocks) == 0 or self.adkd0_data_blocks[-1].iod != iod

    def add_word(self, word_type, data, gst_page):
        if word_type != 5:
            iod = data[:10]
            if self._is_new_adkd0_data_block(iod):
                new_adkd0 = ADKD0DataBlock(gst_page)
                new_adkd0.add_word(word_type, data, gst_page)
                self.adkd0_data_blocks.append(new_adkd0)
            else:
                self.adkd0_data_blocks[-1].add_word(word_type, data, gst_page)
        else:
            if self._missing_word5(gst_page):
                self.adkd0_data_blocks[-1].add_word(word_type, data, gst_page)

    def get_nav_data(self, gst_tag):
        data = None
        for nav_data in self.adkd0_data_blocks:
            if nav_data.gst_start.uint < gst_tag.uint:
                tmp_data = nav_data.get_nav_data()
                data = None if nav_data.gst_limit.uint < gst_tag.uint else tmp_data
            else:
                break
        return data

    def get_complete_iod(self, tag: TagAndInfo):
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

    def __init__(self, gst_start, data):
        self.gst_start = gst_start
        self.data = data

    def __repr__(self):
        return f"GST {self.gst_start[:12].uint} - {self.gst_start[12:].uint}"

    def get_nav_data(self):
        return self.data


class ADKD4DataBlock:
    def __init__(self, gst_start, nav_data_stream):
        self.gst_start = gst_start
        self.nav_data_stream = nav_data_stream


class ADKD4DataStructure:

    def __init__(self):
        self.word_lists = {6: [], 10: []}

    def __repr__(self):
        return f"{self.word_lists}"

    def _is_new_data(self, word_list, data):
        for word in word_list:
            if word.data == data:
                return False
        return True

    def add_word(self, word_type, data, gst_page):

        word_list = self.word_lists[word_type]

        if not word_list or self._is_new_data(word_list, data):
            word_data = ADKD4WordData(gst_page, data)
            word_list.append(word_data)

    def get_nav_data(self, gst_tag):

        nav_data = {6: False, 10: False}

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
        self.tags_accumulated = {}
        self.adkd0_data = {}
        self.adkd4_data = ADKD4DataStructure()

        self.active_words = set()
        for adkd, words in self.words_per_adkd.items():
            if adkd in self.ACTIVE_ADKD:
                self.active_words.update(words)

    def get_data(self, id_data, gst_tag):
        svid = id_data[0]
        adkd = id_data[1]

        if adkd == 0 or adkd == 12:
            if svid not in self.adkd0_data.keys():
                return None
            return self.adkd0_data[svid].get_nav_data(gst_tag)
        elif adkd == 4:
            return self.adkd4_data.get_nav_data(gst_tag)
        else:
            return None

    def add_authenticated_tag(self, tag: TagAndInfo):

        if tag.id in self.tags_accumulated:
            self.tags_accumulated[tag.id].add_tag(tag)
        else:
            complete_iod = None
            if tag.adkd.uint == ADKD0 or tag.adkd.uint == ADKD12:
                complete_iod = self.adkd0_data[tag.prn_d.uint].get_complete_iod(tag)
            self.tags_accumulated[tag.id] = TagAccumulation(tag, iod=complete_iod)

    def _get_word_data(self, page, word_type, adkd):
        data_mask = self.adkd_masks[adkd]['adkd'][word_type]['bits']

        word_data = BitArray()
        for bit_block in data_mask:
            word_data.append(page[bit_block[0]: bit_block[1]])

        return word_data

    def load_adkd0(self, page, word_type, gst_page, svid):

        if svid not in self.adkd0_data:
            self.adkd0_data[svid] = ADKD0DataStructure()

        word_data = self._get_word_data(page, word_type, ADKD0)
        self.adkd0_data[svid].add_word(word_type, word_data, gst_page)

    def load_adkd4(self, page, word_type, gst_sf):

        word_data = self._get_word_data(page, word_type, ADKD4)
        self.adkd4_data.add_word(word_type, word_data, gst_sf)

    def load_page(self, page, gst_page, svid):

        word_type = page[2:8].uint

        if word_type in self.active_words:
            if word_type in self.words_per_adkd[ADKD0]:
                self.load_adkd0(page, word_type, gst_page, svid)
            elif word_type in self.words_per_adkd[ADKD4]:
                self.load_adkd4(page, word_type, gst_page)
            elif word_type in self.words_per_adkd[ADKD5]:
                pass

    def authenticated_data(self):

        for tag_id, tag in self.tags_accumulated.items():
            if tag.acc_length >= config.TAG_LENGTH and tag.new_tags:
                tag.log_authenticated()
                tag.new_tags = False
                # TODO: Eliminar quan les dades deixen de ser valides:
                #       Tinc noves dades al complert I no hi ha cap tag esperant key apuntant a elles
                #       O han passat 4h(?)
