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

from bitstring import BitArray

from .satellite import Satellite
from .subframe_regen import SubFrameRegenerator
from osnma.osnma_core.receiver_state import ReceiverState

from osnma.utils.config import Config, SYNC_SOURCE
import osnma.utils.logger_factory as log_factory

logger = log_factory.get_logger(__name__)


class OSNMAReceiver:

    def __init__(self, input_module, param_dict):

        Config.load_configuration_parameters(param_dict)
        log_factory.configure_loggers()

        self.satellites = {}
        for svid in range(Config.NS):
            self.satellites[svid + 1] = Satellite(svid + 1)

        self.nav_data_input = input_module
        self.receiver_state = ReceiverState()
        self.subframe_regenerator = SubFrameRegenerator()

    def _is_dummy_page(self, data):
        return data.nav_bits[2:8].uint == 63

    def _is_alert_page(self, data):
        return data.nav_bits[1]

    def _sync_calculation(self, t_ref, t_sig):
        return (t_ref + Config.B - Config.TL < t_sig) and (Config.B < Config.TL // 2)

    def sync_check(self, index, data):
        if Config.SYNC_SOURCE == SYNC_SOURCE.SBF:
            return True
        elif Config.SYNC_SOURCE == SYNC_SOURCE.DEFINED and index == 0:
            t_ref = Config.SYNC_TIME
        elif Config.SYNC_SOURCE == SYNC_SOURCE.NTP:
            t_ref = None
        elif Config.SYNC_SOURCE == SYNC_SOURCE.RTC:
            t_ref = None
        else:
            raise Exception(f"{Config.SYNC_SOURCE} is not a valid option.")

        return self._sync_calculation(t_ref, data.wn)

    def start(self, max_iter=0):

        for index, data in self.nav_data_input:

            if index == 0:
                Config.FIRST_TOW = data.tow

            if self._is_alert_page(data):
                continue

            if data.band != 'GAL_L1BC':
                continue

            if self._is_dummy_page(data):
                continue

            if not data.crc:
                logger.warning(f'CRC FAILED\tSVID: {data.svid:02} - TOW: {data.tow} - Page: {(data.tow % 30):02}. '
                               f'Page NOT processed.')
                continue

            self.sync_check(index, data)
            satellite = self.satellites[data.svid]

            # Handle page
            gst_page = BitArray(uint=data.wn, length=12) + BitArray(uint=data.tow, length=20)
            self.receiver_state.load_page(data.nav_bits, gst_page, satellite.svid)
            satellite.new_page(data, data.tow)

            # End of the subframe
            if data.tow % 30 == 29:
                wn = data.wn
                tow = data.tow // 30 * 30
                gst_sf = BitArray(uint=wn, length=12) + BitArray(uint=tow, length=20)
                logger.info(f"--- SUBFRAME --- WN {wn} TOW {tow} SVID {satellite.svid} ---")

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

            if 0 < max_iter < index:
                logger.info("Exit by reaching max iters.")
                return
