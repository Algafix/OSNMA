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
from typing import TYPE_CHECKING, Dict, List
if TYPE_CHECKING:
    from osnma.receiver.receiver import OSNMAReceiver
    from osnma.receiver.satellite import Satellite
    from osnma.cryptographic.gst_class import GST
    from osnma.structures.mack_structures import TagAndInfo, TESLAKey

### imports ###
import pprint
import json
from enum import Enum
from osnma.structures.maclt import mac_lookup_table
from osnma.structures.fields_information import mf_lt, hf_lt, npkt_lt, KS_lt, TS_lt, NMAS, CPKS, OSNMAlibSTATE
from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)

class ADKD(Enum):
    ADKD0 = 0
    ADKD4 = 4
    ADKD12 = 12

STATUS_DICT_TEMPLATE = {
    "Metadata": {
        "GST Subframe": None,
        "Input Module": None,
        "OSNMAlib Status": None,
    },
    "OSNMA Status": None,
    "OSNMA Authenticated Data": None,
    "Nav Data Received": None,
    "OSNMA Data": None
}

class _StatusLogger:

    def __init__(self):

        self.current_subframe_dict = {}
        self.osnma_mack_data = {}
        self.nav_data = {}

    def _get_pkr_dict(self, osnma_r: 'OSNMAReceiver'):

        if osnma_r.receiver_state.osnmalib_state == OSNMAlibSTATE.STARTED:
            # We know the current pkid is in force
            pubk_id = osnma_r.receiver_state.current_pkid
            pkr_handler = osnma_r.receiver_state.pkr_dict[pubk_id]
        elif osnma_r.receiver_state.nma_status == NMAS.DONT_USE:
            if osnma_r.receiver_state.chain_status == CPKS.CREV:
                # The pubk is still valid
                pubk_id = osnma_r.receiver_state.log_last_kroot_auth.get_value('PKID').uint
                pkr_handler = osnma_r.receiver_state.pkr_dict[pubk_id]
            elif osnma_r.receiver_state.log_last_pkr_auth is not None:
                # Case of PKREV or OAM
                pkr_handler = osnma_r.receiver_state.log_last_pkr_auth
            else:
                return None
        else:
            return None

        osnma_pubk_dict = {"NPKID": pkr_handler.get_value("NPKID").uint,
                           "NPKT": npkt_lt[pkr_handler.get_value("NPKT").uint].name,
                           "MID": pkr_handler.get_value("MID").uint}
        return osnma_pubk_dict

    def _get_kroot_dict(self, osnma_r: 'OSNMAReceiver'):

        if osnma_r.receiver_state.osnmalib_state == OSNMAlibSTATE.STARTED:
            # We have a TESLA chain in force
            kroot_handler = osnma_r.receiver_state.tesla_chain_force.dsm_kroot
        elif osnma_r.receiver_state.nma_status == NMAS.DONT_USE and osnma_r.receiver_state.log_last_kroot_auth is not None:
            # Case of DNU with CREV or AM
            kroot_handler = osnma_r.receiver_state.log_last_kroot_auth
        else:
            return None

        osnma_chain_dict = {"NMAS": osnma_r.receiver_state.nma_status.name,
                            "CID": kroot_handler.get_value("CIDKR").uint,
                            "CPKS": osnma_r.receiver_state.chain_status.name,
                            "PKID": kroot_handler.get_value("PKID").uint,
                            "HF": hf_lt[kroot_handler.get_value('HF').uint].name,
                            "MF": mf_lt[kroot_handler.get_value('MF').uint].name,
                            "KS": KS_lt[kroot_handler.get_value('KS').uint],
                            "TS": TS_lt[kroot_handler.get_value('TS').uint],
                            "MACLT": kroot_handler.get_value('MACLT').uint}
        maclt_sequence = mac_lookup_table[osnma_chain_dict["MACLT"]]["sequence"]
        osnma_chain_dict["MACLT Sequence"] = maclt_sequence
        return osnma_chain_dict

    def _get_osnma_chain_dict(self, osnma_r: 'OSNMAReceiver') -> Dict:
        osnma_status_dict = {"Tesla Chain in Force": self._get_kroot_dict(osnma_r),
                             "Public Key in Force": self._get_pkr_dict(osnma_r)}

        return osnma_status_dict

    def _get_osnma_data_auth_dict(self, osnma_r: 'OSNMAReceiver') -> Dict:
        osnma_data_dict = {"ADKD0": {}, "ADKD4": {}, "ADKD12": {}}

        auth_data_dict_handler = osnma_r.receiver_state.nav_data_structure.authenticated_data_dict
        for data_block in auth_data_dict_handler.values():
            svid = f"{data_block.prn_d:02d}"
            adkd = data_block.adkd
            last_adkd_per_sat = osnma_data_dict[f"ADKD{adkd}"]
            if not (saved_data := last_adkd_per_sat.get(svid, False)):
                last_adkd_per_sat[svid] = data_block
            elif saved_data.last_gst < data_block.last_gst:
                last_adkd_per_sat[svid] = data_block

        for adkd in osnma_data_dict.values():
            for svid in adkd.keys():
                adkd[svid] = adkd[svid].get_json()

        return osnma_data_dict

    def log_nav_data(self, svid_int: int, adkd, word_type):
        svid = f"{svid_int:02d}"
        self.nav_data[svid][ADKD(adkd).name][word_type] = True

    def load_mack_data(self, svid_int: int, tag_list: List['TagAndInfo'], tesla_key: 'TESLAKey'):
        svid = f"{svid_int:02d}"
        self.osnma_mack_data[svid]["Tags"] = tag_list
        self.osnma_mack_data[svid]["Key"] = tesla_key if tesla_key is None else tesla_key.get_json()

    def add_satellite(self, gst_sf: 'GST', satellite: 'Satellite'):
        svid = f"{satellite.svid:02d}"

        # Initialize nav data
        if svid not in self.nav_data:
            self.nav_data[svid] = {
                "ADKD0": {1: False, 2: False, 3: False, 4: False, 5: False},
                "ADKD4": {6: False, 10: False},
            }
            if gst_sf.tow % 60 == 0:
                self.nav_data[svid]["ADKD4"][10] = None

        # initialize OSNMA data
        if satellite.subframe_with_osnma():
            self.osnma_mack_data[svid] = {"Tags": [], 'Key': None}

    def do_status_log(self, osnma_r: 'OSNMAReceiver'):

        status_dict = {
            "Metadata": {
                "GST Subframe": [osnma_r.current_gst_subframe.wn, osnma_r.current_gst_subframe.tow],
                "Input Module": osnma_r.nav_data_input.__class__.__name__,
                "OSNMAlib Status": osnma_r.receiver_state.osnmalib_state.name,
            },
            "OSNMA Status": self._get_osnma_chain_dict(osnma_r),
            "OSNMA Authenticated Data": self._get_osnma_data_auth_dict(osnma_r),
            "Nav Data Received": dict(sorted(self.nav_data.items())),
            "OSNMA Data": dict(sorted(self.osnma_mack_data.items()))
        }

        string_object = (f"--- STATUS END OF SUBFRAME GST {osnma_r.current_gst_subframe} ---\n\n"
                         f"OSNMAlib Status: {status_dict['Metadata']['OSNMAlib Status']}\n\n"
                         f"## Nav Data Received in the Subframe\n"
                         f"{pprint.pformat(status_dict['Nav Data Received'], sort_dicts=False, width=150)}\n\n"
                         f"## OSNMA Data Received in the Subframe\n"
                         f"{pprint.pformat(status_dict['OSNMA Data'], sort_dicts=False, width=150)}\n\n"
                         f"## OSNMA Status\n"
                         f"{pprint.pformat(status_dict['OSNMA Status'], sort_dicts=False, width=100, compact=True)}\n\n"
                         f"## OSNMA Authenticated Data\n"
                         f"{pprint.pformat(status_dict['OSNMA Authenticated Data'], sort_dicts=False, width=150)}\n")
        logger.info(string_object)

        if Config.DO_JSON_STATUS:
            with open(Config.JSON_STATUS_PATH, 'w') as f:
                json.dump(status_dict, f)

        self.osnma_mack_data = {}
        self.nav_data = {}

StatusLogger = _StatusLogger()
