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

from enum import IntEnum

from bitstring import BitArray

from osnma.structures.fields_information import NB_DK_lt, NB_DP_lt, CPKS, NMAS, cpks_lt, nmas_lt
from osnma.cryptographic.dsm_kroot import DSMKroot
from osnma.cryptographic.dsm_pkr import DSMPKR
from osnma.osnma_core.tesla_chain import TESLAChain
from osnma.osnma_core.nav_data_manager import NavigationDataManager
from osnma.utils.iohandler import IOHandler
from osnma.utils.exceptions import PublicKeyObjectError, TeslaKeyVerificationFailed, MackParsingError, \
    ReceiverStatusError

from osnma.utils.config import Config
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


class StartStates(IntEnum):
    COLD_START = 0
    WARM_START = 1
    HOT_START = 2
    STARTED = 6


class DigitalSignatureMessage:

    def __init__(self, dsm_id):
        self.blocks_received = {}
        self.total_of_blocks = None
        self.dsm_id = dsm_id
        self.translate_blocks = NB_DK_lt if self.dsm_id < 12 else NB_DP_lt

    def load_dsm_subframe(self, dsm_subframe):

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

    def is_complete(self):
        return len(self.blocks_received) == self.total_of_blocks

    def get_data(self):
        hkroot_data = BitArray()
        for i in range(self.total_of_blocks):
            hkroot_data += self.blocks_received[i]
        self.blocks_received = {}
        self.total_of_blocks = None
        return hkroot_data


