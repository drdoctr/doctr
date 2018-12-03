.. _recipes:

=========
 Recipes
=========

Here are some useful recipes for Doctr.

.. _any-branch:

Deploy docs from any branch
===========================

.. role:: raw-html(raw)
   :format: html

By default, Doctr only deploys docs from the ``master`` branch, but it can be
useful to deploy docs from other branches, to test them out.

The branch name on Travis is stored in the ``$TRAVIS_BRANCH`` environment
variable. One suggestion would be to deploy the docs to a special directory
for each branch. The following will deploy the docs to ``docs`` on master and
:raw-html:`<code>docs-<i>branch</i></code>` on *branch*.

.. code:: yaml

   - if [[ "${TRAVIS_BRANCH}" == "master" ]]; then
       doctr deploy docs;
     else
       doctr deploy --no-require-master "docs-$TRAVIS_BRANCH";
     fi

This will not remove the docs after the branch is merged. You will need to do
that manually.

.. TODO: How can we add steps to do that automatically?

**Note**: It is only possible to deploy docs from branches on the same repo.
For security purposes, it is not possible to deploy from branches on forks
(Travis does not allow access to encrypted environment variables on pull
requests from forks). If you want to deploy the docs for a branch from a pull
request, you will need to push it up to the main repository.

.. _non-master-branch:

Deploy docs from a non-master branch
====================================

If you want to deploy docs from only specific branches other than just
``master``, you can use the ``--branch-whitelist`` flag. This is useful if
your default branch is named something other than ``master``. The default
``--branch-whitelist`` is ``master``. ``--branch-whitelist`` can take any
number of arguments, so it should generally go last in your ``doctr deploy``
call.

.. code:: yaml

   - doctr deploy --built-docs build/ . --branch-whitelist develop

.. _recipe-tags:

Deploy docs from git tags
=========================

Travis CI runs separate builds for git tags that are pushed to your repo. By
default, doctr does not deploy on these builds, but it can be enabled with the
``--build-tags`` flag to ``doctr deploy``. This is useful if you want to use
doctr to deploy versioned docs for releases, for example.

On Travis CI, the tag is set to the environment variable ``$TRAVIS_TAG``,
which is empty otherwise. The following will deploy the docs to ``dev`` for
normal ``master`` builds, and ``version-<TAG NAME>`` for tag builds:

.. code:: yaml

  - if [[ -z "$TRAVIS_TAG" ]]; then
      DEPLOY_DIR=dev;
    else
      DEPLOY_DIR="version-$TRAVIS_TAG";
    fi
  - doctr deploy --build-tags --built-docs build/ $DEPLOY_DIR

If you want to deploy only on a tag, use ``--branch-whitelist`` with no
arguments to tell doctr to not deploy from any branch. For instance, to deploy
only tags to ``latest``:

.. code:: yaml

   - doctr deploy latest --built-docs build/ --build-tags --branch-whitelist

Deploy to a separate repo
=========================

By default, Doctr deploys to the ``gh-pages`` branch of the same repository it
is run from, but you can deploy to the ``gh-pages`` branch of any repository.

To do this, specify a separate deploy and build repository when running
``doctr configure`` (it will ask you for the two separately). You will need
admin access to the deploy repository to upload the deploy key (``doctr
configure`` will prompt you for your GitHub credentials). If you do not have
access, you can run ``doctr configure --no-upload-key``. This will print out the
public deploy key, which you can then give to someone who has admin access to
add to the form on GitHub (``doctr configure`` will print the public key and
the url of the form for someone with admin access to paste it in).

In your ``.travis.yml``, specify the deploy repository with

.. code:: yaml

   - doctr deploy --deploy-repo <deploy repo> deploy_dir

The instructions from ``doctr configure`` will also give you the correct
command to run.

Setting up Doctr for a repo you don't have admin access to
==========================================================

``doctr configure`` by default asks for your GitHub credentials so that it can
upload the deploy key it creates. However, if you do not have admin access to
the repository you are deploying to, you cannot upload the deploy key.

No worries, you can still help. Run

.. code:: bash

   doctr configure --no-upload-key

This will set up doctr, but not require any GitHub credentials. Follow the
instructions on screen. Create a new branch, commit the
``github_deploy_key_org_repo.enc`` file, and edit ``.travis.yml`` to include the
encrypted environment variable and the call to ``doctr deploy``.

Then, create a pull request to the repository. Tell the owner of the
repository to add the public key which Doctr has printed as a deploy key for
the repo (Doctr will also print the url where they can add this). Don't worry,
the key is a public SSH key, so it's OK to post it publicly in the pull
request.

Post-processing the docs on gh-pages
====================================

Sometimes you may want to post-process your docs on the ``gh-pages`` branch.
For example, you may want to add some links to other versions in your
index.html.

You can run any command on the ``gh-pages`` branch with the ``doctr deploy
--command`` flag. This is run after the docs are synced to ``gh-pages`` but
before they are committed and uploaded.

For example, if you have a script in ``gh-pages`` called ``post-process.py``,
you can run

.. code:: bash

   doctr deploy --command 'post-process.py' deploy_dir

Using a separate command to deploy to gh-pages
==============================================

If you already have an existing tool to deploy to ``gh-pages``, you can still
use Doctr to manage your deploy key. Use

.. code:: bash

   doctr deploy --no-sync --command 'command to deploy' deploy_dir

The command to deploy should add any files that you want committed to the
index.

.. _recipe-wikis:

Deploying to a GitHub wiki
==========================

Doctr supports deploying to GitHub wikis. Just use ``org/repo.wiki`` when
as the deploy repo running ``doctr configure``. When deploying, use

.. code:: bash

   doctr deploy --deploy-repo org/repo.wiki .

The deploy key for pushing to a wiki is the same as for pushing to the repo
itself, so if you are pushing to both, you will not need more than one deploy
key.

.. _recipe-github-io:

Using doctr with ``*.github.io`` pages
======================================

Github allows users to create pages at the root URL of users' or
organizations' http://github.io pages. For example, an organization
``coolteam`` can setup a repository at
``https://github.com/coolteam/coolteam.github.io`` and the html files in the
``master`` branch of this repository will be served to
``https://coolteam.github.io``.

With doctr, it is necessary to separate the website source files, e.g. input to
a static site generator, from the output HTML files into two different
branches. The output files must be stored in the ``master`` branch, as per
Github's specification. The source files can be stored in another custom branch
of your choosing, below the name ``source`` is chosen.

To do this:

1. Create a new branch for the source files, e.g. named ``source``, and push
   this to Github.
2. Set this branch as the default branch in the Github settings for the
   repository.
3. Run the ``doctr configure`` command in the ``source`` branch. The source and
   output repositories should both be set to ``coolteam/coolteam.github.io`` in
   the configuration options.
4. Commit the generated encryption key and the ``.travis.yml`` file to the
   ``source`` branch. Do not commit a ``.travis.yml`` file to both the
   ``master`` and ``source`` branches, as this will also cause and infinite
   loop of Travis builds.
5. Lastly, in ``.travis.yml`` make sure that the ``doctr deploy`` command white
   lists the ``source`` branch, like so:

.. code:: bash

   doctr deploy --branch-whitelist source  --built-docs output-directory/ .

The source files should only be pushed to the ``source`` branch and all output
files will be pushed to the ``master`` branch during the Travis builds.
