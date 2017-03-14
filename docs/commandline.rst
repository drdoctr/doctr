=========================
 Doctr Command Line Help
=========================

.. autoprogram:: doctr.__main__:get_parser()
   :prog: doctr


Configuration
-------------

In addition to command line arguments you can configure ``doctr`` using the
``.travis.yml`` files. Command line arguments take precedence over the value
present in the configuration file.

The configuration parameters available from the ``.travis.yml`` file mirror
their command line siblings except doubledashes ``--`` and ``--no-`` prefix are
dropped.

Use a ``doctr`` section in your ``travis.yml`` file to store your doctr
configuration:

.. code:: yaml

  - language: python
  - script:
      - set -e
      - py.test
      - cd docs
      - make html
      - cd ..
      - doctr deploy .
  - doctr:
      - key-path : 'path/to/key/from/repo/root/path.key'
      - deploy-repo : 'myorg/myrepo'


The following options are available from the configuration file and not from
the command line:

``branches``:
  A list of regular expression that matches branches on which ``doctr`` should
  still deploy the documentation. For example ``.*\.x`` will deploy all
  branches like ``3.x``, ``4.x`` ...

