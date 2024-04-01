import paramiko
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import datetime
import os
import requests
from bs4 import BeautifulSoup

from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)

class IDD:
    def __init__(self):
        if Config.CERT_FOLDER != '':
            if not os.path.isdir(Config.CERT_FOLDER):
                logger.warning(f"Path certs not exist")
                
                if not os.path.isdir('Cert/'):
                    os.mkdir("Cert")
                Config.CERT_FOLDER = 'Cert/'
        else:
            if not os.path.isdir('Cert/'):
                os.mkdir("Cert")
            Config.CERT_FOLDER = 'Cert/'
        
        if Config.DOWNLOAD_RCA:
            self.download_RCA()
        
        if Config.DOWNLOAD_SCA:
            self.download_SCA()

        if Config.DOWNLOAD_PKI or Config.DOWNLOAD_MERKLE:
            self.username = input("usuario:")
            self.password = input("contraseña:")

            try:
                self.connect()

                if Config.DOWNLOAD_PKI: 
                    self.download_PK()

                if Config.DOWNLOAD_MERKLE:
                    self.download_MerkleTree()
                
                self.disconnect()            
            except:
                logger.warning(f"failed to establish connection to targeted server")   
        self.authenticate()
            
            

        
    def connect(self):
        self.transport = paramiko.Transport(("osnma.gsc-europa.eu", 2222))

        self.transport.connect(username = self.username, password = self.password)
        logger.info(f"connection established successfully")

        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            
    
    def disconnect(self):
        self.sftp.close()
        self.transport.close()


    def download_PK(self):

        directorios = self.sftp.listdir("OSNMA_PublicKey/Applicable")

        xml = sorted(filter(lambda x: x[-4:] == ".xml",directorios))[-1]

        pki_path = "OSNMA_PublicKey/Applicable/"
        remote_file_path = pki_path + xml

        self.sftp.get(remote_file_path, Config.CERT_FOLDER + "OSNMA_PublicKey.xml")
        self.sftp.get(remote_file_path + ".md5", Config.CERT_FOLDER + "OSNMA_PublicKey.xml.md5")

        tree = ET.parse(Config.CERT_FOLDER + "OSNMA_PublicKey.xml")
        root = tree.getroot()

        cert_file_path = root.find('body').find('PublicKey').find('Certificate').text
        path_cert_file = pki_path + cert_file_path

        self.sftp.get(path_cert_file, Config.CERT_FOLDER + "OSNMA_PublicKey.crt")
        self.sftp.get(path_cert_file + ".md5", Config.CERT_FOLDER + "OSNMA_PublicKey.crt.md5")

        crl_file_path = root.find('body').find('PublicKey').find('CRL').text
        path_crl_file = pki_path + crl_file_path

        self.sftp.get(path_crl_file, Config.CERT_FOLDER + "OSNMA_PublicKeyCRL.crl")
        self.sftp.get(path_crl_file + ".md5", Config.CERT_FOLDER + "OSNMA_PublicKeyCRL.crl.md5")

        Config.PUBK_NAME = Config.CERT_FOLDER + "OSNMA_PublicKey.xml"
        Config.CERT_PKIEE = Config.CERT_FOLDER + "OSNMA_PublicKey.crt"
        Config.CRL_ICA = Config.CERT_FOLDER + "OSNMA_PublicKeyCRL.crl"
        logger.info(f"Download PKI done")


    def download_MerkleTree(self):

        directorios = self.sftp.listdir("OSNMA_MerkleTree/Applicable")

        xml = sorted(filter(lambda x: x[-4:] == ".xml",directorios))[-1]

        pki_path = "OSNMA_MerkleTree/Applicable/"
        remote_file_path = pki_path + xml

        self.sftp.get(remote_file_path, Config.CERT_FOLDER + "OSNMA_MerkleTree.xml")
        self.sftp.get(remote_file_path + ".md5", Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.md5")
        
        tree = ET.parse(Config.CERT_FOLDER + "OSNMA_MerkleTree.xml")
        root = tree.getroot()

        cert_file_path = root.find('body').find('MerkleTree').find('SignatureFile').text
        path_cert_file = pki_path + cert_file_path

        tipe_hash = root.find('body').find('MerkleTree').find('HashFunction').text

        if tipe_hash == "SHA-224":
            self.sftp.get(path_cert_file, Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p224")
            self.sftp.get(path_cert_file + ".md5", Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p224.md5")

        if tipe_hash == "SHA-256":
            self.sftp.get(path_cert_file, Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p256")
            self.sftp.get(path_cert_file + ".md5", Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p256.md5")

        if tipe_hash == "SHA-384":
            self.sftp.get(path_cert_file, Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p384")
            self.sftp.get(path_cert_file + ".md5", Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p384.md5")

        if tipe_hash == "SHA-521":
            self.sftp.get(path_cert_file, Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p521")
            self.sftp.get(path_cert_file + ".md5", Config.CERT_FOLDER + "OSNMA_MerkleTree.xml.p521.md5")

        crl_file_path = root.find('body').find('MerkleTree').find('SignatureVerificationCertificate').text
        path_crl_file = pki_path + crl_file_path

        self.sftp.get(path_crl_file, Config.CERT_FOLDER + "OSNMA_MerkleTree.crt")
        self.sftp.get(path_crl_file + ".md5", Config.CERT_FOLDER + "OSNMA_MerkleTree.crt.md5")

        Config.MERKLE_NAME = Config.CERT_FOLDER + "OSNMA_MerkleTree.xml"
        Config.CERT_MERKLE = Config.CERT_FOLDER + "OSNMA_MerkleTree.crt"
        logger.info(f"Download Merkle Tree done")


    def download_RCA(self):
        
        url = 'https://www.euspa.europa.eu/about/how-we-work/pki/products'

        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = soup.find_all('a')
            hrefs = [""]
            for link in links: 
                href = link.get('href')
                if(href != None):
                    hrefs.append(href)
            href = sorted(filter(lambda x: x[-4:] == ".crt" and os.path.basename(x)[:3] == "rca",hrefs))[-1]

            crt_response = requests.get(href, Config.CERT_FOLDER + "rca.crt")
            
            if crt_response.status_code == 200:
                
                with open(Config.CERT_FOLDER + "rca.crt", 'wb') as f:
                    f.write(crt_response.content)
                logger.info(f"Download certificate RCA done")

                Config.CERT_RCA = Config.CERT_FOLDER + "rca.crt"
            else:
                logger.warning(f"Download certificate RCA failed")
            

            href = sorted(filter(lambda x: x[-4:] == ".crl" and os.path.basename(x)[:3] == "rca",hrefs))[-1]

            crt_response = requests.get(href, Config.CERT_FOLDER + "rca.crl")
            
            if crt_response.status_code == 200:
                
                with open(Config.CERT_FOLDER + "rca.crl", 'wb') as f:
                    f.write(crt_response.content)
                logger.info(f"Download CRL RCA done")

                Config.CRL_RCA = Config.CERT_FOLDER + "rca.crl"
            else:
                logger.warning(f"Download CRL RCA failed")

        else:
            logger.warning(f"Error accessing the website")


    def download_SCA(self):
        url = 'https://www.euspa.europa.eu/about/how-we-work/pki/products'

        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = soup.find_all('a')
            hrefs = [""]
            for link in links: 
                href = link.get('href')
                if(href != None):
                    hrefs.append(href)
            href = sorted(filter(lambda x: x[-4:] == ".crt" and os.path.basename(x)[:3] == "sca",hrefs))[-1]

            crt_response = requests.get(href, Config.CERT_FOLDER + "sca.crt")
            
            if crt_response.status_code == 200:
               
                with open(Config.CERT_FOLDER + "sca.crt", 'wb') as f:
                    f.write(crt_response.content)
                logger.info(f"Download certificate SCA done")
                
                Config.CERT_SCA = Config.CERT_FOLDER + "sca.crt"
            else:
                logger.warning(f"Download certificate SCA failed")
            

            href = sorted(filter(lambda x: x[-4:] == ".crl" and os.path.basename(x)[:3] == "sca",hrefs))[-1]

            crt_response = requests.get(href, Config.CERT_FOLDER + "sca.crl")
            
            if crt_response.status_code == 200:
               
                with open(Config.CERT_FOLDER + "sca.crl", 'wb') as f:
                    f.write(crt_response.content)
                logger.info(f"Download CRL SCA done")

                Config.CRL_SCA = Config.CERT_FOLDER + "sca.crl"
            else:
                logger.warning(f"Download CRL SCA failed")

        else:
            logger.warning(f"Error accessing the website")


    def authenticateCRT(self,cert_subject, cert_emisor, crl):
        # Verificar la validez en el tiempo
        now = datetime.datetime.now()
        if now < cert_subject.not_valid_before or now > cert_subject.not_valid_after:
            logger.warning(f"The certificate is not within its validity period.")
            return 0
        
        if crl != None:
            revoked_cert = crl.get_revoked_certificate_by_serial_number(cert_subject.serial_number)
            if revoked_cert is not None:
                logger.warning(f"The certificate has been revoked")
                return 0
            
        #Verifica si el emisor del certificado es igual al sujeto del certificado emisor
        if cert_subject.issuer != cert_emisor.subject:
            logger.warning(f"The certificate issuer is incorrect")
            return 0
        
        # Verificar la firma del certificado
        try:
            cert_emisor.public_key().verify(
                cert_subject.signature,
                cert_subject.tbs_certificate_bytes,
                cert_emisor.signature_algorithm_parameters,
            )
        except:
            logger.warning(f"The certificate signature is invalid.")
            return 0
        return 1
        

    def authenticateCRL(self,crl, cert):
        # Verificar la validez en el tiempo
        now = datetime.datetime.now()
        if now < crl.last_update or now > crl.next_update:
            logger.warning(f"The CRL is not within its validity period.")
            return 0
        
        if crl.issuer != cert.subject:
            logger.warning(f"The CRL issuer is incorrect.")
            return 0
        
        # Verificar la firma del certificado
        try:
            crl.is_signature_valid(cert.public_key())
            cert.public_key().verify(
                crl.signature,
                crl.tbs_certlist_bytes,
                cert.signature_algorithm_parameters,)
    
        except:
            logger.warning(f"The CRL signature is invalid.")
            return 0
        return 1

    def authenticate(self):
        if os.path.exists(Config.CERT_MERKLE):
            with open(Config.CERT_MERKLE, 'rb') as cert_file:
                cert_data = cert_file.read()

            second_cert_start = cert_data.find(b'-----BEGIN CERTIFICATE-----', 1)


            if second_cert_start != -1:
                certEEMerkleTree = x509.load_pem_x509_certificate(cert_data[:second_cert_start], default_backend())
                certICA = x509.load_pem_x509_certificate(cert_data[second_cert_start:], default_backend())
            
            else:
                logger.warning(f"Two certificates not found in .crt file")
                return
            
        if os.path.exists(Config.CERT_PKIEE):
            with open(Config.CERT_PKIEE, 'rb') as cert_file:
                cert_data = cert_file.read()

            second_cert_start = cert_data.find(b'-----BEGIN CERTIFICATE-----', 1)


            if second_cert_start != -1:
                certEEPKR = x509.load_pem_x509_certificate(cert_data[:second_cert_start], default_backend())
                certICA = x509.load_pem_x509_certificate(cert_data[second_cert_start:], default_backend())
            
            else:
                logger.warning(f"Two certificates not found in .crt file")
                return
            
        if os.path.exists(Config.CRL_ICA):
            with open(Config.CRL_ICA, 'rb') as crl_file:
                crl_data = crl_file.read()
            crlICA = x509.load_pem_x509_crl(crl_data, default_backend())


        if os.path.exists(Config.CERT_SCA):
            with open(Config.CERT_SCA, 'rb') as cert_file:
                cert_data = cert_file.read()
            certSCA = x509.load_pem_x509_certificate(cert_data, default_backend())

        if os.path.exists(Config.CRL_SCA):
            with open(Config.CRL_SCA, 'rb') as crl_file:
                crl_data = crl_file.read()
            crlSCA = x509.load_pem_x509_crl(crl_data, default_backend())
        
        if os.path.exists(Config.CERT_RCA):
            with open(Config.CERT_RCA, 'rb') as cert_file:
                cert_data = cert_file.read()
            certRCA = x509.load_pem_x509_certificate(cert_data, default_backend())

        if os.path.exists(Config.CRL_RCA):
            with open(Config.CRL_RCA, 'rb') as crl_file:
                crl_data = crl_file.read()
            crlRCA = x509.load_pem_x509_crl(crl_data, default_backend())

        if self.authenticateCRT(certEEMerkleTree, certICA, crlICA):
            logger.info(f"Authenticate certificate Merkle Tree done")
        else:
            logger.warning(f"Authenticate certificate Merkle Tree is failed")

        if self.authenticateCRT(certEEPKR, certICA, crlICA):
            logger.info(f"Authenticate certificate EE done")
        else:
            logger.warning(f"Authenticate certificate EE is failed")

        if self.authenticateCRT(certICA, certSCA, crlSCA):
            logger.info(f"Authenticate certificate ICA done")
        else:
            logger.warning(f"Authenticate certificate ICA is failed")

        if self.authenticateCRL(crlICA, certICA):
            logger.info(f"Authenticate CRL ICA done")
        else:
            logger.warning(f"Authenticate CRL ICA is failed")

        if self.authenticateCRT(certSCA, certRCA, crlRCA):
            logger.info(f"Authenticate certificate SCA done")
        else:
            logger.warning(f"Authenticate certificate SCA is failed")

        if self.authenticateCRL(crlSCA, certSCA):
            logger.info(f"Authenticate CRL SCA done")
        else:
            logger.warning(f"Authenticate CRL SCA is failed")

        if self.authenticateCRT(certRCA, certRCA, None):
            logger.info(f"Authenticate certificate RCA done")
        else:
            logger.warning(f"Authenticate certificate RCA is failed")

        if self.authenticateCRL(crlRCA, certRCA):
            logger.info(f"Authenticate CRL RCA done")
        else:
            logger.warning(f"Authenticate CRL RCA is failed")


