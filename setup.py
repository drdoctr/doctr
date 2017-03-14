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
    author='Aaron Meurer and Gil Forsyth',
    author_email='asmeurer@gmail.com',
    url='https://github.com/drdoctr/doctr',
    packages=['doctr', 'doctr.tests'],
    description='Deploy docs from Travis to GitHub pages.',
    long_description=open("README.rst").read(),
    entry_points={'console_scripts': [ 'doctr = doctr.__main__:main']},
    python_requires= '>=3.5',
    install_requires=[
        'pyyaml',
        'requests',
        'cryptography',
    ],
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        ],
    zip_safe=False,
)
