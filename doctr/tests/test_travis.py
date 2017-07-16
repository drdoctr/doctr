"""
So far, very little is actually tested here, because there aren't many
functions that can be tested outside of actually running them on Travis.
"""

import tempfile
import os
from os.path import join

import pytest

from ..travis import sync_from_log, determine_push_rights

@pytest.mark.parametrize("src", ["src"])
@pytest.mark.parametrize("dst", ['.', 'dst'])
def test_sync_from_log(src, dst):
    with tempfile.TemporaryDirectory() as dir:
        try:
            old_curdir = os.path.abspath(os.curdir)
            os.chdir(dir)

            # Set up a src directory with some files
            os.makedirs(src)

            with open(join(src, 'test1'), 'w') as f:
                f.write('test1')

            os.makedirs(join(src, 'testdir'))
            with open(join(src, 'testdir', 'test2'), 'w') as f:
                f.write('test2')

            # Test that the sync happens
            added, removed = sync_from_log(src, dst, 'logfile')

            assert added == [
                join(dst, 'test1'),
                join(dst, 'testdir', 'test2'),
                'logfile',
                ]

            assert removed == []

            with open(join(dst, 'test1')) as f:
                assert f.read() == 'test1'

            with open(join(dst, 'testdir', 'test2')) as f:
                assert f.read() == 'test2'

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join(dst, 'test1'),
                    join(dst, 'testdir', 'test2'),
                    ])

            # Create a new file
            with open(join(src, 'test3'), 'w') as f:
                f.write('test3')

            added, removed = sync_from_log(src, dst, 'logfile')

            assert added == [
                join(dst, 'test1'),
                join(dst, 'test3'),
                join(dst, 'testdir', 'test2'),
                'logfile',
            ]

            assert removed == []

            with open(join(dst, 'test1')) as f:
                assert f.read() == 'test1'

            with open(join(dst, 'testdir', 'test2')) as f:
                assert f.read() == 'test2'

            with open(join(dst, 'test3')) as f:
                assert f.read() == 'test3'

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join(dst, 'test1'),
                    join(dst, 'test3'),
                    join(dst, 'testdir', 'test2'),
                    ])

            # Delete a file
            os.remove(join(src, 'test3'))

            added, removed = sync_from_log(src, dst, 'logfile')

            assert added == [
                join(dst, 'test1'),
                join(dst, 'testdir', 'test2'),
                'logfile',
            ]

            assert removed == [
                join(dst, 'test3'),
            ]

            with open(join(dst, 'test1')) as f:
                assert f.read() == 'test1'

            with open(join(dst, 'testdir', 'test2')) as f:
                assert f.read() == 'test2'

            assert not os.path.exists(join(dst, 'test3'))

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join(dst, 'test1'),
                    join(dst, 'testdir', 'test2'),
                    ])

            # Change a file
            with open(join(src, 'test1'), 'w') as f:
                f.write('test1 modified')

            added, removed = sync_from_log(src, dst, 'logfile')

            assert added == [
                join(dst, 'test1'),
                join(dst, 'testdir', 'test2'),
                'logfile',
            ]

            assert removed == []

            with open(join(dst, 'test1')) as f:
                assert f.read() == 'test1 modified'

            with open(join(dst, 'testdir', 'test2')) as f:
                assert f.read() == 'test2'

            assert not os.path.exists(join(dst, 'test3'))

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join(dst, 'test1'),
                    join(dst, 'testdir', 'test2'),
                    ])

        finally:
            os.chdir(old_curdir)


@pytest.mark.parametrize("""branch_whitelist, TRAVIS_BRANCH,
                         TRAVIS_PULL_REQUEST, TRAVIS_TAG, build_tags,
                         canpush""",
                         [

                             ('master', 'doctr', 'true', "", False, False),
                             ('master', 'doctr', 'false', "", False, False),
                             ('master', 'master', 'true', "", False, False),
                             ('master', 'master', 'false', "", False, True),
                             ('doctr', 'doctr', 'True', "", False, False),
                             ('doctr', 'doctr', 'false', "", False, True),
                             ('set()', 'doctr', 'false', "", False, False),

                             ('master', 'doctr', 'true', "tagname", False, False),
                             ('master', 'doctr', 'false', "tagname", False, False),
                             ('master', 'master', 'true', "tagname", False, False),
                             ('master', 'master', 'false', "tagname", False, False),
                             ('doctr', 'doctr', 'True', "tagname", False, False),
                             ('doctr', 'doctr', 'false', "tagname", False, False),
                             ('set()', 'doctr', 'false', "tagname", False, False),

                             ('master', 'doctr', 'true', "", True, False),
                             ('master', 'doctr', 'false', "", True, False),
                             ('master', 'master', 'true', "", True, False),
                             ('master', 'master', 'false', "", True, True),
                             ('doctr', 'doctr', 'True', "", True, False),
                             ('doctr', 'doctr', 'false', "", True, True),
                             ('set()', 'doctr', 'false', "", True, False),

                             ('master', 'doctr', 'true', "tagname", True, True),
                             ('master', 'doctr', 'false', "tagname", True, True),
                             ('master', 'master', 'true', "tagname", True, True),
                             ('master', 'master', 'false', "tagname", True, True),
                             ('doctr', 'doctr', 'True', "tagname", True, True),
                             ('doctr', 'doctr', 'false', "tagname", True, True),
                             ('set()', 'doctr', 'false', "tagname", True, True),

                         ])
def test_determine_push_rights(branch_whitelist, TRAVIS_BRANCH,
    TRAVIS_PULL_REQUEST, TRAVIS_TAG, build_tags, canpush, monkeypatch):
    branch_whitelist = {branch_whitelist}

    assert determine_push_rights(
        branch_whitelist=branch_whitelist,
        TRAVIS_BRANCH=TRAVIS_BRANCH,
        TRAVIS_PULL_REQUEST=TRAVIS_PULL_REQUEST,
        TRAVIS_TAG=TRAVIS_TAG,
        build_tags=build_tags) == canpush
