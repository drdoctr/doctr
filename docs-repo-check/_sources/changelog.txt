=================
 Doctr Changelog
=================

1.3.2 (2016-09-01)
==================

Major Changes
-------------

- Fix the --built-docs option. (#111)

Minor Changes
-------------

- Get the setup.py description from the README. (#103)
- Add link to GitHub docs for branch protection (thanks @willingc). (#100)

1.3.1 (2016-08-31)
==================

Major Changes
-------------

- Fix a bug that would cause doctr to fail if run on a pull request from a
  fork. (#101)

1.3 (2016-08-30)
================

Major Changes
-------------

- Remove the ``--tmp-dir`` flag from the command line (doctr now always
  deploys using a log file). (#92)
- Python API: Change ``commit_docs`` to actually commit the docs (previously,
  it was done in ``push_docs``). (#92)
- Python API: Don't sync files or get the build dir in ``commit_docs``. This
  is done separately in ``__main__.py``. The Python API for ``commit_docs`` is
  now ``commit_docs(*, added, removed)``. (#92)
- Python API: ``sync_from_log`` automatically includes the log file in the list of added
  files. (#92)
- Support running doctr multiple times in the same build. (#93, #95)
- Add ``doctr deploy --command`` to allow running a command before committing
  and deploying. (#97)
- Add ``doctr deploy --no-sync`` to allow disabling syncing (useful with
  ``doctr deploy --command``). (#97)

Minor Changes
-------------

- Correctly commit the log file. (#92)
- Fix sync_from_log to create dst if it doesn't exist, and add tests for this. (#92)
- Don't assume that doctr is being run from master when creating gh-pages. (#93)
- Return to the previous branch after deploying. (#93)
- Remove extra space before options in configure help text. (#90)

1.2 (2016-08-29)
================

Major Changes
-------------
- Allow ``--gh-pages-docs .`` (deploying to the root directory of the
  ``gh-pages`` branch). (#73)
- Allow deploying to a separate repo (via ``doctr deploy --deploy-repo <repo>``). (#63)
- Automatically detect Sphinx build directory. (#6)
- Add ``--no-require-master`` flag to allow pushing from branches other than master. (#70)

Minor Changes
-------------
- Add a GitHub banner to the docs. (#64)
- Move to the GitHub organization `drdoctr <https://github.com/drdoctr>`_. (#67)
- Check if user/org and repo are valid before generating ssh keys or pinging Travis. (#87)
- Various improvements to documentation.
- Various improvements to error checking.

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
