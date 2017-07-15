import os

from ..local import check_repo_exists, GIT_URL, guess_github_repo
from ..__main__ import on_travis

import pytest
from pytest import raises

TEST_TOKEN = os.environ.get('TESTING_TOKEN', None)
if TEST_TOKEN:
    HEADERS = {'Authorization': 'token {}'.format(TEST_TOKEN)}
else:
    HEADERS = None


@pytest.mark.skipif(not TEST_TOKEN, reason="No API token present")
def test_github_bad_user():
    with raises(RuntimeError):
        check_repo_exists('---/invaliduser', headers=HEADERS)

@pytest.mark.skipif(not TEST_TOKEN, reason="No API token present")
def test_github_bad_repo():
    with raises(RuntimeError):
        check_repo_exists('drdoctr/---', headers=HEADERS)

@pytest.mark.skipif(not TEST_TOKEN, reason="No API token present")
def test_github_repo_exists():
    assert not check_repo_exists('drdoctr/doctr', headers=HEADERS)

@pytest.mark.skipif(not TEST_TOKEN, reason="No API token present")
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

def test_GIT_URL():
    for url in [
        'https://github.com/drdoctr/doctr.git',
        'https://github.com/drdoctr/doctr',
        'git://github.com/drdoctr/doctr.git',
        'git://github.com/drdoctr/doctr',
        'git@github.com:drdoctr/doctr.git',
        'git@github.com:drdoctr/doctr',
        ]:
        assert GIT_URL.fullmatch(url).groups() == ('drdoctr/doctr',), url

    assert not GIT_URL.fullmatch('https://gitlab.com/drdoctr/doctr.git')

def test_guess_github_repo():
    """
    Only works if run in this repo, and if cloned from origin. For safety,
    only run on Travis
    """
    if on_travis():
        assert guess_github_repo() == 'drdoctr/doctr'
