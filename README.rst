Travis docs builder
===================

A tool for automatically building Sphinx docs on Travis CI, and deploying them
to GitHub pages.

This tool is still a work in progress, but once it works it's going to be
awesome.

Usage (this will change)
------------------------

Run

.. code::

   python -m doctr

and enter your data. You will need your GitHub username and password, and the
repo you want to build the docs for.

That repo should already be setup with Travis. The script will create the
``gh-pages`` branch for you, but you will need to go to
``https://github.com/<your repo>/settings`` and enable GitHub pages. You may
also want to enable branch protection for the ``gh-pages`` branch and other
branches, so that this script can't accidentally screw you.

Then add the stuff to your ``.travis.yml``. The command above will tell you a
secure key to add. You should also have something like

.. code:: yaml

   language: python
   python:
     - 3.5

   sudo: false
   env:
     global:
       secure: "<your secure key from doctr here>"

   script:
     - pip install requests cryptography sphinx
     - cd docs
     - make html
     - cd ..
     - doctr <your repo name>


in your ``.travis.yml``. See `the one <.travis.yml>`_ in this repo for example.

**Heads up:** This script requires Python 3.5 or newer. Be sure to run it in a
Python 3.5 or newer section of your build matrix. It should be in the same
build in your build matrix as your docs build, as it reuses that.

Another suggestion: Add

.. code::

   html: SPHINXOPTS += -W

to your Sphinx ``Makefile``. This will make Sphinx error even if there are
warnings, keeping your docs more accurate.
