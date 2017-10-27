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

from cryptography.fernet import Fernet

DOCTR_WORKING_BRANCH = '__doctr_working_branch'

def red(text):
    return "\033[31m%s\033[0m" % text

def blue(text):
    return "\033[34m%s\033[0m" % text

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

def run_command_hiding_token(args, token, shell=False):
    if token:
        stdout = stderr = subprocess.PIPE
    else:
        stdout = stderr = None
    p = subprocess.run(args, stdout=stdout, stderr=stderr, shell=shell)
    if token:
        # XXX: Do this in a way that is streaming
        out, err = p.stdout, p.stderr
        out = out.replace(token, b"~"*len(token))
        err = err.replace(token, b"~"*len(token))
        if out:
            print(out.decode('utf-8'))
        if err:
            print(err.decode('utf-8'), file=sys.stderr)
    return p.returncode

def get_token():
    """
    Get the encrypted GitHub token in Travis.

    Make sure the contents this variable do not leak. The ``run()`` function
    will remove this from the output, so always use it.
    """
    token = os.environ.get("GH_TOKEN", None)
    if not token:
        token = "GH_TOKEN environment variable not set"
    token = token.encode('utf-8')
    return token

def run(args, shell=False, exit=True):
    """
    Run the command ``args``.

    Automatically hides the secret GitHub token from the output.

    If shell=False (recommended for most commands), args should be a list of
    strings. If shell=True, args should be a string of the command to run.

    If exit=True, it exits on nonzero returncode. Otherwise it returns the
    returncode.
    """
    if "DOCTR_DEPLOY_ENCRYPTION_KEY" in os.environ:
        token = b''
    else:
        token = get_token()

    if not shell:
        command = ' '.join(map(shlex.quote, args))
    else:
        command = args
    command = command.replace(token.decode('utf-8'), '~'*len(token))
    print(blue(command))
    sys.stdout.flush()

    returncode = run_command_hiding_token(args, token, shell=shell)

    if exit and returncode != 0:
        sys.exit(red("%s failed: %s" % (command, returncode)))
    return returncode

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

def get_travis_branch():
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

def setup_GitHub_push(deploy_repo, auth_type='deploy_key', full_key_path='github_deploy_key.enc', require_master=None, branch_whitelist=None, deploy_branch='gh-pages'):
    """
    Setup the remote to push to GitHub (to be run on Travis).

    ``auth_type`` should be either ``'deploy_key'`` or ``'token'``.

    For ``auth_type='token'``, this sets up the remote with the token and
    checks out the gh-pages branch. The token to push to GitHub is assumed to be in the ``GH_TOKEN`` environment
    variable.

    For ``auth_type='deploy_key'``, this sets up the remote with ssh access.
    """

    if not branch_whitelist:
        branch_whitelist={'master'}

    if require_master is not None:
        import warnings
        warnings.warn("`setup_GitHub_push`'s `require_master` argument in favor of `branch_whitelist=['master']`",
                DeprecationWarning,
                stacklevel=2)
        branch_whitelist.add('master')

    if auth_type not in ['deploy_key', 'token']:
        raise ValueError("auth_type must be 'deploy_key' or 'token'")

    TRAVIS_BRANCH = os.environ.get("TRAVIS_BRANCH", "")
    TRAVIS_PULL_REQUEST = os.environ.get("TRAVIS_PULL_REQUEST", "")

    canpush = determine_push_rights(branch_whitelist, TRAVIS_BRANCH,
                                    TRAVIS_PULL_REQUEST)

    print("Setting git attributes")
    set_git_user_email()

    remotes = subprocess.check_output(['git', 'remote']).decode('utf-8').split('\n')
    if 'doctr_remote' in remotes:
        print("doctr_remote already exists, removing")
        run(['git', 'remote', 'remove', 'doctr_remote'])
    print("Adding doctr remote")
    if canpush:
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
    else:
        print('setting a read-only GitHub doctr_remote')
        run(['git', 'remote', 'add', 'doctr_remote',
                'https://github.com/{deploy_repo}.git'.format(deploy_repo=deploy_repo)])


    print("Fetching doctr remote")
    run(['git', 'fetch', 'doctr_remote'])

    return canpush

