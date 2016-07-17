import requests
from requests.auth import HTTPBasicAuth

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import json
import base64
from getpass import getpass

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

class AuthenticationFailed(Exception):
    pass

def generate_GitHub_token(username, password=None, OTP=None, note=None, headers=None):
    if not password:
        password = getpass("Enter the GitHub password for {username}: ".format(username=username))

    headers = headers or {}

    if OTP:
        headers['X-GitHub-OTP'] = OTP

    auth = HTTPBasicAuth(username, password)
    AUTH_URL = "https://api.github.com/authorizations"

    note = note or "travis_docs_builder token for pushing to gh-pages from Travis"
    data = {
        "scopes": ["public_repo"],
        "note": note
    }
    r = requests.post(AUTH_URL, auth=auth, headers=headers, data=json.dumps(data))
    if r.status_code == 401:
        two_factor = r.headers.get('X-GitHub-OTP')
        if two_factor:
            print("A two-factor authentication code is required:", two_factor.split(';')[1].strip())
            OTP = input("Authentication code: ")
            return generate_GitHub_token(username=username, password=password,
                OTP=OTP, note=note, headers=headers)

        raise AuthenticationFailed("invalid username or password")

    r.raise_for_status()
    return r.json()['token']
