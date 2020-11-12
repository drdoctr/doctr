"""
So far, very little is actually tested here, because there aren't many
functions that can be tested outside of actually running them on Travis.
"""

import tempfile
import os
from os.path import join

import pytest

from ..travis import Travis
from ..ci import sync_from_log, copy_to_tmp

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

            # First test it is ignored when excluded
            added, removed = sync_from_log(src, dst, 'logfile',
                exclude=['test3'])

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

            assert not os.path.exists(join(dst, 'test3'))

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join(dst, 'test1'),
                    join(dst, 'testdir', 'test2'),
                    ])

            # Now test it it added normally
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

            # First test it is ignored with exclude
            added, removed = sync_from_log(src, dst, 'logfile', exclude=['test3'])
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

            with open(join(dst, 'test3')) as f:
                assert f.read() == 'test3'

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join(dst, 'test1'),
                    join(dst, 'testdir', 'test2'),
                    ])

            # Then test it is removed normally
            # (readd it to the log file, since the exclude removed it)
            with open('logfile', 'a') as f:
                f.write('\n' + join(dst, 'test3'))

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

            # Test excluding a directory

            os.makedirs(join(src, 'testdir2'))
            with open(join(src, 'testdir2', 'test2'), 'w') as f:
                f.write('test2')

            added, removed = sync_from_log(src, dst, 'logfile', exclude=['testdir2'])


            assert added == [
                join(dst, 'test1'),
                join(dst, 'testdir', 'test2'),
                'logfile',
            ]

            assert removed == []

            assert not os.path.exists(join(dst, 'testdir2'))

        finally:
            os.chdir(old_curdir)


@pytest.mark.parametrize("dst", ['dst', 'dst/'])
def test_sync_from_log_file_to_dir(dst):
    with tempfile.TemporaryDirectory() as dir:
        try:
            old_curdir = os.path.abspath(os.curdir)
            os.chdir(dir)

            src = 'file'

            with open(src, 'w') as f:
                f.write('test1')

            # Test that the sync happens
            added, removed = sync_from_log(src, dst, 'logfile')

            assert added == [
                os.path.join('dst', 'file'),
                'logfile',
                ]

            assert removed == []

            assert os.path.isdir(dst)
            # Make sure dst is a file
            with open(os.path.join('dst', 'file')) as f:
                assert f.read() == 'test1'


            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    os.path.join('dst', 'file')
                    ])

        finally:
            os.chdir(old_curdir)


@pytest.mark.parametrize("""branch_whitelist, branch,
                         pull_request, tag, fork, build_tags,
                         canpush""",
                         [

                             ('master', 'doctr', True, "", False, False, False),
                             ('master', 'doctr', False, "", False, False, False),
                             ('master', 'master', True, "", False, False, False),
                             ('master', 'master', False, "", False, False, True),
                             ('doctr', 'doctr', True, "", False, False, False),
                             ('doctr', 'doctr', False, "", False, False, True),
                             ('set()', 'doctr', False, "", False, False, False),

                             ('master', 'doctr', True, "tagname", False, False, False),
                             ('master', 'doctr', False, "tagname", False, False, False),
                             ('master', 'master', True, "tagname", False, False, False),
                             ('master', 'master', False, "tagname", False, False, False),
                             ('doctr', 'doctr', True, "tagname", False, False, False),
                             ('doctr', 'doctr', False, "tagname", False, False, False),
                             ('set()', 'doctr', False, "tagname", False, False, False),

                             ('master', 'doctr', True, "", False, True, False),
                             ('master', 'doctr', False, "", False, True, False),
                             ('master', 'master', True, "", False, True, False),
                             ('master', 'master', False, "", False, True, True),
                             ('doctr', 'doctr', True, "", False, True, False),
                             ('doctr', 'doctr', False, "", False, True, True),
                             ('set()', 'doctr', False, "", False, True, False),

                             ('master', 'doctr', True, "tagname", False, True, True),
                             ('master', 'doctr', False, "tagname", False, True, True),
                             ('master', 'master', True, "tagname", False, True, True),
                             ('master', 'master', False, "tagname", False, True, True),
                             ('doctr', 'doctr', True, "tagname", False, True, True),
                             ('doctr', 'doctr', False, "tagname", False, True, True),
                             ('set()', 'doctr', False, "tagname", False, True, True),

                             ('master', 'doctr', True, "", True, False, False),
                             ('master', 'doctr', False, "", True, False, False),
                             ('master', 'master', True, "", True, False, False),
                             ('master', 'master', False, "", True, False, False),
                             ('doctr', 'doctr', True, "", True, False, False),
                             ('doctr', 'doctr', False, "", True, False, False),
                             ('set()', 'doctr', False, "", True, False, False),

                         ])
def test_determine_push_rights(branch_whitelist, branch,
    pull_request, tag, build_tags, fork, canpush, monkeypatch):
    branch_whitelist = {branch_whitelist}

    CI = Travis()
    assert CI.determine_push_rights(
        branch_whitelist=branch_whitelist,
        branch=branch,
        pull_request=pull_request,
        tag=tag,
        fork=fork,
        build_tags=build_tags) == canpush

@pytest.mark.parametrize("src", ["src", "."])
def test_copy_to_tmp(src):
    with tempfile.TemporaryDirectory() as dir:
        os.makedirs(os.path.join(dir, src), exist_ok=True)
        with open(os.path.join(dir, src, "test"), 'w') as f:
            f.write('test')

        new_dir = copy_to_tmp(os.path.join(dir, src))

        assert os.path.exists(new_dir)
        with open(os.path.join(new_dir, 'test'), 'r') as f:
            assert f.read() == 'test'

        new_dir2 = copy_to_tmp(os.path.join(dir, src, 'test'))

        assert os.path.exists(new_dir2)
        with open(os.path.join(new_dir2), 'r') as f:
            assert f.read() == 'test'
