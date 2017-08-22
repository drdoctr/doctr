=========
 Recipes
=========

Here are some useful recipes for Doctr.

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
       doctr deploy --gh-pages-docs docs;
     else
       doctr deploy --no-require-master --gh-pages-docs "docs-$TRAVIS_BRANCH";
     fi

This will not remove the docs after the branch is merged. You will need to do
that manually.

.. TODO: How can we add steps to do that automatically?

**Note**: It is only possible to deploy docs from branches on the same repo.
For security purposes, it is not possible to deploy from branches on forks
(Travis does not allow access to encrypted environment variables on pull
requests from forks). If you want to deploy the docs for a branch from a pull
request, you will need to push it up to the main repository.

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

   - doctr deploy --deploy-repo <deploy repo>

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
``github_deploy_key.enc`` file, and edit ``.travis.yml`` to include the
encrypted environment variable and the call to ``doctr deploy``.

Then, create a pull request to the repository. Tell the owner of the
repository to add the public key which doctr has printed as a deploy key for
the repo (doctr will also print the url where they can add this). Don't worry,
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

   doctr deploy --command 'post-process.py'

Using a separate command to deploy to gh-pages
==============================================

If you already have an existing tool to deploy to ``gh-pages``, you can still
use Doctr to manage your deploy key. Use

.. code:: bash

   doctr deploy --no-sync --command 'command to deploy'

The command to deploy should add any files that you want committed to the
index.
