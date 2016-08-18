=================
 Doctr Changelog
=================

1.2 (????-??-??)
================

Major Changes
-------------
- Allow --gh-pages-docs to be ``.`` (the root directory). (#73)
- Allow deploying to a separate repo (via ``doctr deploy --deploy-repo``). (#63)
- Automatically detect Sphinx build directory. (#6)
- Add ``--no-require-master`` flag to allow pushing from branches other than master. (#70)

Minor Changes
-------------
- Add a GitHub banner to the docs. (#64)
- Move to the GitHub organization `drdoctr <https://github.com/drdoctr>`_. (#67)

1.1.1 (2016-08-09)
==================

Minor Changes
-------------

- Add installation instructions to the documentation. (#60)
- Fix some lingering "Travis docs builder" -> "Doctr", including in the git
  attributes on Travis. (#60)
- Better error message when the repo doesn't exist in doctr configure. (#59)
- Indicate that repo should be org/reponame in doctr configure. (#59)

1.1 (2016-08-09)
================

Major Changes
-------------

- Add a real command line interface with argparse. (#23)
- Split the command line into ``doctr configure`` and ``doctr deploy``. (#28)
- Add support for using GitHub deploy keys (now the default) (#30)

Minor Changes
-------------

- Add flags to ``doctr deploy`` to change the build and deploy locations of
  the docs. (#52)
- Print more helpful instructions from ``doctr configure``. (#46)
- Add more documentation. (#47)

1.0 (2016-07-22)
================

Major Changes
-------------

- First release. Basic support for configuring doctr to push to Travis (using
  a token) and deploying to gh-pages from Travis.
