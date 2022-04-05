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

import re
import hashlib

from ecdsa.keys import VerifyingKey
from ecdsa.curves import NIST256p
from ecdsa.curves import NIST521p
from bitstring import BitArray

from osnma.cryptographic.dsm_pkr import DSMPKR
from osnma.cryptographic.dsm_kroot import DSMKroot
from osnma.structures.fields_information import NPKT

import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)


class IOHandler:

    def __init__(self, path=''):
        path = path+'/' if (len(path) > 1 and path[-1] != '/') else path
        self.path = path

    def read_merkle_root(self, file_name):
        with open(self.path+file_name, 'r') as merkle_file:
            try:
                file_text = merkle_file.read()
                tree_nodes = file_text.split('<TreeNode>')[1:]
                for node in tree_nodes:
                    if '<j>4</j><i>0</i>' in node:
                        merkle_root = re.findall(r'<x_ji>(.*?)</x_ji>', node)[0]
            except IOError:
                logger.critical(f"IOError while reading the Merkle root file {self.path+file_name}.")
        return BitArray(hex=merkle_root)

    def read_pubk(self, file_name):
        with open(self.path+file_name, 'r') as pubk_file:
            try:
                file_text = pubk_file.read()
                pubk_id = int(re.findall(r'<PKID>(.*?)</PKID>', file_text)[0])
                pubk_type = re.findall(r'<PKType>(.*?)</PKType>', file_text)[0]
                pubk_point = bytes.fromhex(re.findall(r'<point>(.*?)</point>', file_text)[0])

                if 'P-256' in pubk_type:
                    pubk_type = NPKT.ECDSA_P256.value
                    pubk_object = VerifyingKey.from_string(pubk_point, curve=NIST256p, hashfunc=hashlib.sha256)
                elif 'P-521' in pubk_type:
                    pubk_type = NPKT.ECDSA_P521.value
                    pubk_object = VerifyingKey.from_string(pubk_point, curve=NIST521p, hashfunc=hashlib.sha512)
                else:
                    raise Exception(f'Invalid Public Key type or not recognized: {pubk_type} not [P-256, P-512].')

                dsm_pkr = DSMPKR()
                dsm_pkr.set_value('NPKT', pubk_type)
                dsm_pkr.public_key_obj = pubk_object
                dsm_pkr.verified = True

                return pubk_id, dsm_pkr

            except IOError:
                logger.error(f"IOError while reading the Public Key file {self.path + file_name}.")

    def store_pubk(self, pkr: DSMPKR):

        pubk_id = pkr.get_value("NPKID").uint
        pubk_type = 'P-256/SHA-256' if 'NIST256' in pkr.key_curve.name else 'P-521/SHA-512'
        pubk_point = pkr.public_key_obj.to_string('compressed').hex()

        if not pkr.is_verified():
            raise Exception(f'Saving a Public Key that has not been verified. PKID: {pubk_id}')

        with open(self.path + f'OSNMA_PublicKey_{pubk_id}.xml', 'w') as pubk_file:
            try:
                pubk_file.write('<?xml version="1.0" encoding="UTF-8" ?>')
                pubk_file.write(f'<PKID>{pubk_id}</PKID>')
                pubk_file.write(f'<PKType>{pubk_type}</PKType>')
                pubk_file.write(f'<point>{pubk_point}</point>')
            except IOError:
                logger.error(f'Error saving Public Key {pubk_id} to file.')

    def read_kroot(self, file_name='OSNMA_last_KROOT.txt'):
        with open(self.path+file_name, 'r') as kroot_file:
            try:
                kroot_bits = BitArray(hex=kroot_file.readline())
                nmah_bits = BitArray(hex=kroot_file.readline())
            except IOError:
                logger.error(f"IOError while reading the Key Root file {self.path+file_name}.")
        return kroot_bits, nmah_bits

    def store_kroot(self, kroot: DSMKroot, nmah_bits: BitArray):

        if not kroot.is_verified():
            raise Exception(f'Saving a Kroot Key that has not been verified.')

        with open(self.path + f'OSNMA_last_KROOT.txt', 'w') as kroot_file:
            try:
                data_stream = kroot.kroot_data_stream
                kroot_file.write(data_stream.hex+'\n')
                kroot_file.write(nmah_bits.hex)
            except IOError:
                logger.error(f'Error saving Key Root to file.')
