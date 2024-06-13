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

from enum import Enum, IntEnum
from bitstring import BitArray

class OSNMAlibSTATE(IntEnum):
    COLD_START = 0
    WARM_START = 1
    HOT_START = 2
    STARTED = 6
    OSNMA_AM = 7

class Field:
    """
    Class that stores an OSNMA field.
    """

    def __init__(self, name, value, size):
        self.name = name
        self.size = size
        self.value = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size


class FieldsEnum(Enum):
    NMA_H = "NMA_H"
    NMAS = "NMAS"
    CID = "CID"
    CPKS = "CPKS"
    NMA_R = "NMA_R"

    DSM_H = "DSM_H"
    DSM_ID = "DSM_ID"
    BID = "BID"

    NB_DK = "NB_DK"
    PKID = "PKID"
    CIDKR = "CIDKR"
    NMACK = "NMACK"
    HF = "HF"
    MF = "MF"
    KS = "KS"
    TS = "TS"
    MACLT = "MACLT"
    KROOT_R = "KROOT_R"
    MO = "MO"
    WN_K = "WN_K"
    TOWH_K = "TOWH_K"
    ALPHA = "ALPHA"
    KROOT = "KROOT"
    DS = "DS"
    KROOT_P = "P_DK"

    NB_DP = "NB_DP"
    MID = "MID"
    ITN = "ITN"
    NPKT = "NPKT"
    NPKID = "NPKID"
    P_DP = "P_DP"


class NMAS(IntEnum):
    TEST = 1
    OPERATIONAL = 2
    DONT_USE = 3


class CPKS(IntEnum):
    NOMINAL = 1
    EOC = 2
    CREV = 3
    NPK = 4
    PKREV = 5
    NMT = 6
    AM = 7


def parse_nma_header(nma_header: BitArray) -> (NMAS, int, CPKS):
    nma_status = nmas_lt[nma_header[:2].uint]
    cid = nma_header[2:4].uint
    cpks = cpks_lt[nma_header[4:7].uint]
    return nma_status, cid, cpks


class HF(IntEnum):
    SHA_256 = 0
    SHA3_224 = 1
    SHA3_256 = 2


class MF(IntEnum):
    HMAC_SHA_256 = 0
    CMAC_AES = 1


class MO(IntEnum):
    NO_OFFSET = 0
    OFFSET = 1


class NPKT(IntEnum):
    ECDSA_P256 = 1
    ECDSA_P521 = 3
    OAM = 4


nmas_lt = {1: NMAS.TEST, 2: NMAS.OPERATIONAL, 3: NMAS.DONT_USE}
cpks_lt = {1: CPKS.NOMINAL, 2: CPKS.EOC, 3: CPKS.CREV, 4: CPKS.NPK, 5: CPKS.PKREV, 6: CPKS.NMT, 7: CPKS.AM}
hf_lt = {0: HF.SHA_256, 1: HF.SHA3_224, 2: HF.SHA3_256}
mf_lt = {0: MF.HMAC_SHA_256, 1: MF.CMAC_AES}
npkt_lt = {0: None, 1: NPKT.ECDSA_P256, 2: None, 3: NPKT.ECDSA_P521, 4: NPKT.OAM }


NB_DP_lt = ["Reserved", "Reserved", "Reserved", "Reserved", "Reserved", 11, "Reserved", 13, 14, 15, 16,
            "Reserved", "Reserved", "Reserved", "Reserved", "Reserved"]

NB_DP_size_lt = [None, None, None, None, None, 1144, None, 1352, 1456, 1560, 1664, None, None, None, None, None]

NB_DK_lt = ["Reserved", 7, 8, 9, 10, 11, 12, 13, 14, "Reserved", "Reserved", "Reserved", "Reserved", "Reserved",
            "Reserved", "Reserved"]

NB_DK_size_lt = [None, 728, 832, 936, 1040, 1144, 1248, 1352, 1456, None, None, None, None, None, None, None]

NMACK_lt = [None, 480, 240, 160]

KS_lt = [96, 104, 112, 120, 128, 160, 192, 224, 256, "Reserved", "Reserved", "Reserved", "Reserved", "Reserved",
         "Reserved", "Reserved"]

TS_lt = [10, 12, 14, 16, 18, 20, 24, 28, 32, 40, "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved"]

NPKT_size_lt = [None, 264, None, 536, None, None, None, None, None, None, None, None, None, None, None, None]

NPK_DS_lt = [448, 512, 768, 1056]

