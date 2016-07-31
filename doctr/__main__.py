"""
doctr

A tool to automatically deploy docs to GitHub pages from Travis CI.

The doctr command is two commands in one. To use, first run

doctr

on your local machine. This will prompt for your GitHub credentials and the
name of the repo you want to deploy docs for. This will generate a secure key,
which you should insert into your .travis.yml.

Then, on Travis, for the build where you build your docs, add

    - doctr

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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-V', '--version', action='version', version='doctr ' + __version__)
    location = parser.add_mutually_exclusive_group()
    location.add_argument('--travis', action='store_true', default=None,
    help="Run as if on Travis. The default is to detect automatically.")
    location.add_argument('--local', action='store_true', default=None,
    help="Run as if local (not on Travis). The default is to detect automatically.")

    parser.add_argument('--token', action="store_true", default=False,
        help="""Generate a personal access token to push to GitHub. The default is to use a
        deploy key. WARNING: This will grant read/write access to all the
        public repositories for the user. This option is not recommended
        unless you are using a separate GitHub user for deploying.""")

    parser.add_argument("--no-upload-key", action="store_false", default=True,
        dest="upload_key", help="""Don't automatically upload the deploy key
        to GitHub.""")

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
        repo = input("What repo to you want to build the docs for? ")

        if args.token:
            token = generate_GitHub_token()
            encrypted_variable = encrypt_variable("GH_TOKEN={token}".format(token=token).encode('utf-8'), repo=repo)
        else:
            generate_ssh_key("doctr deploy key for {repo}".format(repo=repo))
            key = encrypt_file('github_deploy_key', delete=True)
            encrypted_variable = encrypt_variable(b"DOCTR_DEPLOY_ENCRYPTION_KEY=" + key, repo=repo)

            deploy_keys_url = 'https://github.com/{repo}/settings/keys'.format(repo=repo)

            if args.upload_key:
                with open("github_deploy_key.pub") as f:
                    key = f.read()

                upload_GitHub_deploy_key(repo, key)

                print(dedent("""\
                The deploy key has been added for {repo}.

                Commit the file github_deploy_key.enc to the repository.

                You can go to {deploy_keys_url} to revoke the deploy key.
                """.format(repo=repo, deploy_keys_url=deploy_keys_url)))

            else:
                print(dedent("""\
                Go to {deploy_keys_url} and add the following as a new key:

                {key}

                Be sure to allow write access for the key
                """.format(key=key, deploy_keys_url=deploy_keys_url)))

        travis_content = dedent("""
        env:
          global:
            secure: "{encrypted_variable}"

        """.format(encrypted_variable=encrypted_variable.decode('utf-8')))

        print("Put\n", travis_content, "in your .travis.yml.\n",
            "Also make sure to create an empty gh-pages branch on GitHub, and "
            "enable it at https://github.com/{repo}/settings".format(repo=repo), sep='')

if __name__ == '__main__':
    sys.exit(main())
