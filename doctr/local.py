"""
The code that should be run locally
"""

import json
import uuid
import base64
import subprocess
import re
from getpass import getpass
import urllib
import datetime

import requests
from requests.auth import HTTPBasicAuth

from cryptography.fernet import Fernet

from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


from .common import red

def encrypt_variable(variable, build_repo, *, public_key=None, is_private=False, **login_kwargs):
    """
    Encrypt an environment variable for ``build_repo`` for Travis

    ``variable`` should be a bytes object, of the form ``b'ENV=value'``.

    ``build_repo`` is the repo that ``doctr deploy`` will be run from. It
    should be like 'drdoctr/doctr'.

    ``public_key`` should be a pem format public key, obtained from Travis if
    not provided.
    """
    if not isinstance(variable, bytes):
        raise TypeError("variable should be bytes")

    if not b"=" in variable:
        raise ValueError("variable should be of the form 'VARIABLE=value'")

    if not public_key:
        headers = {'Accept': 'application/vnd.travis-ci.2+json',
                   'Content-Type': 'application/json',
                   'User-Agent': 'MyClient/1.0.0'}
        if is_private:
            tok_dict = generate_GitHub_token(scopes=["read:org", "user:email", "repo"],
                                             note="temporary token to auth against travis",
                                             **login_kwargs)
            data = {'github_token': tok_dict['token']}
            token_id = tok_dict['id']
            res = requests.post('https://api.travis-ci.com/auth/github', data=json.dumps(data), headers=headers)
            res.raise_for_status()
            headers['Authorization'] = 'token {}'.format(res.json()['access_token'])
            tld = 'com'
        else:
            tld = 'org'
        res = requests.get('https://api.travis-ci.{tld}/repos/{build_repo}/key'.format(build_repo=build_repo, tld=tld),
            headers=headers)
        if res.status_code == requests.codes.not_found:
            raise RuntimeError('Could not find requested repo on Travis.  Is Travis enabled?')
        res.raise_for_status()
        public_key = res.json()['key']
        # Remove temporary GH token
        if is_private:
            delete_GitHub_token(token_id, **login_kwargs)

    public_key = public_key.replace("RSA PUBLIC KEY", "PUBLIC KEY").encode('utf-8')
    key = serialization.load_pem_public_key(public_key, backend=default_backend())

    pad = padding.PKCS1v15()

    return base64.b64encode(key.encrypt(variable, pad))

def encrypt_to_file(contents, filename):
    """
    Encrypts ``contents`` and writes it to ``filename``.

    ``contents`` should be a bytes string. ``filename`` should end with
    ``.enc``.

    Returns the secret key used for the encryption.

    Decrypt the file with :func:`doctr.travis.decrypt_file`.

    """
    if not filename.endswith('.enc'):
        raise ValueError("%s does not end with .enc" % filename)

    key = Fernet.generate_key()
    fer = Fernet(key)

    encrypted_file = fer.encrypt(contents)

    with open(filename, 'wb') as f:
        f.write(encrypted_file)

    return key

class AuthenticationFailed(Exception):
    pass

def GitHub_login(*, username=None, password=None, OTP=None, headers=None):
    """
    Login to GitHub.

    If no username, password, or OTP (2-factor authentication code) are
    provided, they will be requested from the command line.

    Returns a dict of kwargs that can be passed to functions that require
    authenticated connections to GitHub.
    """
    if not username:
        username = input("What is your GitHub username? ")

    if not password:
        password = getpass("Enter the GitHub password for {username}: ".format(username=username))

    headers = headers or {}

    if OTP:
        headers['X-GitHub-OTP'] = OTP

    auth = HTTPBasicAuth(username, password)

    r = requests.get('https://api.github.com/', auth=auth, headers=headers)
    if r.status_code == 401:
        two_factor = r.headers.get('X-GitHub-OTP')
        if two_factor:
            if OTP:
                print(red("Invalid authentication code"))
            # For SMS, we have to make a fake request (that will fail without
            # the OTP) to get GitHub to send it. See https://github.com/drdoctr/doctr/pull/203
            auth_header = base64.urlsafe_b64encode(bytes(username + ':' + password, 'utf8')).decode()
            login_kwargs = {'auth': None, 'headers': {'Authorization': 'Basic {}'.format(auth_header)}}
            try:
                generate_GitHub_token(**login_kwargs)
            except (requests.exceptions.HTTPError, GitHubError):
                pass
            print("A two-factor authentication code is required:", two_factor.split(';')[1].strip())
            OTP = input("Authentication code: ")
            return GitHub_login(username=username, password=password, OTP=OTP, headers=headers)

        raise AuthenticationFailed("invalid username or password")

    GitHub_raise_for_status(r)
    return {'auth': auth, 'headers': headers}


class GitHubError(RuntimeError):
    pass

