Doctr
=====

A tool for automatically deploying docs from Travis CI to GitHub pages.

Doctr helps deploy things to GitHub pages from Travis CI by managing the
otherwise complicated tasks of generating, encrypting, managing SSH deploy
keys, and syncing files to the ``gh-pages`` branch. Doctr was originally
designed for documentation, but it can be used to deploy any kind of website
to GitHub pages that can be built on Travis CI. For example, you can use doctr
to deploy a `blog
<http://www.asmeurer.com/blog/posts/automatically-deploying-this-blog-to-github-pages-with-travis-ci/>`_
or website that uses a `static site generator <https://www.staticgen.com/>`_.

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

Run doctr configure
~~~~~~~~~~~~~~~~~~~

First use doctr to generate the necessary key files so that travis can push
to your gh-pages (or other) branch.

Run

.. code::

   doctr configure

and enter your data. You will need your GitHub username and password, and the
repo organization / name for which you want to build the docs.

**Note**: That repo should already be set up with Travis. We recommend enabling
`branch protection <https://help.github.com/articles/about-protected-branches/>`_
for the ``gh-pages`` branch and other branches, as the deploy key
used by doctr has the ability to push to any branch in your repo.

Edit your travis file
~~~~~~~~~~~~~~~~~~~~~

Doctr will output a bunch of text as well as instructions for next steps. You
need to edit your ``.travis.yml`` with this text. It contains the secure key
that lets travis communicate with your github repository, as well as the
code to run (in ``script:``) in order to build the docs and deploy doctr.

Your ``.travis.yml`` file should look something like this:

.. code:: yaml

   # doctr requires python >=3.5
   language: python
   python:
     - 3.6

   # This gives doctr the key we've generated
   sudo: false
   env:
     global:
       secure: "<your secure key from doctr here>"

   # This is the script to build the docs on travis, then deploy
   script:
     - set -e
     - pip install doctr
     - cd docs
     - make html
     - cd ..
     - doctr deploy . --built-docs path/to/built/html/

See `the travis config file
<https://github.com/drdoctr/doctr/blob/master/.travis.yml>`_ used by Doctr itself for example.

   **Note:** You can deploy ``doctr`` to a different folder by giving it a different path
   in the call to ``deploy``. E.g., ``doctr deploy docs/``.

   **Warning:** Be sure to add ``set -e`` in ``script``, to prevent ``doctr`` from  running
   when the docs build fails.

   **Warning:** Put ``doctr deploy .`` in the ``script`` section of your ``.travis.yml``. If
   you use ``after_success``, it will `not cause
   <https://docs.travis-ci.com/user/customizing-the-build#Breaking-the-Build>`_
   the build to fail.

Commit your new files and build your site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``doctr configure`` will create a new file that contains your key. Commit this as
well as the changes to ``.travis.yml``. Once you push to github, travis should
now automatically build your documentation and deploy it.

Notes
-----

**Doctr requires Python 3.5 or newer.** Be sure to run it in a
Python 3.5 or newer section of your build matrix. It should be in the same
build in your build matrix as your docs build, as it reuses that.

**Doctr does not require Sphinx.** It will work with deploying anything to
GitHub pages. However, if you do use Sphinx, doctr will find your Sphinx
docs automatically (otherwise use ``doctr deploy . --built-docs <DOCS PATH>``).

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
