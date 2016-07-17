import requests

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import base64

def encrypt_variable(variable, repo, public_key=None):
    """
    Encrypt an environment variable for repo for Travis

    ``variable`` should be a bytes object.
    ``repo`` should be like 'gforsyth/travis_docs_builder'
    ``public_key`` should be a pem format public key, obtained from Travis if
        not provided.
    """
    if not isinstance(variable, bytes):
        raise TypeError("variable should be bytes")

    if not b"=" in variable:
        raise ValueError("variable should be of the form 'VARIABLE=value'")

    if not public_key:
        # TODO: Error handling
        r = requests.get('https://api.travis-ci.org/repos/{repo}/key'.format(repo=repo),
            headers={'Accept': 'application/vnd.travis-ci.2+json'})
        public_key = r.json()['key']

    public_key = public_key.replace("RSA PUBLIC KEY", "PUBLIC KEY").encode('utf-8')
    key = serialization.load_pem_public_key(public_key, backend=default_backend())

    pad = padding.PKCS1v15()

    return base64.b64encode(key.encrypt(variable, pad))
