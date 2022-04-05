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

from typing import Union, List
from bitstring import BitArray


class TESLAKey:
    """Class to encapsulate the TESLA keys received. It allows to load only partial information and then complete it
    when the TESLA Chain is created.
    """

    def __init__(self, wn: Union[BitArray, int, str], tow: Union[BitArray, int, str], key: Union[BitArray, str, bytes],
                 svid: int = None, n_block: int = None, index: int = None):
        """Instantiates the TESLAKey object. Verified is set to false by default. Special treatment for KROOT (index
        = 0) key.

        :param wn: GST Week Number at the start of the Galileo subframe where the TESLA key is received.
        :param tow: GST Time of Week (seconds) at the start of the Galileo subframe where the TESLA key is received.
        :param key: Value of the TESLA key received.
        :param svid: Satellite number (NS). Value between 1 and 36. 0 for KROOT.
        :param n_block: MACK block where the key has been received (1, 2 or 3). 0 for KROOT.
        :param index: Index of the key if it is known.
        """
        self.verified = False
        self.index = index
        self.n_block = n_block
        self.svid = svid
        self.key = BitArray(key)

        if isinstance(wn, BitArray) or isinstance(wn, str):
            self.wn = BitArray(wn)
        elif isinstance(wn, int):
            self.wn = BitArray(uint=wn, length=12)
        else:
            raise TypeError(f"Only supported int or BitArray, not {type(wn)} for {wn}")

        if isinstance(tow, BitArray) or isinstance(tow, str):
            self.tow = BitArray(tow)
        elif isinstance(tow, int):
            self.tow = BitArray(uint=tow, length=20)
        else:
            raise TypeError(f"Only supported int or BitArray, not {type(tow)} for {tow}")

        self.gst_sf = self.wn + self.tow

    def get_as_dict(self) -> dict:
        """Returns the key in a dictionary format for debug or log purposes.

        :return: TESLA key in a dictionary object with 'Index', 'WN', 'TOW', 'Key' and 'Verified' keys.
        :rtype: dict
        """
        return {'Index': self.index, 'WN': self.wn.uint, 'TOW': self.tow.uint, 'Block Index': self.n_block,
                'Key': self.key.hex, 'Verified': self.verified}

    def set_gst(self, gst_sf: BitArray):
        """Set the GST at the start of the Galileo Subframe where the key is received.

        :param gst_sf: GST at the start of the subframe.
        :type gst_sf: BitArray
        """
        self.wn = gst_sf[:12]
        self.tow = gst_sf[12:]

    def set_index(self, index: int):
        """Set the TESLA Chain index for this key.

        :param index: Index of the Key in the TESLA Chain.
        :type index: int
        """
        self.index = index

    def set_verified(self, verified: bool):
        """Set the verified status for the TESLA Key.

        :param verified: Status of the Key.
        :type verified: bool
        """
        self.verified = verified

    def is_verified(self) -> bool:
        """Checks the status of the TESLA Key.

        :return: Status of the Key.
        :rtype: bool
        """
        return self.verified

    def calculate_index(self, gst_0: BitArray, nmack: int) -> int:
        """Computes the key index if it is not already set and returns it. This method needs the correct values for
        the TESLA Chain where the key belongs to be able to compute the index.

        :param gst_0: Time applicability of the chain GST_0, is the same as the GST for the first key. Not the KROOT.
        :type gst_0: BitArray
        :param nmack: Number of MACK blocs transmitted per MACK message within a subframe.
        :type nmack: int
        :return: Index of the Key in the TESLA Chain.
        :rtype: int
        """
        if self.index is None:
            # ICD 1.1
            # past_keys = ((self.gst_sf.uint - gst_0.uint) // 30) * ns * nmack
            # self.index = past_keys + (self.n_block - 1) * ns + ((self.svid - 1) % ns) + 1

            # ICD 1.2 Test Phase: All satellites transmit the same key at the same epoch
            past_keys = (self.gst_sf.uint - gst_0.uint) // 30
            self.index = past_keys * nmack + self.n_block

        return self.index


class MACSeqObject:

    def __init__(self, gst, svid, macseq_value, flex_list=None, key_id=None):
        self.gst = gst
        self.svid = BitArray(uint=svid, length=8)
        self.macseq_value = macseq_value
        self.flex_list = flex_list
        self.key_id = key_id
        self.tesla_key = None

    @property
    def has_key(self):
        return self.tesla_key is not None

    def get_log(self):
        wn = self.gst[:12].uint
        tow = self.gst[12:].uint
        return f"PRN_A: {self.svid.uint} GST_SF: {wn} {tow} TAGS ADDED: {len(self.flex_list)}"


