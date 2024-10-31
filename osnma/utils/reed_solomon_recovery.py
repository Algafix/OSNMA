
from typing import List, Optional

import reedsolo
from bitstring import BitArray

from osnma.utils.config import Config
from osnma.utils.exceptions import ReedSolomonRecoveryError

import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)

CED_WORDS = [1,2,3,4]
RS_CED_WORDS = [17,18,19,20]
REED_SOLOMON_WORDS = CED_WORDS + RS_CED_WORDS

# Primitive polynomial for GF(256): x^8 + x^4 + x^3 + x^2 + 1 = 0x11d
# Parity octets: 60
# fcr = 1 because Galileo uses a matlab like implementation that starts at 1 instead of 0
rs = reedsolo.RSCodec(60, nsize=255, fcr=1, prim=0x11d)

class ReedSolomonSatellite:
    def __init__(self, svid: int):
        self.svid = svid
        self.full_iod = None
        self.partial_iod = None
        self.ced_words: List[Optional[BitArray]] = [None, None, None, None]
        self.rs_ced_words: List[Optional[BitArray]] = [None, None, None, None]

    def _reset_decoding_buffer(self, full_iod: BitArray = None, partial_iod: BitArray = None):
        if full_iod:
            self.full_iod = full_iod
            self.partial_iod = full_iod[-2:]
        elif partial_iod:
            self.full_iod = None
            self.partial_iod = partial_iod
        self.ced_words = [None, None, None, None]
        self.rs_ced_words = [None, None, None, None]

    def _generate_info_vector(self) -> bytes:
        """
        Information vector of 58 octets.
        WT1 has a special treatment and 16 octets (128 bits) in the information vector.
        WT2-4 have the same treatment and 14 octets (112 bits) in the information vector.
        """
        info_vector = BitArray(58 * 8)
        if self.ced_words[0] is not None:
            info_vector[0:128] = self.ced_words[0]
            info_vector[6:8] = self.ced_words[0][14:16]
            info_vector[8:16] = self.ced_words[0][6:14]
        for i, word in enumerate(self.ced_words[1:]):
            if word is not None:
                info_vector[128 + 112*i: 128 + 112*(i+1)] = word[16:128]
        return info_vector.bytes

    def _generate_parity_vector(self) -> bytes:
        """
        Parity vector of 60 octets.
        Each WT have the same treatment and 15 octets in the parity vector.
        """
        parity_vector = BitArray(60 * 8)
        for i, word in enumerate(self.rs_ced_words):
            if word is not None:
                parity_vector[120*i:(120*i)+8] = word[6:14]
                parity_vector[(120*i)+8:120*(i+1)] = word[16:128]
        return parity_vector.bytes

    def _get_erasure_positions(self) -> List[int]:
        erasure_positions = []
        for i, word in enumerate(self.ced_words):
            if word is None:
                if i == 0:
                    erasure_positions.extend(range(0,16))
                else:
                    erasure_positions.extend(range(16 + 14 * (i-1), 16 + 14 * i))
        for i, word in enumerate(self.rs_ced_words):
            if word is None:
                erasure_positions.extend(range(58 + 15 * i, 58 + 15 * (i+1)))
        return erasure_positions

    def _swap_code_vector_format(self, code_vector: bytes) -> bytes:
        """
        The information vector is 58 bytes, and the parity vector is 60 bytes.
        Each vector is reversed independently
        """
        reversed_vector = code_vector[:58][::-1] + code_vector[58:][::-1]
        return reversed_vector

    def _swap_erasure_format(self, erasures: List[int]) -> List[int]:
        fixed_erasures = [57 - i if i <= 57 else 117 - i + 58 for i in erasures]
        return fixed_erasures

    def _extract_ced_words_and_iod(self, decoded_info_vector: bytes):
        info_vector = BitArray(decoded_info_vector)
        iod_2_lsb = info_vector[6:8]
        iod = info_vector[8:16] + iod_2_lsb

        # Fix WT1 IOD problem
        wt1 = info_vector[:128]
        wt1[6:16] = iod

        ced_words = [wt1]
        for i in range(3):
            extracted_word = info_vector[128+112*i:128+112*(i+1)]
            ced_word = BitArray(uint=i+2, length=6) + iod + extracted_word
            ced_words.append(ced_word)

        return ced_words, iod, iod_2_lsb

    def _extract_rs_ced_words(self, decoded_parity_vector: bytes, lsb_iod: BitArray):
        parity_vector = BitArray(decoded_parity_vector)
        rs_ced_words = []
        for i in range(4):
            extracted_word = parity_vector[120*i:120*(i+1)]
            rs_ced_word = BitArray(uint=i+17, length=6) + extracted_word[:8] + lsb_iod + extracted_word[8:]
            rs_ced_words.append(rs_ced_word)
        return rs_ced_words

    def _extract_and_update_words(self, decoded_msgecc_gal: bytes):
        ced_words, iod, iod_2_lsb = self._extract_ced_words_and_iod(decoded_msgecc_gal[:58])
        rs_ced_words = self._extract_rs_ced_words(decoded_msgecc_gal[58:], iod_2_lsb)

        # Check and update IOD
        if self.partial_iod != iod_2_lsb:
            raise ReedSolomonRecoveryError(f"Partial IOD in ReedSolomon recovery does not match. SVID {self.svid:02d}.")
        elif self.full_iod is not None and self.full_iod != iod:
            raise ReedSolomonRecoveryError(f"Partial IOD in ReedSolomon recovery does not match. SVID {self.svid:02d}.")
        self.full_iod = iod

        # Check words for return
        return_ced_words = {}
        for i, (saved_word, decoded_word) in enumerate(zip(self.ced_words, ced_words)):
            if saved_word is None:
                self.ced_words[i] = decoded_word
                return_ced_words[i+1] = decoded_word
            elif saved_word != decoded_word:
                raise ReedSolomonRecoveryError(f"Decoded WT {i+1} from SVID {self.svid:02d} does not match the saved one.")

        for i, (saved_word, decoded_word) in enumerate(zip(self.rs_ced_words, rs_ced_words)):
            if saved_word is None:
                self.rs_ced_words[i] = decoded_word
            elif saved_word != decoded_word:
                raise ReedSolomonRecoveryError(f"Decoded WT {i+1} from SVID {self.svid:02d} does not match the saved one.")

        return return_ced_words

    def _decode_rs_message(self):
        # Generate code vector and erasure position formatted for the reedsolo library
        info_vector = self._generate_info_vector()
        parity_vector = self._generate_parity_vector()
        code_vector = info_vector + parity_vector
        erasure_positions = self._get_erasure_positions()
        code_vector_lib = self._swap_code_vector_format(code_vector)
        erasure_positions_lib = self._swap_erasure_format(erasure_positions)

        # Decode and addapt for the Galileo format
        decoded_msg, decoded_msgecc, errata_pos = rs.decode(code_vector_lib, erase_pos=erasure_positions_lib)
        decoded_msgecc_gal = self._swap_code_vector_format(decoded_msgecc)

        # Extract words and save them. Create fake pages for further OSNMAlib processing (will be modified)
        return_ced_words = self._extract_and_update_words(decoded_msgecc_gal)
        return_ced_pages = {}
        for wt, word in return_ced_words.items():
            return_ced_pages[wt] = BitArray('0b00') + word[:112] + BitArray(bin='0'*8) + word[112:] + BitArray(bin='0'*102)
        return return_ced_pages

    def add_word(self, wt: int, word: BitArray):
        if wt in CED_WORDS:
            full_iod = word[6:16]
            partial_iod = full_iod[-2:]
            if (self.full_iod is not None and self.full_iod != full_iod) or \
                    self.partial_iod != partial_iod:
                self._reset_decoding_buffer(full_iod=full_iod)
            elif self.full_iod is None and self.partial_iod == partial_iod:
                self.full_iod = full_iod
            self.ced_words[wt-1] = word
        elif wt in RS_CED_WORDS:
            partial_iod = word[14:16]
            if self.partial_iod != partial_iod:
                self._reset_decoding_buffer(partial_iod=partial_iod)
            self.rs_ced_words[wt-17] = word

    def recover_words(self):
        if len([word for word in self.ced_words if word is not None]) == 4:
            if self.full_iod is None:
                raise ReedSolomonRecoveryError("IOD is not None but 4 CED pages received")
            return {}
        elif len([word for word in [*self.ced_words,*self.rs_ced_words] if word is not None]) >= 4:
            return self._decode_rs_message()
        else:
            return {}

class ReedSolomonRecovery:
    def __init__(self):
        self.rs_data = {}
        for svid in range(Config.NS):
            self.rs_data[svid] = ReedSolomonSatellite(svid)

    def add_rs_word(self, wt: int, page: BitArray, svid: int):
        word = page[2:114] + page[122:138]
        self.rs_data[svid].add_word(wt, word)

    def recover_words(self, svid: int):
        return self.rs_data[svid].recover_words()



