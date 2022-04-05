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

import hashlib
from ecdsa import curves, VerifyingKey
from bitstring import BitArray

from .dsm_message import DSM, to_bitarray
from ..structures.fields_information import NB_DP_lt, NB_DP_size_lt, NPKT_size_lt, NPK_DS_lt, NPKT, crypto_structure, section_structure

import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


class DSMPKR(DSM):

    def __init__(self):
        super().__init__()

        self.merkle_root = None
        self.pk_type = None
        self.hash_f = None
        self.key_curve = None
        self.public_key_obj = None

    def _extra_actions(self, name):

        if name != 'P_DP':
            uint_value = self.get_value(name).uint

            if name == 'NB_DP':
                self.size_blocks = NB_DP_lt[uint_value]
                self.size_bits = NB_DP_size_lt[uint_value]
            elif name == 'NPKT':
                self.set_size('NPK', NPKT_size_lt[uint_value])
                self._set_key_params(uint_value)
                try:
                    padding_size = self.size_bits - 1040 - self.get_size('NPK')
                    self.set_size('P_DP', padding_size)
                except TypeError as e:
                    logger.warning(f"Cannot compute Padding length: Missing attribute NB_DP")

    @to_bitarray
    def set_merkle_root(self, merkle_root):
        self.merkle_root = merkle_root

    def get_signature_len(self):
        return NPK_DS_lt[self.get_value("NPKT").uint]

    def get_public_key(self):
        return self.public_key_obj

    def process_data(self, data_stream):
        super().process_structure_data(section_structure["DSM_PKR"], data_stream)

    def _store_key_object(self):
        key_bytes = self.get_value('NPK').bytes
        self.public_key_obj = VerifyingKey.from_string(key_bytes, curve=self.key_curve, hashfunc=self.hash_f)

    def _set_key_params(self, npkt):
        if npkt == NPKT.ECDSA_P224:
            self.hash_f = hashlib.sha224
            self.key_curve = curves.NIST224p
        elif npkt == NPKT.ECDSA_P256:
            self.hash_f = hashlib.sha256
            self.key_curve = curves.NIST256p
        elif npkt == NPKT.ECDSA_P384:
            self.hash_f = hashlib.sha384
            self.key_curve = curves.NIST384p
        elif npkt == NPKT.ECDSA_P521:
            self.hash_f = hashlib.sha512
            self.key_curve = curves.NIST521p

    def _length_verification(self):
        length_adding = 1040 + self.get_size('NPK') + self.get_size('P_DP')
        length_nb_field = self.size_bits
        return length_adding == length_nb_field

    def _padding_verification(self, leaf):

        full_padding = BitArray(hashlib.sha256((self.merkle_root + leaf).tobytes()).digest())
        correct_padding = full_padding[:self.get_size('P_DP')]

        return correct_padding == self.get_value('P_DP')

    def _pkr_merkle_verification(self, leaf):

        # Isolate the 4 intermediate nodes
        itn = self.get_value('ITN')
        itn_list = [itn[256 * i: 256 * (i + 1)] for i in range(4)]

        # Obtain the id of the leaf node
        mid = self.get_value('MID').uint

        # Compute merkle root. If the position if even, the new node is appended. If the position
        # is odd, it's prepended. Then the position is divided by 2 because its a log2 tree
        node = hashlib.sha256(leaf.bytes).digest()
        for it_node in itn_list:
            if mid % 2 == 0:
                node = BitArray(hashlib.sha256((node + it_node).bytes).digest())
            else:
                node = BitArray(hashlib.sha256((it_node + node).bytes).digest())
            mid = mid // 2

        return node == self.merkle_root

    def pkr_verification(self):
        """Craft and authenticates the new public key message with the saved merkle root.

        :returns: True if the computed Merkle root is the same that the one saved.
        :rtype: bool
        """

        is_length_correct = self._length_verification()
        if not is_length_correct:
            logger.error(f"Length of the loaded attributes is not consistent.")

        if self.merkle_root is None:
            raise AttributeError("Missing Merkle root")

        message = BitArray()
        for field in crypto_structure['PKR']:
            message.append(self.get_value(field))

        is_padding_correct = self._padding_verification(message)
        if not is_padding_correct:
            logger.error(f"Padding values not consistent.")

        is_pkr_correct = self._pkr_merkle_verification(message)
        if not is_pkr_correct:
            logger.error(f"The new public key is not consistent with the merkle root.")

        self.verified = is_length_correct and is_padding_correct and is_pkr_correct

        if self.verified:
            self._store_key_object()

        return self.verified

