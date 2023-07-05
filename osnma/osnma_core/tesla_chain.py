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

from osnma.cryptographic.dsm_kroot import DSMKroot
from osnma.cryptographic.mack_msg_parser import MACKMessageParser
from osnma.osnma_core.tag_verification import TagStateStructure
from osnma.structures.fields_information import HF, KS_lt, TS_lt, MF
from osnma.structures.mack_structures import TESLAKey, MACSeqObject, TagAndInfo
from osnma.utils.exceptions import FieldValueNotRecognized, TeslaKeyVerificationFailed, MackParsingError

from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from bitstring import BitArray
from typing import Union, List

import hashlib
import hmac
import traceback

import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


class TESLAChain:
    """This class represents the TESLA Chain and stores all the necessary information for it's handling. The class is
    designed with flexibility in mind allowing to store not verified keys in the chain as long as they are consistent
    with the chain. This not verified keys will be verified or discarded once a verified key (KROOT or floating KROOT)
    is loaded.

    """

    def __init__(self, nav_data_structure, dsm_kroot: DSMKroot):
        """Initialize a TESLAChain object. Set the :class:`TESLAChain` attributes to those in the :class:`DSMKroot` and
        stores a pointer to the object. At the end, a :class:`TESLAKey` object is created for the KROOT with the GST_sf
        30s less than GST0.

        :param dsm_kroot: DSMKroot object with the values to initialize the TESLAChain object.
        :type dsm_kroot: DSMKroot, optional
        """

        # Copy and conversion of the necessary parameters from the low level dsm_kroot object
        self.dsm_kroot = dsm_kroot
        self.chain_id = dsm_kroot.get_value('CIDKR').uint
        self.alpha = dsm_kroot.get_value('ALPHA')
        self.nmack = dsm_kroot.get_value('NMACK').uint
        self.key_size = KS_lt[dsm_kroot.get_value('KS').uint]
        self.tag_size = TS_lt[dsm_kroot.get_value('TS').uint]
        self.maclt = dsm_kroot.get_value('MACLT').uint

        gst0_wn = dsm_kroot.get_value('WN_K')
        gst0_tow = dsm_kroot.get_value('TOWH_K').uint * 3600
        self.GST0 = gst0_wn + BitArray(uint=gst0_tow, length=20)

        # Define the hash function to be used during this chain
        hash_index = dsm_kroot.get_value('HF').uint
        if hash_index == HF.SHA_256:
            self.hash_function = hashlib.sha256
        elif hash_index == HF.SHA3_224:
            self.hash_function = hashlib.sha3_224
        elif hash_index == HF.SHA3_256:
            self.hash_function = hashlib.sha3_256
        else:
            raise FieldValueNotRecognized(f"DMSKroot field HF value {hash_index} not recognised")

        # Define the mac function to be used during this chain
        mac_f_index = dsm_kroot.get_value('MF').uint
        if mac_f_index == MF.HMAC_SHA_256:
            self.mac_function = self._hmac256
        elif mac_f_index == MF.CMAC_AES:
            self.mac_function = self._cmac_aes
            logger.warning('cmac_aes not tested')
        else:
            raise FieldValueNotRecognized(f"DMSKroot field MF value {mac_f_index} not recognised")

        #gst0_tow = 604770 if gst0_tow == 0 else gst0_tow # TODO: solucionar amb anell a gst
        # Define the two keys that the chain will be storing at any time: kroot and last verified tesla key
        root_key = TESLAKey(gst0_wn, gst0_tow - 30, dsm_kroot.get_value('KROOT'), is_kroot=True)
        root_key.set_verified(dsm_kroot.is_verified())
        self.root_tesla_key = root_key
        self.last_tesla_key = root_key

        # Instantiate the auxiliary object for the tag management and parsing of messages
        self.nav_data_structure = nav_data_structure
        self.mac_msg_parser = MACKMessageParser(self)
        self.tags_structure = TagStateStructure(self, self.nav_data_structure)

    def _hmac256(self, key, message):
        mac = hmac.new(key=key.tobytes(), msg=message.tobytes(), digestmod=hashlib.sha256)
        return BitArray(mac.digest())

    def _cmac_aes(self, key, message):
        mac = CMAC.new(key.tobytes(), msg=message.tobytes(), ciphermod=AES)
        return BitArray(mac.digest())

    def _compute_gst_subframe(self, index: int) -> BitArray:
        """Compute the GST of the subframe corresponding to a TESLA key index. Uses GST0, ns and nmack values to
        perform the computation.

        For the KROOT of the chain (index = 0) returns GST0 - 30s.

        :param index: Index of a TESLA key.
        :type index: int
        :return: GST at the start of the subframe
        :rtype: BitArray
        """

        if index == 0:
            gst_subframe = self.GST0.uint - 30
        else:
            # ICD v1.1
            # gst_subframe = self.GST0.uint + 30 * ((index - 1) // (self.ns * self.nmack))

            # ICD v1.2 Test Phase
            gst_subframe = (self.GST0.uint-30) + 30 * -(index // -self.nmack)
        gst_subframe = BitArray(uint=gst_subframe, length=32)

        return gst_subframe

    def _compute_next_key(self, tesla_key: TESLAKey) -> TESLAKey:
        """Compute the next TESLA key in the chain using the TESLA key passed as parameter and the values of
        the chain. Calculates the GST corresponding to the next key index and then computes the hash of the
        concatenations ( currentKEY || GST_nextkey || alpha )

        :param tesla_key: TESLA key object with the index value computed.
        :type tesla_key: TESLAKey
        :return: The next (index - 1) TESLA key of the chain.
        :rtype: TESLAKey
        """
        next_index = tesla_key.index - 1
        gst = self._compute_gst_subframe(next_index)
        key_digest = self.hash_function((tesla_key.key + gst + self.alpha).tobytes()).digest()
        key_value = key_digest[:(self.key_size // 8)]  # digest is a bytes object, key_size are bits
        computed_tesla_key = TESLAKey(gst[:12], gst[12:], key_value, index=next_index)

        return computed_tesla_key

    def parse_mack_message(self, mack_message: List[BitArray], gst_sf: BitArray, prn_a: int, nma_status: BitArray):
        """Parse a MACK message bit stream. Then handles the MACK object to the tag structure to add the new tags to the
        tag list. Finally, add the key(s) received to the TESLA key chain.

        :param nma_status: nma status of that subframe
        :type nma_status: BitArray
        :param mack_message: MACK message bit stream.
        :type mack_message: BitArray
        :param gst_sf: GST at the start of the subframe in which the MACK message is transmitted.
        :type gst_sf: BitArray
        :param prn_a: PRN of the satellite that broadcasted the message.
        :type prn_a: int
        """

        try:
            mack_object = self.mac_msg_parser.parse_mack_message(mack_message, gst_sf, prn_a, nma_status)
        except Exception as e:
            raise MackParsingError(f"Error parsing MACK Message from SVID {prn_a} at "
                                   f"{gst_sf[:12].uint} {gst_sf[12:].uint}\n{traceback.print_exc()}")
        else:
            self.tags_structure.load_mack_message(mack_object)
            if tesla_key := mack_object.get_key():
                self.add_key(tesla_key)

    def update_tag_lists(self):
        self.tags_structure.update_tag_lists()

    def get_key_index(self, gst_sf: BitArray) -> int:
        """Computes the key index that would have a key received on the subframe specified and in the position specified
        The index is relative to the first kroot received for this chain.

        :param gst_sf: GST value at the start of the subframe where the key is received.
        :type gst_sf: BitArray
        :return: index of the key
        """
        # ICD 1.1
        # past_keys = ((self.gst_sf.uint - gst_0.uint) // 30) * ns * nmack
        # self.index = past_keys + (self.n_block - 1) * ns + ((self.svid - 1) % ns) + 1

        # ICD 1.2 Test Phase: All satellites transmit the same key at the same epoch
        past_keys = (gst_sf.uint - self.GST0.uint) // 30
        index = past_keys * self.nmack + 1

        return index

    def get_wn_towh(self) -> (int, int):
        """Get the WN and TOWH (hours) of Chain applicability. Computed from the continuous GST0 attribute.

        :return: Tuple[WN,TOWH]
        :rtype: (int, int)
        """
        return self.GST0[:12].uint, self.GST0[12:].uint//3600

    def set_cid(self, cid: int):
        """Set the CID of the TESLA Chain. This value identifies each Chain and rolls over 3.

        :param cid: Chain ID value, from 0 to 3.
        :type cid: int
        """
        self.chain_id = cid

    def add_key(self, new_tesla_key: TESLAKey) -> (bool, int):
        """Verifies the new tesla key by computing the necessary hashes until reaching the index of the
        `self.last_tesla_key`. Then compares the key value. If the keys are the same, the key is verified and the
        `self.last_tesla_key` value is updated.

        :param new_tesla_key: TESLA Key to be added to the Chain.
        :type new_tesla_key: TESLAKey
        :return: Tuple indicating if the key has been verified and its index.
        :rtype: (bool, int)
        """

        # Calculate the index of the new key
        new_tesla_key.calculate_index(self.GST0)

        # Starts with the hashes
        new_key_index = new_tesla_key.index
        last_tesla_key = self.last_tesla_key
        tesla_key = new_tesla_key
        key_verified = False
        for key_index in reversed(range(new_key_index + 1)):
            if key_index > last_tesla_key.index:
                # Normal case when a new key is received. If its not the first key, it will compute only 1 key
                tesla_key = self._compute_next_key(tesla_key)
            elif key_index == last_tesla_key.index and tesla_key.key == last_tesla_key.key:
                new_tesla_key.set_verified(True)
                self.last_tesla_key = new_tesla_key
                key_verified = True
                break
            else:
                raise TeslaKeyVerificationFailed(f"Tesla Key {new_tesla_key.index} from svid {new_tesla_key.svid}"
                                                 f"{' Reconstructed' if new_tesla_key.reconstructed else ''},"
                                                 f" received at {new_tesla_key.wn.uint} {new_tesla_key.tow.uint} failed verification.\n"
                                                 f"Last authenticated key: {last_tesla_key.index} at {last_tesla_key.tow.uint}.\n"
                                                 f"Last hash: {key_index} {tesla_key.key}")

        # if key_verified and new_tesla_key.tow.uint != last_tesla_key.tow.uint:
        #     logger.info(f"Subframe with Tesla Key Authenticated {new_tesla_key.wn.uint} {new_tesla_key.tow.uint} {' - Regenerated' if new_tesla_key.reconstructed else ''}\n")

        return key_verified, new_key_index

    def _update_tags_key(self, tesla_key: TESLAKey, index: int):

        for macseq_tag in self.tags_structure.macseq_awaiting_key:
            if not macseq_tag.has_key and macseq_tag.key_id == index:
                macseq_tag.tesla_key = tesla_key

        for tag in self.tags_structure.tags_awaiting_key:
            if not tag.has_key and tag.key_id == index:
                tag.tesla_key = tesla_key

    def _get_tesla_key(self, wanted_key_index: int) -> TESLAKey:
        """Retrieves a TESLA key according to the index provided. In the strange case that the key solicited is not the
        last key verified, it is computed. That situation can happen in case of discontinuities in the reception from
        the satellites.

        :param wanted_key_index: Index of the tesla key to be retrieved
        :type wanted_key_index: int
        """

        return_tesla_key = self.last_tesla_key
        number_of_hashes = abs(wanted_key_index - self.last_tesla_key.index)
        for _ in range(number_of_hashes):
            return_tesla_key = self._compute_next_key(return_tesla_key)

        return return_tesla_key

    def key_check(self, mack_structure: Union[MACSeqObject, TagAndInfo]) -> bool:
        """Checks if the key belonging to the index argument is verified or not. Simply checks if
        the index provided in less than the last verified index.

        :param mack_structure: Index value of the key to check.
        :type mack_structure: Union[MACSeqObject,TagAndInfo]
        :return: True if the index is less than self.last_tesla_key.index
        :rtype: bool
        """

        tag_has_key = False
        if mack_structure.has_key:
            tag_has_key = True
        elif mack_structure.key_id <= self.last_tesla_key.index:
            tag_tesla_key = self._get_tesla_key(mack_structure.key_id)
            mack_structure.tesla_key = tag_tesla_key
            tag_has_key = True

        return tag_has_key

    def update_kroot(self, dsm_kroot: DSMKroot):
        """Updates the self.dsm_kroot message with a newest one. The rest of the chain parameters are maintained
        linked to the first dsm_kroot message for consistency with the key indexes already set to the tags.

        :param dsm_kroot:
        :return:
        """
        if not dsm_kroot.is_verified():
            raise Exception("Updating TESLA Chain KROOT with a not verified DSM KROOT.")
        self.dsm_kroot = dsm_kroot
