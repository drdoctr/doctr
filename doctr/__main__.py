"""
doctr

A tool to automatically deploy docs to GitHub pages from Travis CI.

The doctr command is two commands in one. To use, first run

doctr local

on your local machine. This will prompt for your GitHub credentials and the
name of the repo you want to deploy docs for. This will generate a secure key,
which you should insert into your .travis.yml.

Then, on Travis, for the build where you build your docs, add

    - doctr travis

to the end of the build to deploy the docs to GitHub pages.  This will only
run on the master branch, and won't run on pull requests.

For more information, see https://gforsyth.github.io/doctr/docs/
"""

import sys
import os
import argparse

from .local import generate_GitHub_token, encrypt_variable
from .travis import setup_GitHub_push, commit_docs, push_docs, get_repo
from . import __version__

def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter, epilog="""
Run --help on the subcommands like 'doctr travis --help' to see the
options available.
        """,
        )
    parser.add_argument('-V', '--version', action='version', version='doctr ' + __version__)

    location = parser.add_subparsers(title='location', dest='location',
        description="Location doctr is being run from")
    travis_parser = location.add_parser('travis', help="Run as if on Travis.")
    travis_parser.set_defaults(func=travis)
    travis_parser.add_argument('--force', action='store_true', help="""Run the travis command even
    if we do not appear to be on Travis.""")

    local_parser = location.add_parser('local', help="Run as if local (not on Travis).")
    local_parser.set_defaults(func=local)
    local_parser.add_argument('--force', action='store_true', help="""Run the local command even
    if we appear to be on Travis.""")

    args = parser.parse_args()

    if not args.location:
        parser.print_usage()
        parser.exit(1)

    args.func(args, parser)

def on_travis():
    return os.environ.get("TRAVIS_JOB_NUMBER", '')

def travis(args, parser):
    if not args.force and not on_travis():
        parser.error("doctr does not appear to be running on Travis. Use "
            "doctr travis --force to run anyway.")

    repo = get_repo()
    if setup_GitHub_push(repo):
        commit_docs()
        push_docs()

def local(args, parser):
    if not args.force and on_travis():
        parser.error("doctr appears to be running on Travis. Use "
            "doctr local --force to run anyway.")

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
