from .local import (encrypt_variable_travis, encrypt_to_file, GitHub_post,
    generate_GitHub_token, upload_GitHub_deploy_key, generate_ssh_key,
    check_repo_exists, guess_github_repo)
from .travis import Travis

from .ci import sync_from_log, copy_to_tmp, find_sphinx_build_dir

__all__ = [
    'encrypt_variable_travis', 'encrypt_to_file', 'GitHub_post',
    'generate_GitHub_token', 'upload_GitHub_deploy_key', 'generate_ssh_key',
    'check_repo_exists', 'guess_github_repo',

    'Travis',

    'sync_from_log', 'copy_to_tmp', 'find_sphinx_build_dir',
]

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
