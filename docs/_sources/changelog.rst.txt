=================
 Doctr Changelog
=================

1.6.2 (2017-10-20)
==================

Minor Changes
-------------

- Fix some typos in the ``doctr configure`` output. Thanks :user:`bnaul` and
  :user:`ocefpaf`. (:issue:`261` and :issue:`260`)
- Fix the retry logic for pushing. (:issue:`265`)
- Better messaging when doctr fails because of an error from a command.
  (:issue:`263`)
- Fix an error when ``--command`` makes changes to a file that isn't synced,
  and no synced files are actually changed. Note, currently, if ``--command``
  adds or changes any files that aren't the new ones that are synced, they
  will not be committed unless they are manually added to the index. This
  should be improved in a future version (see :issue:`267`). (:issue:`266`)

1.6.1 (2017-09-27)
==================

Minor Changes
-------------

- Revert the change to ``--command`` from 1.6.0 that makes it run on the
  original branch. If you want to run a command on the original branch, just
  run it before running doctr. ``--command`` now runs on the deploy branch, as
  it did before. This does not revert the other change to ``--command`` from
  1.6.0 (running with ``shell=True``). (:issue:`259`)

1.6.0 (2017-09-26)
==================

Major Changes
-------------

- Fix pushing to .github.io repos (thanks :user:`danielballan`). (:issue:`190`)
- Run ``--command`` on the original branch, not the deploy branch.
  (:issue:`192`)
- Run ``--command`` with ``shell=True``. (:issue:`193`)
- Fix ``doctr configure`` for 2-factor authentication from SMS (thanks
  :user:`techgaun`). (:issue:`203`)
- Copy ``--built-docs`` to a temporary directory before syncing. Fixes syncing
  of committed files. (:issue:`215`)
- Only set the git username and password on Travis if they aren't set already.
  (:issue:`216`)
- Guess the repo automatically in ``doctr configure``. (:issue:`217`)
- Use ``git stash`` instead of ``git reset --hard`` on Travis. Fixes syncing
  tracked files with changes. (:issue:`219`)
- Automatically retry on failure in Travis. Fixes race conditions from pushing
  from concurrent builds. (:issue:`222`)
- Use the "ours" merge strategy on merge. This should avoid issues when there
  are merge conflicts on gh-pages from other non-doctr commits. (:issue:`232`)
- Allow ``--built-docs`` to be a file. (:issue:`252`)

Minor Changes
-------------

- Improve instructions (thanks :user:`choldgraf`). (:issue:`186`)
- Skip GitHub tests if no API token is present (:issue:`187`)
- Invalid input won't kill ``doctr configure`` but will instead prompt again for valid
  input. Prevents users from having to go through the whole login rigamarole
  again. (:issue:`181`, :issue:`188`)
- Make it clearer in the docs that doctr isn't just for Sphinx. (:issue:`196`)
- Print a red error message when doctr fails. (:issue:`239`)
- Fix some rendering in the docs (thanks :user:`CJ-Wright`). (:issue:`249`)
- Fix out of order command output (except when doctr uses a token). Also,
  print doctr commands in blue. (:issue:`250`)

1.5.3 (2017-04-07)
==================
- Fix for ``doctr configure`` crashing (:issue:`179`)

1.5.2 (2017-03-29)
==================
- Fix for bug that prevented deploying using ``no-require-master``

1.5.1 (2017-03-17)
==================
- Fix for critical bug that allowed pushing docs from any branch. (:issue:`160`)

1.5.0 (2017-03-15)
==================
- The ``--gh-pages-docs`` flag of ``doctr deploy`` has been deprecated.
  Specify the deploy directory like ``doctr deploy .`` or ``doctr deploy docs``.
  There is also no longer a default deploy directory. (:issue:`128`)
- ``setup_GitHub_push`` now takes a ``branch_whitelist`` parameter instead of
  of a ``require_master``
- ``.travis.yml`` can be used to store some of doctr configuration in addition
  to the command line flags. Write doctr configuration under the ``doctr`` key.
  (:issue:`137`)
- All boolean command line flags now have a counterpart that can overwrite
  the config values set in ``.travis.yml``
- ``doctr`` can now deploy to organization accounts (``github.io``)
  (:issue:`25`)
- Added ``--deploy-branch-name`` flag to specify which branch docs will be
  deployed to

1.4.1 (2017-01-11)
==================
- Fix Travis API endpoint when checking if a repo exists. (:issue:`143`)
- Add warnings about needing ``set -e`` in ``.travis.yml``. (:issue:`146`)
- Explicitly pull from ``doctr_remote`` on Travis. (:issue:`147`)
- Don't attempt to push ``gh-pages`` to the remote when pushing is disallowed
  (e.g., on a pull request). (:issue:`150`)
- ``doctr configure`` now deletes the public key automatically. (:issue:`151`)

1.4.0 (2016-11-11)
==================

- Set the git ``user.email`` configuration option. This is now required by the
  latest versions of git. (:issue:`138`, :issue:`139`)
- Add more information to the automated commit messages. (:issue:`134`)
- Run doctr tests on Travis with a personal access token, avoiding rate
  limiting errors. (:issue:`133`)
- Run all doctr steps except for the push on every build. Add ``--no-push``
  option. Thanks :user:`Carreau`. (:issue:`125`, :issue:`126`, :issue:`132`)
- Clarify in docs that doctr is not just for Sphinx. (:issue:`129`,
  :issue:`130`)
- Use the latest version of sphinxcontrib.autoprogram to build the doctr docs.
  (:issue:`127`)
- Check that the build repo exists on Travis. (:issue:`114`, :issue:`123`)

1.3.3 (2016-09-20)
==================

- Add support for private GitHub repositories using travis-ci.com (thanks
  :user:`dan-blanchard`). (:issue:`121`)
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
- Add link to GitHub docs for branch protection (thanks :user:`willingc`). (:issue:`100`)

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
