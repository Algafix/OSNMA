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
from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from osnma.receiver.receiver import OSNMAReceiver
    from osnma.receiver.satellite import Satellite

### imports ###
import pprint
from osnma.structures.maclt import mac_lookup_table
from osnma.structures.fields_information import mf_lt, hf_lt, npkt_lt
from osnma.osnma_core.receiver_state import StartStates

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)


def int_pformat(object, indent=1, width=80, depth=None, *, compact=False, sort_dicts=True):
    class FormatPrinter(pprint.PrettyPrinter):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def format(self, object, context, maxlevels, level):
            if isinstance(object, int):
                return f'{object:02d}', 1, 0
            else:
                return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

    return FormatPrinter(indent=indent, width=width, depth=depth,
                         compact=compact, sort_dicts=sort_dicts).pformat(object)


def _get_osnma_chain_dict(osnma_r: 'OSNMAReceiver') -> Dict:
    osnma_status_dict = {"Tesla Chain in Force": None, "Public Key in Force": None}

    if osnma_r.receiver_state.start_status == StartStates.STARTED:
        osnma_chain_dict = {}
        kroot_handler = osnma_r.receiver_state.tesla_chain_force.dsm_kroot
        osnma_chain_dict["NMAS"] = osnma_r.receiver_state.nma_status.name
        osnma_chain_dict["CID"] = osnma_r.receiver_state.tesla_chain_force.chain_id
        osnma_chain_dict["CPKS"] = osnma_r.receiver_state.chain_status.name
        osnma_chain_dict["PKID"] = osnma_r.receiver_state.current_pkid
        osnma_chain_dict["HF"] = hf_lt[kroot_handler.get_value('HF').uint].name
        osnma_chain_dict["MF"] = mf_lt[kroot_handler.get_value('MF').uint].name
        osnma_chain_dict["KS"] = osnma_r.receiver_state.tesla_chain_force.key_size
        osnma_chain_dict["TS"] = osnma_r.receiver_state.tesla_chain_force.tag_size
        osnma_chain_dict["MACLT"] = osnma_r.receiver_state.tesla_chain_force.maclt
        maclt_sequence = mac_lookup_table[osnma_chain_dict["MACLT"]]["sequence"]
        osnma_chain_dict["MACLT Sequence"] = maclt_sequence
        osnma_status_dict["Tesla Chain in Force"] = osnma_chain_dict

        osnma_pubk_dict = {}
        pubk_id = osnma_r.receiver_state.current_pkid
        pkr_in_force_handler = osnma_r.receiver_state.pkr_dict[pubk_id]
        osnma_pubk_dict["NPKID"] = pkr_in_force_handler.get_value("NPKID").uint
        osnma_pubk_dict["NPKT"] = npkt_lt[pkr_in_force_handler.get_value("NPKT").uint].name
        osnma_pubk_dict["MID"] = pkr_in_force_handler.get_value("MID").uint

        osnma_status_dict["Public Key in Force"] = osnma_pubk_dict

    return osnma_status_dict


def _get_osnma_data_auth_dict(osnma_r: 'OSNMAReceiver') -> Dict:
    osnma_data_dict = {"ADKD0": {}, "ADKD4": {}, "ADKD12": {}}

    auth_data_dict_handler = osnma_r.receiver_state.nav_data_structure.authenticated_data_dict
    for data_block in auth_data_dict_handler.values():
        svid = data_block.prn_d
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


def _get_subframe_nav_data(satellites: Dict[int, 'Satellite']) -> Dict:
    nav_data_per_satellite = {}
    for svid, satellite in satellites.items():
        if satellite.is_active():
            nav_data_per_satellite[svid] = {"ADKD0": satellite.words_adkd0, "ADKD4": satellite.words_adkd4}
    return nav_data_per_satellite


def _get_subframe_osnma_data(osnma_r: 'OSNMAReceiver', satellites: Dict[int, 'Satellite']):
    osnma_data_per_satellite = {}
    if osnma_r.receiver_state.start_status != StartStates.STARTED:
        return f"OSNMA has not started: {osnma_r.receiver_state.start_status.name}"
    for svid, satellite in satellites.items():
        if satellite.is_active() and satellite.subframe_with_osnma():
            osnma_data_per_satellite[svid] = {"Tags": satellite.osnma_tags_log}
            tk_log = satellite.osnma_tesla_key_log
            osnma_data_per_satellite[svid]["Key"] = tk_log if tk_log is None else tk_log.get_json()

    return osnma_data_per_satellite


def do_status_log(osnma_r: 'OSNMAReceiver'):

    status_dict = {"OSNMA Status": {}}
    status_dict["OSNMA Status"] = _get_osnma_chain_dict(osnma_r)
    status_dict["OSNMA Authenticated Data"] = _get_osnma_data_auth_dict(osnma_r)
    status_dict["Nav Data Received"] = _get_subframe_nav_data(osnma_r.satellites)
    status_dict["OSNMA Data"] = _get_subframe_osnma_data(osnma_r, osnma_r.satellites)

    string_object = (f"--- STATUS END OF SUBFRAME GST {osnma_r.current_gst_subframe} ---\n\n"
                     f"## Nav Data Received in the Subframe\n"
                     f"{int_pformat(status_dict['Nav Data Received'], sort_dicts=False, width=150)}\n\n"
                     f"## OSNMA Data Received in the Subframe\n"
                     f"{int_pformat(status_dict['OSNMA Data'], sort_dicts=False, width=150)}\n\n"
                     f"## OSNMA Status\n"
                     f"{pprint.pformat(status_dict['OSNMA Status'], sort_dicts=False, width=150)}\n\n"
                     f"## OSNMA Authenticated Data\n"
                     f"{int_pformat(status_dict['OSNMA Authenticated Data'], sort_dicts=False, width=150)}\n")
    logger.info(string_object)
