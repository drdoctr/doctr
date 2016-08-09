=================
 Doctr Changelog
=================

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