def GitHub_raise_for_status(r):
    """
    Call instead of r.raise_for_status() for GitHub requests

    Checks for common GitHub response issues and prints messages for them.
    """
    # This will happen if the doctr session has been running too long and the
    # OTP code gathered from GitHub_login has expired.

    # TODO: Refactor the code to re-request the OTP without exiting.
    if r.status_code == 401 and r.headers.get('X-GitHub-OTP'):
        raise GitHubError("The two-factor authentication code has expired. Please run doctr configure again.")
    if r.status_code == 403 and r.headers.get('X-RateLimit-Remaining') == '0':
        reset = int(r.headers['X-RateLimit-Reset'])
        limit = int(r.headers['X-RateLimit-Limit'])
        reset_datetime = datetime.datetime.fromtimestamp(reset, datetime.timezone.utc)
        relative_reset_datetime = reset_datetime - datetime.datetime.now(datetime.timezone.utc)
        # Based on datetime.timedelta.__str__
        mm, ss = divmod(relative_reset_datetime.seconds, 60)
        hh, mm = divmod(mm, 60)
        def plural(n):
            return n, abs(n) != 1 and "s" or ""

        s = "%d minute%s" % plural(mm)
        if hh:
            s = "%d hour%s, " % plural(hh) + s
        if relative_reset_datetime.days:
            s = ("%d day%s, " % plural(relative_reset_datetime.days)) + s
        authenticated = limit >= 100
        message = """\
Your GitHub API rate limit has been hit. GitHub allows {limit} {un}authenticated
requests per hour. See {documentation_url}
for more information.
""".format(limit=limit, un="" if authenticated else "un", documentation_url=r.json()["documentation_url"])
        if authenticated:
            message += """
Note that GitHub's API limits are shared across all oauth applications. A
common cause of hitting the rate limit is the Travis "sync account" button.
"""
        else:
            message += """
You can get a higher API limit by authenticating. Try running doctr configure
again without the --no-upload-key flag.
"""
        message += """
Your rate limits will reset in {s}.\
""".format(s=s)
        raise GitHubError(message)
    r.raise_for_status()


def GitHub_post(data, url, *, auth, headers):
    """
    POST the data ``data`` to GitHub.

    Returns the json response from the server, or raises on error status.

    """
    r = requests.post(url, auth=auth, headers=headers, data=json.dumps(data))
    GitHub_raise_for_status(r)
    return r.json()


def generate_GitHub_token(*, note="Doctr token for pushing to gh-pages from Travis", scopes=None, **login_kwargs):
    """
    Generate a GitHub token for pushing from Travis

    The scope requested is public_repo.

    If no password or OTP are provided, they will be requested from the
    command line.

    The token created here can be revoked at
    https://github.com/settings/tokens.
    """
    if scopes is None:
        scopes = ['public_repo']
    AUTH_URL = "https://api.github.com/authorizations"
    data = {
        "scopes": scopes,
        "note": note,
        "note_url": "https://github.com/drdoctr/doctr",
        "fingerprint": str(uuid.uuid4()),
    }
    return GitHub_post(data, AUTH_URL, **login_kwargs)


def delete_GitHub_token(token_id, *, auth, headers):
    """Delete a temporary GitHub token"""
    r = requests.delete('https://api.github.com/authorizations/{id}'.format(id=token_id), auth=auth, headers=headers)
    GitHub_raise_for_status(r)


def upload_GitHub_deploy_key(deploy_repo, ssh_key, *, read_only=False,
    title="Doctr deploy key for pushing to gh-pages from Travis", **login_kwargs):
    """
    Uploads a GitHub deploy key to ``deploy_repo``.

    If ``read_only=True``, the deploy_key will not be able to write to the
    repo.
    """
    DEPLOY_KEY_URL = "https://api.github.com/repos/{deploy_repo}/keys".format(deploy_repo=deploy_repo)

    data = {
        "title": title,
        "key": ssh_key,
        "read_only": read_only,
    }
    return GitHub_post(data, DEPLOY_KEY_URL, **login_kwargs)

def generate_ssh_key():
    """
    Generates an SSH deploy public and private key.

    Returns (private key, public key), a tuple of byte strings.
    """

    key = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=4096
        )
    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    public_key = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )

    return private_key, public_key

def check_repo_exists(deploy_repo, service='github', *, auth=None, headers=None):
    """
    Checks that the repository exists on GitHub.

    This should be done before attempting generate a key to deploy to that
    repo.

    Raises ``RuntimeError`` if the repo is not valid.

    Returns whether or not the repo is private
    """
    headers = headers or {}
    if deploy_repo.count("/") != 1:
        raise RuntimeError('"{deploy_repo}" should be in the form username/repo'.format(deploy_repo=deploy_repo))

    user, repo = deploy_repo.split('/')
    if service == 'github':
        REPO_URL = 'https://api.github.com/repos/{user}/{repo}'
    elif service == 'travis':
        REPO_URL = 'https://api.travis-ci.org/repo/{user}%2F{repo}'
        headers['Travis-API-Version'] = '3'
    else:
        raise RuntimeError('Invalid service specified for repo check (neither "travis" nor "github")')

    wiki = False
    if repo.endswith('.wiki') and service == 'github':
        wiki = True
        repo = repo[:-5]

    r = requests.get(REPO_URL.format(user=urllib.parse.quote(user),
        repo=urllib.parse.quote(repo)), auth=auth, headers=headers)

    if r.status_code == requests.codes.not_found:
        raise RuntimeError('"{user}/{repo}" not found on {service}'.format(user=user,
                                                                           repo=repo,
                                                                           service=service))

    if service == 'github':
        GitHub_raise_for_status(r)
    else:
        r.raise_for_status()

    private = r.json().get('private', False)

    if wiki and not private:
        # private wiki needs authentication, so skip check for existence
        p = subprocess.run(['git', 'ls-remote', '-h', 'https://github.com/{user}/{repo}.wiki'.format(
            user=user, repo=repo)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if p.stderr or p.returncode:
            raise RuntimeError('Wiki not found. Please create a wiki')
        return False

    return private

GIT_URL = re.compile(r'(?:git@|https://|git://)github\.com[:/](.*?)(?:\.git)?')

def guess_github_repo():
    """
    Guesses the github repo for the current directory

    Returns False if no guess can be made.
    """
    p = subprocess.run(['git', 'ls-remote', '--get-url', 'origin'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.stderr or p.returncode:
        return False

    url = p.stdout.decode('utf-8').strip()
    m = GIT_URL.fullmatch(url)
    if not m:
        return False
    return m.group(1)
