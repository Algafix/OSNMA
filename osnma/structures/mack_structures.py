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
from typing import Union, List, Optional

######## imports ########
from osnma.cryptographic.gst_class import GST
from bitstring import BitArray


class TESLAKey:
    """Class to encapsulate the TESLA keys received. It allows to load only partial information and then complete it
    when the TESLA Chain is created.
    """

    def __init__(self, gst_sf: GST, key: Union[BitArray, str, bytes],
                 svid: int = None, index: int = None, gst_start: GST = GST(), reconstructed: bool = False, is_kroot: bool = False):
        """Instantiates the TESLAKey object. If the Telsa Key is_kroot, index and svid are set to 0.

        :param gst_sf: GST at the start of the Galileo subframe where the TESLA key is received.
        :param key: Value of the TESLA key received.
        :param svid: Satellite number (NS). Value between 1 and 36. Set to 0 for KROOT.
        :param is_kroot: If this Tesla Key comes from an HKROOT message.
        :param index: Index of the key if it is known. Set to 0 for KROOT.
        """
        self.verified: bool = False
        self.key = BitArray(key)
        self.reconstructed = reconstructed

        self.is_kroot = is_kroot
        if is_kroot:
            self.index = 0
            self.svid = 0
        else:
            self.index = index
            self.svid = svid

        self.gst_sf = gst_sf
        self.gst_start: GST = gst_start

    def get_as_dict(self) -> dict:
        """Returns the key in a dictionary format for debug or log purposes.

        :return: TESLA key in a dictionary object with 'Index', 'WN', 'TOW', 'Key' and 'Verified' keys.
        :rtype: dict
        """
        return {'Index': self.index, 'WN': self.gst_sf.wn, 'TOW': self.gst_sf.wn, 'is_kroot': self.is_kroot,
                'Key': self.key.hex, 'Verified': self.verified}

    def set_gst(self, gst_sf: GST):
        """Set the GST at the start of the Galileo Subframe where the key is received.

        :param gst_sf: GST at the start of the subframe.
        :type gst_sf: BitArray
        """
        self.gst_sf = gst_sf

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

    def calculate_index(self, gst_0: GST) -> int:
        """Computes the key index based on the GST0 of the first HKROOT of this chain and returns it. This method is not
        intended to be called on the Tesla key from the first kroot message, which requires the index to be set to 0 on
        the constructor.

        :param gst_0: Time applicability of the chain GST_0, is the same as the GST for the first key. Not the KROOT.
        :return: Index of the Key in the TESLA Chain.
        """
        if self.index is None:
            # ICD 1.2 Test Phase: All satellites transmit the same key at the same epoch
            past_keys = (self.gst_sf - gst_0) // 30
            self.index = past_keys + 1

        return self.index


class MACSeqObject:

    def __init__(self, gst: GST, svid: BitArray, macseq_value: BitArray, flex_list: List['TagAndInfo'] = None, key_id: int = None):
        self.gst = gst
        self.svid = svid
        self.macseq_value = macseq_value
        self.flex_list = flex_list
        self.key_id = key_id
        self.tesla_key: Optional[TESLAKey] = None

    @property
    def has_key(self):
        return self.tesla_key is not None

    def get_log(self) -> str:
        return f"PRN_A: {self.svid.uint} GST_SF: {self.gst} FLX Tags: {len(self.flex_list)}"


class TagAndInfo:

    def __init__(self, tag_value: BitArray, prn_d: BitArray, adkd: BitArray, iod_tag: BitArray, gst_subframe: GST,
                 prn_a: BitArray, ctr: int, nma_status: BitArray):
        self.tag_value = tag_value
        self.prn_d = prn_d
        self.prn_a = prn_a
        self.adkd = adkd
        self.iod_tag = iod_tag
        self.new_data = iod_tag[0]
        self.ctr = ctr
        self.gst_subframe = gst_subframe
        self.nma_status = nma_status

        self.id = (self.prn_d.uint, self.adkd.uint, self.iod_tag[1:].uint)
        self.verified: bool = False
        self.key_id: Optional[int] = None
        self.tesla_key: Optional[TESLAKey] = None
        self.is_tag0 = False

    def __repr__(self) -> str:
        return f"{{ID: {self.id} PRN_A: {self.prn_a.uint}}}"

    @property
    def has_key(self) -> bool:
        return self.tesla_key is not None

    def get_log(self) -> str:
        return f"{self.id} PRN_A: {self.prn_a.uint} GST_SF: {self.gst_subframe}"


class Tag0AndSeq(TagAndInfo):

    def __init__(self, tag0_value: BitArray, prn_a: BitArray, iod_tag: BitArray, gst_subframe: GST, mac_seq: BitArray,
                 nma_status: BitArray):
        prn_d = prn_a  # PRN_D used to compute the id as bitarray
        adkd = BitArray('0x0')  # TAG0 has adkd 0
        super().__init__(tag0_value, prn_d, adkd, iod_tag, gst_subframe, prn_a, 1, nma_status)
        self.mac_seq = mac_seq
        self.is_tag0 = True

    def is_new_data(self) -> bool:
        return self.iod_tag[0] == 1

    def get_log(self) -> str:
        return f"{super().get_log()} TAG0"


class MACKMessage:

    def __init__(self, gst_sf: GST, chain_id: int, svid: BitArray, nr_tags: int, tags: List[TagAndInfo] = None, tesla_key: TESLAKey = None):

        self.svid = svid
        self.gst_sf = gst_sf
        self.chain_id = chain_id
        self.nr_tags = nr_tags
        self.tesla_key = tesla_key
        self.tags: List[TagAndInfo] = tags if tags else []

        self.tag0_and_seq: Optional[Tag0AndSeq] = None
        self.macseq: Optional[MACSeqObject] = None

    def add_key(self, key: TESLAKey):
        self.tesla_key = key

    def add_tag(self, tag: Optional[TagAndInfo]):
        if len(self.tags) >= self.nr_tags:
            raise ValueError(f"No more tags can be added to this MACKMessage. Block tags: {self.nr_tags};"
                             f" current tags: {len(self.tags)}.")
        else:
            self.tags.append(tag)

    def add_tag0(self, tag0: Tag0AndSeq):
        if self.tag0_and_seq is None:
            self.tag0_and_seq = tag0
            self.macseq = MACSeqObject(self.gst_sf, self.svid, self.tag0_and_seq.mac_seq)
            self.add_tag(tag0)
        else:
            raise ValueError(f"Tag0 of this MACKMessage already filled.")

    def get_macseq(self, tag_list: List[TagAndInfo]) -> MACSeqObject:
        if self.macseq:
            self.macseq.flex_list = tag_list
        return self.macseq

    def get_key(self) -> TESLAKey:
        return self.tesla_key

    def get_tag0(self) -> Tag0AndSeq:
        return self.tag0_and_seq
