import paramiko
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import Certificate, CertificateRevocationList
import datetime
import os
import requests
from bs4 import BeautifulSoup
from osnma.utils.exceptions import DateException,RevokedException, IssuerException, VerifyException, IDDException

from osnma.utils.config import Config

######## logger ########
import osnma.utils.logger_factory as logger_factory
logger = logger_factory.get_logger(__name__)

class IDD:
    def __init__(self): 
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
        logger.info(f"disconnection successfully")


    def download_PK(self):

        directorios = self.sftp.listdir("OSNMA_PublicKey/Applicable")
        
        xml = sorted(filter(lambda x: x[-4:] == ".xml",directorios))[-1]
        
        pki_path = "OSNMA_PublicKey/Applicable/"
        remote_file_path = pki_path + xml
        
        self.sftp.get(remote_file_path, f"{Config.CERT_FOLDER}/" + xml)
        self.sftp.get(remote_file_path + ".md5", f"{Config.CERT_FOLDER}/" + xml + ".md5")

        tree = ET.parse(f"{Config.CERT_FOLDER}/" + xml)
        root = tree.getroot()

        cert_file_path = root.find('body').find('PublicKey').find('Certificate').text
        path_cert_file = pki_path + cert_file_path

        self.sftp.get(path_cert_file, f"{Config.CERT_FOLDER}/" + cert_file_path)
        self.sftp.get(path_cert_file + ".md5", f"{Config.CERT_FOLDER}/" + cert_file_path + ".md5")

        crl_file_path = root.find('body').find('PublicKey').find('CRL').text
        path_crl_file = pki_path + crl_file_path

        self.sftp.get(path_crl_file, f"{Config.CERT_FOLDER}/" + crl_file_path)
        self.sftp.get(path_crl_file + ".md5", f"{Config.CERT_FOLDER}/" + crl_file_path + ".md5")

        Config.PUBK_NAME = f"{Config.CERT_FOLDER}/" + xml
        Config.IDD_CERT["CERT_PKIEE"] = cert_file_path
        Config.IDD_CRL["CRL_ICA"] = crl_file_path
        logger.info(f"Download PKI done")


    def download_MerkleTree(self):

        directorios = self.sftp.listdir("OSNMA_MerkleTree/Applicable")

        xml = sorted(filter(lambda x: x[-4:] == ".xml",directorios))[-1]

        pki_path = "OSNMA_MerkleTree/Applicable/"
        remote_file_path = pki_path + xml

        self.sftp.get(remote_file_path, f"{Config.CERT_FOLDER}/" + xml)
        self.sftp.get(remote_file_path + ".md5", f"{Config.CERT_FOLDER}/" + xml + ".md5")
        
        tree = ET.parse(f"{Config.CERT_FOLDER}/" + xml)
        root = tree.getroot()

        sig_file_path = root.find('body').find('MerkleTree').find('SignatureFile').text
        path_sig_file = pki_path + sig_file_path

        self.sftp.get(path_sig_file, f"{Config.CERT_FOLDER}/" + sig_file_path)
        self.sftp.get(path_sig_file + ".md5", f"{Config.CERT_FOLDER}/" + sig_file_path + ".md5")

        cert_file_path = root.find('body').find('MerkleTree').find('SignatureVerificationCertificate').text
        path_cert_file = pki_path + cert_file_path

        self.sftp.get(path_cert_file, f"{Config.CERT_FOLDER}/" + cert_file_path)
        self.sftp.get(path_cert_file + ".md5", f"{Config.CERT_FOLDER}/" + cert_file_path + ".md5")
        
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


    def authenticate(self):
        entity = ["EEPKI", "MerkleTree", "ICA", "SCA", "RCA"]
        certs = {}
        crls = {}
        count = 0
        check = 0
        for name,value in Config.IDD_CERT.items():
            value = f"{Config.CERT_FOLDER}/" + value
            if os.path.exists(value):
                with open(value, 'rb') as cert_file:
                    cert_data = cert_file.read()

                second_cert_start = cert_data.find(b'-----BEGIN CERTIFICATE-----', 1)


                if second_cert_start != -1:
                    certs[entity[count]] = x509.load_pem_x509_certificate(cert_data[:second_cert_start], default_backend())
                    certs[entity[2]] = x509.load_pem_x509_certificate(cert_data[second_cert_start:], default_backend())
                    check = count + 1
                    
            
            count = count + 1
            if count > 1: break      

        count2 = 0
        for name,value in Config.IDD_CERT.items():
            value = f"{Config.CERT_FOLDER}/" + value
            if check == 0:
                if os.path.exists(value):
                    with open(value, 'rb') as cert_file:
                        cert_data = cert_file.read()
                    certs[entity[count2]] = x509.load_pem_x509_certificate(cert_data, default_backend())
                else:
                    logger.warning(f"{name} file don't found")
            if check == 1:
                if count2 > 2 or count2 == 1:
                    if os.path.exists(value):
                        with open(value, 'rb') as cert_file:
                            cert_data = cert_file.read()
                        certs[entity[count2]] = x509.load_pem_x509_certificate(cert_data, default_backend())
                    else:
                        logger.warning(f"{name} file don't found")
            if check == 2:
                if count2 > 2 or count2 == 0:
                    if os.path.exists(value):
                        with open(value, 'rb') as cert_file:
                            cert_data = cert_file.read()
                        certs[entity[count2]] = x509.load_pem_x509_certificate(cert_data, default_backend())
                    else:
                        logger.warning(f"{name} file don't found")
            if check == 3:
                if count2 > 2:
                    if os.path.exists(value):
                        with open(value, 'rb') as cert_file:
                            cert_data = cert_file.read()
                        certs[entity[count2]] = x509.load_pem_x509_certificate(cert_data, default_backend())
                    else:
                        logger.warning(f"{name} file don't found")
            count2 = count2 + 1

        count = 2
        for name,value in Config.IDD_CRL.items():
            value = f"{Config.CERT_FOLDER}/" + value
            if os.path.exists(value):
                with open(value, 'rb') as crl_file:
                    crl_data = crl_file.read()
                crls[entity[count]] = x509.load_pem_x509_crl(crl_data, default_backend())
            else:
                logger.warning(f"{name} file don't found")
            count = count + 1

        try:
            self.authenticateCRT(certs[entity[0]], certs[entity[2]], crls[entity[2]])
            logger.info(f"Authenticate {certs[entity[0]].subject} certificate done")
        except IDDException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except Exception as e:
            logger.critical(f"{e}")
            exit(1)
 
        count = 1
        for crl in crls:
            try:
                self.authenticateCRT(certs[entity[count]], certs[entity[count+1]], crls[crl])
                logger.info(f"Authenticate {certs[entity[count]].subject} certificate done")
            except IDDException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except Exception as e:
                logger.critical(f"{e}")
                exit(1)
            count = count + 1

        try:
            self.authenticateCRT(certs[entity[4]], certs[entity[4]], None)
            logger.info(f"Authenticate {certs[entity[4]].subject} certificate done")
        except IDDException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except Exception as e:
            logger.critical(f"{e}")
            exit(1)

        count = 2
        for crl in crls:
            try:
                self.authenticateCRL(crls[crl], certs[entity[count]])
                logger.info(f"Authenticate {crls[crl].issuer} CRL done")
            except IDDException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except Exception as e:
                logger.critical(f"{e}")
                exit(1)
            count = count + 1