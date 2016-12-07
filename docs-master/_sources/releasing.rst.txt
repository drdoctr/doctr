Releasing
---------

Here is how to do a release:

- Create a release branch (branch protection makes it impossible to push
  directly to master, so you have to release from a branch). I recommend
  naming the branch something other than the release number, as that makes the
  below commands not work until you delete the branch.
- Update ``docs/changelog.rst``. Add the release date.
- Make a pull request with the release branch.
- Make sure all the Travis checks pass on the commit you plan to tag.
- Tag the release. The tag name should be the version number of the release,
  like ``git tag 2.0 -a``. Include the ``-a`` flag. This will ask for some
  commit message for the tag (you can just use something like "Doctr 2.0
  release", or you can put the changelog in there if you want).
- Do ``python setup.py sdist upload``. It uses the tag to get the version number, so
  you need to do this after you tag.
- Push up the tag (``git push origin 2.0``).
- Merge the pull request.
- Create a pull request to the `conda-forge feedstock
  <https://github.com/conda-forge/doctr-feedstock>`_ to update it. Make sure
  to do a pull request from a fork. Merge it once those tests pass.
