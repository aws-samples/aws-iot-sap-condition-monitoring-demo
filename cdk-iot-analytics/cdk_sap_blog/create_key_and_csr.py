"""
    Description:

    - This module assumes that the `certs/` directory is located one level
      above the location of this module (i.e. `../certs/`)
    - The purpose of this module is to provide a mechanism for developers
      to use for having their X509 Certificate Signing Requests from 
      crypto coprocessors such as the ATECC608 signed by AWS IoT Core. If
      not using a custom Private Key and CSR, this module can create them.
"""
from OpenSSL import crypto
import os
import sys
import datetime
import requests


#Variables
TYPE_RSA = crypto.TYPE_RSA
TYPE_DSA = crypto.TYPE_DSA
HERE = os.path.dirname(os.path.abspath(__file__))
CERTS_DIR = os.path.join(HERE, '..', 'certs')
now = datetime.datetime.now()
d = now.date()

#Pull these out of scope
global key

def download_root_CA():
    with open('certs/AmazonRootCA1.pem', 'w+') as f:
        f.write(
            requests.get(
                'https://www.amazontrust.com/repository/AmazonRootCA1.pem'
            ).content.decode()
        )

def generatekey(cn, bitlength=4096):
    global key
    keypath = os.path.join(CERTS_DIR, cn + '.key.pem')
    if os.path.exists(keypath):
        print(f"Using existing Private Key file: {keypath}")
        with open(keypath, 'r') as f:
            key = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read())
    else:
        key = crypto.PKey()
        print("Generating Key...")
        key.generate_key(TYPE_RSA, bitlength)
        with open(keypath, "w") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode())
        print(f"Private Key created: {keypath}")
    return keypath

def generatecsr(keypath, cn):
    global key
    csrpath = os.path.join(CERTS_DIR, cn + '.csr.pem')
    req = crypto.X509Req()
    req.get_subject().CN = cn
    req.get_subject().C = "US"
    req.get_subject().ST = "MN"
    req.get_subject().L = "Lake Elmo"
    req.get_subject().O = "Amazon Web Services"
    req.get_subject().OU = "Partner Solution Architecture"
    req.set_pubkey(key)
    req.sign(key, "sha256")

    if os.path.exists(csrpath):
        print(f"Using existing CSR: {csrpath}")
    else:
        with open(csrpath, "w") as f:
            f.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req).decode())
        print(f"Created CSR: {csrpath}")

    return csrpath


def generate_key_and_csr(thing_name, bitlength=4096):
    keypath = None
    csrpath = os.path.join(CERTS_DIR, thing_name + '.csr.pem')
    if os.path.exists(csrpath):
        print(f"CSR already exists: {csrpath}")
    else:
        keypath = generatekey(thing_name, bitlength=bitlength)
        csrpath = generatecsr(keypath, thing_name)
    return keypath, csrpath

if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) < 2:
        exit("Provide thing_name as arg.")
    download_root_CA()
    generate_key_and_csr(sys.argv[1])