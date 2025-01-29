
from typing import List, Optional, Tuple, Dict

import reedsolo
from bitstring import BitArray

from osnma.utils.config import Config
from osnma.cryptographic.gst_class import GST
from osnma.utils.exceptions import ReedSolomonRecoveryError

import osnma.utils.logger_factory as log_factory
logger = log_factory.get_logger(__name__)

CED_WORDS = [1,2,3,4]
RS_CED_WORDS = [17,18,19,20]
REED_SOLOMON_WORDS = CED_WORDS + RS_CED_WORDS

RS_CED_SIZE = 120
WT1_CED_SIZE = 128
CED_SIZE = 112

# Primitive polynomial for GF(256): x^8 + x^4 + x^3 + x^2 + 1 = 0x11d
# Parity octets: 60
# fcr = 1 because Galileo uses a matlab like implementation that starts at 1 instead of 0
rs = reedsolo.RSCodec(60, nsize=255, fcr=1, prim=0x11d)

class ReedSolomonSatellite:
    def __init__(self, svid: int):
        self.svid: int = svid
        self.last_update_gst: GST = GST(wn=0, tow=0)
        self.full_iod: Optional[BitArray] = None
        self.iod_2_lsb: Optional[BitArray] = None
        self.ced_words: List[Optional[BitArray]] = [None, None, None, None]
        self.rs_ced_words: List[Optional[BitArray]] = [None, None, None, None]

    def _reset_decoding_buffer(self, full_iod: BitArray = None, iod_2_lsb: BitArray = None):
        """
        Reset decoding buffer of CED and RS CED words. Add the new iod or only the 2 LSB.
        """
        if full_iod:
            self.full_iod = full_iod
            self.iod_2_lsb = full_iod[-2:]
        elif iod_2_lsb:
            self.full_iod = None
            self.iod_2_lsb = iod_2_lsb
        else:
            self.full_iod = None
            self.iod_2_lsb = None
        self.ced_words = [None, None, None, None]
        self.rs_ced_words = [None, None, None, None]

    def _generate_info_vector(self) -> bytes:
        """
        Information vector of 58 octets.
        WT1 has a special treatment and 16 octets (128 bits) in the information vector.
        The first byte of the WT1 is always the word type and partial iod: 0b000001 + iod_2_lsb
        WT2-4 have the same treatment and 14 octets (112 bits) in the information vector.
        """
        info_vector = BitArray(58 * 8)
        # Word Type 1
        if self.ced_words[0] is not None:
            info_vector[0:WT1_CED_SIZE] = self.ced_words[0]
            info_vector[6:8] = self.ced_words[0][14:16]
            info_vector[8:16] = self.ced_words[0][6:14]
        else:
            info_vector[:8] = BitArray('0b000001') + self.iod_2_lsb
        # Word Types 2, 3, and 4
        for i, word in enumerate(self.ced_words[1:]):
            if word is not None:
                info_vector[WT1_CED_SIZE+CED_SIZE*i:WT1_CED_SIZE+CED_SIZE*(i+1)] = word[16:128]
        return info_vector.bytes

    def _generate_parity_vector(self) -> bytes:
        """
        Parity vector of 60 octets.
        Each WT have the same treatment and 15 octets in the parity vector.
        """
        parity_vector = BitArray(60 * 8)
        for i, word in enumerate(self.rs_ced_words):
            if word is not None:
                parity_vector[RS_CED_SIZE*i:(RS_CED_SIZE*i)+8] = word[6:14]
                parity_vector[(RS_CED_SIZE*i)+8:RS_CED_SIZE*(i+1)] = word[16:128]
        return parity_vector.bytes

    def _get_erasure_positions(self) -> List[int]:
        """
        Calculate the erasure positions for the Reed Solomon decoding.
        Word Type 1 is special: the first byte is always known and it has more bytes than WT 2, 3, and 4
        """
        erasure_positions = []
        for i, word in enumerate(self.ced_words):
            if word is None:
                if i == 0:
                    erasure_positions.extend(range(1,16))  # The first byte is always known. Word Type + iod_2_lsb
                else:
                    erasure_positions.extend(range(16 + 14 * (i-1), 16 + 14 * i))
        for i, word in enumerate(self.rs_ced_words):
            if word is None:
                erasure_positions.extend(range(58 + 15 * i, 58 + 15 * (i+1)))
        return erasure_positions

    def _swap_code_vector_format(self, code_vector: bytes) -> bytes:
        """
        The information vector is 58 bytes, and the parity vector is 60 bytes.
        Each vector is reversed independently.
        """
        reversed_vector = code_vector[:58][::-1] + code_vector[58:][::-1]
        return reversed_vector

    def _swap_erasure_format(self, erasures: List[int]) -> List[int]:
        """
        Since the information and parity vectors are reversed, the list with the erasure positions also needs to
        accommodate the new format.
        """
        fixed_erasures = [57 - i if i <= 57 else 117 - i + 58 for i in erasures]
        return fixed_erasures

    def _extract_ced_words_and_iod(self, decoded_info_vector: bytes) -> Tuple[List[BitArray], BitArray, BitArray]:
        """
        Convert the output of the Reed Solomon information vector decoding to proper CED Galileo words.
        That is mainly adding the word type and iod at the beginning, with some special cases for WT1.
        """
        info_vector = BitArray(decoded_info_vector)

        # Regenerate WT 1 and IOD
        iod_2_lsb = info_vector[6:8]
        iod = info_vector[8:16] + iod_2_lsb
        wt1 = info_vector[:WT1_CED_SIZE]
        wt1[6:16] = iod

        # Regenerate WT 2, 3, and 4
        ced_words = [wt1]
        for i in range(3):
            extracted_word = info_vector[WT1_CED_SIZE + CED_SIZE*i:WT1_CED_SIZE + CED_SIZE*(i+1)]
            ced_word = BitArray(uint=i+2, length=6) + iod + extracted_word
            ced_words.append(ced_word)

        return ced_words, iod, iod_2_lsb

    def _extract_rs_ced_words(self, decoded_parity_vector: bytes, iod_2_lsb: BitArray) -> List[BitArray]:
        """
        Convert the output of the Reed Solomon parity vector decoding to proper RS CED Galileo words.
        They are not used for navigation, but useful for sanity checks.
        """
        parity_vector = BitArray(decoded_parity_vector)
        rs_ced_words = []
        for i in range(4):
            extracted_word = parity_vector[RS_CED_SIZE*i:RS_CED_SIZE*(i+1)]
            rs_ced_word = BitArray(uint=i+17, length=6) + extracted_word[:8] + iod_2_lsb + extracted_word[8:]
            rs_ced_words.append(rs_ced_word)
        return rs_ced_words

    def _extract_and_update_words(self, decoded_msgecc_gal: bytes) -> Dict[int, BitArray]:
        """
        Regenerate proper Galileo words from the RS decoding output, update the IOD, perform several sanity checks, and
        decide which CED words to return.
        """
        ced_words, iod, iod_2_lsb = self._extract_ced_words_and_iod(decoded_msgecc_gal[:58])
        rs_ced_words = self._extract_rs_ced_words(decoded_msgecc_gal[58:], iod_2_lsb)

        # IOD sanity check and update IOD
        if self.iod_2_lsb != iod_2_lsb:
            raise ReedSolomonRecoveryError(f"IOD 2 LSB in ReedSolomon recovery does not match. SVID {self.svid:02d}.")
        elif self.full_iod is not None and self.full_iod != iod:
            raise ReedSolomonRecoveryError(f"Full IOD in ReedSolomon recovery does not match. SVID {self.svid:02d}.")
        self.full_iod = iod

        # CED words sanity check, and selection of missing CED words for return
        return_ced_words = {}
        for i, (saved_word, decoded_word) in enumerate(zip(self.ced_words, ced_words)):
            if saved_word is None:
                self.ced_words[i] = decoded_word
                return_ced_words[i+1] = decoded_word
            elif saved_word != decoded_word:
                raise ReedSolomonRecoveryError(f"Decoded WT {i+1} from SVID {self.svid:02d} does not match the saved one.")

        # RS CED words sanity check
        for i, (saved_word, decoded_word) in enumerate(zip(self.rs_ced_words, rs_ced_words)):
            if saved_word is None:
                self.rs_ced_words[i] = decoded_word
            elif saved_word != decoded_word:
                raise ReedSolomonRecoveryError(f"Decoded WT {i+16} from SVID {self.svid:02d} does not match the saved one.")

        return return_ced_words

    def _decode_rs_message(self) -> Dict[int, BitArray]:
        """
        Generate the code vector (information and parity vectors), calculate the erasure positions, adapt both for the
        RS library format, and perform the RS decoding. Then, extract the recovered CED words from the information
        vector and return the missing ones.
        """
        # Generate the code vector and erasure positions, formatted for the reedsolo library
        info_vector = self._generate_info_vector()
        parity_vector = self._generate_parity_vector()
        code_vector = info_vector + parity_vector
        erasure_positions = self._get_erasure_positions()
        code_vector_lib = self._swap_code_vector_format(code_vector)
        erasure_positions_lib = self._swap_erasure_format(erasure_positions)

        # RS decoding and adapt the output to the Galileo format
        try:
            decoded_msg, decoded_msgecc, errata_pos = rs.decode(code_vector_lib, erase_pos=erasure_positions_lib)
        except Exception:
            raise ReedSolomonRecoveryError(f"Error when decoding. SVID {self.svid}.")
        decoded_msgecc_gal = self._swap_code_vector_format(decoded_msgecc)

        # Extract the missing CED words
        return_ced_words = self._extract_and_update_words(decoded_msgecc_gal)
        return return_ced_words

    def add_word(self, wt: int, word: BitArray, gst: GST):
        """
        Add a new word to the buffer. Check the IOD to determine if the decoding buffer should be reset.
        """
        # Avoid collision on the iod value, reset the buffers after 30 minutes of not seeing the satellite
        if gst > self.last_update_gst + 1800:
            self._reset_decoding_buffer()
        self.last_update_gst = gst

        if wt in CED_WORDS:
            full_iod = word[6:16]
            iod_2_lsb = full_iod[-2:]
            if (self.full_iod is not None and self.full_iod != full_iod) or \
                    self.iod_2_lsb != iod_2_lsb:
                self._reset_decoding_buffer(full_iod=full_iod)
            elif self.full_iod is None and self.iod_2_lsb == iod_2_lsb:
                self.full_iod = full_iod
            self.ced_words[wt-1] = word
        elif wt in RS_CED_WORDS:
            iod_2_lsb = word[14:16]
            if self.iod_2_lsb != iod_2_lsb:
                self._reset_decoding_buffer(iod_2_lsb=iod_2_lsb)
            self.rs_ced_words[wt-17] = word

    def recover_words(self) -> Dict[int, BitArray]:
        """
        Returns the recovered CED words if there are at least 4 pages in total and any CED words are missing.
        Else, return an empty dictionary. May raise `ReedSolomonRecoveryError` if any of the inconsistency checks fail.
        """
        if len([word for word in self.ced_words if word is not None]) == 4:
            if self.full_iod is None:
                raise ReedSolomonRecoveryError("IOD is None but 4 CED pages received")
            return {}
        elif len([word for word in [*self.ced_words,*self.rs_ced_words] if word is not None]) >= 4:
            return self._decode_rs_message()
        else:
            return {}

class ReedSolomonRecovery:
    def __init__(self):
        self.rs_data = {}
        for svid in range(Config.NS+1):
            self.rs_data[svid] = ReedSolomonSatellite(svid)

    def add_rs_word(self, wt: int, word: BitArray, svid: int, gst: GST):
        """
        Add a new word to the buffer. Check the IOD to determine if the decoding buffer should be reset.
        """
        self.rs_data[svid].add_word(wt, word, gst)

    def recover_words(self, svid: int) -> Dict[int, BitArray]:
        """
        Returns the recovered CED words if there are at least 4 pages in total and any CED words are missing.
        Else, return an empty dictionary. May raise `ReedSolomonRecoveryError` if any of the inconsistency checks fail.
        """
        return self.rs_data[svid].recover_words()