def set_git_user_email():
    """
    Set global user and email for git user if not already present on system
    """
    username = subprocess.run(shlex.split('git config user.name'), stdout=subprocess.PIPE)
    if not username.stdout:
        run(['git', 'config', '--global', 'user.name', "Doctr (Travis CI)"])

    email = subprocess.run(shlex.split('git config user.email'), stdout=subprocess.PIPE)
    if not email.stdout:
        # We need a dummy email or git will fail. We use this one as per
        # https://help.github.com/articles/keeping-your-email-address-private/.
        run(['git', 'config', '--global', 'user.email', 'drdoctr@users.noreply.github.com'])

def checkout_deploy_branch(deploy_branch, canpush=True):
    """
    Checkout the deploy branch, creating it if it doesn't exist.
    """
    # Create an empty branch with .nojekyll if it doesn't already exist
    create_deploy_branch(deploy_branch, push=canpush)
    remote_branch = "doctr_remote/{}".format(deploy_branch)
    print("Checking out doctr working branch tracking", remote_branch)
    clear_working_branch()
    # If gh-pages doesn't exist the above create_deploy_branch() will create
    # it we can push, but if we can't, it won't and the --track would fail.
    if run(['git', 'rev-parse', '--verify', remote_branch], exit=False) == 0:
        extra_args = ['--track', remote_branch]
    else:
        extra_args = []
    run(['git', 'checkout', '-b', DOCTR_WORKING_BRANCH] + extra_args)
    print("Done")

    return canpush

def clear_working_branch():
    local_branch_names = subprocess.check_output(['git', 'branch']).decode('utf-8').split()
    if DOCTR_WORKING_BRANCH in local_branch_names:
        run(['git', 'branch', '-D', DOCTR_WORKING_BRANCH])

def deploy_branch_exists(deploy_branch):
    """
    Check if there is a remote branch with name specified in ``deploy_branch``.

    Note that default ``deploy_branch`` is ``gh-pages`` for regular repos and
    ``master`` for ``github.io`` repos.

    This isn't completely robust. If there are multiple remotes and you have a
    ``deploy_branch`` branch on the non-default remote, this won't see it.
    """
    remote_name = 'doctr_remote'
    branch_names = subprocess.check_output(['git', 'branch', '-r']).decode('utf-8').split()

    return '{}/{}'.format(remote_name, deploy_branch) in branch_names

def create_deploy_branch(deploy_branch, push=True):
    """
    If there is no remote branch with name specified in ``deploy_branch``,
    create one.

    Note that default ``deploy_branch`` is ``gh-pages`` for regular
    repos and ``master`` for ``github.io`` repos.

    Return True if ``deploy_branch`` was created, False if not.
    """
    if not deploy_branch_exists(deploy_branch):
        print("Creating {} branch on doctr_remote".format(deploy_branch))
        clear_working_branch()
        run(['git', 'checkout', '--orphan', DOCTR_WORKING_BRANCH])
        # delete everything in the new ref.  this is non-destructive to existing
        # refs/branches, etc...
        run(['git', 'rm', '-rf', '.'])
        print("Adding .nojekyll file to working branch")
        run(['touch', '.nojekyll'])
        run(['git', 'add', '.nojekyll'])
        run(['git', 'commit', '-m', 'Create new {} branch with .nojekyll'.format(deploy_branch)])
        if push:
            print("Pushing working branch to remote {} branch".format(deploy_branch))
            run(['git', 'push', '-u', 'doctr_remote', '{}:{}'.format(DOCTR_WORKING_BRANCH, deploy_branch)])
        # return to master branch and clear the working branch
        run(['git', 'checkout', 'master'])
        run(['git', 'branch', '-D', DOCTR_WORKING_BRANCH])
        # fetch the remote so that doctr_remote/{deploy_branch} is resolved
        run(['git', 'fetch', 'doctr_remote'])

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

