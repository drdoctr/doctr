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
