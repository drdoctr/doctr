import os

from ..local import check_repo_exists

from pytest import raises

TEST_AUTH = os.environ.get('TESTING_TOKEN')

def test_bad_user():
    with raises(RuntimeError):
        check_repo_exists('---/invaliduser', auth=TEST_AUTH)

def test_bad_repo():
    with raises(RuntimeError):
        check_repo_exists('drdoctr/---', auth=TEST_AUTH)

def test_repo_exists():
    assert not check_repo_exists('drdoctr/doctr', auth=TEST_AUTH)

def test_invalid_repo():
    with raises(RuntimeError):
        check_repo_exists('fdsf', auth=TEST_AUTH)

    with raises(RuntimeError):
        check_repo_exists('fdsf/fdfs/fd', auth=TEST_AUTH)
