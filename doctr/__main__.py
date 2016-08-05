"""
doctr

A tool to automatically deploy docs to GitHub pages from Travis CI.

The doctr command is two commands in one. To use, first run

doctr configure

on your local machine. This will prompt for your GitHub credentials and the
name of the repo you want to deploy docs for. This will generate a secure key,
which you should insert into your .travis.yml.

Then, on Travis, for the build where you build your docs, add

    - doctr deploy

to the end of the build to deploy the docs to GitHub pages.  This will only
run on the master branch, and won't run on pull requests.

For more information, see https://gforsyth.github.io/doctr/docs/
"""

import sys
import os
import argparse

from textwrap import dedent

from .local import (generate_GitHub_token, encrypt_variable, encrypt_file,
    upload_GitHub_deploy_key, generate_ssh_key)
from .travis import setup_GitHub_push, commit_docs, push_docs, get_repo
from . import __version__

def main():
    # This uses RawTextHelpFormatter so that the description (the docstring of
    # this module) is formatted correctly. Unfortunately, that means that
    # parser help is not text wrapped (but all other help is).
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter, epilog="""
Run --help on the subcommands like 'doctr deploy --help' to see the
options available.
        """,
        )
    parser.add_argument('-V', '--version', action='version', version='doctr ' + __version__)

    location = parser.add_subparsers(title='location', dest='location',
        description="Location doctr is being run from")
    deploy_parser = location.add_parser('deploy', help=""""Deploy the docs to GitHub from Travis.""")
    deploy_parser.set_defaults(func=deploy)
    deploy_parser.add_argument('--force', action='store_true', help="""Run the deploy command even
    if we do not appear to be on Travis.""")
    deploy_parser.add_argument('--token', action='store_true', default=False,
        help="""Push to GitHub using a personal access token. Use this if you
        used 'doctr configure --token'.""")
    deploy_parser.add_argument('--key-path', default='github_deploy_key.enc',
        help="""Path of the encrypted GitHub deploy key. The default is '%(default)s'.""")

    configure_parser = location.add_parser('configure', help="Configure doctr. This command should be run locally (not on Travis).")
    configure_parser.set_defaults(func=configure)
    configure_parser.add_argument('--force', action='store_true', help="""Run the configure command even
    if we appear to be on Travis.""")
    configure_parser.add_argument('--token', action="store_true", default=False,
        help="""Generate a personal access token to push to GitHub. The default is to use a
        deploy key. WARNING: This will grant read/write access to all the
        public repositories for the user. This option is not recommended
        unless you are using a separate GitHub user for deploying.""")
    configure_parser.add_argument("--no-upload-key", action="store_false", default=True,
        dest="upload_key", help="""Don't automatically upload the deploy key
        to GitHub.""")
    configure_parser.add_argument('--key-path', default='github_deploy_key',
        help="""Path to save the encrypted GitHub deploy key. The default is '%(default)s'.
    The .enc extension is added to the file automatically.""")


    args = parser.parse_args()

    if not args.location:
        parser.print_usage()
        parser.exit(1)

    args.func(args, parser)

def on_travis():
    return os.environ.get("TRAVIS_JOB_NUMBER", '')

def deploy(args, parser):
    if not args.force and not on_travis():
        parser.error("doctr does not appear to be running on Travis. Use "
            "doctr deploy --force to run anyway.")

    repo = get_repo()
    if setup_GitHub_push(repo, auth_type='token' if args.token else
        'deploy_key', full_key_path=args.key_path):
        commit_docs()
        push_docs()

class IncrementingInt:
    def __init__(self, i=0):
        self.i = i

    def __repr__(self):
        ret = repr(self.i)
        self.i += 1
        return ret

    __str__ = __repr__

def configure(args, parser):
    if not args.force and on_travis():
        parser.error("doctr appears to be running on Travis. Use "
            "doctr configure --force to run anyway.")

    repo = input("What repo do you want to build the docs for? ")

    N = IncrementingInt(1)

    if args.token:
        token = generate_GitHub_token()
        encrypted_variable = encrypt_variable("GH_TOKEN={token}".format(token=token).encode('utf-8'),
        repo=repo)
        print(dedent("""
        A personal access token for doctr has been created.

        You can go to https://github.com/settings/tokens to revoke it."""))

        print("\n============ You should now do the following ============\n")
    else:
        ssh_key = generate_ssh_key("doctr deploy key for {repo}".format(repo=repo), keypath=args.key_path)
        key = encrypt_file(args.key_path, delete=True)
        encrypted_variable = encrypt_variable(b"DOCTR_DEPLOY_ENCRYPTION_KEY=" + key, repo=repo)

        deploy_keys_url = 'https://github.com/{repo}/settings/keys'.format(repo=repo)

        if args.upload_key:

            upload_GitHub_deploy_key(repo, ssh_key)

            print(dedent("""
            The deploy key has been added for {repo}.

            You can go to {deploy_keys_url} to revoke the deploy key.\
            """.format(repo=repo, deploy_keys_url=deploy_keys_url, keypath=args.key_path)))
            print("\n============ You should now do the following ============\n")
        else:
            print("\n============ You should now do the following ============\n")
            print(dedent("""\
            {N}. Go to {deploy_keys_url} and add the following as a new key:

            {ssh_key}
            Be sure to allow write access for the key.
            """.format(ssh_key=ssh_key, deploy_keys_url=deploy_keys_url, N=N)))

        # TODO: Should we just delete the public key?

        print(dedent("""\
        {N}. Commit the file {keypath}.enc. The file {keypath}.pub contains the
        public deploy key for GitHub. It does not need to be
        committed.
        """.format(keypath=args.key_path, N=N)))

        if args.key_path != 'github_deploy_key':
            options = '--key-path {keypath}.enc'.format(keypath=args.key_path)
        else:
            options = ''

        print(dedent("""\
        {N}. Add

            - pip install doctr
            - doctr deploy {options}

        to the docs build of your .travis.yml.
        """.format(options=options, N=N)))

    print(dedent("""\
    {N}. Put

        env:
          global:
            - secure: "{encrypted_variable}"

    in your .travis.yml.
    """.format(encrypted_variable=encrypted_variable.decode('utf-8'), N=N)))

if __name__ == '__main__':
    sys.exit(main())
