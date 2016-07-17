# Travis docs builder

A tool for automatically building Sphinx docs on Travis CI, and deploying them
to GitHub pages.

This tool is still a work in progress, but once it works it's going to be
awesome.

## Usage (this will change)

Run

    ./travis_docs_builder.py

and enter your data. You will need your GitHub username and password, and the
repo you want to build the docs for.

That repo should already be setup with Travis. Additionally, you should enable
GitHub pages for the repo. Create a `gh-pages` branch (ideally an empty one
**Note: if you do it on GitHub it will do it based on `master`**). Go to
https://github.com/<your repo>/settings and enable GitHub pages. You may also
want to enable branch protection for the `gh-pages` branch and other branches,
so that this script can't accidentally screw you.

Then add the stuff to your `.travis.yml`. The command above will tell you a
secure key to add. You should also have something like

``` yaml
language: python
python:
  - 3.5

sudo: false
env:
  global:
    secure: "<your secure key from ./travis_docs_builder.py here>"

script:
  - pip install requests cryptography sphinx
  - cd docs
  - make html
  - cd ..
  - ./travis_docs_builder.py <your repo name>
```

in your `.travis.yml`. See [the one](.travis.yml) in this repo for example.

**Heads up:** This script requires Python 3.5 or newer. Be sure to run it in a
Python 3.5 or newer section of your build matrix. It should be in the same
build in your build matrix as your docs build, as it reuses that.

Another suggestion: Add

    html: SPHINXOPTS += -W


to your Sphinx `Makefile`. This will make Sphinx error even if there are
warnings, keeping your docs more accurate.
