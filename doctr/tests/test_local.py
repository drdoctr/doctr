import os

from ..local import check_repo_exists

from pytest import raises

TEST_TOKEN = os.environ.get('TESTING_TOKEN')
HEADERS = {'Authorization': 'token {}'.format(TEST_TOKEN)}


def test_bad_user():
    with raises(RuntimeError):
        check_repo_exists('---/invaliduser', headers=HEADERS)

def test_bad_repo():
    with raises(RuntimeError):
        check_repo_exists('drdoctr/---', headers=HEADERS)

def test_repo_exists():
    assert not check_repo_exists('drdoctr/doctr', headers=HEADERS)

def test_invalid_repo():
    with raises(RuntimeError):
        check_repo_exists('fdsf', headers=HEADERS)

    with raises(RuntimeError):
        check_repo_exists('fdsf/fdfs/fd', headers=HEADERS)
