#!/usr/bin/env python

import sys
if sys.version_info < (3,5):
    sys.exit("doctr requires Python 3.5 or newer")

from setuptools import setup
import versioneer

setup(
    name='doctr',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='''Deploy docs from Travis to GitHub pages.''',
    author='Aaron Meurer and Gil Forsyth',
    author_email='asmeurer@gmail.com',
    url='https://github.com/gforsyth/doctr',
    packages=['doctr'],
    long_description="""
doctr

Deploy docs from Travis to GitHub pages.

License: MIT

""",
    entry_points={'console_scripts': [ 'doctr = doctr.__main__:main']},
    install_requires=[
        'requests',
        'cryptography',
    ],
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        ],
    zip_safe=False,
)
