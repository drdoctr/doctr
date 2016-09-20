from ..local import check_repo_exists

from pytest import raises

def test_bad_user():
    with raises(RuntimeError):
        check_repo_exists('---/invaliduser')

def test_bad_repo():
    with raises(RuntimeError):
        check_repo_exists('drdoctr/---')

def test_repo_exists():
    assert not check_repo_exists('drdoctr/doctr')

def test_invalid_repo():
    with raises(RuntimeError):
        check_repo_exists('fdsf')

    with raises(RuntimeError):
        check_repo_exists('fdsf/fdfs/fd')

def test_bad_travis_user():
    with raises(RuntimeError):
        # Travis is case-sensitive
        check_repo_exists('dRdoctr/doctr', service='travis')

def test_bad_travis_repo():
    with raises(RuntimeError):
        # Travis is case-sensitive
        check_repo_exists('drdoctr/DoCtR', service='travis')

def test_travis_repo_exists():
    assert not check_repo_exists('drdoctr/doctr', service='travis')