class TagAndInfo:

    def __init__(self, tag_value: BitArray, prn_d: BitArray, adkd: BitArray, iod_tag: BitArray, gst_subframe: BitArray,
                 prn_a: int, ctr: int, mack_block: int, nma_status: BitArray):
        self.tag_value = tag_value
        self.prn_d = prn_d
        self.prn_a = BitArray(uint=prn_a, length=8)
        self.adkd = adkd
        self.iod_tag = iod_tag
        self.new_data = iod_tag[0]
        self.ctr = ctr
        self.gst_subframe = gst_subframe
        self.mack_block = mack_block
        self.nma_status = nma_status

        self.id = (self.prn_d.uint, self.adkd.uint, self.iod_tag[1:].uint)
        self.verified = False
        self.key_id = None
        self.tesla_key = None

    def __repr__(self) -> str:
        return f"{{ID: {self.id} PRN_A: {self.prn_a.uint} New: {self.iod_tag[0]} GST TOW: " \
               f"{self.gst_subframe[12:].uint}}}"

    @property
    def has_key(self):
        return self.tesla_key is not None

    def get_log(self):
        wn = self.gst_subframe[:12].uint
        tow = self.gst_subframe[12:].uint
        return f"{self.id} PRN_A: {self.prn_a.uint} GST_SF: {wn} {tow}"


class Tag0AndSeq(TagAndInfo):

    def __init__(self, tag0_value: BitArray, prn_a: int, iod_tag: BitArray, gst_subframe: BitArray, mac_seq: BitArray,
                 nma_status: BitArray):
        prn_d = BitArray(uint=prn_a, length=8)  # PRN_D used to compute the id as bitarray
        adkd = BitArray('0x0')  # TAG0 has adkd 0
        super().__init__(tag0_value, prn_d, adkd, iod_tag, gst_subframe, prn_a, 1, 1, nma_status)
        self.mac_seq = mac_seq
        self.is_tag0 = True

    def is_new_data(self):
        return self.iod_tag[0] == 1

    def get_log(self):
        return f"{super().get_log()} TAG0"


class MACKBlock:

    def __init__(self, block_number: int, ntags: int, tags=None, tesla_key=None):
        """
        :param block_number: Position of the block
        :type block_number: int
        :param ntags: number of tags in this block.
        :type ntags: int
        :param tags: List of tags.
        :type tags: List[TagAndInfo]
        :param tesla_key: Tesla Key of this MACK block.
        :type tesla_key: TESLAKey
        """
        self.block_number = block_number
        self.tesla_key = tesla_key
        self.ntags = ntags

        self.tags = tags if tags else []

    def add_key(self, key: TESLAKey):
        self.tesla_key = key

    def add_tag(self, tag):
        if len(self.tags) >= self.ntags:
            raise ValueError(f"No more tags can be added to this block. Block tags due to NMACK: {self.ntags};"
                             f" current tags: {len(self.tags)}.")
        else:
            self.tags.append(tag)

    def add_tags(self, tags):
        if len(tags) >= self.ntags:
            raise ValueError(f"Tag list parameter has more tags than the maximum amount due to chain properties. Max "
                             f"block tags: {self.ntags}; tags to be added: {len(tags)}.")
        else:
            self.tags = tags


class MACKHeaderBlock(MACKBlock):

    def __init__(self, ntags, tags=None, tesla_key=None):
        super().__init__(1, ntags, tags, tesla_key)

    def get_tag_header(self) -> Tag0AndSeq:
        return self.tags[0]

    def add_tag(self, tag):
        if tag.ctr == 1 and not isinstance(tag, Tag0AndSeq):
            raise TypeError(f"The first tag must be a MACHeader, not {type(tag)}")
        else:
            super().add_tag(tag)

    def add_tags(self, tags):
        if tags[0] is not isinstance(tags[0], Tag0AndSeq):
            raise TypeError(f"The first tag must be a MACHeader, not {type(tags[0])}")
        else:
            super().add_tags(tags)


class MACKMessage:

    def __init__(self, gst_sf, chain_id, nmack, svid, mack_blocks=None):
        """
        :param gst_sf: Galileo Satellite Time of the subframe, 32 bits value.
        :type gst_sf: BitArray

        :param chain_id: ID of the TESLA Chain in force when this MACKMessage was received.
        :type chain_id: int

        :param nmack: Number of MACK blocks per MACKMessage
        :type nmack: int

        :param mack_blocks: List of MACKBlock
        :type mack_blocks: List[MACKHeaderBlock, MACKBlock]
        """
        self.svid = svid
        self.gst_sf = gst_sf
        self.chain_id = chain_id
        self.nmack = nmack
        self.macseq = None

        self.mack_blocks = mack_blocks if mack_blocks else []

    def add_mack_block(self, mack_block: MACKBlock):

        if mack_block.block_number == 1 and not isinstance(mack_block, MACKHeaderBlock):
            raise TypeError(f"The first mack block must be a MACKHeaderBlock, not {type(mack_block)}")
        elif len(self.mack_blocks) >= self.nmack:
            raise ValueError(f"No more blocks can be added to this message. NMACK of {self.nmack}; current blocks:"
                             f" {len(self.mack_blocks)}.")
        else:
            self.mack_blocks.append(mack_block)
            if mack_block.block_number == 1:
                self.set_macseq()

    def set_macseq(self):
        self.macseq = MACSeqObject(self.gst_sf, self.svid, self.get_tag0().mac_seq)

    def get_macseq(self, tag_list):
        self.macseq.flex_list = tag_list
        return self.macseq

    def get_keys(self):
        """
        Return a list with the key or keys in the block.
        :return: List[TESLAKey]
        """
        return [block.tesla_key for block in self.mack_blocks]

    def get_tag0(self):
        return self.mack_blocks[0].get_tag_header()
