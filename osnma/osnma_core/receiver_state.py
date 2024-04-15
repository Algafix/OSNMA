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
from typing import TYPE_CHECKING, List, Optional, Tuple, Dict
if TYPE_CHECKING:
    from osnma.receiver.satellite import Satellite

######## imports ########
from enum import IntEnum

from bitstring import BitArray

from osnma.structures.fields_information import NB_DK_lt, NB_DP_lt, CPKS, NMAS, cpks_lt, nmas_lt
from osnma.cryptographic.dsm_kroot import DSMKroot
from osnma.cryptographic.dsm_pkr import DSMPKR
from osnma.cryptographic.gst_class import GST
from osnma.osnma_core.tesla_chain import TESLAChain
from osnma.osnma_core.nav_data_manager import NavigationDataManager
from osnma.utils.iohandler import IOHandler
from osnma.utils.exceptions import PublicKeyObjectError, TeslaKeyVerificationFailed, MackParsingError
from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)


class HKROOT(IntEnum):
    NMA_HEADER_END = 8
    DSM_ID_START = 8
    DSM_ID_END = 12
    BID_START = 12
    BID_END = 16
    DATA_START = 16
    NB_START = 16
    NB_END = 20


class OSNMAlibSTATE(IntEnum):
    COLD_START = 0
    WARM_START = 1
    HOT_START = 2
    STARTED = 6
    OSNMA_AM = 7


class DigitalSignatureMessage:

    def __init__(self, dsm_id: int):
        self.blocks_received: Dict[int, BitArray] = {}
        self.total_of_blocks: Optional[int] = None
        self.dsm_id = dsm_id
        self.translate_blocks = NB_DK_lt if self.dsm_id < 12 else NB_DP_lt

    def load_dsm_subframe(self, dsm_subframe: BitArray):

        bid = dsm_subframe[HKROOT.BID_START:HKROOT.BID_END].uint
        self.blocks_received[bid] = dsm_subframe[HKROOT.DATA_START:]
        logger.info(f"Received block {bid} from DSM ID {self.dsm_id}.")
        logger.info(f"\tDSM ID {self.dsm_id} blocks: {self.blocks_received.keys()}\n")

        if bid == 0:
            number_of_blocks_field = dsm_subframe[HKROOT.NB_START:HKROOT.NB_END].uint
            self.total_of_blocks = self.translate_blocks[number_of_blocks_field]
            logger.info(f"DSM ID {self.dsm_id} number of blocks: {self.total_of_blocks}\n")
            if self.total_of_blocks == "Reserved":
                logger.warning(f'The Number of Blocks field is {number_of_blocks_field} with value "Reserved"\n')

    def is_complete(self) -> bool:
        return len(self.blocks_received) == self.total_of_blocks

    def get_data(self) -> BitArray:
        hkroot_data = BitArray()
        for i in range(self.total_of_blocks):
            hkroot_data += self.blocks_received[i]
        self.blocks_received = {}
        self.total_of_blocks = None
        return hkroot_data


