=================
 Doctr Changelog
=================

1.4.0 (2016-11-11)
==================

- Set the git ``user.email`` configuration option. This is now required by the
  latest versions of git. (:issue:`138`, :issue:`139`)
- Add more information to the automated commit messages. (:issue:`134`)
- Run doctr tests on Travis with a personal access token, avoiding rate
  limiting errors. (:issue:`133`)
- Run all doctr steps except for the push on every build. Add ``--no-push``
  option. Thanks @Carreau. (:issue:`125`, :issue:`126`, :issue:`132`)
- Clarify in docs that doctr is not just for Sphinx. (:issue:`129`,
  :issue:`130`)
- Use the latest version of sphinxcontrib.autoprogram to build the doctr docs.
  (:issue:`127`)
- Check that the build repo exists on Travis. (:issue:`114`, :issue:`123`)

1.3.3 (2016-09-20)
==================

- Add support for private GitHub repositories using travis-ci.com (thanks
  @dan-blanchard). (:issue:`121`)
- Add a list of projects using doctr to the docs. (:issue:`116`)
- Use the sphinx-issues extension in the changelog. (:issue:`99`)
- Swap "description" and "long_description" in setup.py. (:issue:`120`)

1.3.2 (2016-09-01)
==================

Major Changes
-------------

- Fix the --built-docs option. (:issue:`111`)

Minor Changes
-------------

- Get the setup.py description from the README. (:issue:`103`)
- Add link to GitHub docs for branch protection (thanks @willingc). (:issue:`100`)

1.3.1 (2016-08-31)
==================

Major Changes
-------------

- Fix a bug that would cause doctr to fail if run on a pull request from a
  fork. (:issue:`101`)

1.3 (2016-08-30)
================

Major Changes
-------------

- Remove the ``--tmp-dir`` flag from the command line (doctr now always
  deploys using a log file). (:issue:`92`)
- Python API: Change ``commit_docs`` to actually commit the docs (previously,
  it was done in ``push_docs``). (:issue:`92`)
- Python API: Don't sync files or get the build dir in ``commit_docs``. This
  is done separately in ``__main__.py``. The Python API for ``commit_docs`` is
  now ``commit_docs(*, added, removed)``. (:issue:`92`)
- Python API: ``sync_from_log`` automatically includes the log file in the list of added
  files. (:issue:`92`)
- Support running doctr multiple times in the same build. (:issue:`93`, :issue:`95`)
- Add ``doctr deploy --command`` to allow running a command before committing
  and deploying. (:issue:`97`)
- Add ``doctr deploy --no-sync`` to allow disabling syncing (useful with
  ``doctr deploy --command``). (:issue:`97`)

Minor Changes
-------------

- Correctly commit the log file. (:issue:`92`)
- Fix sync_from_log to create dst if it doesn't exist, and add tests for this. (:issue:`92`)
- Don't assume that doctr is being run from master when creating gh-pages. (:issue:`93`)
- Return to the previous branch after deploying. (:issue:`93`)
- Remove extra space before options in configure help text. (:issue:`90`)

1.2 (2016-08-29)
================

Major Changes
-------------
- Allow ``--gh-pages-docs .`` (deploying to the root directory of the
  ``gh-pages`` branch). (:issue:`73`)
- Allow deploying to a separate repo (via ``doctr deploy --deploy-repo <repo>``). (:issue:`63`)
- Automatically detect Sphinx build directory. (:issue:`6`)
- Add ``--no-require-master`` flag to allow pushing from branches other than master. (:issue:`70`)

Minor Changes
-------------
- Add a GitHub banner to the docs. (:issue:`64`)
- Move to the GitHub organization `drdoctr <https://github.com/drdoctr>`_. (:issue:`67`)
- Check if user/org and repo are valid before generating ssh keys or pinging Travis. (:issue:`87`)
- Various improvements to documentation.
- Various improvements to error checking.

1.1.1 (2016-08-09)
==================

Minor Changes
-------------

- Add installation instructions to the documentation. (:issue:`60`)
- Fix some lingering "Travis docs builder" -> "Doctr", including in the git
  attributes on Travis. (:issue:`60`)
- Better error message when the repo doesn't exist in doctr configure. (:issue:`59`)
- Indicate that repo should be org/reponame in doctr configure. (:issue:`59`)

1.1 (2016-08-09)
================

Major Changes
-------------

- Add a real command line interface with argparse. (:issue:`23`)
- Split the command line into ``doctr configure`` and ``doctr deploy``. (:issue:`28`)
- Add support for using GitHub deploy keys (now the default) (:issue:`30`)

Minor Changes
-------------

- Add flags to ``doctr deploy`` to change the build and deploy locations of
  the docs. (:issue:`52`)
- Print more helpful instructions from ``doctr configure``. (:issue:`46`)
- Add more documentation. (:issue:`47`)

1.0 (2016-07-22)
================

Major Changes
-------------

- First release. Basic support for configuring doctr to push to Travis (using
  a token) and deploying to gh-pages from Travis.
