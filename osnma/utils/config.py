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


class Config:

    SCENARIO_PATH = ''
    EXEC_PATH = ''
    MERKLE_NAME = 'OSNMA_MerkleTree.xml'
    PUBK_NAME = ''
    KROOT_NAME = ''

    FILE_LOG_LEVEL = logging.INFO
    CONSOLE_LOG_LEVEL = logging.DEBUG
    LOG_CONSOLE = True
    LOG_FILE = True
    LOGS_PATH = ''

    SYNC_SOURCE = 0
    SYNC_TIME = None
    TL = 30
    B = 1

    NS = 36
    TAG_LENGTH = 40
    ACTIVE_ADKD = {0, 4, 12}

    DO_HKROOT_REGEN = True
    DO_CRC_FAILED_EXTRACTION = True
    DO_TESLA_KEY_REGEN = True

    STOP_AT_FAF = False
    FIRST_GST = None

    @classmethod
    def load_configuration_parameters(cls, param_dict: Dict[str, Any]):

        if not param_dict['exec_path']:
            raise AttributeError("The 'exec_path' is a mandatory parameter.")

        for k, v in param_dict.items():
            if k.upper() in cls.__dict__:
                if 'LOG_LEVEL' in k.upper() and type(v) == str:
                    v = log_factory.str_to_log_level[v]
                elif k.upper().endswith('_PATH'):
                    v = Path(v)
                setattr(cls, k.upper(), v)

        if not param_dict.get('logs_path', False):
            cls.LOGS_PATH = cls.EXEC_PATH

class SYNC_SOURCE(IntEnum):
    SBF = 0
    DEFINED = 1
    NTP = 2
    RTC = 3