class ReceiverState:

    def __init__(self):

        self.osnmalib_state = OSNMAlibSTATE.COLD_START
        self.chain_status = CPKS.NOMINAL
        self.nma_status = NMAS.TEST

        self.nma_header: Optional[BitArray] = None

        self.pkr_dict: Dict[int, DSMPKR] = {}
        self.current_pkid: Optional[int] = None
        self.merkle_root: Optional[BitArray] = None
        self.new_merkle_root: Optional[BitArray] = None

        self.tesla_chain_force: Optional[TESLAChain] = None
        self.next_tesla_chain: Optional[TESLAChain] = None

        self.nav_data_structure = NavigationDataManager()
        self.io_handler = IOHandler(Config.EXEC_PATH)

        self.dsm_messages: List[DigitalSignatureMessage] = []
        for i in range(16):
            self.dsm_messages.append(DigitalSignatureMessage(i))

        self.kroot_waiting_mack: List[Tuple[List[Optional[BitArray]], GST, int, BitArray]] = []

        self._initialize_status()

    def _initialize_status(self):

        merkle_file = Config.MERKLE_NAME
        pubkey_file = Config.PUBK_NAME
        kroot_file = Config.KROOT_NAME
        self.merkle_root = self.io_handler.read_merkle_root(merkle_file)
        logger.info(f"Start status {self.osnmalib_state.name}\n")

        if pubkey_file:
            try:
                dsm_pkr, pubk_id = self.io_handler.read_pubk(pubkey_file)
            except Exception as e:
                logger.warning(e)
            else:
                self.pkr_dict[pubk_id] = dsm_pkr
                self.osnmalib_state = OSNMAlibSTATE.WARM_START
                logger.info(f"Public Key ID {pubk_id} read. Start status {self.osnmalib_state.name}\n")
                if kroot_file:
                    try:
                        kroot_bits, nmah_bits = self.io_handler.read_kroot(kroot_file)
                        dsm_kroot = DSMKroot(self.pkr_dict)
                        dsm_kroot.set_value('NMA_H', nmah_bits)
                        dsm_kroot.process_data(kroot_bits)
                        if dsm_kroot.kroot_verification():
                            # self._chain_status_handler(nmah_bits, dsm_kroot)
                            self.nma_status, _, self.chain_status = self._nma_header_parser(nmah_bits)
                            self.nma_header = nmah_bits
                            self.tesla_chain_force = TESLAChain(self.nav_data_structure, dsm_kroot)
                            self.current_pkid = dsm_kroot.get_value('PKID').uint
                            self.osnmalib_state = OSNMAlibSTATE.HOT_START
                            logger.info(f"KROOT read with NMA Status {self.nma_status.name} and Chain Status {self.chain_status.name}. Start status {self.osnmalib_state.name}\n")
                        else:
                            logger.warning(f"KROOT read is not verified. Not used.")
                    except IOError as e:
                        logger.warning(e)
                    except PublicKeyObjectError:
                        logger.warning('Saved Key Root PKID is not consistent with the stored Public Key. Not used.')

    def _nma_header_parser(self, nma_header: BitArray) -> (NMAS, int, CPKS):
        nma_status = nmas_lt[nma_header[:2].uint]
        cid = nma_header[2:4].uint
        cpks = cpks_lt[nma_header[4:7].uint]
        return nma_status, cid, cpks

    def _subframe_actions(self, nma_header: BitArray):
        if self.chain_status == CPKS.EOC and self.next_tesla_chain is not None:
            current_chain_in_force = nma_header[2:4].uint
            if current_chain_in_force == self.next_tesla_chain.chain_id:
                logger.info(f"New chain in force: CID {current_chain_in_force} GST0"
                            f"{self.next_tesla_chain.GST0}")
                self.tesla_chain_force = self.next_tesla_chain
                self.next_tesla_chain = None

    def _fallback_to_state(self, new_osnmalib_state: OSNMAlibSTATE, cpks: CPKS = CPKS.NOMINAL):

        logger.info(f"Fallback to {new_osnmalib_state.name} from {self.osnmalib_state.name}")

        self.osnmalib_state = new_osnmalib_state
        self.chain_status = cpks

        self.tesla_chain_force = None
        self.next_tesla_chain = None
        self.kroot_waiting_mack = []

        self.current_pkid = None

        if new_osnmalib_state == OSNMAlibSTATE.COLD_START:
            self.pkr_dict = {}
        if new_osnmalib_state == OSNMAlibSTATE.OSNMA_AM:
            self.pkr_dict = {}
            self.merkle_root = None
            self.nma_status = NMAS.DONT_USE

    def _kroot_is_cid(self, nma_header: BitArray, dsm_kroot: DSMKroot, cid_kroot: int):
        """
        This function is called when the KROOT received is the KROOT in force as per CID.
        It is only called after a KROOT is first successfully verified.
        """

        self.io_handler.store_kroot(dsm_kroot, nma_header)

        if self.osnmalib_state != OSNMAlibSTATE.STARTED:
            self.tesla_chain_force = TESLAChain(self.nav_data_structure, dsm_kroot)
            self.current_pkid = dsm_kroot.get_value('PKID').uint
            logger.info(f"Start status from {self.osnmalib_state.name} to {OSNMAlibSTATE.STARTED.name}.")
            self.osnmalib_state = OSNMAlibSTATE.STARTED
        else:
            if cid_kroot == self.tesla_chain_force.chain_id:
                logger.info(f"KROOT with CID {cid_kroot} already read and in use.")
                self.tesla_chain_force.update_kroot(dsm_kroot)
            else:
                self.tesla_chain_force = TESLAChain(self.nav_data_structure, dsm_kroot)
                self.current_pkid = dsm_kroot.get_value('PKID').uint
                self.next_tesla_chain = None
                logger.warning(f"Chain changed during downtime. Set to CID {cid_kroot}.")

    def _chain_status_handler(self, nma_header: BitArray, dsm_kroot: DSMKroot):

        new_nmas, cid, new_cpks = self._nma_header_parser(nma_header)
        self.nma_status = new_nmas
        self.chain_status = new_cpks
        self.nma_header = nma_header
        cid_kroot = dsm_kroot.get_value('CIDKR').uint

        logger.info(f"NMAS is {new_nmas.name}.")
        logger.info(f"Chain in force is {cid}.")
        logger.info(f"CPKS is {new_cpks.name}.\n")

        if new_cpks == CPKS.NOMINAL:
            self._kroot_is_cid(nma_header, dsm_kroot, cid_kroot)

        elif new_cpks == CPKS.EOC:
            if cid == cid_kroot:
                self._kroot_is_cid(nma_header, dsm_kroot, cid_kroot)
            else:
                self.next_tesla_chain = TESLAChain(self.nav_data_structure, dsm_kroot)
                logger.info(f"Stored as next TESLA Chain. In force at {self.next_tesla_chain.GST0}.")

        elif new_cpks == CPKS.CREV:
            if new_nmas == NMAS.DONT_USE:
                if self.osnmalib_state == OSNMAlibSTATE.STARTED and cid == self.tesla_chain_force.chain_id:
                    logger.warning("TESLA Chain revocation process detected. TESLA Chain in use discarded.")
                    self._fallback_to_state(OSNMAlibSTATE.WARM_START, new_cpks)
            else:
                self._kroot_is_cid(nma_header, dsm_kroot, cid_kroot)

        elif new_cpks == CPKS.NPK:
            pkid = dsm_kroot.get_value('PKID').uint
            self._kroot_is_cid(nma_header, dsm_kroot, cid_kroot)
            if pkid != self.current_pkid:
                logger.info(f"Public Key in force changed from {self.current_pkid} to {pkid}.")
                self.pkr_dict.pop(self.current_pkid)
                self.current_pkid = pkid

        elif new_cpks == CPKS.PKREV:
            if new_nmas == NMAS.DONT_USE:
                if self.osnmalib_state == OSNMAlibSTATE.STARTED:
                    logger.warning("Public Key revocation process detected. Public Key and TESLA Chain in use discarded.")
                    self._fallback_to_state(OSNMAlibSTATE.COLD_START, new_cpks)
            else:
                self._kroot_is_cid(nma_header, dsm_kroot, cid_kroot)

        elif new_cpks == CPKS.NMT:
            self._kroot_is_cid(nma_header, dsm_kroot, cid_kroot)
            pkid = dsm_kroot.get_value('PKID').uint

            if self.new_merkle_root is None and pkid != 1:
                logger.warning(f"Reading new Merkle Tree root: {Config.NEW_MERKLE_NAME}")
                self.new_merkle_root = self.io_handler.read_merkle_root("new_OSNMA_MerkleTree.xml")

            if self.current_pkid != pkid:
                    logger.info(f"Public Key in force changed from {self.current_pkid} to {pkid}.")
                    logger.info(f"Deleting previous Merkle Root.")
                    self.merkle_root = self.new_merkle_root
                    self.pkr_dict.pop(self.current_pkid)
                    self.current_pkid = pkid

        elif new_cpks == CPKS.AM:
            logger.warning("OAM Detected - Please connect to the GSC OSNMA Server")
            self._fallback_to_state(OSNMAlibSTATE.OSNMA_AM, CPKS.AM)

        else:
            logger.error(f"CPKS {new_cpks} not valid")

    def process_kroot_message(self, nma_header: BitArray, kroot: BitArray):
        """
        Creates a DSMKroot object with the received information and tries to verify it. If the verification is correct,
        create a TESLAChain object with this key and a MACKMessageParser. Also stores the key by its CID in the
        receivers list.
        """
        try:
            dsm_kroot = DSMKroot(self.pkr_dict)
            dsm_kroot.set_value('NMA_H', nma_header)
            dsm_kroot.process_data(kroot)
        except PublicKeyObjectError as e:
            logger.error(f"Problem with the Public Key for authenticating this DSMKroot: {e}")
            if self.osnmalib_state == OSNMAlibSTATE.WARM_START:
                self._fallback_to_state(OSNMAlibSTATE.COLD_START)
        else:
            if dsm_kroot.kroot_verification():
                logger.info(f"KROOT with CID: {dsm_kroot.get_value('CIDKR').uint} - PKID: "
                            f"{dsm_kroot.get_value('PKID').uint} - GST0: WN {dsm_kroot.get_value('WN_K').uint} TOW "
                            f"{dsm_kroot.get_value('TOWH_K').uint*3600}\n\tAUTHENTICATED\n")
                self._chain_status_handler(nma_header, dsm_kroot)
            else:
                logger.error(
                    f"KROOT with CID: {dsm_kroot.get_value('CIDKR').uint} - PKID: {dsm_kroot.get_value('PKID').uint}"
                    f" - GST0: WN {dsm_kroot.get_value('WN_K').uint} TOW {dsm_kroot.get_value('TOWH_K').uint*3600}"
                    f"\n\tFAILED\n")
                if self.osnmalib_state == OSNMAlibSTATE.WARM_START:
                    self._fallback_to_state(OSNMAlibSTATE.COLD_START)

    def process_pkr_message(self, pkr: BitArray):

        dsm_pkr = DSMPKR(pkr_message=pkr)
        npkid = dsm_pkr.get_value('NPKID').uint

        if self.chain_status == CPKS.NMT and npkid < self.current_pkid:
            dsm_pkr.merkle_root = self.new_merkle_root
        else:
            dsm_pkr.merkle_root = self.merkle_root

        if dsm_pkr.pkr_verification():
            logger.info(f"PKR with NPKID {npkid} verified.")

            if dsm_pkr.is_OAM:
                logger.warning("OAM Detected - Please connect to the GSC OSNMA Server")
                self._fallback_to_state(OSNMAlibSTATE.OSNMA_AM, CPKS.AM)
                return

            if npkid not in self.pkr_dict:
                self.pkr_dict[npkid] = dsm_pkr
                self.io_handler.store_pubk(dsm_pkr)
                logger.info(f"New PK. Current PKs: {self.pkr_dict.keys()}")
            else:
                logger.info(f"PK already read: {self.pkr_dict.keys()}")
            if self.osnmalib_state == OSNMAlibSTATE.COLD_START:
                self.osnmalib_state = OSNMAlibSTATE.WARM_START
                logger.info(f"Start status from {OSNMAlibSTATE.COLD_START.name} to {self.osnmalib_state.name}")
        else:
            logger.error(f"PKR verification failed! PRK received: NPKID {npkid}, NPKT {dsm_pkr.get_value('NPKT').uint}, MID {dsm_pkr.get_value('MID').uint}.")

    def process_hkroot_subframe(self, hkroot_sf: BitArray, is_consecutive_hkroot=False) -> BitArray:

        if self.osnmalib_state == OSNMAlibSTATE.OSNMA_AM:
            logger.warning(f"OSNMA Alert Message. Not processing OSNMA data. Connect to the GSC OSNMA sever.")
            return BitArray(uint=NMAS.DONT_USE.value, length=2)

        sf_nma_header = hkroot_sf[:HKROOT.NMA_HEADER_END]
        if is_consecutive_hkroot:
            self._subframe_actions(sf_nma_header)
        dsm_id = hkroot_sf[HKROOT.DSM_ID_START:HKROOT.DSM_ID_END].uint
        dsm_message = self.dsm_messages[dsm_id]
        dsm_message.load_dsm_subframe(hkroot_sf)

        # If we have all the blocks
        if dsm_message.is_complete():
            dsm_data = dsm_message.get_data()
            if dsm_id <= 11:
                if self.osnmalib_state != OSNMAlibSTATE.COLD_START:
                    self.process_kroot_message(sf_nma_header, dsm_data)
            else:
                self.process_pkr_message(dsm_data)

        return sf_nma_header[:2]

    def process_mack_subframe(self, mack_subframe: List[Optional[BitArray]], gst_subframe: GST, satellite: 'Satellite', sf_nma_status: BitArray):

        if self.nma_status == NMAS.DONT_USE:
            logger.warning(f"NMA Status: Don't Use. Navigation data authentication not performed.")
            self.kroot_waiting_mack = []
            return

        if self.tesla_chain_force is None:
            self.kroot_waiting_mack.append((mack_subframe, gst_subframe, satellite.svid, sf_nma_status))
        else:
            try:
                if self.kroot_waiting_mack:
                    for w_mack in self.kroot_waiting_mack:
                        self.tesla_chain_force.parse_mack_message(w_mack[0], w_mack[1], w_mack[2], w_mack[3])
                    self.kroot_waiting_mack = []
                tags_log, tkey = self.tesla_chain_force.parse_mack_message(mack_subframe, gst_subframe, satellite.svid, sf_nma_status)
                satellite.osnma_tags_log = tags_log
                satellite.osnma_tesla_key_log = tkey

            except MackParsingError as e:
                # Unable to parse the message correctly
                logger.error(f"Unable to parse the MACK message correctly.\n{e}")
                if self.osnmalib_state == OSNMAlibSTATE.HOT_START:
                    self._fallback_to_state(OSNMAlibSTATE.WARM_START)
                else:
                    logger.warning("Deleting first mack message from waiting list")
                    self.kroot_waiting_mack = self.kroot_waiting_mack[1:]
            except TeslaKeyVerificationFailed as e:
                # Unable to verify the TESLA key
                logger.error(f"Failed authenticating a TESLA key.\n{e}")
                if self.osnmalib_state == OSNMAlibSTATE.HOT_START:
                    self._fallback_to_state(OSNMAlibSTATE.WARM_START)
                else:
                    logger.warning("Deleting first mack message from waiting list")
                    self.kroot_waiting_mack = self.kroot_waiting_mack[1:]
            else:
                if self.osnmalib_state == OSNMAlibSTATE.HOT_START and tkey is not None:
                    self.osnmalib_state = OSNMAlibSTATE.STARTED
                    logger.info(f"One TESLA key verified. Start Status: {self.osnmalib_state.name}")

    def load_nav_data_page(self, nav_bits: BitArray, gst_page: GST, satellite: 'Satellite'):
        self.nav_data_structure.load_page(nav_bits, gst_page, satellite)


if __name__ == '__main__':
    pass
