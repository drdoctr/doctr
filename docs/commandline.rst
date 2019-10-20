=========================
 Doctr Command Line Help
=========================

.. autoprogram:: doctr.__main__:get_parser()
   :prog: doctr


Deployment Procedure
--------------------

Starting from a checkout of a white-listed branch on Travis, with the
documentation having been built successfully, ``doctr deploy`` takes the
following steps:

* copy the ``BUILT_DOCS`` directory to a temporary location
* stash the current checkout
* check out the ``DEPLOY_BRANCH_NAME`` (default ``gh-pages``) on the
  ``DEPLOY_REPO`` (current repo, by default)
* "Synchronize":
   - if there is a file ``.doctr-files`` in the ``deploy_directory``, remove all
     files listed therein (excluding ``EXCLUDE``)
   - copy all files from the (copied) ``BUILT_DOCS`` directory to the
     ``deploy_directory`` (excluding ``EXCLUDE``)
   - create a new ``.doctr-files`` log that contains all files of the previous
     ``.doctr-files``, minus those removed, plus those added. That is, a list
     of all files in the ``deploy_directory`` that exist due to ``doctr``
* run ``COMMAND`` if ``--command`` was given
* run ``git add`` for any files that were added during synchronization, and
  ``git rm`` for any files that were removed
* commit and push the ``DEPLOY_BRANCH_NAME``
* switch back to the original checkout and un-stash

As a result of the above procedure, if ``COMMAND`` creates any new files that
were not present during the synchronization, it must ``git add`` those
files for them to be committed later.


Configuration
-------------

In addition to command line arguments you can configure ``doctr`` using the
``.travis.yml`` files. Command line arguments take precedence over the value
present in the configuration file.

The configuration parameters available from the ``.travis.yml`` file mirror
their command line siblings except doubledashes ``--`` and ``--no-`` prefix are
dropped.

Use a ``doctr`` section in your ``travis.yml`` file to store your doctr
configuration:

.. code:: yaml

  - language: python
  - script:
      - set -e
      - py.test
      - cd docs
      - make html
      - cd ..
      - doctr deploy .
  - doctr:
      - key-path : 'path/to/key/from/repo/root/path.key'
      - deploy-repo : 'myorg/myrepo'


The following options are available from the configuration file and not from
the command line:

``branches``:
  A list of regular expression that matches branches on which ``doctr`` should
  still deploy the documentation. For example ``.*\.x`` will deploy all
  branches like ``3.x``, ``4.x`` ...

