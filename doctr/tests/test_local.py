import os
import uuid

from ..local import check_repo_exists, update_travis_yml

from pytest import raises, mark

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

@mark.parametrize('travis_in, travis_add',[
    ('language: python3\n', 'env:\n  global:\n    secure: mykey\n'),
    ('language: python3\nenv:\n  matrix:\n    - foo="bar"\n', '  global:\n    - secure: mykey\n'),
    ('language: python3\nenv:\n  global:\n    - FOO=bar\n', '    - secure: mykey\n'),
])
def test_missing_yml_bits(travis_in, travis_add, tmpdir):

    p = tmpdir.join('.travis.yml')
    p.write(travis_in)

    assert update_travis_yml(str(p), 'mykey'.encode('utf-8'))
    assert str(p.read()) == travis_in + travis_add
    print(str(p.read()))

def test_missing_travis_yml():
    fname = str(uuid.uuid1())
    assert update_travis_yml(fname, 'mykey'.encode('utf-8'))
    os.remove(fname)

def test_bad_yml(tmpdir):
    p = tmpdir.join('.travis.yml')
    p.write('foo:\nbar==:baz')
    with raises(RuntimeError):
        update_travis_yml(str(p), 'mykey'.encode('utf-8'))
