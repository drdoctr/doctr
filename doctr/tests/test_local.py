from ..local import check_repo_exists

from pytest import raises

def test_bad_user():
    with raises(RuntimeError):
        check_repo_exists('---/invaliduser')

def test_bad_repo():
    with raises(RuntimeError):
        check_repo_exists('drdoctr/---')

def test_repo_exists():
    assert check_repo_exists('drdoctr/doctr')

def test_invalid_repo():
    with raises(RuntimeError):
        check_repo_exists('fdsf')

    with raises(RuntimeError):
        check_repo_exists('fdsf/fdfs/fd')
