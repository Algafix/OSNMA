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

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF, SBFLive
from osnma.input_formats.input_galmon import GALMON


def sbf_live():
    config_dict = {
        'exec_path': 'scenarios/live/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBFLive('192.168.3.1', 20000)
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


def galmon_live():
    config_dict = {
        'exec_path': 'scenarios/galmon_live/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = GALMON()
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


def sbf_new_config():
    config_dict = {
        'scenario_path': 'scenarios/new_live_config/osnma_new_config.sbf',
        'exec_path': 'scenarios/new_live_config/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


if __name__ == "__main__":

    #sbf_new_config()

    galmon_live()

    #sbf_live()
