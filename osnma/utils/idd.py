import paramiko
from paramiko import SSHException
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import Certificate, CertificateRevocationList
import hashlib
import datetime
import os
import requests
from bs4 import BeautifulSoup
from osnma.utils.exceptions import DateException,RevokedException, IssuerException, VerifyException, IDDException, MD5Exception

from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)

class IDD:
    def __init__(self):

        # Avoid running anything if the user does not want to
        if not self._idd_coherence_check():
            return

        Config.IDD_CERT = {
            "CERT_PKIEE" : '',
            "CERT_MERKLE" : '',
            "CERT_ICA" : '',
            "CERT_SCA" : '',
            "CERT_RCA" : ''
        }
        Config.IDD_CERT.update(Config.USER_IDD_CERT)

        Config.IDD_CRL = {
            "CRL_ICA" : '',
            "CRL_SCA" : '',
            "CRL_RCA" : ''
        }
        Config.IDD_CRL.update(Config.USER_IDD_CRL)

        if not os.path.isdir(f"{Config.CERT_FOLDER}"):
            logger.warning(f"Path certs not exist")
            a = f"{Config.EXEC_PATH}" + '/Cert'
            if not os.path.isdir(a):
                os.mkdir(a)
            Config.CERT_FOLDER = a
        
        if Config.DOWNLOAD_RCA:
            self.web_download("rca")
        
        if Config.DOWNLOAD_SCA:
            self.web_download("sca")

        if Config.DOWNLOAD_PKI or Config.DOWNLOAD_MERKLE:
            #self.username = input("usuario:")
            #self.password = input("contraseña:")
            self.username = "AlexGP"
            self.password = "Alex1564382!"

            try:
                self.connect()

                if Config.DOWNLOAD_PKI:
                    self.download_PK()

                if Config.DOWNLOAD_MERKLE:
                    self.download_MerkleTree()

                self.disconnect()
            except SSHException as e:
                logger.warning(f"Failed to establish connection to targeted server: {e} Trying to continue...")
            except Exception as e:
                logger.warning(f"Error when downloading PKI and MerkleTree: {e} Trying to continue...")

        self.parser()
        self.authenticate()


    def _idd_coherence_check(self):
        # TODO: Define more inconsistencies, e.g. provide RCA CERT without CLR

        download_idd_info = (Config.DOWNLOAD_RCA or Config.DOWNLOAD_SCA or Config.DOWNLOAD_PKI or Config.DOWNLOAD_MERKLE)
        provided_idd_info = (Config.USER_IDD_CRL or Config.USER_IDD_CERT)

        if not download_idd_info and not provided_idd_info:
            return False

        return True


    def connect(self):
        self.transport = paramiko.Transport(("osnma.gsc-europa.eu", 2222))
        self.transport.connect(username = self.username, password = self.password)
        logger.info(f"Connection with the SFTP server established successfully")
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)


    def disconnect(self):
        self.sftp.close()
        self.transport.close()


    def validate_MD5(self, file_path):
        new_file_path = f"{Config.CERT_FOLDER}/" + file_path
        hash = hashlib.md5()
        with open(new_file_path, 'rb') as file:
            for bloque in iter(lambda: file.read(4096), b""):
                hash.update(bloque)
        
        file_path_MD5 = new_file_path + ".md5"
        with open(file_path_MD5, 'r') as file_MD5:
            expected_md5 = file_MD5.read().strip()
            
        return hash.hexdigest() == expected_md5


    def extract_ica(self, path):
        new_path = f"{Config.CERT_FOLDER}/" + path
        if os.path.exists(new_path):
            with open(new_path, 'rb') as cert_file:
                cert_data = cert_file.read()

            second_cert_start = cert_data.find(b'-----BEGIN CERTIFICATE-----', 1)
            if second_cert_start != -1:
                try:
                    with open(new_path, 'wb') as ee_cert:
                        ee_cert.write(cert_data[:second_cert_start])
                    
                    if Config.DOWNLOAD_ICA:
                        ica_path = f"{Config.CERT_FOLDER}/" + "OSNMA_ICA.crt"
                        with open(ica_path, 'wb') as ica_cert:
                            ica_cert.write(cert_data[second_cert_start:])
                        Config.DOWNLOAD_ICA = False
                        Config.IDD_CERT["CERT_ICA"] = "OSNMA_ICA.crt"
                except:
                    logger.warning(f"ICA certificate could not be created")
            else:
                logger.warning(f"ICA certificate could not be created")


    def download_PK(self):
        sftp_public_key_path = "OSNMA_PublicKey/Applicable/"

        # Download Public Key XML and MD5
        public_key_files = self.sftp.listdir(sftp_public_key_path)
        pubk_xml = sorted(filter(lambda x: x[-4:] == ".xml", public_key_files))[-1]
        remote_file_path = sftp_public_key_path + pubk_xml

        self.sftp.get(remote_file_path, f"{Config.CERT_FOLDER}/" + pubk_xml)
        self.sftp.get(remote_file_path + ".md5", f"{Config.CERT_FOLDER}/" + pubk_xml + ".md5")

        if not self.validate_MD5(pubk_xml):
            raise MD5Exception(f"{pubk_xml}")

        # Find and download the certificate to authenticate the key
        pubk_xml_parser = ET.parse(f"{Config.CERT_FOLDER}/" + pubk_xml).getroot()
        cert_file_path = pubk_xml_parser.find('body').find('PublicKey').find('Certificate').text
        path_cert_file = sftp_public_key_path + cert_file_path

        self.sftp.get(path_cert_file, f"{Config.CERT_FOLDER}/" + cert_file_path)
        self.sftp.get(path_cert_file + ".md5", f"{Config.CERT_FOLDER}/" + cert_file_path + ".md5")

        if not self.validate_MD5(cert_file_path):
            raise MD5Exception(f"{cert_file_path}")
        
        self.extract_ica(cert_file_path)

        # Find and download the CRL for the key
        crl_file_path = pubk_xml_parser.find('body').find('PublicKey').find('CRL').text
        path_crl_file = sftp_public_key_path + crl_file_path

        self.sftp.get(path_crl_file, f"{Config.CERT_FOLDER}/" + crl_file_path)
        self.sftp.get(path_crl_file + ".md5", f"{Config.CERT_FOLDER}/" + crl_file_path + ".md5")

        if not self.validate_MD5(crl_file_path):
            raise MD5Exception(f"{crl_file_path}")

        # Save the file names in the Config object
        Config.PUBK_NAME = f"{Config.CERT_FOLDER}/" + pubk_xml
        Config.IDD_CERT["CERT_PKIEE"] = cert_file_path
        Config.IDD_CRL["CRL_ICA"] = crl_file_path
        logger.info(f"Download of the Public Key done")


    def download_MerkleTree(self):

        sftp_merkle_tree_path = "OSNMA_MerkleTree/Applicable/"

        # Download Merkle Tree XML and MD5
        merkle_tree_files = self.sftp.listdir(sftp_merkle_tree_path)
        xml = sorted(filter(lambda x: x[-4:] == ".xml", merkle_tree_files))[-1]
        remote_file_path = sftp_merkle_tree_path + xml

        self.sftp.get(remote_file_path, f"{Config.CERT_FOLDER}/" + xml)
        self.sftp.get(remote_file_path + ".md5", f"{Config.CERT_FOLDER}/" + xml + ".md5")

        if not self.validate_MD5(xml):
            raise MD5Exception(f"{xml}")
        
        # Download Merkle Tree Signature
        merkle_tree_xml_parser = ET.parse(f"{Config.CERT_FOLDER}/" + xml).getroot()
        sig_file_path = merkle_tree_xml_parser.find('body').find('MerkleTree').find('SignatureFile').text
        path_sig_file = sftp_merkle_tree_path + sig_file_path

        self.sftp.get(path_sig_file, f"{Config.CERT_FOLDER}/" + sig_file_path)
        self.sftp.get(path_sig_file + ".md5", f"{Config.CERT_FOLDER}/" + sig_file_path + ".md5")

        if not self.validate_MD5(sig_file_path):
            raise MD5Exception(f"{sig_file_path}")
        
        # Download Merkle Tree Certificate
        cert_file_path = merkle_tree_xml_parser.find('body').find('MerkleTree').find('SignatureVerificationCertificate').text
        path_cert_file = sftp_merkle_tree_path + cert_file_path

        self.sftp.get(path_cert_file, f"{Config.CERT_FOLDER}/" + cert_file_path)
        self.sftp.get(path_cert_file + ".md5", f"{Config.CERT_FOLDER}/" + cert_file_path + ".md5")

        if not self.validate_MD5(cert_file_path):
            raise MD5Exception(f"{cert_file_path}")

        self.extract_ica(cert_file_path)

        # Save the file names in the Config object
        Config.MERKLE_NAME = f"{Config.CERT_FOLDER}/" + xml
        Config.IDD_CERT["CERT_MERKLE"] = cert_file_path
        logger.info(f"Download Merkle Tree done")


    def web_download(self, type: str):
        
        url = 'https://www.euspa.europa.eu/about/corporate-documents/pki-public-key-infrastructure/pki-products'

        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = soup.find_all('a')
            hrefs = [""]
            for link in links: 
                href = link.get('href')
                if(href != None):
                    hrefs.append(href)
            href = sorted(filter(lambda x: x[-4:] == ".crt" and os.path.basename(x)[:3] == type,hrefs))[-1]
            path_cert = f"{Config.CERT_FOLDER}/" + os.path.basename(href)

            crt_response = requests.get(href, path_cert)
            
            if crt_response.status_code == 200:
                
                with open(path_cert, 'wb') as f:
                    f.write(crt_response.content)
                logger.info(f"Download {type} certificate done")
                if type == "rca":
                    Config.IDD_CERT["CERT_RCA"] = os.path.basename(href)
                else:
                    Config.IDD_CERT["CERT_SCA"] = os.path.basename(href)
            else:
                logger.warning(f"Download {type} certificate failed")
            

            href = sorted(filter(lambda x: x[-4:] == ".crl" and os.path.basename(x)[:3] == type,hrefs))[-1]
            path_crl = f"{Config.CERT_FOLDER}/" + os.path.basename(href)

            crl_response = requests.get(href, path_crl)
            
            if crl_response.status_code == 200:
                
                with open(path_crl, 'wb') as f:
                    f.write(crl_response.content)
                logger.info(f"Download {type} CRL done")
                if type == "rca":
                    Config.IDD_CRL["CRL_RCA"] = os.path.basename(href)
                else:
                    Config.IDD_CRL["CRL_SCA"] = os.path.basename(href)
            else:
                logger.warning(f"Download {type} CRL failed")

        else:
            logger.warning(f"Error accessing the website")


    def authenticateCRT(self,cert_subject: Certificate, cert_emisor: Certificate, crl: CertificateRevocationList):
        
        now = datetime.datetime.now()
        if now < cert_subject.not_valid_before or now > cert_subject.not_valid_after:
            raise DateException(f"certificate {cert_subject.subject}")
        
        if crl != None:
            revoked_cert = crl.get_revoked_certificate_by_serial_number(cert_subject.serial_number)
            if revoked_cert is not None:
                raise RevokedException(f"certificate {cert_subject.subject}")
            
        
        if cert_subject.issuer != cert_emisor.subject:
            raise IssuerException(f"certificate {cert_subject.subject}")
        
        try:
            cert_emisor.public_key().verify(
                cert_subject.signature,
                cert_subject.tbs_certificate_bytes,
                cert_emisor.signature_algorithm_parameters,
            )
        except:
            raise VerifyException(f"certificate {cert_subject.subject}")
        

    def authenticateCRL(self,crl: CertificateRevocationList, cert: Certificate):
        
        now = datetime.datetime.now()
        if now < crl.last_update or now > crl.next_update:
            raise DateException(f"CRL {crl.issuer}")
        
        if crl.issuer != cert.subject:
            raise IssuerException(f"CRL {crl.issuer}")
        
        
        try:
            crl.is_signature_valid(cert.public_key())
            cert.public_key().verify(
                crl.signature,
                crl.tbs_certlist_bytes,
                cert.signature_algorithm_parameters,)
    
        except:
            raise VerifyException(f"CRL {crl.issuer}")


    def parser(self):
        truth_chain = [
            ["CERT_MERKLE", "CERT_ICA", "CRL_ICA"],
            ["CERT_PKIEE", "CERT_ICA", "CRL_ICA"],
            ["CERT_ICA", "CERT_SCA", "CRL_SCA"],
            ["CERT_SCA", "CERT_RCA", "CRL_RCA"],
            ["CERT_RCA", "CERT_RCA", None]
        ]
        idd_cert = []
        idd_crl = []
        self.user_truth_chain = []

        for crt, crt_issuer, crl in truth_chain:
            if Config.IDD_CERT[crt] != "" and Config.IDD_CERT[crt_issuer] != "" and (crl is None or Config.IDD_CRL[crl] != ""):
                value_0 = f"{Config.CERT_FOLDER}/" + Config.IDD_CERT[crt]
                value_1 = f"{Config.CERT_FOLDER}/" + Config.IDD_CERT[crt_issuer]
                if crl is not None:
                    value_2 = f"{Config.CERT_FOLDER}/" + Config.IDD_CRL[crl]
                if os.path.exists(value_0) and os.path.exists(value_1) and os.path.exists(value_2):
                    self.user_truth_chain.append([crt, crt_issuer, crl])
                    idd_cert.append(crt)
                    idd_cert.append(crt_issuer)
                    if crl is not None:
                        idd_crl.append(crl)
                else:
                    break
            else:
                break

        idd_cert =list(set(idd_cert))
        idd_crl =list(set(idd_crl))

        self.authenticate_entity = {None : None}

        for name in idd_cert:
            value = Config.IDD_CERT[name]
            path = f"{Config.CERT_FOLDER}/" + value
            if os.path.exists(path) and value != "":
                with open(path, 'rb') as cert_file:
                    cert_data = cert_file.read()
                self.authenticate_entity[name] = x509.load_pem_x509_certificate(cert_data, default_backend())
            else:
                logger.warning(f"{name} file don't found")

        for name in idd_crl:
            value = Config.IDD_CRL[name]
            path = f"{Config.CERT_FOLDER}/" + value
            if os.path.exists(path) and value != "":
                with open(path, 'rb') as crl_file:
                    crl_data = crl_file.read()
                self.authenticate_entity[name] = x509.load_pem_x509_crl(crl_data, default_backend())
            else:
                logger.warning(f"{name} file don't found")
        
        
    def authenticate(self): 
        try:
            for crt, crt_issuer, crl in self.user_truth_chain:
                if crl is not None:
                    self.authenticateCRL( self.authenticate_entity[crl],  self.authenticate_entity[crt_issuer])
                    logger.info(f"Authenticate { self.authenticate_entity[crl].issuer} CRL done")

                self.authenticateCRT( self.authenticate_entity[crt],  self.authenticate_entity[crt_issuer],  self.authenticate_entity[crl])
                logger.info(f"Authenticate { self.authenticate_entity[crt].subject} certificate done")
        except IDDException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except Exception as e:
            logger.critical(f"{e}")
            exit(1)