field_info = {

    # NMA Header
    'NMA_H': {
        'size': 8,
        'name': 'NMA_H'
    },
    'NMAS': {
        'size': 2,
        'name': 'NMAS'
    },
    'CID': {
        'size': 2,
        'name': 'CID'
    },
    'CPKS': {
        'size': 3,
        'name': 'CPKS'
    },
    'NMA_R': {
        'size': 1,
        'name': 'NMA_R'
    },

    # DSM Header
    'DSM_H': {
        'size': 8,
        'name': 'DSM_H'
    },
    'DSM_ID': {
        'size': 4,
        'name': 'DSM_ID'
    },
    'BID': {
        'size': 4,
        'name': 'BID'
    },

    # DSM KROOT
    'NB_DK': {
        'size': 4,
        'name': 'NB_DK'
    },
    'PKID': {
        'size': 4,
        'name': 'PKID'
    },
    'CIDKR': {
        'size': 2,
        'name': 'CIDKR'
    },
    'NMACK': {
        'size': 2,
        'name': 'NMACK'
    },
    'HF': {
        'size': 2,
        'name': 'HF'
    },
    'MF': {
        'size': 2,
        'name': 'MF'
    },
    'KS': {
        'size': 4,
        'name': 'KS'
    },
    'TS': {
        'size': 4,
        'name': 'TS'
    },
    'MACLT': {
        'size': 8,
        'name': 'MACLT'
    },
    'KROOT_R': {
        'size': 2,
        'name': 'KROOT_R'
    },
    'MO': {
        'size': 2,
        'name': 'MO'
    },
    'WN_K': {
        'size': 12,
        'name': 'WN_K'
    },
    'TOWH_K': {
        'size': 8,
        'name': 'TOWH_K'
    },
    'ALPHA': {
        'size': 48,
        'name': 'ALPHA'
    },
    'KROOT': {
        'size': 0,
        'name': 'KROOT'
    },
    'DS': {
        'size': 0,
        'name': 'DS'
    },
    'P_DK': {
        'size': 0,
        'name': 'P_DK'
    },

    # DSM PKR
    'NB_DP': {
        'size': 4,
        'name': 'NB_DP'
    },
    'MID': {
        'size': 4,
        'name': 'MID'
    },
    'ITN': {
        'size': 1024,
        'name': 'ITN'
    },
    'NPKT': {
        'size': 4,
        'name': 'NPKT'
    },
    'NPKID': {
        'size': 4,
        'name': 'NPKID'
    },
    'NPK': {
        'size': 0,
        'name': 'NPK'
    },
    'P_DP': {
        'size': 0,
        'name': 'P_DP'
    },

    # MACK
    'MACK_MSG': {
        'size': 480,
        'name': 'MACK_MSG'
    },
    'TAG0': {
        'size': 0,
        'name': 'TAG0'
    },
    'MACSEQ': {
        'size': 12,
        'name': 'MACSEQ'
    },
    'IOD_TAG': {
        'size': 4,
        'name': 'IOD_TAG'
    },
    'TAG_INFO': {
        'size': 16,
        'name': 'TAG_INFO'
    },
    'PRN_D': {
        'size': 8,
        'name': 'PRN_D'
    },
    'ADKD': {
        'size': 4,
        'name': 'ADKD'
    }

}

section_structure = {
    'NMA_H': ['NMA_S', 'CID', 'CPKS', 'NMA_R'],
    'DSM_H': ['DSM_ID', 'BID'],
    'HKROOT': ['NMA_H', 'DSM_H', 'DMS_block'],
    'DSM_KROOT': ['NB_DK', 'PKID', 'CIDKR', 'NMACK', 'HF', 'MF', 'KS', 'TS', 'MACLT', 'KROOT_R', 'MO', 'WN_K', 'TOWH_K',
                  'ALPHA', 'KROOT', 'DS', 'P_DK'],
    'DSM_PKR': ['NB_DP', 'MID', 'ITN', 'NPKT', 'NPKID', 'NPK', 'P_DP']
}

crypto_structure = {
    'KROOT': ['NMA_H', 'CIDKR', 'NMACK', 'HF', 'MF', 'KS', 'TS', 'MACLT', 'KROOT_R', 'MO', 'WN_K', 'TOWH_K',
              'ALPHA', 'KROOT'],
    'MAC0': ['PRN', 'GST_WN', 'GST_TOW', 'CTR', 'NMA_S', 'navdata', 'P3'],
    'MAC': ['PRN', 'PRN_N', 'GST_WN', 'GST_TOW', 'CTR', 'NMA_S', 'navdata', 'P3'],
    'PKR': ['NPKT', 'NPKID', 'NPK'],
    'TESLA_KEY': ['nKEY', 'GST', 'ALPHA', 'P3']
}

