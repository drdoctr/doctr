Doctr
=====

A tool for automatically deploying docs from Travis CI to GitHub pages.

Contribute to Doctr development on `GitHub
<https://github.com/drdoctr/doctr>`_.

Installation
------------

Install doctr with pip

.. code::

   pip install doctr

or conda

.. code::

   conda install -c conda-forge doctr

**Note that doctr requires Python 3.5 or newer.**

Usage
-----

Run

.. code::

   doctr configure

and enter your data. You will need your GitHub username and password, and the
repo you want to build the docs for.

That repo should already be setup with Travis. We recommend enabling
`branch protection <https://help.github.com/articles/about-protected-branches/>`_
for the ``gh-pages`` branch and other branches, as the deploy key
used by Doctr has the ability to push to any branch in your repo.

Then add the stuff to your ``.travis.yml`` and commit the encrypted deploy
key. The command above will tell you what to do. You should also have
something like

.. code:: yaml

   language: python
   python:
     - 3.6

   sudo: false
   env:
     global:
       secure: "<your secure key from doctr here>"

   script:
     - set -e
     - pip install sphinx doctr
     - cd docs
     - make html
     - cd ..
     - doctr deploy


in your ``.travis.yml``. See `the one
<https://github.com/drdoctr/doctr/blob/master/.travis.yml>`_ used by Doctr
itself for example.

.. warning::

   Be sure to add ``set -e`` in ``script``, to prevent ``doctr`` from running
   when the docs build fails.

.. warning::

   Put ``doctr deploy`` in the ``script`` section of your ``.travis.yml``. If
   you use ``after_success``, it will `not cause
   <https://docs.travis-ci.com/user/customizing-the-build#Breaking-the-Build>`_
   the build to fail.



**Heads up:** Doctr requires Python 3.5 or newer. Be sure to run it in a
Python 3.5 or newer section of your build matrix. It should be in the same
build in your build matrix as your docs build, as it reuses that.

Another suggestion: If you use Sphinx, add

.. code::

   html: SPHINXOPTS += -W

to your Sphinx ``Makefile``. This will make Sphinx error even if there are
warnings, keeping your docs more accurate.

**Note: Doctr does not require Sphinx. It will work with deploying anything to
GitHub pages.** However, if you do use Sphinx, doctr will find your Sphinx
docs automatically (otherwise use ``doctr deploy --built-docs <DOCS PATH>``).

FAQ
---

- **Why did you build this?**

  Deploying to GitHub pages from Travis is not amazingly difficult, but it's
  difficult enough that we wanted to write the code to do it once. We found
  that Travis docs uploading scripts are cargo culted and done in a way that
  is difficult to reproduce, especially the do-once steps of setting up keys.
  The ``doctr configure`` command handles key generation automatically, and
  tells you everything you need to do to set Doctr up. It is also completely
  self-contained (it does not depend on the ``travis`` Ruby gem).  The ``doctr
  deploy`` command handles key decryption (for deploy keys) and hiding tokens
  from the command output (for personal access tokens).

  Furthermore, most Travis deploy guides that we've found recommend setting up
  a GitHub personal access token to push to GitHub pages. GitHub personal
  access tokens grant read/write access to all public GitHub repositories for
  a given user. A more secure way is to use a GitHub deploy key, which grants
  read/write access only to a single repository. Doctr creates a GitHub deploy
  key by default (although the option to use a token exists if you know what
  you are doing).

- **Why not Read the Docs?**

  Read the Docs is great, but it has some limitations:

  - You are limited in what you can install in Read the Docs. Travis lets you
    run arbitrary code, which may be necessary to build your documentation.

  - Read the Docs deploys to readthedocs.io. Doctr deploys to GitHub pages.
    This is often more convenient, as your docs can easily sit alongside other
    website materials for your project on GitHub pages.

  In general, you should already be building your docs on Travis anyway (to
  test that they build), so it seems natural to deploy them from there.

- **Why does Doctr require Python 3.5 or newer?**

  There are several language features of Python that we wanted to make use of
  that are not available in earlier versions of Python, such as `keyword-only
  arguments <https://www.python.org/dev/peps/pep-3102/>`_,
  `subprocess.run
  <https://docs.python.org/3/library/subprocess.html#subprocess.run>`_, and
  `recursive globs <https://docs.python.org/3/library/glob.html>`_. These
  features help keep the Doctr code cleaner and more maintainable.

  If you cannot build your documentation in Python 3, you will need to
  install Python 3.6 in Travis to run Doctr.

- **I would use this, but it's missing a feature that I want.**

  Doctr is still very new. We welcome all `feature requests
  <https://github.com/drdoctr/doctr/issues>`_ and `pull requests
  <https://github.com/drdoctr/doctr/pulls>`_.

- **Why is it called Doctr?**

  Because it deploys **doc**\ umentation from **Tr**\ avis. And it makes you
  feel good.

Projects using Doctr
--------------------

- `SymPy <http://www.sympy.org/en/index.html>`_

- `conda <http://conda.pydata.org/docs/>`_

- `doctr <https://drdoctr.github.io/doctr/>`_

- `PyGBe <https://barbagroup.github.io/pygbe/docs/>`_

- `xonsh <http://xon.sh>`_

Are you using doctr?  Please add your project to the list!
