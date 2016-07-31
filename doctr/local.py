"""
The code that should be run locally
"""

from getpass import getpass
import base64
import json
import uuid
import subprocess
import os

import requests
from requests.auth import HTTPBasicAuth

from cryptography.fernet import Fernet

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def encrypt_variable(variable, repo, public_key=None):
    """
    Encrypt an environment variable for ``repo`` for Travis

    ``variable`` should be a bytes object, of the form ``b'ENV=value'``.

    ``repo`` should be like 'gforsyth/doctr'.

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

def encrypt_file(file):
    """
    Encrypts the file ``file``.

    The encrypted file is saved to the same location with the ``.enc``
    extension.

    Returns the secret key used for the encryption.

    Decrypt the file with :func:`decrypt_file`.

    """
    key = Fernet.generate_key()
    fer = Fernet(key)

    with open(file, 'rb') as f:
        encrypted_file = fer.encrypt(f.read())

    with open(file + '.enc', 'wb') as f:
        f.write(encrypted_file)

    return key

def decrypt_file(file, key):
    """
    Decrypts the file ``file``.

    The encrypted file is assumed to end with the ``.enc`` extension. The
    decrypted file is saved to the same location without the ``.enc``
    extension.

    The permissions on the decrypted file are automatically set to 0o600.

    See also :func:`encrypt_file`.

    """
    if not file.endswith('.enc'):
        raise ValueError("%s does not end with .enc" % file)

    fer = Fernet(key)

    with open(file, 'rb') as f:
        decrypted_file = fer.decrypt(f.read())

    with open(file[:4], 'wb') as f:
        f.write(decrypted_file)

    os.chmod(file[:4], 0o600)

class AuthenticationFailed(Exception):
    pass

def generate_GitHub_token(username, password=None, OTP=None, note=None, headers=None):
    """
    Generate a GitHub token for pushing from Travis

    The scope requested is public_repo.

    If no password or OTP are provided, they will be requested from the
    command line.

    The token created here can be revoked at
    https://github.com/settings/tokens. The default note is
    "Doctr token for pushing to gh-pages from Travis".
    """
    if not password:
        password = getpass("Enter the GitHub password for {username}: ".format(username=username))

    headers = headers or {}

    if OTP:
        headers['X-GitHub-OTP'] = OTP

    auth = HTTPBasicAuth(username, password)
    AUTH_URL = "https://api.github.com/authorizations"

    note = note or "Doctr token for pushing to gh-pages from Travis"
    data = {
        "scopes": ["public_repo"],
        "note": note,
        "note_url": "https://github.com/gforsyth/doctr",
        "fingerprint": str(uuid.uuid4()),
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

def generate_ssh_key(note, name='github_deploy_key'):
    """
    Generates an SSH deploy public and private key.
    """
    p = subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '4096', '-C', note,
        '-f', name, '-N', ''])

    if p.returncode:
        raise RuntimeError("SSH key generation failed")