def copy_to_tmp(source):
    """
    Copies ``source`` to a temporary directory, and returns the copied location.
    """
    tmp_dir = tempfile.mkdtemp()
    # Use pathlib because os.path.basename is different depending on whether
    # the path ends in a /
    p = pathlib.Path(source)
    new_dir = os.path.join(tmp_dir, p.name)
    if os.path.isdir(source):
        shutil.copytree(source, new_dir)
    else:
        shutil.copy2(source, new_dir)
    return new_dir

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

    if os.path.isdir(src):
        if not src.endswith(os.sep):
            src += os.sep
        files = glob.iglob(join(src, '**'), recursive=True)
    else:
        files = [src]
        src = os.path.dirname(src) + os.sep

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
    Commit the docs to the current branch

    Assumes that :func:`setup_GitHub_push`, which sets up the ``doctr_remote``
    remote, has been run.

    Returns True if changes were committed and False if no changes were
    committed.
    """
    TRAVIS_BUILD_NUMBER = os.environ.get("TRAVIS_BUILD_NUMBER", "<unknown>")
    TRAVIS_BRANCH = os.environ.get("TRAVIS_BRANCH", "<unknown>")
    TRAVIS_COMMIT = os.environ.get("TRAVIS_COMMIT", "<unknown>")
    TRAVIS_REPO_SLUG = os.environ.get("TRAVIS_REPO_SLUG", "<unknown>")
    TRAVIS_JOB_ID = os.environ.get("TRAVIS_JOB_ID", "")
    DOCTR_COMMAND = ' '.join(map(shlex.quote, sys.argv))

    for f in added:
        run(['git', 'add', f])
    for f in removed:
        run(['git', 'rm', f])

    commit_message = """\
Update docs after building Travis build {TRAVIS_BUILD_NUMBER} of
{TRAVIS_REPO_SLUG}

The docs were built from the branch '{TRAVIS_BRANCH}' against the commit
{TRAVIS_COMMIT}.

The Travis build that generated this commit is at
https://travis-ci.org/{TRAVIS_REPO_SLUG}/jobs/{TRAVIS_JOB_ID}.

The doctr command that was run is

    {DOCTR_COMMAND}
""".format(
    TRAVIS_BUILD_NUMBER=TRAVIS_BUILD_NUMBER,
    TRAVIS_BRANCH=TRAVIS_BRANCH,
    TRAVIS_COMMIT=TRAVIS_COMMIT,
    TRAVIS_REPO_SLUG=TRAVIS_REPO_SLUG,
    TRAVIS_JOB_ID=TRAVIS_JOB_ID,
    DOCTR_COMMAND=DOCTR_COMMAND,
    )

    # Only commit if there were changes
    if run(['git', 'diff-index', '--exit-code', '--cached', '--quiet', 'HEAD', '--'], exit=False) != 0:
        print("Committing")
        run(['git', 'commit', '-am', commit_message])
        return True

    return False

def push_docs(deploy_branch='gh-pages', retries=3):
    """
    Push the changes to the branch named ``deploy_branch``.

    Assumes that :func:`setup_GitHub_push` has been run and returned True, and
    that :func:`commit_docs` has been run. Does not push anything if no changes
    were made.

    """

    code = 1
    while code and retries:
        print("Pulling")
        code = run(['git', 'pull', '-s', 'recursive', '-X', 'ours',
            'doctr_remote', deploy_branch], exit=False)
        print("Pushing commit")
        code = run(['git', 'push', '-q', 'doctr_remote',
            '{}:{}'.format(DOCTR_WORKING_BRANCH, deploy_branch)], exit=False)
        if code:
            retries -= 1
            print("Push failed, retrying")
            time.sleep(1)
        else:
            return
    sys.exit("Giving up...")

def determine_push_rights(branch_whitelist, TRAVIS_BRANCH, TRAVIS_PULL_REQUEST):
    """Check if Travis is running on ``master`` (or a whitelisted branch) to
    determine if we can/should push the docs to the deploy repo
    """
    canpush = True

    if not any([re.compile(x).match(TRAVIS_BRANCH) for x in branch_whitelist]):
        print("The docs are only pushed to gh-pages from master. To allow pushing from "
        "a non-master branch, use the --no-require-master flag", file=sys.stderr)
        print("This is the {TRAVIS_BRANCH} branch".format(TRAVIS_BRANCH=TRAVIS_BRANCH), file=sys.stderr)
        canpush = False

    if TRAVIS_PULL_REQUEST != "false":
        print("The website and docs are not pushed to gh-pages on pull requests", file=sys.stderr)
        canpush = False

    return canpush
