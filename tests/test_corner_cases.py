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

import sys
sys.path.insert(0, '..')
import re
import logging
from pathlib import Path

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF
import osnma.utils.logger_factory as logger_factory
LOGS_PATH = Path(__file__).parent / 'corner_cases_logs/'


def get_base_logger_and_file_handler():
    base_logger = logger_factory.get_logger('osnma')
    file_handler = None
    log_filename = None

    for handler in base_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            log_filename = file_handler.baseFilename
            break

    return base_logger, file_handler, log_filename


def change_of_word_type_5(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/change_of_word_type_5/change_wt5.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/change_of_word_type_5/',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_last_KROOT.txt'
    }

    input_module = SBF(config_dict['scenario_path'], use_satellites_list=[25,3,5])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start(start_at_tow=133650)

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)



if __name__ == "__main__":

    general_log_level = logging.ERROR
    test_passed = 0
    test_done = 0

    print(f"\nChange of Word Type 5")
    try:
        change_of_word_type_5(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print('\n=====================================')
    print(f'\tTEST PASSED: {test_passed}/{test_done}')
    print('=====================================')



