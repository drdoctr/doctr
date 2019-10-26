import os
import binascii

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
    with raises(RuntimeError):
        check_repo_exists('drdoctr/---.wiki', headers=HEADERS)

@pytest.mark.skipif(not TEST_TOKEN, reason="No API token present")
def test_github_repo_exists():
    assert check_repo_exists('drdoctr/doctr', headers=HEADERS) == {'private': False, 'service': 'github'}
    assert check_repo_exists('drdoctr/doctr.wiki', headers=HEADERS) == {'private': False, 'service': 'github'}

@pytest.mark.parametrize('service', ['travis', 'travis-ci.org', 'travis-ci.com'])
@pytest.mark.parametrize('repo', ['com', 'org', 'both', 'neither'])
def test_check_repo_exists_org_com(repo, service):
    deploy_repo = 'drdoctr/testing-travis-ci-' + repo
    if (repo == 'neither' or
        repo == 'org' and service == 'travis-ci.com' or
        repo == 'com' and service == 'travis-ci.org'):
        with raises(RuntimeError):
            check_repo_exists(deploy_repo, service)
    elif (repo == 'org' or
          repo == 'both' and service == 'travis-ci.org'):
        assert check_repo_exists(deploy_repo, service) == {'private': False,
                                                           'service': 'travis-ci.org'}
    else:
        assert check_repo_exists(deploy_repo, service) == {'private': False,
                                                           'service': 'travis-ci.com'}

@pytest.mark.skipif(not TEST_TOKEN, reason="No API token present")
def test_github_invalid_repo():
    with raises(RuntimeError):
        check_repo_exists('fdsf', headers=HEADERS)

    with raises(RuntimeError):
        check_repo_exists('fdsf/fdfs/fd', headers=HEADERS)

def test_travis_bad_user():
    with raises(RuntimeError):
        rand_hex = binascii.hexlify(os.urandom(32)).decode('utf-8')
        check_repo_exists('drdoctr{}/doctr'.format(rand_hex), service='travis')

def test_travis_bad_repo():
    with raises(RuntimeError):
        rand_hex = binascii.hexlify(os.urandom(32)).decode('utf-8')
        check_repo_exists('drdoctr/doctr{}'.format(rand_hex), service='travis')

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

@pytest.mark.skipif(os.environ.get('TRAVIS_REPO_SLUG', '') != 'drdoctr/doctr', reason="Not run on Travis fork builds")
@pytest.mark.skipif(not on_travis(), reason="Not on Travis")
def test_guess_github_repo():
    """
    Only works if run in this repo, and if cloned from origin. For safety,
    only run on Travis and not run on fork builds.
    """
    assert guess_github_repo() == 'drdoctr/doctr'
