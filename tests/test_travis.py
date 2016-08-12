import os

from doctr.travis import find_sphinx_build_dir

def test_find_sphinx_build_dir():
    curdir = os.path.abspath(os.curdir)
    try:
        os.chdir(os.path.abspath(os.path.join(__file__, os.pardir, os.pardir)))
        assert 'tests' in os.listdir(os.curdir)
        assert find_sphinx_build_dir() == os.path.join('docs', '_build')
    finally:
        os.chdir(curdir)
