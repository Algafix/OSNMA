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
from typing import TYPE_CHECKING, Dict, List, Optional
if TYPE_CHECKING:
    from bitstring import BitArray
    from osnma.receiver.receiver import OSNMAReceiver
    from osnma.receiver.satellite import Satellite
    from osnma.cryptographic.gst_class import GST
    from osnma.structures.mack_structures import TagAndInfo, TESLAKey, MACSeqObject
    from osnma.cryptographic.dsm_pkr import DSMPKR
    from osnma.cryptographic.dsm_kroot import DSMKroot
    from io import TextIOWrapper

### imports ###
import pprint
import json
from enum import Enum
from pathlib import Path
from osnma.structures.maclt import mac_lookup_table
from osnma.structures.fields_information import (mf_lt, hf_lt, npkt_lt, KS_lt, TS_lt, NMAS, CPKS, OSNMAlibSTATE,
                                                 parse_nma_header, NB_DP_lt, NB_DK_lt)
from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)

class ADKD(Enum):
    ADKD0 = 0
    ADKD4 = 4
    ADKD12 = 12

class _StatusLogger:

    def __init__(self, logs_path = None):

        self.json_file_name: Optional[Path] = logs_path / 'status_log.json' if logs_path is not None else None
        self.json_file: Optional[TextIOWrapper] = None

        self.osnma_material_received = {}
        self.nav_data_received = {}
        self.verified_osnma_material = {
            "tesla_key": [],
            "macseq": [],
            "tags": [],
            "last_kroot": None,
            "last_pkr": None,
        }

        self.last_verified_kroot: Optional['DSMKroot'] = None
        self.last_verified_pkr: Optional['DSMPKR'] = None

    def _get_nma_status(self, osnma_r: 'OSNMAReceiver'):
        nma_status = {
            'nmas': osnma_r.receiver_state.nma_status.name if osnma_r.receiver_state.nma_status else None,
            'cid': osnma_r.receiver_state.chain_id,
            'cpks': osnma_r.receiver_state.chain_status.name if osnma_r.receiver_state.chain_status else None,
        }
        return nma_status

    def _get_pkr_in_force(self, osnma_r: 'OSNMAReceiver'):

        if osnma_r.receiver_state.osnmalib_state == OSNMAlibSTATE.STARTED:
            # We know the current pkid is in force
            pubk_id = osnma_r.receiver_state.current_pkid
            pkr_handler = osnma_r.receiver_state.pkr_dict[pubk_id]
        elif osnma_r.receiver_state.nma_status == NMAS.DONT_USE:
            if osnma_r.receiver_state.chain_status == CPKS.CREV:
                # The pubk is still valid
                pubk_id = self.last_verified_kroot.get_value('PKID').uint
                pkr_handler = osnma_r.receiver_state.pkr_dict[pubk_id]
            elif self.last_verified_pkr is not None:
                # Case of PKREV or OAM
                pkr_handler = self.last_verified_pkr
            else:
                return None
        else:
            return None

        osnma_pubk_dict = {
            "npkid": pkr_handler.get_value("NPKID").uint,
            "npkt": npkt_lt[pkr_handler.get_value("NPKT").uint].name,
            "mid": pkr_handler.get_value("MID").uint
        }
        return osnma_pubk_dict

    def _get_chain_in_force(self, osnma_r: 'OSNMAReceiver'):

        if osnma_r.receiver_state.osnmalib_state == OSNMAlibSTATE.STARTED:
            # We have a TESLA chain in force
            kroot_handler = osnma_r.receiver_state.tesla_chain_force.dsm_kroot
        elif osnma_r.receiver_state.nma_status == NMAS.DONT_USE and self.last_verified_kroot is not None:
            # Case of DNU with CREV or AM
            kroot_handler = self.last_verified_kroot
        else:
            return None

        osnma_chain_dict = {
            "pkid": kroot_handler.get_value("PKID").uint,
            "cidkr": kroot_handler.get_value("CIDKR").uint,
            "hf": hf_lt[kroot_handler.get_value('HF').uint].name,
            "mf": mf_lt[kroot_handler.get_value('MF').uint].name,
            "ks": KS_lt[kroot_handler.get_value('KS').uint],
            "ts": TS_lt[kroot_handler.get_value('TS').uint],
            "maclt": kroot_handler.get_value('MACLT').uint,
        }
        maclt_sequence = mac_lookup_table[osnma_chain_dict["maclt"]]["sequence"]
        osnma_chain_dict["maclt_sequence"] = maclt_sequence
        return osnma_chain_dict

    def _get_osnma_status_dict(self, osnma_r: 'OSNMAReceiver') -> Dict:
        osnma_status_dict = {
            "nma_status": self._get_nma_status(osnma_r),
            "tesla_chain_in_force": self._get_chain_in_force(osnma_r),
            "public_key_in_force": self._get_pkr_in_force(osnma_r)
        }

        return osnma_status_dict

    def _get_authenticated_nav_data(self, osnma_r: 'OSNMAReceiver') -> Dict:
        osnma_data_dict = {"ADKD0": {}, "ADKD4": {}, "ADKD12": {}}

        auth_data_dict_handler = osnma_r.receiver_state.nav_data_structure.authenticated_data_dict
        for data_block in auth_data_dict_handler.values():
            svid = data_block.prn_d
            adkd = data_block.adkd
            last_adkd_per_sat = osnma_data_dict[ADKD(adkd).name]
            if not (saved_data := last_adkd_per_sat.get(svid, False)):
                last_adkd_per_sat[svid] = data_block
            elif saved_data.last_gst < data_block.last_gst:
                last_adkd_per_sat[svid] = data_block

        for adkd in osnma_data_dict.values():
            for svid in adkd.keys():
                adkd[svid] = adkd[svid].get_json()

        return osnma_data_dict

    def _parse_tag(self, tag: 'TagAndInfo'):
        tag_dict = {
            'prn_a': tag.prn_a.uint,
            'prn_d': tag.prn_d.uint,
            'adkd': tag.adkd.uint,
            'cop': tag.cop.uint,
            'flx': tag.is_flx,
            'verification': tag.is_verified,
            'GST': [tag.gst_subframe.wn, tag.gst_subframe.tow]
        }
        return tag_dict

    def log_auth_macseq(self, macseq: 'MACSeqObject'):
        macseq_dict = {
            'prn_a': macseq.svid.uint,
            'flex_tags': [tag.get_json() for tag in macseq.flex_list],
            'verification': macseq.is_verified,
            'GST': [macseq.gst.wn, macseq.gst.tow],
        }
        self.verified_osnma_material['macseq'].append(macseq_dict)

    def log_auth_tag(self, tag: 'TagAndInfo'):
        tag_dict = self._parse_tag(tag)
        self.verified_osnma_material['tags'].append(tag_dict)

    def log_auth_tesla_key(self, tesla_key: 'TESLAKey'):
        tesla_key_dict = {
            'svid': tesla_key.svid,
            'verification': tesla_key.verified,
            'GST': [tesla_key.gst_sf.wn, tesla_key.gst_sf.tow],
            'reconstructed': tesla_key.reconstructed
        }
        self.verified_osnma_material['tesla_key'].append(tesla_key_dict)

    def log_auth_kroot(self, dsm_kroot: 'DSMKroot'):
        if dsm_kroot.is_verified():
            self.last_verified_kroot = dsm_kroot

        nmas, cid, cpks = parse_nma_header(dsm_kroot.get_value("NMA_H"))
        reserved_nmah = int(dsm_kroot.get_value("NMA_H")[-1])

        nb_dk = dsm_kroot.get_value("NB_DK").uint
        pkid = dsm_kroot.get_value("PKID").uint
        cidkr = dsm_kroot.get_value("CIDKR").uint
        reserved1 = dsm_kroot.get_value("NMACK").uint
        hf = dsm_kroot.get_value("HF").uint
        mf = dsm_kroot.get_value("MF").uint
        ks = dsm_kroot.get_value("KS").uint
        ts = dsm_kroot.get_value("TS").uint
        maclt = dsm_kroot.get_value("MACLT").uint
        reserved2 = (dsm_kroot.get_value("KROOT_R") + dsm_kroot.get_value("MO")).uint
        wn_k = dsm_kroot.get_value("WN_K").uint
        towh_k = dsm_kroot.get_value("TOWH_K").uint
        alpha = dsm_kroot.get_value("ALPHA").hex
        kroot = dsm_kroot.get_value("KROOT").hex
        ds = dsm_kroot.get_value("DS").hex
        p_dk = dsm_kroot.get_value("P_DK").bin

        dsm_kroot_dict = {
            "verification": dsm_kroot.is_verified(),
            "nma_header": {
                "nmas": [nmas.value, nmas.name],
                "cid": [cid, None],
                "cpks": [cpks.value, cpks.name],
                "reserved_nmah": [reserved_nmah, None],
            },
            "fields": {
                "nb_dk": [nb_dk, NB_DK_lt[nb_dk]],
                "pkid": [pkid, None],
                "cidkr": [cidkr, None],
                "reserved1": [reserved1, None],
                "hf": [hf, hf_lt[hf].name],
                "mf": [mf, mf_lt[mf].name],
                "ks": [ks, KS_lt[ks]],
                "ts": [ts, TS_lt[ts]],
                "maclt": [maclt, None],
                "reserved2": [reserved2, None],
                "wn_k": [wn_k, None],
                "towh_k": [towh_k, towh_k * 3600],
                "alpha": [alpha, None],
                "kroot": [kroot, None],
                "ds": [ds, None],
                "p_dk": [p_dk, None],
            }
        }

        self.verified_osnma_material["last_kroot"] = dsm_kroot_dict

    def log_auth_pkr(self, dsm_pkr: 'DSMPKR'):
        if dsm_pkr.is_verified():
            self.last_verified_pkr = dsm_pkr

        nb_dp = dsm_pkr.get_value("NB_DP").uint
        mid = dsm_pkr.get_value("MID").uint
        intermediate = dsm_pkr.get_value("ITN")
        itn1, itn2, itn3, itn4 = intermediate.cut(len(intermediate)//4)
        npkt = dsm_pkr.get_value("NPKT").uint
        npkid = dsm_pkr.get_value("NPKID").uint
        npk = dsm_pkr.get_value("NPK").hex
        p_dp = dsm_pkr.get_value("P_DP").bin

        dsm_pkr_dict = {
            "verification": dsm_pkr.is_verified(),
            "merkle_tree_root": dsm_pkr.merkle_root.hex,
            "fields": {
                "nb_dp": [nb_dp, NB_DP_lt[nb_dp]],
                "mid": [mid, None],
                "itn1": [itn1.hex, None],
                "itn2": [itn2.hex, None],
                "itn3": [itn3.hex, None],
                "itn4": [itn4.hex, None],
                "npkt": [npkt, npkt_lt[npkt].name],
                "npkid": [npkid, None],
                "npk": [npk, None],
                "p_dp": [p_dp, None],
            }
        }
        self.verified_osnma_material["last_pkr"] = dsm_pkr_dict

    def log_nav_data(self, svid: int, adkd, word_type):
        self.nav_data_received[svid][ADKD(adkd).name][word_type] = True

    def log_mack_data(self, svid, tag_list: List['TagAndInfo'], tesla_key: 'TESLAKey'):
        osnma_mack_data = self.osnma_material_received[svid]['mack_data']
        osnma_mack_data["tags"] = tag_list
        osnma_mack_data["tesla_key"] = tesla_key if tesla_key is None else tesla_key.key.hex

    def log_hkroot_data(self, svid: int, received_blocks: List[Optional['BitArray']]):
        osnma_hkroot_data = self.osnma_material_received[svid]['hkroot_data']

        if nma_header := received_blocks[0]:
            nmas, cid, cpks = parse_nma_header(nma_header)
            osnma_hkroot_data["nma_header"] = {
                "nmas": nmas.name,
                "cid": cid,
                "cpks": cpks.name,
            }

        if dsm_header := received_blocks[1]:
            osnma_hkroot_data["dsm_header"] = {
                "dsm_id": dsm_header[0:4].uint,
                "block_id": dsm_header[4:8].uint,
            }

        osnma_hkroot_data["dsm_blocks"] = [True if block is not None else False for block in received_blocks[2:]]

    def add_satellite(self, gst_sf: 'GST', satellite: 'Satellite'):
        svid = satellite.svid

        # Initialize nav data
        if svid not in self.nav_data_received:
            self.nav_data_received[svid] = {
                "ADKD0": {1: False, 2: False, 3: False, 4: False, 5: False},
                "ADKD4": {6: False, 10: False},
            }
            if gst_sf.tow % 60 == 0:
                self.nav_data_received[svid]["ADKD4"][10] = None

        # initialize OSNMA data
        if satellite.subframe_with_osnma() and svid not in self.osnma_material_received:
            self.osnma_material_received[svid] = {
                "hkroot_data": {"nma_header": None, "dsm_header": None, "dsm_blocks": []},
                "mack_data": {"tags": [], 'tesla_key': None},
            }

    def _json_file_logging(self, status_dict):
        if Config.DO_STATUS_LOG and Config.LOG_FILE:
            if self.json_file is None:
                self.json_file = open(self.json_file_name, 'w')
                self.json_file.write("[\n")
                self.json_file.write(json.dumps(status_dict))
                self.json_file.write("\n]")
            else:
                self.json_file.seek(self.json_file.tell() - 2)  # \n]
                self.json_file.write(',\n')
                self.json_file.write(json.dumps(status_dict))
                self.json_file.write("\n]")

    def _subframe_reset(self):
        self.osnma_material_received = {}
        self.nav_data_received = {}
        self.verified_osnma_material["tesla_key"] = []
        self.verified_osnma_material["tags"] = []
        self.verified_osnma_material["macseq"] = []

    def do_status_log(self, osnma_r: 'OSNMAReceiver'):

        status_dict = {
            "metadata": {
                "GST_subframe": [osnma_r.current_gst_subframe.wn, osnma_r.current_gst_subframe.tow],
                "input_module": osnma_r.nav_data_input.__class__.__name__,
                "OSNMAlib_status": osnma_r.receiver_state.osnmalib_state.name,
            },
            "OSNMA_status": self._get_osnma_status_dict(osnma_r),
            "OSNMA_material_received": dict(sorted(self.osnma_material_received.items())),
            "nav_data_received": dict(sorted(self.nav_data_received.items())),
            "verified_OSNMA_material": self.verified_osnma_material,
            "authenticated_nav_data": self._get_authenticated_nav_data(osnma_r),
        }

        string_object = (f"--- STATUS END OF SUBFRAME GST {osnma_r.current_gst_subframe} ---\n\n"
                         f"OSNMAlib Status: {status_dict['metadata']['OSNMAlib_status']}\n\n"
                         f"## OSNMA Status\n"
                         f"{pprint.pformat(status_dict['OSNMA_status'], sort_dicts=False, width=100, compact=True)}\n\n"
                         f"## OSNMA Material Received in the Subframe\n"
                         f"{pprint.pformat(status_dict['OSNMA_material_received'], sort_dicts=False, width=150)}\n\n"
                         f"## Navigation Data Received in the Subframe\n"
                         f"{pprint.pformat(status_dict['nav_data_received'], sort_dicts=False, width=150)}\n\n"
                         f"## Verified OSNMA Material\n"
                         f"{pprint.pformat(status_dict['verified_OSNMA_material'], sort_dicts=False, width=150)}\n\n"
                         f"## Authenticated Navigation Data\n"
                         f"{pprint.pformat(status_dict['authenticated_nav_data'], sort_dicts=False, width=150)}\n")

        logger.info(string_object)

        self._json_file_logging(status_dict)

        if Config.DO_JSON_STATUS:
            with open(Config.JSON_STATUS_PATH, 'w') as f:
                json.dump(status_dict, f)

        self._subframe_reset()

    def initialize(self, logs_path: Path):
        self.__init__(logs_path)

    def close(self):
        if self.json_file is not None:
            self.json_file.close()

StatusLogger = _StatusLogger()
