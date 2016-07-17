import requests
from requests.auth import HTTPBasicAuth

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import json
import base64
from getpass import getpass
import os
import subprocess
import shutil
import sys

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
    """
    Generate a GitHub token for pushing from Travis

    The scope requested is public_repo.

    If no password or OTP are provided, they will be requested from the
    command line.

    The token created here can be revoked at
    https://github.com/settings/tokens. The default note is
    "travis_docs_builder token for pushing to gh-pages from Travis".
    """
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

# XXX: Do this in a way that is streaming
def run_command_hiding_token(args, token):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.stdout, p.stderr
    out = out.replace(token, "~"*len(token))
    err = err.replace(token, "~"*len(token))
    return (out, err)

def setup_GitHub_push(repo):
    """
    Setup the remote to push to GitHub (to be run on Travis).

    This sets up the remote with the token and checks out the gh-pages branch.

    The token to push to GitHub is assumed to be in the GH_TOKEN environment
    variable.

    """
    TRAVIS_BRANCH = os.environ.get("TRAVIS_BRANCH", "")
    TRAVIS_PULL_REQUEST = os.environ.get("TRAVIS_PULL_REQUEST", "")

    token = os.environ.get("GH_TOKEN", None)
    if not token:
        raise RuntimeError("GH_TOKEN environment variable not set")

    run = lambda args: run_command_hiding_token(run, token)

    if TRAVIS_BRANCH != "master":
        print("The docs are only pushed to gh-pages from master", file=sys.stderr)
        print("This is the $TRAVIS_BRANCH branch", file=sys.stderr)
        return False

    if TRAVIS_PULL_REQUEST != "false":
        print("The website and docs are not pushed to gh-pages on pull requests", sys.stderr)
        return False

    print("Setting git attributes")
    # Should we add some user.email?
    run(['git', 'config', '--global', 'user.name', "Conda (Travis CI)"])

    print("Adding token remote")
    run(['git', 'remote', 'add', 'origin_token',
        'https://{token}@github.com/{repo}.git'.format(token=token, repo=repo)])
    print("Fetching token remote")
    run(['git', 'fetch', 'origin_token'])
    print("Checking out gh-pages")
    run(['git', 'checkout', '-b', 'gh-pages', '--track', 'origin_token/gh-pages'])
    print("Done")

    return True


# Here is the logic to get the Travis job number, to only run commit_docs in
# the right build.
#
# TRAVIS_JOB_NUMBER = os.environ.get("TRAVIS_JOB_NUMBER", '')
# ACTUAL_TRAVIS_JOB_NUMBER = TRAVIS_JOB_NUMBER.split('.')[1]

def commit_docs(*, built_docs='docs/build/html', gh_pages_docs='docs', tmp_dir='_docs'):
    """
    Commit the docs to gh-pages

    Assumes that setup_GitHub_push() has been run, which sets up the
    origin_token remote.
    """
    TRAVIS_BUILD_NUMBER = os.environ.get("TRAVIS_BUILD_NUMBER", "<unknown>")

    token = os.environ.get("GH_TOKEN", None)
    if not token:
        raise RuntimeError("GH_TOKEN environment variable not set")

    run = lambda args: run_command_hiding_token(run, token)

    print("Moving built docs into place")
    shutil.copytree(built_docs, tmp_dir)
    shutil.rmtree(gh_pages_docs)
    os.rename(tmp_dir, gh_pages_docs)
    run(['git', 'add', '-A', gh_pages_docs])

        # Only push if there were changes
    if subprocess.run(['git', 'diff-index', '--quiet', 'HEAD', '--'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:

        print("Committing")
        run(['git', 'commit', '-am', "Update docs after building Travis build " + TRAVIS_BUILD_NUMBER])
        print("Pulling")
        run(["git", "pull"])
        print("Pushing commit")
        run(['git', 'push', '-q', 'origin_token', 'gh-pages'])
    else:
        print("The docs have not changed. Not updating")
