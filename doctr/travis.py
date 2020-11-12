"""
The code that should be run on Travis
"""

import os
import shlex
import subprocess
import sys
import re

import requests

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

    def repo_slug(self):
        return os.environ["TRAVIS_REPO_SLUG"]

    def is_pull_request(self):
        return os.environ.get("TRAVIS_PULL_REQUEST", "") != "false"

    def commit_message(self):
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
