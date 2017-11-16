from .local import (encrypt_variable, encrypt_file, GitHub_post,
    generate_GitHub_token, upload_GitHub_deploy_key, generate_ssh_key,
    check_repo_exists, guess_github_repo)
from .travis import (decrypt_file, setup_deploy_key, get_token, run,
    setup_GitHub_push, checkout_deploy_branch, deploy_branch_exists,
    set_git_user_email, create_deploy_branch, copy_to_tmp, sync_from_log,
    commit_docs, push_docs, get_current_repo, find_sphinx_build_dir)

__all__ = [
    'encrypt_variable', 'encrypt_file', 'GitHub_post',
    'generate_GitHub_token', 'upload_GitHub_deploy_key', 'generate_ssh_key',
    'check_repo_exists', 'guess_github_repo',

    'decrypt_file', 'setup_deploy_key', 'get_token', 'run',
    'setup_GitHub_push', 'set_git_user_email', 'checkout_deploy_branch', 'deploy_branch_exists',
    'create_deploy_branch', 'copy_to_tmp', 'sync_from_log', 'commit_docs', 'push_docs', 'get_current_repo', 'find_sphinx_build_dir'
]

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