class ReceiverState:

    def __init__(self):

        self.start_status = StartStates.COLD_START
        self.chain_status = CPKS.NOMINAL
        self.nma_status = NMAS.TEST

        self.nma_header = None

        self.pkr_dict = {}
        self.current_pkid = None
        self.merkle_root = None

        self.tesla_chain_force = None
        self.next_tesla_chain = None

        self.nav_data_structure = NavigationDataManager()
        self.io_handler = IOHandler(Config.EXEC_PATH)

        self.dsm_messages = []
        for i in range(16):
            self.dsm_messages.append(DigitalSignatureMessage(i))

        self.kroot_waiting_mack = []

        self._initialize_status()

    def _initialize_status(self):

        merkle_file = Config.MERKLE_NAME
        pubkey_file = Config.PUBK_NAME
        kroot_file = Config.KROOT_NAME
        self.merkle_root = self.io_handler.read_merkle_root(merkle_file)
        logger.info(f"\nStart status {self.start_status.name}\n")

        if pubkey_file:
            try:
                pubk_id, dsm_pkr = self.io_handler.read_pubk(pubkey_file)
            except IOError:
                logger.warning("Error reading the saved Public Key. Not used.")
            else:
                self.pkr_dict[pubk_id] = dsm_pkr
                self.start_status = StartStates.WARM_START
                logger.info(f"Public Key {pubk_id} read. Start status {self.start_status.name}\n")
                if kroot_file:
                    try:
                        kroot_bits, nmah_bits = self.io_handler.read_kroot(kroot_file)
                        dsm_kroot = DSMKroot(self.pkr_dict)
                        dsm_kroot.set_value('NMA_H', nmah_bits)
                        dsm_kroot.process_data(kroot_bits)
                        if dsm_kroot.kroot_verification():
                            self._chain_status_handler(nmah_bits, dsm_kroot)
                            self.current_pkid = dsm_kroot.get_value('PKID').uint
                            self.start_status = StartStates.HOT_START
                            logger.info(f"KROOT read. Start status {self.start_status.name}\n")
                        else:
                            logger.warning(f"KROOT read is not verified. Not used.")
                    except IOError:
                        logger.error(f"Error reading the saved Root Key. Not used.")
                    except PublicKeyObjectError:
                        logger.warning('Saved Key Root PKID is not consistent with the stored Public Key. Not used.')

    def _nma_header_parser(self, nma_header):
        nma_status = nmas_lt[nma_header[:2].uint]
        cid = nma_header[2:4].uint
        cpks = cpks_lt[nma_header[4:7].uint]
        return nma_status, cid, cpks

    def _subframe_actions(self, nma_header):
        if self.chain_status == CPKS.EOC and self.next_tesla_chain is not None:
            current_chain_in_force = nma_header[2:4].uint
            if current_chain_in_force == self.next_tesla_chain.chain_id:
                logger.info(f"New chain in force: CID {current_chain_in_force} GST0"
                            f"{self.next_tesla_chain.GST0[:12].uint} {self.next_tesla_chain.GST0[12:].uint}")
                self.tesla_chain_force = self.next_tesla_chain
                self.next_tesla_chain = None

    def _fallback_to_warm_start(self):

        logger.info(f"Fallback to {StartStates.WARM_START.name} from {self.start_status.name}.")

        self.start_status = StartStates.WARM_START
        self.chain_status = CPKS.NOMINAL

        self.current_pkid = None

        self.tesla_chain_force = None
        self.next_tesla_chain = None
        self.kroot_waiting_mack = []

    def _fallback_to_cold_start(self):

        logger.info(f"Fallback to {StartStates.COLD_START.name} from {self.start_status.name}")

        self.start_status = StartStates.COLD_START
        self.chain_status = CPKS.NOMINAL

        self.pkr_dict = {}
        self.current_pkid = None

        self.tesla_chain_force = None
        self.next_tesla_chain = None
        self.kroot_waiting_mack = []

    def _store_next_tesla_chain(self, cid_kroot, dsm_kroot):
        if cid_kroot != self.tesla_chain_force.chain_id and self.next_tesla_chain is None:
            self.next_tesla_chain = TESLAChain(self.nav_data_structure, dsm_kroot)
            logger.info(f"Saved as next chain. In force at {self.next_tesla_chain.GST0[:12].uint}"
                        f" {self.next_tesla_chain.GST0[12:].uint}")

    def _chain_status_handler(self, nma_header, dsm_kroot):

        nmas, cid, cpks = self._nma_header_parser(nma_header)
        self.nma_header = nma_header
        self.nma_status = nmas
        cid_kroot = dsm_kroot.get_value('CIDKR').uint
        logger.info(f"NMAS is {nmas.name}.")
        logger.info(f"Chain in force is {cid}.")
        logger.info(f"CPKS is {cpks.name}.\n")

        if self.start_status != StartStates.STARTED:
            # Haven't received the kroot in force
            if self.chain_status == CPKS.NOMINAL:
                self.chain_status = cpks
                if cid_kroot == cid and nmas != NMAS.DONT_USE:
                    # The key received is in force, the cpks doesn't matter
                    self.tesla_chain_force = TESLAChain(self.nav_data_structure, dsm_kroot)
                    self.io_handler.store_kroot(dsm_kroot, nma_header)
                    self.current_pkid = dsm_kroot.get_value('PKID').uint
                    logger.info(f"Start status from {self.start_status.name} to {StartStates.STARTED.name}.")
                    self.start_status = StartStates.STARTED
                elif cpks == CPKS.EOC:
                    # The key received is not in force and EOC
                    self.next_tesla_chain = TESLAChain(self.nav_data_structure, dsm_kroot)
                elif cpks == CPKS.PKREV:
                    # The receiver connects at PKREV Step 1
                    self.next_tesla_chain = TESLAChain(self.nav_data_structure, dsm_kroot)
                else:
                    raise ReceiverStatusError(f"CID {cid}, CIDK {cid_kroot} and CPKS {cpks.name} not possible in"
                                              f" {self.start_status.name} if stored CPKS is {self.chain_status.name}")
            elif self.chain_status == CPKS.EOC:
                # The key read was not the one in force
                self.chain_status = cpks
                if cid_kroot == cid:
                    self.tesla_chain_force = TESLAChain(self.nav_data_structure, dsm_kroot)
                    self.io_handler.store_kroot(dsm_kroot, nma_header)
                    self.current_pkid = dsm_kroot.get_value('PKID').uint
                    logger.info(f"Start status from {self.start_status.name} to {StartStates.STARTED.name}.")
                    self.start_status = StartStates.STARTED
            elif self.chain_status == CPKS.PKREV:
                self.chain_status = cpks
                if cid == self.next_tesla_chain.chain_id:
                    # PKREV has changed from Step1 to Step2
                    self.tesla_chain_force = self.next_tesla_chain
                    self.next_tesla_chain = None
                    new_dsm_kroot = self.tesla_chain_force.dsm_kroot
                    self.io_handler.store_kroot(new_dsm_kroot, new_dsm_kroot.get_value('NMA_H'))
                    logger.info(f"Start status from {self.start_status.name} to {StartStates.STARTED.name}.")
                    self.start_status = StartStates.STARTED
            else:
                raise ReceiverStatusError(f"Saved chain status {self.chain_status.name} not possible in"
                                          f" {self.start_status.name} state.")

        elif self.start_status == StartStates.STARTED:
            # The receiver has the KROOT in force
            if nmas == NMAS.DONT_USE:
                if cpks == CPKS.PKREV:
                    logger.info(f"Public Key {self.current_pkid} revoked.")
                    self._fallback_to_cold_start()
                elif cpks == CPKS.CREV:
                    logger.info(f"TESLA Chain {self.tesla_chain_force.chain_id} revoked")
                    self._fallback_to_warm_start()
                else:
                    raise ReceiverStatusError(f"NMA Status set to {nmas.name} and CPKS to {cpks.name}. Invalid.")

            elif self.chain_status == CPKS.NOMINAL or self.chain_status == CPKS.CREV or self.chain_status == CPKS.PKREV:
                if cpks == CPKS.NOMINAL or cpks == CPKS.CREV or cpks == CPKS.PKREV:
                    if cid_kroot == self.tesla_chain_force.chain_id:
                        logger.info(f"KROOT with CID {cid_kroot} already read and in use.\n")
                        self.tesla_chain_force.update_kroot(dsm_kroot)
                        self.io_handler.store_kroot(dsm_kroot, nma_header)
                    elif cid_kroot == cid:
                        self.tesla_chain_force = TESLAChain(self.nav_data_structure, dsm_kroot)
                        self.io_handler.store_kroot(dsm_kroot, nma_header)
                        self.next_tesla_chain = None
                        logger.warning(f"Chain changed during downtime. Set to CID {cid_kroot}.\n")
                    else:
                        raise ReceiverStatusError(f"CPKS to {cpks.name} and the CIDKR {cid_kroot} is not the "
                                                  f"one stored nor the current CID.")
                elif cpks == CPKS.EOC:
                    # TESLA Chain renewal, stores the new chain if necessary
                    self.chain_status = CPKS.EOC
                    self._store_next_tesla_chain(cid_kroot, dsm_kroot)
                elif cpks == CPKS.NPK:
                    # Public key is being renewed
                    self.chain_status = CPKS.NPK
                else:
                    raise ReceiverStatusError(f"CPKS status not recognized: {cpks.name}")

            elif self.chain_status == CPKS.EOC:
                if cpks == CPKS.EOC:
                    # TESLA Chain renewal, stores the new chain if necessary
                    self._store_next_tesla_chain(cid_kroot, dsm_kroot)
                elif cpks == CPKS.NOMINAL:
                    # The EOC has ended, the next TESLA Chain should be in force
                    self.chain_status = CPKS.NOMINAL
                    if cid != self.tesla_chain_force.chain_id:
                        logger.info("A different kroot should be in force.")
                        if cid == cid_kroot:
                            self.tesla_chain_force = TESLAChain(self.nav_data_structure, dsm_kroot)
                            self.next_tesla_chain = None
                            self.io_handler.store_kroot(dsm_kroot, nma_header)
                            logger.info("The KROOT in force is the one read.")
                        elif self.next_tesla_chain and cid == self.next_tesla_chain.chain_id:
                            self.tesla_chain_force = self.next_tesla_chain
                            self.next_tesla_chain = None
                            new_dsm_kroot = self.tesla_chain_force.dsm_kroot
                            self.io_handler.store_kroot(new_dsm_kroot, new_dsm_kroot.get_value('NMA_H'))
                            logger.info("The KROOT in force is the saved one.")
                        else:
                            raise ReceiverStatusError(f"CID {cid} in CPKS {cpks.name} after CPKS {CPKS.EOC.name} is not"
                                                      f" the one saved in force, nor the one read, nor the next tesla.")
                else:
                    raise ReceiverStatusError(f"CPKS status {cpks.name} not possible after {self.chain_status.name}.")

            elif self.chain_status == CPKS.NPK:
                pkid = dsm_kroot.get_value('PKID').uint
                if pkid != self.current_pkid:
                    logger.info(f"PK in force changed from {self.current_pkid} to {pkid}")
                    self.pkr_dict.pop(self.current_pkid)
                    self.current_pkid = pkid

    def process_kroot_message(self, nma_header, kroot):
        """
        Creates a DSMKroot object with the received information and tries to verify it. If the verification is correct,
        create a TESLAChain object with this key and a MACKMessageParser. Also stores the key by its CID in the
        receivers list.
        :param nma_header:
        :return:
        """
        try:
            dsm_kroot = DSMKroot(self.pkr_dict)
            dsm_kroot.set_value('NMA_H', nma_header)
            dsm_kroot.process_data(kroot)
        except PublicKeyObjectError as e:
            logger.error(f"Problem with the Public Key for authenticating this DSMKroot: {e}")
            if self.start_status == StartStates.WARM_START:
                self._fallback_to_cold_start()
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
                if self.start_status == StartStates.WARM_START:
                    self._fallback_to_cold_start()

    def process_pkr_message(self, pkr):
        dsm_pkr = DSMPKR()
        dsm_pkr.process_data(pkr)
        dsm_pkr.set_merkle_root(self.merkle_root)

        npkid = dsm_pkr.get_value('NPKID').uint
        if dsm_pkr.pkr_verification():
            logger.info(f"PKR with NPKID {npkid} verified.")

            if dsm_pkr.is_OAM:
                logger.warning("OAM Detected - Please connect to the GSC OSNMA Server")
                logger.info("Falling back to Cold Start - Discarding any cryptographic material.\n")
                self.start_status = StartStates.COLD_START
                return

            if npkid not in self.pkr_dict:
                self.pkr_dict[npkid] = dsm_pkr
                self.io_handler.store_pubk(dsm_pkr)
                logger.info(f"New PK. Current PKs: {self.pkr_dict.keys()}")
            else:
                logger.info(f"PK already read: {self.pkr_dict.keys()}")
            if self.start_status == StartStates.COLD_START:
                self.start_status = StartStates.WARM_START
                logger.info(f"Start status from {StartStates.COLD_START.name} to {self.start_status.name}")
        else:
            logger.error(f"PKR with NPKID {npkid} failed.")

    def process_hkroot_subframe(self, hkroot_sf, is_consecutive_hkroot=False):

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
                if self.start_status != StartStates.COLD_START:
                    self.process_kroot_message(sf_nma_header, dsm_data)
            else:
                self.process_pkr_message(dsm_data)

        return sf_nma_header[:2]

    def process_mack_subframe(self, mack_subframe, gst_subframe, svid, sf_nma_status):

        if self.nma_status == NMAS.DONT_USE:
            logger.warning(f"NMA Status: Don't Use. Subframe tags not processed.")
            self.kroot_waiting_mack = []
            return

        if self.tesla_chain_force is None:
            self.kroot_waiting_mack.append((mack_subframe, gst_subframe, svid, sf_nma_status))
        else:
            try:
                if self.kroot_waiting_mack:
                    for w_mack in self.kroot_waiting_mack:
                        self.tesla_chain_force.parse_mack_message(w_mack[0], w_mack[1], w_mack[2], w_mack[3])
                    self.kroot_waiting_mack = []
                self.tesla_chain_force.parse_mack_message(mack_subframe, gst_subframe, svid, sf_nma_status)
                self.tesla_chain_force.update_tag_lists()

            except MackParsingError as e:
                # Unable to parse the message correctly
                logger.error(f"ERROR: Unable to parse the MACK message correctly.\n{e}")
                if self.start_status == StartStates.HOT_START:
                    self._fallback_to_warm_start()
                else:
                    logger.warning("WARNING: Deleting first mack message from waiting list")
                    self.kroot_waiting_mack = self.kroot_waiting_mack[1:]
            except TeslaKeyVerificationFailed as e:
                # Unable to verify the TESLA key
                logger.error(f"Failed authenticating a TESLA key.\n{e}")
                if self.start_status == StartStates.HOT_START:
                    self._fallback_to_warm_start()
                else:
                    logger.warning("WARNING: Deleting first mack message from waiting list")
                    self.kroot_waiting_mack = self.kroot_waiting_mack[1:]
            else:
                if self.start_status == StartStates.HOT_START:
                    self.start_status = StartStates.STARTED
                    logger.info(f"One TESLA key verified. Start Status: {self.start_status.name}")

    def load_page(self, nav_bits, gst_page, svid):
        self.nav_data_structure.load_page(nav_bits, gst_page, svid)


if __name__ == '__main__':
    pass
