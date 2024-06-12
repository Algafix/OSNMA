
import argparse
import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF


parser = argparse.ArgumentParser(description='Runs OSNMAlib against the provided SBF file that contains the block '
                                             'GALRawINAV.')
parser.add_argument('sbf_file', metavar='file', type=str, default='current_config.sbf', nargs='?',
                    help='name of the SBF file.')
args = parser.parse_args()


def sbf_current_config():
    config_dict = {
        'scenario_path': args.sbf_file,
        'exec_path': '.',
        'download_pki': True,
        'download_merkle': True,
        'download_sca': True,
        'download_rca': True,
        'download_ica': True,
        # 'USER_IDD_CERT' : {
        #     "CERT_PKIEE" : "Cert/pki_1.crt",
        #     "CERT_MERKLE" : "Cert/mk_1.crt",
        #     "CERT_ICA" : "Cert/ica_1.crt",
        #     "CERT_SCA" : "Cert/sca_1.crt",
        #     "CERT_RCA" : "Cert/rca_1.crt"
        # },
        #
        # 'USER_IDD_CRL' : {
        #     "CRL_ICA" : 'Cert/OSNMA_PublicKeyCRL_20240115100000_newPKID_1.crl',
        #     "CRL_SCA" : 'Cert/sca_001_01.crl',
        #     "CRL_RCA" : 'Cert/rca_001_01.crl'
        # }
        #
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


if __name__ == "__main__":

    print(f"Running file {args.sbf_file}")
    sbf_current_config()
