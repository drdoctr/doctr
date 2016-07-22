"""
doctr

A tool to automatically deploy docs to GitHub pages from Travis CI.
"""

import sys
import os
import argparse

from .local import generate_GitHub_token, encrypt_variable
from .travis import setup_GitHub_push, commit_docs, push_docs, get_repo
from . import __version__

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-V', '--version', action='version', version='doctr ' + __version__)
    location = parser.add_mutually_exclusive_group()
    location.add_argument('--travis', action='store_true', default=None, help="""Run
    the Travis script. The default is to detect automatically.""")
    location.add_argument('--local', action='store_true', default=None, help="""Run
    the local script. The default is to detect automatically (only run if not
    on Travis).""")

    args = parser.parse_args()

    if args.local == args.travis == None:
        on_travis = os.environ.get("TRAVIS_JOB_NUMBER", '')
    else:
        on_travis = args.travis

    if on_travis:
        repo = get_repo()
        if setup_GitHub_push(repo):
            commit_docs()
            push_docs()
    else:
        username = input("What is your GitHub username? ")
        token = generate_GitHub_token(username)

        repo = input("What repo to you want to build the docs for? ")
        encrypted_variable = encrypt_variable("GH_TOKEN={token}".format(token=token).encode('utf-8'), repo=repo)
        travis_content = """
env:
  global:
    secure: "{encrypted_variable}"

""".format(encrypted_variable=encrypted_variable.decode('utf-8'))

        print("Put\n", travis_content, "in your .travis.yml.\n",
            "Also make sure to create an empty gh-pages branch on GitHub, and "
            "enable it at https://github.com/{repo}/settings".format(repo=repo), sep='')

if __name__ == '__main__':
    sys.exit(main())
