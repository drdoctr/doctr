"""
So far, very little is actually tested here, because there aren't many
functions that can be tested outside of actually running them on Travis.
"""

import tempfile
import os
from os.path import join

from ..travis import sync_from_log

def test_sync_from_log():
    with tempfile.TemporaryDirectory() as dir:
        try:
            old_curdir = os.path.abspath(os.curdir)
            os.chdir(dir)

            # Set up a src directory with some files
            os.makedirs('src')

            with open(join('src', 'test1'), 'w') as f:
                f.write('test1')

            os.makedirs(join('src', 'testdir'))
            with open(join('src', 'testdir', 'test2'), 'w') as f:
                f.write('test2')

            # Test that the sync happens
            added, removed = sync_from_log('src', '.', 'logfile')

            assert added == [
                join('.', 'test1'),
                join('.', 'testdir', 'test2'),
                ]

            assert removed == []

            with open('test1') as f:
                assert f.read() == 'test1'

            with open(join('testdir', 'test2')) as f:
                assert f.read() == 'test2'

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join('.', 'test1'),
                    join('.', 'testdir', 'test2'),
                    ])

            # Create a new file
            with open(join('src', 'test3'), 'w') as f:
                f.write('test3')

            added, removed = sync_from_log('src', '.', 'logfile')

            assert added == [
                join('.', 'test1'),
                join('.', 'test3'),
                join('.', 'testdir', 'test2'),
            ]

            assert removed == []

            with open('test1') as f:
                assert f.read() == 'test1'

            with open(join('testdir', 'test2')) as f:
                assert f.read() == 'test2'

            with open('test3') as f:
                assert f.read() == 'test3'

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join('.', 'test1'),
                    join('.', 'test3'),
                    join('.', 'testdir', 'test2'),
                    ])

            # Delete a file
            os.remove(join('src', 'test3'))

            added, removed = sync_from_log('src', '.', 'logfile')

            assert added == [
                join('.', 'test1'),
                join('.', 'testdir', 'test2'),
            ]

            assert removed == [
                join('.', 'test3'),
            ]

            with open('test1') as f:
                assert f.read() == 'test1'

            with open(join('testdir', 'test2')) as f:
                assert f.read() == 'test2'

            assert not os.path.exists('test3')

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join('.', 'test1'),
                    join('.', 'testdir', 'test2'),
                    ])

            # Change a file
            with open(join('src', 'test1'), 'w') as f:
                f.write('test1 modified')

            added, removed = sync_from_log('src', '.', 'logfile')

            assert added == [
                join('.', 'test1'),
                join('.', 'testdir', 'test2'),
            ]

            assert removed == []

            with open('test1') as f:
                assert f.read() == 'test1 modified'

            with open(join('testdir', 'test2')) as f:
                assert f.read() == 'test2'

            assert not os.path.exists('test3')

            with open('logfile') as f:
                assert f.read() == '\n'.join([
                    join('.', 'test1'),
                    join('.', 'testdir', 'test2'),
                    ])

        finally:
            os.chdir(old_curdir)
