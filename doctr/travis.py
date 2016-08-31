"""
The code that should be run on Travis
"""

import os
import shlex
import shutil
import subprocess
import sys
import glob

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

def setup_deploy_key(keypath='github_deploy_key', key_ext='.enc'):
    """
    Decrypts the deploy key and configures it with ssh

    The key is assumed to be encrypted as keypath + key_ext, and the
    encryption key is assumed to be set in the environment variable
    DOCTR_DEPLOY_ENCRYPTION_KEY.

    """
    key = os.environ.get("DOCTR_DEPLOY_ENCRYPTION_KEY", None)
    if not key:
        raise RuntimeError("DOCTR_DEPLOY_ENCRYPTION_KEY environment variable is not set")

    key_filename = os.path.basename(keypath)
    key = key.encode('utf-8')
    decrypt_file(keypath + key_ext, key)

    key_path = os.path.expanduser("~/.ssh/" + key_filename)
    os.makedirs(os.path.expanduser("~/.ssh"), exist_ok=True)
    os.rename(keypath, key_path)

    with open(os.path.expanduser("~/.ssh/config"), 'a') as f:
        f.write("Host github.com"
                '  IdentityFile "%s"'
                "  LogLevel ERROR\n" % key_path)

    # start ssh-agent and add key to it
    # info from SSH agent has to be put into the environment
    agent_info = subprocess.check_output(['ssh-agent', '-s'])
    agent_info = agent_info.decode('utf-8')
    agent_info = agent_info.split()

    AUTH_SOCK = agent_info[0].split('=')[1][:-1]
    AGENT_PID = agent_info[3].split('=')[1][:-1]

    os.putenv('SSH_AUTH_SOCK', AUTH_SOCK)
    os.putenv('SSH_AGENT_PID', AGENT_PID)

    run(['ssh-add', os.path.expanduser('~/.ssh/' + key_filename)])

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
    Get the encrypted GitHub token in Travis.

    Make sure the contents this variable do not leak. The ``run()`` function
    will remove this from the output, so always use it.
    """
    token = os.environ.get("GH_TOKEN", None)
    if not token:
        raise RuntimeError("GH_TOKEN environment variable not set")
    token = token.encode('utf-8')
    return token

def run(args):
    """
    Run the command ``args``.

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

def get_current_repo():
    """
    Get the GitHub repo name for the current directory.

    Assumes that the repo is in the ``origin`` remote.
    """
    remote_url = subprocess.check_output(['git', 'config', '--get',
        'remote.origin.url']).decode('utf-8')

    # Travis uses the https clone url
    _, org, git_repo = remote_url.rsplit('.git', 1)[0].rsplit('/', 2)
    return (org + '/' + git_repo)

def setup_GitHub_push(deploy_repo, auth_type='deploy_key', full_key_path='github_deploy_key.enc', require_master=True):
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

    if TRAVIS_BRANCH != "master" and require_master:
        print("The docs are only pushed to gh-pages from master. To allow pushing from "
        "a non-master branch, use the --no-require-master flag", file=sys.stderr)
        print("This is the {TRAVIS_BRANCH} branch".format(TRAVIS_BRANCH=TRAVIS_BRANCH), file=sys.stderr)
        return False

    if TRAVIS_PULL_REQUEST != "false":
        print("The website and docs are not pushed to gh-pages on pull requests", file=sys.stderr)
        return False

    print("Setting git attributes")
    # Should we add some user.email?
    run(['git', 'config', '--global', 'user.name', "Doctr (Travis CI)"])

    remotes = subprocess.check_output(['git', 'remote']).decode('utf-8').split('\n')
    if 'doctr_remote' in remotes:
        print("doctr_remote already exists, removing")
        run(['git', 'remote', 'remove', 'doctr_remote'])
    print("Adding doctr remote")
    if auth_type == 'token':
        token = get_token()
        run(['git', 'remote', 'add', 'doctr_remote',
            'https://{token}@github.com/{deploy_repo}.git'.format(token=token.decode('utf-8'),
                deploy_repo=deploy_repo)])
    else:
        keypath, key_ext = full_key_path.rsplit('.', 1)
        key_ext = '.' + key_ext
        setup_deploy_key(keypath=keypath, key_ext=key_ext)
        run(['git', 'remote', 'add', 'doctr_remote',
            'git@github.com:{deploy_repo}.git'.format(deploy_repo=deploy_repo)])

    print("Fetching doctr remote")
    run(['git', 'fetch', 'doctr_remote'])

    #create gh-pages empty branch with .nojekyll if it doesn't already exist
    new_gh_pages = create_gh_pages()
    print("Checking out gh-pages")
    local_gh_pages_exists = 'gh-pages' in subprocess.check_output(['git', 'branch']).decode('utf-8').split()
    if new_gh_pages or local_gh_pages_exists:
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
        # delete everything in the new ref.  this is non-destructive to existing
        # refs/branches, etc...
        run(['git', 'rm', '-rf', '.'])
        print("Adding .nojekyll file to gh-pages branch")
        run(['touch', '.nojekyll'])
        run(['git', 'add', '.nojekyll'])
        run(['git', 'commit', '-m', 'Create new gh-pages branch with .nojekyll'])
        print("Pushing gh-pages branch to remote")
        run(['git', 'push', '-u', 'doctr_remote', 'gh-pages'])
        # return to master branch
        run(['git', 'checkout', '-'])

        return True
    return False

