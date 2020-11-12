import os
import shlex
import sys

from .ci import CI

class GitHubActions(CI):
    def branch(self):
        """Get the name of the branch that the PR is from.

        Note that this is not simply ``$TRAVIS_BRANCH``. the ``push`` build will
        use the correct branch (the branch that the PR is from) but the ``pr``
        build will use the _target_ of the PR (usually master). So instead, we ask
        for ``$TRAVIS_PULL_REQUEST_BRANCH`` if it's a PR build, and
        ``$TRAVIS_BRANCH`` if it's a push build.
        """
        head_ref = os.environ.get("GITHUB_HEAD_REF", "")
        if head_ref:
            return head_ref
        GITHUB_REF = os.environ.get("GITHUB_REF", "")
        if "refs/heads/" in GITHUB_REF:
            return GITHUB_REF[len('refs/heads/'):]
        return ""

    def tag(self):
        GITHUB_REF = os.environ.get("GITHUB_REF", "")
        if "refs/tags/" in GITHUB_REF:
            return GITHUB_REF[len('refs/tags/'):]
        return ""

    def repo_slug(self):
        return os.environ["GITHUB_REPOSITORY"]

    def is_pull_request(self):
        return os.environ.get("GITHUB_EVENT_NAME", "") != "pull_request"


    def commit_message(self):
        GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID", "<unknown>")
        GITHUB_RUN_NUMBER = os.environ.get("GITHUB_RUN_NUMBER", "<unknown>")
        branch = self.branch() or "<unknown>"
        tag = self.tag()
        typ = 'branch' if branch else 'tag'
        branch_or_tag = branch or tag
        GITHUB_SHA = os.environ.get("GITHUB_SHA", "<unknown>")
        repo_slug = self.repo_slug
        web_url = (os.environ.get("GITHUB_SERVER_URL", "<unknown>") + '/' +
                   repo_slug + '/runs/' + GITHUB_RUN_NUMBER)

        DOCTR_COMMAND = ' '.join(map(shlex.quote, sys.argv))

        commit_message = """\
    Update docs after building GitHub Actions build {GITHUB_RUN_ID} ({GITHUB_RUN_NUMBER}) of {repo_slug}

    The docs were built from the {typ} '{branch_or_tag}' against the commit
    {GITHUB_SHA}.

    The GitHub Actions build that generated this commit is at
    {web_url}.

    The doctr command that was run is

        {DOCTR_COMMAND}
    """.format(
        GITHUB_RUN_ID=GITHUB_RUN_ID,
        GITHUB_RUN_NUMBER=GITHUB_RUN_NUMBER,
        repo_slug=repo_slug,
        typ=typ,
        branch_or_tag=branch_or_tag,
        GITHUB_SHA=GITHUB_SHA,
        web_url=web_url,
        DOCTR_COMMAND=DOCTR_COMMAND,
        )
        return commit_message
