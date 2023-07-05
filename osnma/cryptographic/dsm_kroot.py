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

import ecdsa
from bitstring import BitArray

from .dsm_message import DSM
from ..structures.fields_information import NB_DK_lt, NB_DK_size_lt, KS_lt, crypto_structure, section_structure
from ..utils.exceptions import PublicKeyObjectError

import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


class DSMKroot(DSM):

    def __init__(self, pkr_dict=None):
        super().__init__()

        self.pkr_dict = pkr_dict
        self.public_key = None
        self.kroot_data_stream = None

    def _extra_actions(self, name):

        if name != 'P_DK':
            uint_value = self.fields[name].value.uint

            if name == 'NB_DK':
                self.size_blocks = NB_DK_lt[uint_value]
                self.size_bits = NB_DK_size_lt[uint_value]
            elif name == 'PKID':
                self._pkr_verification(uint_value)
                self.set_size('DS', self.pkr_dict[uint_value].get_signature_len())
                self.public_key = self.pkr_dict[uint_value].get_public_key()
                self._compute_padding_size()
            elif name == 'KS':
                self.set_size('KROOT', KS_lt[uint_value])
                self._compute_padding_size()

    def _compute_padding_size(self):
        padding_size = self.size_bits - 104 - self.get_size('KROOT') - self.get_size('DS')
        self.set_size('P_DK', padding_size)

    def _pkr_verification(self, pkr_id):
        if self.pkr_dict is None:
            raise PublicKeyObjectError("Empty pkr dictionary.")
        elif pkr_id not in self.pkr_dict:
            raise PublicKeyObjectError(f"PKID {pkr_id} not in the pkr dictionary objects.")
        elif not self.pkr_dict[pkr_id].is_verified():
            raise PublicKeyObjectError(f"Public key ID {pkr_id} is not verified.")

    def _length_verification(self):
        length_adding = 104 + self.get_size('KROOT') + self.get_size('DS') + self.get_size('P_DK')
        length_nb_field = self.size_bits
        return length_adding == length_nb_field

    def _padding_verification(self, kroot_m):

        full_padding = BitArray(hashlib.sha256((kroot_m + self.get_value("DS")).tobytes()).digest())
        correct_padding = full_padding[:self.get_size('P_DK')]

        return correct_padding == self.get_value('P_DK')

    def _digital_signature_verification(self, kroot_m):

        verification_result = None
        try:
            verification_result = self.public_key.verify(self.get_value("DS").tobytes(), kroot_m.tobytes())
        except ecdsa.BadSignatureError:
            verification_result = False
        finally:
            return verification_result

    def set_pkr_dict(self, pkr_dict):
        self.pkr_dict = pkr_dict

    def process_data(self, data_stream):
        self.kroot_data_stream = data_stream
        super().process_structure_data(section_structure["DSM_KROOT"], data_stream)

    def kroot_verification(self):
        """Authenticates the saved KROOT with the current Public Key or the path for the one
        passed as parameter.

        :returns: The result of the verification of KROOT
        :rtype: bool
        """

        is_length_correct = self._length_verification()
        if not is_length_correct:
            logger.error(f"Length of the loaded attributes is not consistent.")

        # Create the kroot signature message
        kroot_auth = BitArray()
        for field in crypto_structure["KROOT"]:
            kroot_auth.append(self.get_value(field))

        is_padding_correct = self._padding_verification(kroot_auth)
        if not is_padding_correct:
            logger.error(f"Padding value is not consistent.")

        is_ds_correct = self._digital_signature_verification(kroot_auth)
        if not is_ds_correct:
            logger.error(f"Digital signature is not consistent with the keys.")

        self.verified = is_length_correct and is_padding_correct and is_ds_correct
        return self.verified
