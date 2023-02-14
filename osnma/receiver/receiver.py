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

import json
from enum import IntEnum
from pathlib import Path

from bitstring import BitArray

from .satellite import Satellite
from .subframe_regen import SubFrameRegenerator
from osnma.osnma_core.receiver_state import ReceiverState

import osnma.utils.config as config
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)


def load_configuration_parameters(custom_parameters):

    with open(Path(__file__).parent.parent / 'utils/config_params.json') as params_file:
        param_dict = json.load(params_file)
        param_dict.update(custom_parameters)

    if 'exec_path' in param_dict:
        config.EXEC_PATH = Path(param_dict['exec_path'])
    else:
        raise AttributeError("The 'exec_path' is a mandatory parameter.")

    if 'scenario_path' in param_dict:
        config.SCENARIO_PATH = Path(param_dict['scenario_path'])
    else:
        raise AttributeError("The 'scenario_path' is a mandatory parameter.")

    if 'merkle_name' in param_dict:
        config.MERKLE_NAME = str(param_dict['merkle_name'])

    if 'pubk_name' in param_dict:
        config.PUBK_NAME = str(param_dict['pubk_name'])

    if 'kroot_name' in param_dict:
        config.KROOT_NAME = str(param_dict['kroot_name'])

    if 'console_log_level' in param_dict:
        console_log_level = param_dict['console_log_level']
        try:
            config.CONSOLE_LOG_LEVEL = log_factory.str_to_log_level[console_log_level]
        except KeyError:
            if isinstance(console_log_level, int):
                config.CONSOLE_LOG_LEVEL = console_log_level
            else:
                raise KeyError(f'Log level {console_log_level} not defined.')

    if 'file_log_level' in param_dict:
        file_log_level = param_dict['file_log_level']
        try:
            config.FILE_LOG_LEVEL = log_factory.str_to_log_level[file_log_level]
        except KeyError:
            if isinstance(file_log_level, int):
                config.FILE_LOG_LEVEL = file_log_level
            else:
                raise KeyError(f'Log level {file_log_level} not defined.')

    if 'log_console' in param_dict:
        config.LOG_CONSOLE = param_dict['log_console']

    if 'logs_path' in param_dict:
        config.LOGS_PATH = Path(param_dict['logs_path']) if param_dict['logs_path'] else Path(config.EXEC_PATH)

    if 'sync_source' in param_dict:
        config.SYNC_SOURCE = param_dict['sync_source']

    if config.SYNC_SOURCE == SYNC_SOURCE.DEFINED and 'sync_time' in param_dict:
        config.SYNC_TIME = param_dict['sync_time']

    if 'tl' in param_dict:
        config.TL = param_dict['tl']

    if 'b' in param_dict:
        config.B = param_dict['b']

    if 'ns' in param_dict:
        config.NS = param_dict['ns']

    if 'tag_length' in param_dict:
        config.TAG_LENGTH = param_dict['tag_length']


class SYNC_SOURCE(IntEnum):
    SBF = 0
    DEFINED = 1
    NTP = 2
    RTC = 3


class OSNMAReceiver:

    def __init__(self, input_module, param_dict):

        load_configuration_parameters(param_dict)
        log_factory.configure_loggers()

        self.satellites = {}
        for svid in range(config.NS):
            self.satellites[svid+1] = Satellite(svid+1)

        self.nav_data_input = input_module
        self.receiver_state = ReceiverState()
        self.subframe_regenerator = SubFrameRegenerator()

    def _is_dummy_page(self, data):
        return data.nav_bits[2:8].uint == 63

    def _is_alert_page(self, data):
        return data.nav_bits[1]

    def _sync_calculation(self, t_ref, t_sig):
        return (t_ref + config.B - config.TL < t_sig) and (config.B < config.TL//2)

    def sync_check(self, index, data):
        if config.SYNC_SOURCE == SYNC_SOURCE.SBF:
            return True
        elif config.SYNC_SOURCE == SYNC_SOURCE.DEFINED and index == 0:
            t_ref = config.sync_time
        elif config.SYNC_SOURCE == SYNC_SOURCE.NTP:
            t_ref = None
        elif config.SYNC_SOURCE == SYNC_SOURCE.RTC:
            t_ref = None
        else:
            raise Exception(f"{config.sync_source} is not a valid option.")

        return self._sync_calculation(t_ref, data.wn)

    def start(self, max_iter=0):

        for index, data in self.nav_data_input:

            if self._is_alert_page(data):
                continue

            if data.band != 'GAL_L1BC':
                continue

            if self._is_dummy_page(data):
                continue

            if not data.crc:
                logger.warning(f'CRC FAILED\tSVID: {data.svid} - TOW: {data.tow} - Page: {data.tow%30}.'
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
                tow = data.tow//30 * 30
                gst_sf = BitArray(uint=wn, length=12) + BitArray(uint=tow, length=20)
                logger.info(f"--- SUBFRAME --- WN {wn} TOW {tow} SVID {satellite.svid} ---")

                if satellite.subframe_with_osnma():
                    raw_hkroot_sf = satellite.get_hkroot_subframe()
                    hkroot_sf = self.subframe_regenerator.load_dsm_block(raw_hkroot_sf, gst_sf, satellite.svid)
                    if hkroot_sf:
                        # The full subframe has been received consecutively. Use mack_sf.
                        nma_status = self.receiver_state.process_hkroot_subframe(hkroot_sf, is_consecutive_hkroot=True)
                        mack_sf = satellite.get_mack_subframe()
                        self.receiver_state.process_mack_subframe(mack_sf, gst_sf, satellite.svid, nma_status)
                    else:
                        # Broken subframe. Reconstruct if possible hkroot. Noting with mack, yet.
                        for regen_hkroot_sf, bid in self.subframe_regenerator.get_regenerated_blocks():
                            logger.info(f'Regenerated BID {bid}')
                            self.receiver_state.process_hkroot_subframe(regen_hkroot_sf)
                        # Satellite class is filtering and never relying
                        logger.warning('Broken HKROOT Subframe')
                else:
                    logger.info(f"No OSNMA data.")

            if 0 < max_iter < index:
                logger.info("Exit by reaching max iters.")
                return
