Travis docs builder
===================

A tool for automatically building Sphinx docs on Travis CI, and deploying them
to GitHub pages.

This tool is still a work in progress, but once it works it's going to be
awesome.

Usage
-----

Run

.. code::

   doctr configure

and enter your data. You will need your GitHub username and password, and the
repo you want to build the docs for.

That repo should already be setup with Travis. We recommend enabling branch
protection for the ``gh-pages`` branch and other branches, as the deploy key
used by Doctr has the ability to push to any branch in your repo.

Then add the stuff to your ``.travis.yml`` and commit the encrypted deploy
key. The command above will tell you what to do. You should also have
something like

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
     - doctr deploy


in your ``.travis.yml``. See `the one
<https://github.com/gforsyth/doctr/blob/master/.travis.yml>`_ used by Doctr
itself for example.

**Heads up:** Doctr requires Python 3.5 or newer. Be sure to run it in a
Python 3.5 or newer section of your build matrix. It should be in the same
build in your build matrix as your docs build, as it reuses that.

Another suggestion: Add

.. code::

   html: SPHINXOPTS += -W

to your Sphinx ``Makefile``. This will make Sphinx error even if there are
warnings, keeping your docs more accurate.
