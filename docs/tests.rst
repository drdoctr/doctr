=========================
 Notes for testing doctr
=========================

GitHub Test Authentication
--------------------------

Many of the ``doctr`` tests in ``doctr/tests/test_local.py`` contact GitHub to
check that invalid repo names raise errors, etc. However, the GitHub API has a
hard limit of 60 requests / hour for unauthenticated requests and it is very
easy to run over this when pushing many changes.

In order to avoid this limit, there is a GitHub Personal Access Token stored in
the ``doctr`` Travis account that is available as the environment variable
``$TESTING_TOKEN``.

To regenerate / change this token, first go to `GitHub Settings
<https://github.com/settings/tokens>`_ and create a Personal Access Token. Make
sure that all of the checkboxes are unchecked (this token should only have
privileges to check in with the GitHub API).

You can add the updated token to Travis on the `doctr Travis Settings Page
<https://travis-ci.org/drdoctr/doctr/settings>`_.

Paste the token string into the ``Value`` field and ``TESTING_TOKEN`` in the
``Name`` field (unless you have changed this value in
``doctr/tests/test_local.py``).

travis-ci.com cs. travis-ci.org
-------------------------------

Travis CI is `migrating
<https://blog.travis-ci.com/2018-05-02-open-source-projects-on-travis-ci-com-with-github-apps>`_
from .org to .com. While the migration is in place, it is possible to enable a
repository on both. However, the same repository on each will have different
public keys. Doctr presently only supports one at a time. On Travis itself,
there is little difference in the doctr code, but there is a lot of code in
``configure`` to automatically determine which is enabled.

The repos:

- https://github.com/drdoctr/testing-travis-ci-com
- https://github.com/drdoctr/testing-travis-ci-org
- https://github.com/drdoctr/testing-travis-ci-both
- https://github.com/drdoctr/testing-travis-ci-neither

Are enabled on Travis CI .com, .org, both, and neither. To enable a repo on
.org, go to https://travis-ci.org/organizations/drdoctr/repositories and make
sure it is checked. To enable a repo on .com, go to the `Travis CI Apps
settings
<https://github.com/organizations/drdoctr/settings/installations/272524>`_ on
GitHub, and make sure "only selected repositories" is enabled with those repos
that should be enabled.

There are automated tests in the test suite that check the function that
determines which of .org/.com it is enabled on, which test against these repos
(``test_check_repo_exists_org_com``).

Private Repositories
--------------------

Doctr also supports private repositories on GitHub. GitHub allows free private
repositories, but they must be made on a user account, not the ``drdoctr``
org.

To build a private repo, you have to use travis-ci.com. The free plan only
allows 100 builds, so you might have to make a new user to continue testing.
Unless we get a paid plan, testing should only be done manually, when
necessary.

GitHub does not allow GitHub pages on private repositories on the free plan,
but you can just manually verify that things are pushed to the ``gh-pages``
branch.
