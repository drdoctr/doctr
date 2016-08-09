=================
 Doctr Changelog
=================

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
