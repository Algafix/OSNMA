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
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from osnma.osnma_core.nav_data_manager import NavigationDataManager
    from osnma.structures.mack_structures import MACSeqObject, TagAndInfo

######## imports ########
from osnma.cryptographic.dsm_kroot import DSMKroot
from osnma.cryptographic.mack_msg_parser import MACKMessageParser
from osnma.cryptographic.gst_class import GST
from osnma.osnma_core.tag_verification import TagStateStructure
from osnma.structures.fields_information import HF, KS_lt, TS_lt, MF
from osnma.structures.mack_structures import TESLAKey
from osnma.utils.status_logger import StatusLogger
from osnma.utils.exceptions import FieldValueNotRecognized, TeslaKeyIndexError, MackParsingError

from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from bitstring import BitArray

import hashlib
import hmac
import traceback

######## logger ########
import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


class TESLAChain:
    """This class represents the TESLA Chain and stores all the necessary information for it's handling. The class is
    designed with flexibility in mind allowing to store not verified keys in the chain as long as they are consistent
    with the chain. This not verified keys will be verified or discarded once a verified key (KROOT or floating KROOT)
    is loaded.

    """

    def __init__(self, nav_data_structure: 'NavigationDataManager', dsm_kroot: DSMKroot):
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
        self.GST0 = GST(wn=dsm_kroot.get_value('WN_K').uint, tow=dsm_kroot.get_value('TOWH_K').uint * 3600)

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

        root_key = TESLAKey(self.GST0 - 30, dsm_kroot.get_value('KROOT'), is_kroot=True)
        root_key.set_verified(dsm_kroot.is_verified())
        self.root_tesla_key = root_key
        self.last_tesla_key = root_key

        # Instantiate the auxiliary object for the tag management and parsing of messages
        self.mac_msg_parser = MACKMessageParser(self)
        self.tesla_key_gst_start_offset = self.mac_msg_parser.tesla_key_gst_start_offset
        self.tags_structure = TagStateStructure(self, nav_data_structure)

    def _hmac256(self, key: BitArray, message: BitArray):
        mac = hmac.new(key=key.tobytes(), msg=message.tobytes(), digestmod=hashlib.sha256)
        return BitArray(mac.digest())

    def _cmac_aes(self, key: BitArray, message: BitArray):
        mac = CMAC.new(key.tobytes(), msg=message.tobytes(), ciphermod=AES)
        return BitArray(mac.digest())

    def _compute_gst_subframe(self, index: int) -> GST:
        """Compute the GST of the subframe corresponding to a TESLA key index. Uses GST0, ns and nmack values to
        perform the computation.

        For the KROOT of the chain (index = 0) returns GST0 - 30s.

        :param index: Index of a TESLA key.
        :type index: int
        :return: GST at the start of the subframe
        :rtype: BitArray
        """

        if index == 0:
            gst_subframe = self.GST0 - 30
        else:
            gst_subframe = (self.GST0-30) + 30 * -(index // -self.nmack)

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
        gst_sf = self._compute_gst_subframe(next_index)
        key_digest = self.hash_function((tesla_key.key + gst_sf.bitarray + self.alpha).tobytes()).digest()
        key_value = key_digest[:(self.key_size // 8)]  # digest is a bytes object, key_size are bits
        key_gst_start = gst_sf + self.tesla_key_gst_start_offset
        computed_tesla_key = TESLAKey(gst_sf, key_value, index=next_index, gst_start=key_gst_start)

        return computed_tesla_key

    def parse_mack_message(self, mack_message: list[BitArray], gst_sf: GST, prn_a: int, nma_status: BitArray, do_log = True)\
            -> TESLAKey | None:
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
            raise MackParsingError(f"Error parsing MACK Message from SVID {prn_a} at {gst_sf}\n{traceback.print_exc()}")
        else:
            tags_log = self.tags_structure.load_mack_message(mack_object)
            if tesla_key := mack_object.get_key():
                StatusLogger.log_auth_tesla_key(tesla_key)
                verified, is_new_key = self.add_key(tesla_key)
                if verified and is_new_key:
                    self.tags_structure.update_tag_lists()
            if do_log:
                StatusLogger.log_mack_data(prn_a, tags_log, tesla_key)
            return tesla_key

    def get_key_index(self, gst_sf: GST) -> int:
        """Computes the key index that would have a key received on the subframe specified and in the position specified
        The index is relative to the first kroot received for this chain.

        :param gst_sf: GST value at the start of the subframe where the key is received.
        :type gst_sf: BitArray
        :return: index of the key
        """

        past_keys = (gst_sf - self.GST0) // 30
        index = past_keys * self.nmack + 1

        return index

    def add_key(self, new_tesla_key: TESLAKey) -> (bool, int):
        """Verifies the new tesla key by computing the necessary hashes until reaching the index of the
        `self.last_tesla_key`. Then compares the key value. If the keys are the same, the key is verified and the
        `self.last_tesla_key` value is updated.

        :param new_tesla_key: TESLA Key to be added to the Chain.
        :type new_tesla_key: TESLAKey
        :return: Tuple indicating if the key has been verified and if it is a new key.
        :rtype: (bool, bool)
        """

        # Calculate the index of the new key
        new_tesla_key.calculate_index(self.GST0)

        if new_tesla_key.index < 0:
            raise TeslaKeyIndexError(f"TESLA key from SVID {new_tesla_key.svid}: {new_tesla_key.key} received at"
                                     f" {new_tesla_key.gst_sf} has a negative key index {new_tesla_key.index} and was"
                                     f" transmitted before the TESLA key root at {self.root_tesla_key.gst_sf}.")

        # Copy the key reference to iterate on it
        new_key_index = new_tesla_key.index
        is_new_key = (self.last_tesla_key.index < new_key_index)
        tesla_key = new_tesla_key

        key_verified = False
        for key_index in reversed(range(new_key_index + 1)):
            if key_index > self.last_tesla_key.index:
                tesla_key = self._compute_next_key(tesla_key)
            elif key_index == self.last_tesla_key.index and tesla_key.key == self.last_tesla_key.key:
                key_verified = True
                break
            else:
                e = (f"Failed authentication of TESLA key {new_tesla_key.index} from SVID {new_tesla_key.svid}: "
                     f"{new_tesla_key.key}.{' Reconstructed.' if new_tesla_key.reconstructed else ''}"
                     f" Received at {new_tesla_key.gst_sf}\nLast authenticated key index {self.last_tesla_key.index}"
                     f" at {self.last_tesla_key.gst_sf}: {self.last_tesla_key.key} ")
                logger.error(e)
                break

        if key_verified:
            new_tesla_key.set_verified(True)
            self.last_tesla_key = new_tesla_key
            logger.info(f"Tesla key {new_tesla_key.index} Authenticated at {new_tesla_key.gst_sf}"
                        f"{' - Regenerated' if new_tesla_key.reconstructed else ''}\n")

        return key_verified, is_new_key

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

    def key_check(self, mack_structure: 'MACSeqObject | TagAndInfo') -> bool:
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
