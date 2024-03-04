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
from typing import Dict, Tuple, Optional
from osnma.input_formats.base_classes import PageIterator, DataFormat

######## imports ########
from osnma.receiver.satellite import Satellite
from osnma.receiver.subframe_regen import SubFrameRegenerator
from osnma.osnma_core.receiver_state import ReceiverState
from osnma.utils.config import Config
from osnma.utils.exceptions import StoppedAtFAF
from osnma.cryptographic.gst_class import GST
from osnma.utils.status_logger import do_status_log
from osnma.utils.bits_logger import BitsLogger

from bitstring import BitArray

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)


class OSNMAReceiver:

    def __init__(self, input_module: PageIterator, param_dict: dict):

        Config.load_configuration_parameters(param_dict)
        log_factory.configure_loggers()

        # Initialize all objects
        self.satellites: Dict[int, Satellite] = {}
        for svid in range(Config.NS):
            self.satellites[svid + 1] = Satellite(svid + 1)

        self.nav_data_input = input_module
        self.receiver_state = ReceiverState()
        self.subframe_regenerator = SubFrameRegenerator()
        self.current_gst_subframe = GST()
        self.bits_logger = BitsLogger()

        Config.FIRST_GST = None

    def _is_dummy_page(self, data: DataFormat) -> bool:
        return data.nav_bits[2:8].uint == 63

    def _is_alert_page(self, data: DataFormat) -> bool:
        return data.nav_bits[1]

    def _get_gst_subframe(self, gst: GST):
        return GST(wn=gst.wn, tow=gst.tow // 30 * 30)

    def _do_status_log(self):
        if Config.DO_STATUS_LOG:
            try:
                do_status_log(self)
            except Exception as e:
                logger.exception(f"Error doing status logging")

    def _do_bits_log(self):
        if Config.DO_BITS_LOG:
            try:
                self.bits_logger.do_bits_log(self.current_gst_subframe, self.satellites)
            except Exception as e:
                logger.exception(f"Error doing bits logging")

    def _filter_page(self, data: DataFormat):
        """
        Filter page if it is not useful for teh current OSNMA implementation.
        Checks for CRC, alert pages, dummy pages, other signals aside from E1BC, etc.
        Also, sets the FIST_TOW variable if not specified.
        """

        if Config.FIRST_GST is None:
            Config.FIRST_GST = data.gst_page

        if not self.current_gst_subframe:
            self.current_gst_subframe = self._get_gst_subframe(data.gst_page)

        if data.gst_page < Config.FIRST_GST:
            return True

        if data.band != 'GAL_L1BC':
            return True

        if self._is_alert_page(data):
            return True

        if self._is_dummy_page(data):
            return True

        if not data.crc:
            logger.warning(f'CRC FAILED\tSVID: {data.svid:02} - TOW: {data.gst_page.tow} - '
                           f'Page: {(data.gst_page.tow % 30):02} - Page NOT processed.')
            return True

        return False

    def _end_of_subframe_satellite(self, gst_sf: GST, satellite: Satellite):
        """
        Process all the data of satellite at the end of the subframe
        """

        logger.info(f"--- SUBFRAME --- WN {gst_sf.wn} TOW {gst_sf.tow} SVID {satellite.svid:02} ---")

        if satellite.subframe_with_osnma():
            raw_hkroot_sf = satellite.get_hkroot_subframe()
            hkroot_sf = self.subframe_regenerator.load_dsm_block(raw_hkroot_sf, gst_sf, satellite.svid)
            if hkroot_sf:
                # The full subframe has been received consecutively.
                nma_status = self.receiver_state.process_hkroot_subframe(hkroot_sf, is_consecutive_hkroot=True)
                mack_sf = satellite.get_mack_subframe()
                self.receiver_state.process_mack_subframe(mack_sf, gst_sf, satellite, nma_status)
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
                        mack_sf, gst_sf, satellite, BitArray(uint=self.receiver_state.nma_status.value, length=2))
        else:
            logger.info(f"No OSNMA data.")

    def _end_of_subframe_global(self):
        """
        Process OSNMA data for all satellites for which we haven't received the last page (we couldn't know if they were
        finished). Note that in a real live scenario a clock can be used instead of having to wait for the next page.
        """
        # Process active subframe satellites for which we lost the last page
        for satellite in self.satellites.values():
            if satellite.is_active() and not satellite.is_already_processed():
                self._end_of_subframe_satellite(self.current_gst_subframe, satellite)
        # Collect status
        self._do_status_log()
        self._do_bits_log()
        # Reset
        for satellite in self.satellites.values():
            if satellite.is_active():
                satellite.reset()

    def start(self, start_at_gst: Optional[Tuple[int, int]] = None):
        """
        Start the processing of data from the defined input module.

        :param start_at_gst: Tuple with (WN, TOWs) telling the receiver when to start to process OSNMA data. If not
            provided, the TTFAF will be calculated with respect to the first GST read.
        """

        if start_at_gst:
            Config.FIRST_GST = GST(wn=start_at_gst[0], tow=start_at_gst[1])

        try:
            for page in self.nav_data_input:

                if self._filter_page(page):
                    continue

                # The subframe has finished, process leftovers of OSNMA data and reset objects
                if (gst_sf := self._get_gst_subframe(page.gst_page)) > self.current_gst_subframe:
                    self._end_of_subframe_global()
                    self.current_gst_subframe = gst_sf

                # Add OSNMA data to satellite
                satellite = self.satellites[page.svid]
                satellite.new_page(page)

                # Add nav data of the page to the navigation data manager
                self.receiver_state.load_nav_data_page(page.nav_bits, page.gst_page, satellite)

                # If we get the last subframe page of this satellite, process it now instead of waiting
                if page.gst_page % 30 == 29:
                    self._end_of_subframe_satellite(self.current_gst_subframe, satellite)
                    satellite.set_already_processed()

        except StoppedAtFAF as e:
            self._do_status_log()
            return e.ttfaf, e.first_tow, e.faf_tow
