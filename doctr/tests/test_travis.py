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


@pytest.mark.parametrize("travis_branch, travis_pr, whitelist, canpush",
                         [('doctr', 'true', 'master', False),
                          ('doctr', 'false', 'master', False),
                          ('master', 'true', 'master', False),
                          ('master', 'false', 'master', True),
                          ('doctr', 'True', 'doctr', False),
                          ('doctr', 'false', 'doctr', True),
                          ('doctr', 'false', 'set()', False),
                         ])
def test_determine_push_rights(travis_branch, travis_pr, whitelist, canpush, monkeypatch):
    branch_whitelist = {whitelist}

    assert determine_push_rights(branch_whitelist, travis_branch, travis_pr) == canpush
