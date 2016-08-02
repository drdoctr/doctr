"""
The code that should be run on Travis
"""

import os
import shlex
import shutil
import subprocess
import sys

from cryptography.fernet import Fernet

def decrypt_file(file, key):
    """
    Decrypts the file ``file``.

    The encrypted file is assumed to end with the ``.enc`` extension. The
    decrypted file is saved to the same location without the ``.enc``
    extension.

    The permissions on the decrypted file are automatically set to 0o600.

    See also :func:`doctr.local.encrypt_file`.

    """
    if not file.endswith('.enc'):
        raise ValueError("%s does not end with .enc" % file)

    fer = Fernet(key)

    with open(file, 'rb') as f:
        decrypted_file = fer.decrypt(f.read())

    with open(file[:-4], 'wb') as f:
        f.write(decrypted_file)

    os.chmod(file[:-4], 0o600)

def setup_deploy_key():
    """
    Decrypts the deploy key and configures it with ssh

    The key is assumed to be encrypted as github_deploy_key.enc, and the
    encryption key is assumed to be set in the environment variable
    DOCTR_DEPLOY_ENCRYPTION_KEY.

    """
    key = os.environ.get("DOCTR_DEPLOY_ENCRYPTION_KEY", None)
    if not key:
        raise RuntimeError("DOCTR_DEPLOY_ENCRYPTION_KEY environment variable is not set")

    key = key.encode('utf-8')
    decrypt_file('github_deploy_key.enc', key)

    key_path = os.path.expanduser("~/.ssh/github_deploy_key")
    os.makedirs(os.path.expanduser("~/.ssh"), exist_ok=True)
    os.rename("github_deploy_key", key_path)

    with open(os.path.expanduser("~/.ssh/config"), 'a') as f:
        f.write("Host github.com"
                '  IdentityFile "%s"'
                "  LogLevel ERROR\n" % key_path)
    run(['ssh-add', '~/.ssh/github_deploy_key'])

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
    if "DOCTR_DEPLOY_ENCRYPTION_KEY" in os.environ:
        token = b''
    else:
        token = get_token()
    out, err, returncode = run_command_hiding_token(args, token)
    if out:
        print(out.decode('utf-8'))
    if err:
        print(err.decode('utf-8'), file=sys.stderr)
    if returncode != 0:
        sys.exit(returncode)

def get_repo():
    """
    Get the GitHub repo name for the current directory.

    Assumes that the repo is in the ``origin`` remote.
    """
    remote_url = subprocess.check_output(['git', 'config', '--get',
        'remote.origin.url']).decode('utf-8')

    # Travis uses the https clone url
    _, org, git_repo = remote_url.rsplit('.git', 1)[0].rsplit('/', 2)
    return (org + '/' + git_repo)

def setup_GitHub_push(repo, auth_type='deploy_key'):
    """
    Setup the remote to push to GitHub (to be run on Travis).

    ``auth_type`` should be either ``'deploy_key'`` or ``'token'``.

    For ``auth_type='token'``, this sets up the remote with the token and
    checks out the gh-pages branch. The token to push to GitHub is assumed to be in the ``GH_TOKEN`` environment
    variable.

    For ``auth_type='deploy_key'``, this sets up the remote with ssh access.
    """
    if auth_type not in ['deploy_key', 'token']:
        raise ValueError("auth_type must be 'deploy_key' or 'token'")

    TRAVIS_BRANCH = os.environ.get("TRAVIS_BRANCH", "")
    TRAVIS_PULL_REQUEST = os.environ.get("TRAVIS_PULL_REQUEST", "")

#    if TRAVIS_BRANCH != "master":
#        print("The docs are only pushed to gh-pages from master", file=sys.stderr)
#        print("This is the {TRAVIS_BRANCH} branch".format(TRAVIS_BRANCH=TRAVIS_BRANCH), file=sys.stderr)
#        return False
#
#    if TRAVIS_PULL_REQUEST != "false":
#        print("The website and docs are not pushed to gh-pages on pull requests", file=sys.stderr)
#        return False

    print("Setting git attributes")
    # Should we add some user.email?
    run(['git', 'config', '--global', 'user.name', "Travis docs builder (Travis CI)"])

    print("Adding doctr remote")
    if auth_type == 'token':
        token = get_token()
        run(['git', 'remote', 'add', 'doctr_remote',
            'https://{token}@github.com/{repo}.git'.format(token=token.decode('utf-8'),
                repo=repo)])
    else:
        setup_deploy_key()
        run(['git', 'remote', 'add', 'doctr_remote',
            'git@github.com:{repo}.git'.format(repo=repo)])

    print("Fetching doctr remote")
    run(['git', 'fetch', 'doctr_remote'])

    #create gh-pages empty branch with .nojekyll if it doesn't already exist
    new_gh_pages = create_gh_pages()
    print("Checking out gh-pages")
    if new_gh_pages:
        run(['git', 'checkout', 'gh-pages'])
    else:
        run(['git', 'checkout', '-b', 'gh-pages', '--track', 'doctr_remote/gh-pages'])
    print("Done")

    return True

def gh_pages_exists():
    """
    Check if there is a remote gh-pages branch.

    This isn't completely robust. If there are multiple remotes and you have a
    ``gh-pages`` branch on the non-default remote, this won't see it.

    """
    remote_name = 'doctr_remote'
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
        run(['git', 'push', '-u', 'doctr_remote', 'gh-pages'])
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

    Assumes that :func:`setup_GitHub_push`, which sets up the ``doctr_remote``
    remote, has been run and returned True.

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
        run(['git', 'push', '-q', 'doctr_remote', 'gh-pages'])
    else:
        print("The docs have not changed. Not updating")
