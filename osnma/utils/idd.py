import paramiko
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import datetime
import os
import requests
from bs4 import BeautifulSoup
from osnma.utils.exceptions import DateException,RevokedException, IssuerException, VerifyException

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
            self.web_download("rca")
        
        if Config.DOWNLOAD_SCA:
            self.web_download("sca")

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
        logger.info(f"disconnection successfully")


    def download_PK(self):

        directorios = self.sftp.listdir("OSNMA_PublicKey/Applicable")
        
        xml = sorted(filter(lambda x: x[-4:] == ".xml",directorios))[-1]
        
        pki_path = "OSNMA_PublicKey/Applicable/"
        remote_file_path = pki_path + xml
        
        self.sftp.get(remote_file_path, Config.CERT_FOLDER + xml)
        self.sftp.get(remote_file_path + ".md5", Config.CERT_FOLDER + xml + ".md5")

        tree = ET.parse(Config.CERT_FOLDER + xml)
        root = tree.getroot()

        cert_file_path = root.find('body').find('PublicKey').find('Certificate').text
        path_cert_file = pki_path + cert_file_path

        self.sftp.get(path_cert_file, Config.CERT_FOLDER + cert_file_path)
        self.sftp.get(path_cert_file + ".md5", Config.CERT_FOLDER + cert_file_path + ".md5")

        crl_file_path = root.find('body').find('PublicKey').find('CRL').text
        path_crl_file = pki_path + crl_file_path

        self.sftp.get(path_crl_file, Config.CERT_FOLDER + crl_file_path)
        self.sftp.get(path_crl_file + ".md5", Config.CERT_FOLDER + crl_file_path + ".md5")

        Config.PUBK_NAME = Config.CERT_FOLDER + xml
        Config.IDD_CERT["CERT_PKIEE"] = Config.CERT_FOLDER + cert_file_path
        Config.IDD_CRL["CRL_ICA"] = Config.CERT_FOLDER + crl_file_path
        logger.info(f"Download PKI done")


    def download_MerkleTree(self):

        directorios = self.sftp.listdir("OSNMA_MerkleTree/Applicable")

        xml = sorted(filter(lambda x: x[-4:] == ".xml",directorios))[-1]

        pki_path = "OSNMA_MerkleTree/Applicable/"
        remote_file_path = pki_path + xml

        self.sftp.get(remote_file_path, Config.CERT_FOLDER + xml)
        self.sftp.get(remote_file_path + ".md5", Config.CERT_FOLDER + xml + ".md5")
        
        tree = ET.parse(Config.CERT_FOLDER + xml)
        root = tree.getroot()

        sig_file_path = root.find('body').find('MerkleTree').find('SignatureFile').text
        path_sig_file = pki_path + sig_file_path

        self.sftp.get(path_sig_file, Config.CERT_FOLDER + sig_file_path)
        self.sftp.get(path_sig_file + ".md5", Config.CERT_FOLDER + sig_file_path + ".md5")

        cert_file_path = root.find('body').find('MerkleTree').find('SignatureVerificationCertificate').text
        path_cert_file = pki_path + cert_file_path

        self.sftp.get(path_cert_file, Config.CERT_FOLDER + cert_file_path)
        self.sftp.get(path_cert_file + ".md5", Config.CERT_FOLDER + cert_file_path + ".md5")

        Config.MERKLE_NAME = Config.CERT_FOLDER + xml
        Config.IDD_CERT["CERT_MERKLE"] = Config.CERT_FOLDER + cert_file_path
        logger.info(f"Download Merkle Tree done")


    def web_download(self, type):
        
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
            path_cert = Config.CERT_FOLDER + os.path.basename(href)

            crt_response = requests.get(href, path_cert)
            
            if crt_response.status_code == 200:
                
                with open(path_cert, 'wb') as f:
                    f.write(crt_response.content)
                logger.info(f"Download {type} certificate done")
                if type == "rca":
                    Config.IDD_CERT["CERT_RCA"] = path_cert
                else:
                    Config.IDD_CERT["CERT_SCA"] = path_cert
            else:
                logger.warning(f"Download {type} certificate failed")
            

            href = sorted(filter(lambda x: x[-4:] == ".crl" and os.path.basename(x)[:3] == type,hrefs))[-1]
            path_crl = Config.CERT_FOLDER + os.path.basename(href)

            crl_response = requests.get(href, path_crl)
            
            if crl_response.status_code == 200:
                
                with open(path_crl, 'wb') as f:
                    f.write(crl_response.content)
                logger.info(f"Download {type} CRL done")
                if type == "rca":
                    Config.IDD_CRL["CRL_RCA"] = path_crl
                else:
                    Config.IDD_CRL["CRL_SCA"] = path_crl
            else:
                logger.warning(f"Download {type} CRL failed")

        else:
            logger.warning(f"Error accessing the website")


    def authenticateCRT(self,cert_subject, cert_emisor, crl):
        
        now = datetime.datetime.now()
        if now < cert_subject.not_valid_before or now > cert_subject.not_valid_after:
            raise DateException(f"The certificate {cert_subject.subject} is not within its validity period.")
        
        if crl != None:
            revoked_cert = crl.get_revoked_certificate_by_serial_number(cert_subject.serial_number)
            if revoked_cert is not None:
                raise RevokedException(f"The certificate {cert_subject.subject} has been revoked")
            
        
        if cert_subject.issuer != cert_emisor.subject:
            raise IssuerException(f"The issuer and the subject of the certificate {cert_subject.subject} have not matched.")
        
        try:
            cert_emisor.public_key().verify(
                cert_subject.signature,
                cert_subject.tbs_certificate_bytes,
                cert_emisor.signature_algorithm_parameters,
            )
        except:
            raise VerifyException(f"The certificate {cert_subject.subject} signature is invalid.")
        

    def authenticateCRL(self,crl, cert):
        
        now = datetime.datetime.now()
        if now < crl.last_update or now > crl.next_update:
            raise DateException(f"The CRL {crl.issuer} is not within its validity period.")
        
        if crl.issuer != cert.subject:
            raise IssuerException(f"The issuer and the subject of the CRL {crl.issuer} have not matched.")
        
        
        try:
            crl.is_signature_valid(cert.public_key())
            cert.public_key().verify(
                crl.signature,
                crl.tbs_certlist_bytes,
                cert.signature_algorithm_parameters,)
    
        except:
            raise VerifyException(f"The CRL {crl.issuer} signature is invalid.")


    def authenticate(self):
        cert = [0,0,0,0,0]
        crl = [0,0,0]
        count = 0
        check = 0
        for name,value in Config.IDD_CERT.items():
            
            if os.path.exists(value):
                with open(value, 'rb') as cert_file:
                    cert_data = cert_file.read()

                second_cert_start = cert_data.find(b'-----BEGIN CERTIFICATE-----', 1)


                if second_cert_start != -1:
                    cert[count] = x509.load_pem_x509_certificate(cert_data[:second_cert_start], default_backend())
                    cert[2] = x509.load_pem_x509_certificate(cert_data[second_cert_start:], default_backend())
                    check = count + 1
                    
            
            count = count + 1
            if count > 1: break      

        count2 = 0
        for name,value in Config.IDD_CERT.items():
            if check == 0:
                if os.path.exists(value):
                    with open(value, 'rb') as cert_file:
                        cert_data = cert_file.read()
                    cert[count2] = x509.load_pem_x509_certificate(cert_data, default_backend())
                else:
                    logger.warning(f"{name} file don't found")
            if check == 1:
                if count2 > 2 or count2 == 1:
                    if os.path.exists(value):
                        with open(value, 'rb') as cert_file:
                            cert_data = cert_file.read()
                        cert[count2] = x509.load_pem_x509_certificate(cert_data, default_backend())
                    else:
                        logger.warning(f"{name} file don't found")
            if check == 2:
                if count2 > 2 or count2 == 0:
                    if os.path.exists(value):
                        with open(value, 'rb') as cert_file:
                            cert_data = cert_file.read()
                        cert[count2] = x509.load_pem_x509_certificate(cert_data, default_backend())
                    else:
                        logger.warning(f"{name} file don't found")
            if check == 3:
                if count2 > 2:
                    if os.path.exists(value):
                        with open(value, 'rb') as cert_file:
                            cert_data = cert_file.read()
                        cert[count2] = x509.load_pem_x509_certificate(cert_data, default_backend())
                    else:
                        logger.warning(f"{name} file don't found")
            count2 = count2 + 1

        count = 0
        for name,value in Config.IDD_CRL.items():
            if os.path.exists(value):
                with open(value, 'rb') as crl_file:
                    crl_data = crl_file.read()
                crl[count] = x509.load_pem_x509_crl(crl_data, default_backend())
            else:
                logger.warning(f"{name} file don't found")
            count = count + 1


        try:
            self.authenticateCRT(cert[0], cert[2], crl[0])
            logger.info(f"Authenticate {cert[0].subject} certificate done")
        except DateException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except RevokedException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except IssuerException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except VerifyException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except Exception as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")

        count = 1
        for value in crl:
            try:
                self.authenticateCRT(cert[count], cert[count+1], value)
                logger.info(f"Authenticate {cert[count].subject} certificate done")
            except DateException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except RevokedException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except IssuerException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except VerifyException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except Exception as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            count = count + 1

        try:
            self.authenticateCRT(cert[4], cert[4], None)
            logger.info(f"Authenticate {cert[4].subject} certificate done")
        except DateException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except RevokedException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except IssuerException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except VerifyException as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")
        except Exception as e:
            if Config.IDD_STRICT:
                logger.critical(f"{e}")
                exit(1)
            else:
                logger.warning(f"{e}")

        count = 2
        for value in crl:
            try:
                self.authenticateCRL(value, cert[count])
                logger.info(f"Authenticate {value.issuer} CRL done")
            except DateException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except IssuerException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except VerifyException as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            except Exception as e:
                if Config.IDD_STRICT:
                    logger.critical(f"{e}")
                    exit(1)
                else:
                    logger.warning(f"{e}")
            count = count + 1