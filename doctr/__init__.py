from .local import (encrypt_variable, encrypt_file, GitHub_post,
    generate_GitHub_token, upload_GitHub_deploy_key, generate_ssh_key)
from .travis import (decrypt_file, setup_deploy_key, get_token, run,
    setup_GitHub_push, gh_pages_exists, create_gh_pages, commit_docs,
    push_docs, get_current_repo)

__all__ = [
    'encrypt_variable', 'encrypt_file', 'GitHub_post',
    'generate_GitHub_token', 'upload_GitHub_deploy_key', 'generate_ssh_key',

    'decrypt_file', 'setup_deploy_key', 'get_token', 'run', 'setup_GitHub_push', 'gh_pages_exists',
    'create_gh_pages', 'commit_docs', 'push_docs', 'get_current_repo',
]

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
