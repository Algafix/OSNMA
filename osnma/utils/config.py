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

import logging
from typing import Dict, Any
from pathlib import Path
from enum import IntEnum

import osnma.utils.logger_factory as log_factory


class _Config:

    def __init__(self):
        self.SCENARIO_PATH = ''  # Not needed, may be used for debug
        self.EXEC_PATH = ''
        self.MERKLE_NAME = 'OSNMA_MerkleTree.xml'
        self.PUBK_NAME = ''
        self.KROOT_NAME = ''
        self.NEW_MERKLE_NAME = 'new_OSNMA_MerkleTree.xml'

        self.FILE_LOG_LEVEL = logging.INFO
        self.CONSOLE_LOG_LEVEL = logging.INFO
        self.LOGS_PATH = ''

        self.LOG_CONSOLE = True
        self.LOG_FILE = True
        self.DO_VERBOSE_LOG = True
        self.DO_STATUS_LOG = True
        self.DO_LAST_STATUS_LOGGING = False
        self.LAST_STATUS_FILE = 'last_state.json'
        self.DO_API_LOGGING = False
        self.API_SUBFRAME_BITS_FILE = 'api_subframe_bits.json'
        self.API_SUBFRAME_STATUS_FILE = 'api_subframe_status.json'

        self.SYNC_SOURCE = 0
        self.SYNC_TIME = None
        self.TL = 30
        self.B = 1

        self.NS = 36
        self.TAG_LENGTH = 40
        self.ACTIVE_ADKD = {0, 4, 12}

        self.DO_HKROOT_REGEN = True
        self.DO_CRC_FAILED_EXTRACTION = True
        self.DO_TESLA_KEY_REGEN = True
        self.DO_COP_LINK_OPTIMIZATION = False
        self.DO_DUAL_FREQUENCY = False
        self.STOP_AT_FAF = False

        self.FIRST_GST = None
        self.LAST_GST = None

    def load_configuration_parameters(self, param_dict: Dict[str, Any]):
        """
        Re-loads the default configuration and adds the configuration defined in `param_dict`.
        """

        self.__init__()

        if not param_dict['exec_path']:
            raise AttributeError("The 'exec_path' is a mandatory parameter.")

        for k, v in param_dict.items():
            if (attr := k.upper()) in self.__dict__:
                if 'LOG_LEVEL' in attr and isinstance(v, str):
                    v = log_factory.str_to_log_level[v]
                elif attr.endswith('_PATH'):
                    v = Path(v)
                setattr(self, attr, v)

        if not param_dict.get('logs_path', False):
            self.LOGS_PATH = self.EXEC_PATH

Config = _Config()


class SYNC_SOURCE(IntEnum):
    SBF = 0
    DEFINED = 1
    NTP = 2
    RTC = 3
