import requests

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import base64

r = requests.get('https://api.travis-ci.org/repos/gforsyth/travis_docs_builder/key', headers={'Accept': 'application/vnd.travis-ci.2+json'})

public_key = r.json()['key'].replace("RSA PUBLIC KEY", "PUBLIC KEY").encode('utf-8')
key = serialization.load_pem_public_key(public_key, backend=default_backend())

pad = padding.PKCS1v15()

print(base64.b64encode(key.encrypt(b'a=b', pad)))
