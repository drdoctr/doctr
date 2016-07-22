"""
The code that should be run on Travis
"""

import os
import shlex
import shutil
import subprocess
import sys

# XXX: Do this in a way that is streaming
def run_command_hiding_token(args, token):
    command = ' '.join(map(shlex.quote, args))
    command = command.replace(token.decode('utf-8'), '~'*len(token))
    print(command)
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.stdout, p.stderr
    out = out.replace(token, b"~"*len(token))
    err = err.replace(token, b"~"*len(token))
    return (out, err, p.returncode)

def get_token():
    """
    Get the encrypted GitHub token in Travis

    Make sure the contents this variable do not link. The ``run()`` function
    will remove this from the output, so always use it.
    """
    token = os.environ.get("GH_TOKEN", None)
    if not token:
        raise RuntimeError("GH_TOKEN environment variable not set")
    token = token.encode('utf-8')
    return token

def run(args):
    """
    Run the command args

    Automatically hides the secret GitHub token from the output.
    """
    token = get_token()
    out, err, returncode = run_command_hiding_token(args, token)
    if out:
        print(out.decode('utf-8'))
    if err:
        print(err.decode('utf-8'), file=sys.stderr)
    if returncode != 0:
        sys.exit(returncode)

def setup_GitHub_push(repo):
    """
    Setup the remote to push to GitHub (to be run on Travis).

    This sets up the remote with the token and checks out the gh-pages branch.

    The token to push to GitHub is assumed to be in the ``GH_TOKEN`` environment
    variable.

    """
    TRAVIS_BRANCH = os.environ.get("TRAVIS_BRANCH", "")
    TRAVIS_PULL_REQUEST = os.environ.get("TRAVIS_PULL_REQUEST", "")

    if TRAVIS_BRANCH != "master":
        print("The docs are only pushed to gh-pages from master", file=sys.stderr)
        print("This is the {TRAVIS_BRANCH} branch".format(TRAVIS_BRANCH=TRAVIS_BRANCH), file=sys.stderr)
        return False

    if TRAVIS_PULL_REQUEST != "false":
        print("The website and docs are not pushed to gh-pages on pull requests", file=sys.stderr)
        return False

    token = get_token()

    print("Setting git attributes")
    # Should we add some user.email?
    run(['git', 'config', '--global', 'user.name', "Travis docs builder (Travis CI)"])

    print("Adding token remote")
    run(['git', 'remote', 'add', 'origin_token',
        'https://{token}@github.com/{repo}.git'.format(token=token.decode('utf-8'), repo=repo)])
    print("Fetching token remote")
    run(['git', 'fetch', 'origin_token'])
    #create gh-pages empty branch with .nojekyll if it doesn't already exist
    new_gh_pages = create_gh_pages()
    print("Checking out gh-pages")
    if new_gh_pages:
        run(['git', 'checkout', 'gh-pages'])
    else:
        run(['git', 'checkout', '-b', 'gh-pages', '--track', 'origin_token/gh-pages'])
    print("Done")

    return True

def gh_pages_exists():
    """
    Check if there is a remote gh-pages branch.

    This isn't completely robust. If there are multiple remotes and you have a
    ``gh-pages`` branch on the non-default remote, this won't see it.

    """
    remote_name = 'origin_token'
    branch_names = subprocess.check_output(['git', 'branch', '-r']).decode('utf-8').split()

    return '{}/gh-pages'.format(remote_name) in branch_names

def create_gh_pages():
    """
    If there is no remote ``gh-pages`` branch, create one.

    Return True if ``gh-pages`` was created, False if not.
    """
    if not gh_pages_exists():
        print("Creating gh-pages branch")
        run(['git', 'checkout', '--orphan', 'gh-pages'])
        #delete everything in the new ref.  this is non-destructive to existing
        #refs/branches, etc...
        run(['git', 'rm', '-rf', '.'])
        print("Adding .nojekyll file to gh-pages branch")
        run(['touch', '.nojekyll'])
        run(['git', 'add', '.nojekyll'])
        run(['git', 'commit', '-m', '"create new gh-pages branch with .nojekyll"'])
        print("Pushing gh-pages branch to remote")
        run(['git', 'push', '-u', 'origin_token', 'gh-pages'])
        #return to master branch
        run(['git', 'checkout', 'master'])

        return True
    return False

# Here is the logic to get the Travis job number, to only run commit_docs in
# the right build.
#
# TRAVIS_JOB_NUMBER = os.environ.get("TRAVIS_JOB_NUMBER", '')
# ACTUAL_TRAVIS_JOB_NUMBER = TRAVIS_JOB_NUMBER.split('.')[1]

def commit_docs(*, built_docs='docs/_build/html', gh_pages_docs='docs', tmp_dir='_docs'):
    """
    Commit the docs to ``gh-pages``

    Assumes that :func:`setup_GitHub_push`, which sets up the `origin_token` remote,
    has been run and returned True.

    """
    print("Moving built docs into place")
    shutil.copytree(built_docs, tmp_dir)
    if os.path.exists(gh_pages_docs):
        # Won't exist on the first build
        shutil.rmtree(gh_pages_docs)
    os.rename(tmp_dir, gh_pages_docs)
    run(['git', 'add', '-A', gh_pages_docs])

def push_docs():
    """
    Push the changes to the `gh-pages` branch.

    Assumes that :func:`setup_GitHub_push` has been run and returned True, and
    that :func:`commit_docs` has been run. Does not push anything if no changes
    were made.

    """
    TRAVIS_BUILD_NUMBER = os.environ.get("TRAVIS_BUILD_NUMBER", "<unknown>")

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
