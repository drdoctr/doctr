"""
The code that should be run on Travis
"""

import os
import shlex
import shutil
import subprocess
import sys
import glob
import re
import pathlib
import tempfile
import time

import requests

from cryptography.fernet import Fernet

from .common import red, blue, yellow
from .ci import CI

class Travis(CI):
    def branch(self):
        """Get the name of the branch that the PR is from.

        Note that this is not simply ``$TRAVIS_BRANCH``. the ``push`` build will
        use the correct branch (the branch that the PR is from) but the ``pr``
        build will use the _target_ of the PR (usually master). So instead, we ask
        for ``$TRAVIS_PULL_REQUEST_BRANCH`` if it's a PR build, and
        ``$TRAVIS_BRANCH`` if it's a push build.
        """
        if os.environ.get("TRAVIS_PULL_REQUEST", "") == "true":
            return os.environ.get("TRAVIS_PULL_REQUEST_BRANCH", "")
        else:
            return os.environ.get("TRAVIS_BRANCH", "")

    def tag(self):
        return os.environ.get("TRAVIS_TAG", "")

    def is_fork(self):
        # Check if the repo is a fork
        TRAVIS_REPO_SLUG = os.environ["TRAVIS_REPO_SLUG"]
        REPO_URL = 'https://api.github.com/repos/{slug}'
        r = requests.get(REPO_URL.format(slug=TRAVIS_REPO_SLUG))
        fork = r.json().get('fork', False)
        return fork

    def is_pull_request(self):
        return os.environ.get("TRAVIS_PULL_REQUEST", "") != "false"

def set_git_user_email():
    """
    Set global user and email for git user if not already present on system
    """
    username = subprocess.run(shlex.split('git config user.name'), stdout=subprocess.PIPE).stdout.strip().decode('utf-8')
    if not username or username == "Travis CI User":
        run(['git', 'config', '--global', 'user.name', "Doctr (Travis CI)"])
    else:
        print("Not setting git user name, as it's already set to %r" % username)

    email = subprocess.run(shlex.split('git config user.email'), stdout=subprocess.PIPE).stdout.strip().decode('utf-8')
    if not email or email == "travis@example.org":
        # We need a dummy email or git will fail. We use this one as per
        # https://help.github.com/articles/keeping-your-email-address-private/.
        run(['git', 'config', '--global', 'user.email', 'drdoctr@users.noreply.github.com'])
    else:
        print("Not setting git user email, as it's already set to %r" % email)

# Here is the logic to get the Travis job number, to only run commit_docs in
# the right build.
#
# TRAVIS_JOB_NUMBER = os.environ.get("TRAVIS_JOB_NUMBER", '')
# ACTUAL_TRAVIS_JOB_NUMBER = TRAVIS_JOB_NUMBER.split('.')[1]

def commit_message():
    TRAVIS_BUILD_NUMBER = os.environ.get("TRAVIS_BUILD_NUMBER", "<unknown>")
    TRAVIS_BRANCH = os.environ.get("TRAVIS_BRANCH", "<unknown>")
    TRAVIS_COMMIT = os.environ.get("TRAVIS_COMMIT", "<unknown>")
    TRAVIS_REPO_SLUG = os.environ.get("TRAVIS_REPO_SLUG", "<unknown>")
    TRAVIS_JOB_WEB_URL = os.environ.get("TRAVIS_JOB_WEB_URL", "<unknown>")
    TRAVIS_TAG = os.environ.get("TRAVIS_TAG", "")
    branch = "tag" if TRAVIS_TAG else "branch"

    DOCTR_COMMAND = ' '.join(map(shlex.quote, sys.argv))

    commit_message = """\
Update docs after building Travis build {TRAVIS_BUILD_NUMBER} of
{TRAVIS_REPO_SLUG}

The docs were built from the {branch} '{TRAVIS_BRANCH}' against the commit
{TRAVIS_COMMIT}.

The Travis build that generated this commit is at
{TRAVIS_JOB_WEB_URL}.

The doctr command that was run is

    {DOCTR_COMMAND}
""".format(
    branch=branch,
    TRAVIS_BUILD_NUMBER=TRAVIS_BUILD_NUMBER,
    TRAVIS_BRANCH=TRAVIS_BRANCH,
    TRAVIS_COMMIT=TRAVIS_COMMIT,
    TRAVIS_REPO_SLUG=TRAVIS_REPO_SLUG,
    TRAVIS_JOB_WEB_URL=TRAVIS_JOB_WEB_URL,
    DOCTR_COMMAND=DOCTR_COMMAND,
    )
    return commit_message

def determine_push_rights(*, branch_whitelist, TRAVIS_BRANCH,
    TRAVIS_PULL_REQUEST, TRAVIS_TAG, build_tags, fork):
    """Check if Travis is running on ``master`` (or a whitelisted branch) to
    determine if we can/should push the docs to the deploy repo
    """
    canpush = True

    if TRAVIS_TAG:
        if not build_tags:
            print("The docs are not pushed on tag builds. To push on future tag builds, use --build-tags")
        return build_tags

    if not any([re.compile(x).match(TRAVIS_BRANCH) for x in branch_whitelist]):
        print("The docs are only pushed to gh-pages from master. To allow pushing from "
        "a non-master branch, use the --no-require-master flag", file=sys.stderr)
        print("This is the {TRAVIS_BRANCH} branch".format(TRAVIS_BRANCH=TRAVIS_BRANCH), file=sys.stderr)
        canpush = False

    if TRAVIS_PULL_REQUEST != "false":
        print("The website and docs are not pushed to gh-pages on pull requests", file=sys.stderr)
        canpush = False

    if fork:
        print("The website and docs are not pushed to gh-pages on fork builds.", file=sys.stderr)
        canpush = False

    if last_commit_by_doctr():
        print(red("The last commit on this branch was pushed by doctr. Not pushing to "
        "avoid an infinite build-loop."), file=sys.stderr)
        canpush = False

    return canpush