def find_sphinx_build_dir():
    """
    Find build subfolder within sphinx docs directory.

    This is called by :func:`commit_docs` if keyword arg ``built_docs`` is not
    specified on the command line.
    """
    build = glob.glob('**/*build/html', recursive=True)
    if not build:
        raise RuntimeError("Could not find Sphinx build directory automatically")
    build_folder = build[0]

    return build_folder

# Here is the logic to get the Travis job number, to only run commit_docs in
# the right build.
#
# TRAVIS_JOB_NUMBER = os.environ.get("TRAVIS_JOB_NUMBER", '')
# ACTUAL_TRAVIS_JOB_NUMBER = TRAVIS_JOB_NUMBER.split('.')[1]

def sync_from_log(src, dst, log_file):
    """
    Sync the files in ``src`` to ``dst``.

    The files that are synced are logged to ``log_file``. If ``log_file``
    exists, the files in ``log_file`` are removed first.

    Returns ``(added, removed)``, where added is a list of all files synced from
    ``src`` (even if it already existed in ``dst``), and ``removed`` is every
    file from ``log_file`` that was removed from ``dst`` because it wasn't in
    ``src``. ``added`` also includes the log file.
    """
    from os.path import join, exists, isdir
    if not src.endswith(os.sep):
        src += os.sep

    added, removed = [], []

    if not exists(log_file):
        # Assume this is the first run
        print("%s doesn't exist. Not removing any files." % log_file)
    else:
        with open(log_file) as f:
            files = f.read().strip().split('\n')

        for new_f in files:
            new_f = new_f.strip()
            if exists(new_f):
                os.remove(new_f)
                removed.append(new_f)
            else:
                print("Warning: File %s doesn't exist." % new_f, file=sys.stderr)

    files = glob.iglob(join(src, '**'), recursive=True)
    # sorted makes this easier to test
    for f in sorted(files):
        new_f = join(dst, f[len(src):])
        if isdir(f):
            os.makedirs(new_f, exist_ok=True)
        else:
            shutil.copy2(f, new_f)
            added.append(new_f)
            if new_f in removed:
                removed.remove(new_f)

    with open(log_file, 'w') as f:
        f.write('\n'.join(added))

    added.append(log_file)

    return added, removed

def commit_docs(*, added, removed):
    """
    Commit the docs to ``gh-pages``

    Assumes that :func:`setup_GitHub_push`, which sets up the ``doctr_remote``
    remote, has been run and returned True.

    Returns True if changes were committed and False if no changes were
    committed.
    """
    TRAVIS_BUILD_NUMBER = os.environ.get("TRAVIS_BUILD_NUMBER", "<unknown>")

    for f in added:
        run(['git', 'add', f])
    for f in removed:
        run(['git', 'rm', f])

    # Only commit if there were changes
    if subprocess.run(['git', 'diff-index', '--quiet', 'HEAD', '--'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
        print("Committing")
        run(['git', 'commit', '-am', "Update docs after building Travis build " + TRAVIS_BUILD_NUMBER])
        return True

    return False

def push_docs():
    """
    Push the changes to the ``gh-pages`` branch.

    Assumes that :func:`setup_GitHub_push` has been run and returned True, and
    that :func:`commit_docs` has been run. Does not push anything if no changes
    were made.

    """

    print("Pulling")
    run(["git", "pull"])
    print("Pushing commit")
    run(['git', 'push', '-q', 'doctr_remote', 'gh-pages'])
