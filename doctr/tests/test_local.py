import os
import tempfile
import subprocess

from ..local import check_repo_exists, in_git_root

import pytest
from pytest import raises

TEST_TOKEN = os.environ.get('TESTING_TOKEN', None)
if TEST_TOKEN:
    HEADERS = {'Authorization': 'token {}'.format(TEST_TOKEN)}
else:
    HEADERS = None


def test_github_bad_user():
    with raises(RuntimeError):
        check_repo_exists('---/invaliduser', headers=HEADERS)

def test_github_bad_repo():
    with raises(RuntimeError):
        check_repo_exists('drdoctr/---', headers=HEADERS)

def test_github_repo_exists():
    assert not check_repo_exists('drdoctr/doctr', headers=HEADERS)

def test_github_invalid_repo():
    with raises(RuntimeError):
        check_repo_exists('fdsf', headers=HEADERS)

    with raises(RuntimeError):
        check_repo_exists('fdsf/fdfs/fd', headers=HEADERS)

def test_travis_bad_user():
    with raises(RuntimeError):
        # Travis is case-sensitive
        check_repo_exists('dRdoctr/doctr', service='travis')

def test_travis_bad_repo():
    with raises(RuntimeError):
        # Travis is case-sensitive
        check_repo_exists('drdoctr/DoCtR', service='travis')

def test_travis_repo_exists():
    assert not check_repo_exists('drdoctr/doctr', service='travis')

@pytest.fixture(scope="module")
def test_repo():
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    subprocess.call(['git', 'init'])
    return {'repo_dir': temp_dir}

@pytest.mark.parametrize('subdir, _bool', [
    ('a_subdir', False),
    ('.', True),
])
def test_in_git_root(subdir, _bool, test_repo):
    os.chdir(test_repo['repo_dir'])
    try:
        os.mkdir(subdir)
    except FileExistsError:
        pass
    os.chdir(subdir)
    assert in_git_root() is _bool

def test_not_in_git_repo():
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    with raises(RuntimeError):
        in_git_root()
