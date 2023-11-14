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
from typing import List, Dict, Optional
from osnma.input_formats.base_classes import PageIterator, DataFormat

######## imports ########
from osnma.receiver.satellite import Satellite
from osnma.receiver.subframe_regen import SubFrameRegenerator
from osnma.osnma_core.receiver_state import ReceiverState
from osnma.utils.config import Config
from osnma.cryptographic.gst_class import GST

from bitstring import BitArray

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)


class OSNMAReceiver:

    def __init__(self, input_module: PageIterator, param_dict: dict):

        Config.load_configuration_parameters(param_dict)
        log_factory.configure_loggers()

        self.satellites: Dict[int, Satellite] = {}
        for svid in range(Config.NS):
            self.satellites[svid + 1] = Satellite(svid + 1)

        self.nav_data_input = input_module
        self.receiver_state = ReceiverState()
        self.subframe_regenerator = SubFrameRegenerator()

    def _is_dummy_page(self, data: DataFormat) -> bool:
        return data.nav_bits[2:8].uint == 63

    def _is_alert_page(self, data: DataFormat) -> bool:
        return data.nav_bits[1]

    def _sync_calculation(self, t_ref, t_sig):
        return (t_ref + Config.B - Config.TL < t_sig) and (Config.B < Config.TL // 2)

    def filter_page(self, data: DataFormat):
        """
        Filter page if it is not useful for teh current OSNMA implementation.
        Checks for CRC, alert pages, dummy pages, other signals aside from E1BC, etc.
        Also, sets the FIST_TOW variable if not specified.

        :param data: Complete page to filter if needed.
        :return: True if needs to be filtered out, False otherwise.
        """

        if Config.FIRST_TOW is None:
            Config.FIRST_TOW = data.tow

        if data.tow < Config.FIRST_TOW:
            return True

        if data.band != 'GAL_L1BC':
            return True

        if self._is_alert_page(data):
            return True

        if self._is_dummy_page(data):
            return True

        if not data.crc:
            logger.warning(f'CRC FAILED\tSVID: {data.svid:02} - TOW: {data.tow} - Page: {(data.tow % 30):02}. '
                           f'Page NOT processed.')
            return True

        return False

    def start(self, start_at_tow: Optional[int] = None):

        # If not defined, it will select the first tow read
        Config.FIRST_TOW = start_at_tow

        for page in self.nav_data_input:

            if self.filter_page(page):
                continue

            satellite = self.satellites[page.svid]

            # Handle page
            gst_page = GST(wn=page.wn, tow=page.tow)
            self.receiver_state.load_page(page.nav_bits, gst_page, satellite.svid)
            satellite.new_page(page, page.tow)

            # End of the subframe
            if page.tow % 30 == 29:
                gst_sf = GST(wn=page.wn, tow=page.tow // 30 * 30)
                logger.info(f"--- SUBFRAME --- WN {gst_sf.wn} TOW {gst_sf.tow} SVID {satellite.svid} ---")

                if satellite.subframe_with_osnma():
                    raw_hkroot_sf = satellite.get_hkroot_subframe()
                    hkroot_sf = self.subframe_regenerator.load_dsm_block(raw_hkroot_sf, gst_sf, satellite.svid)
                    if hkroot_sf:
                        # The full subframe has been received consecutively.
                        nma_status = self.receiver_state.process_hkroot_subframe(hkroot_sf, is_consecutive_hkroot=True)
                        mack_sf = satellite.get_mack_subframe()
                        self.receiver_state.process_mack_subframe(mack_sf, gst_sf, satellite.svid, nma_status)
                    else:
                        # Broken subframe. Reconstruct if possible hkroot. Extract what is possible from MACK.
                        logger.warning('Broken HKROOT Subframe. Regenerating HKROOT and processing MACK if active.')
                        if Config.DO_HKROOT_REGEN:
                            for regen_hkroot_sf, bid in self.subframe_regenerator.get_regenerated_blocks():
                                logger.info(f'HKROOT regenerated. BID {bid}')
                                self.receiver_state.process_hkroot_subframe(regen_hkroot_sf)
                        if Config.DO_CRC_FAILED_EXTRACTION:
                            mack_sf = satellite.get_mack_subframe()
                            self.receiver_state.process_mack_subframe(
                                mack_sf, gst_sf, satellite.svid, BitArray(uint=self.receiver_state.nma_status.value, length=2))
                else:
                    logger.info(f"No OSNMA data.")
