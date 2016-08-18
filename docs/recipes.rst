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

**Note**: It is only possible to deploy docs from branches on the same repo.
For security purposes, it is not possible to deploy from branches on forks
(Travis does not allow access to encrypted environment variables on pull
requests from forks). If you want to deploy the docs for a branch from a pull
request, you will need to push it up to the main repository.
