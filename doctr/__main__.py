"""
doctr

A tool to automatically deploy docs to GitHub pages from Travis CI.

The doctr command is two commands in one. To use, first run::

    doctr configure

on your local machine. This will prompt for your GitHub credentials and the
name of the repo you want to deploy docs for. This will generate a secure key,
which you should insert into your .travis.yml.

Then, on Travis, for the build where you build your docs, add::

    - doctr deploy . --built-docs path/to/built/html/

to the end of the build to deploy the docs to GitHub pages.  This will only
run on the master branch, and won't run on pull requests.

For more information, see https://drdoctr.github.io/doctr/docs/
"""

import sys
import os
import os.path
import argparse
import subprocess
import yaml
import json
import shlex

from pathlib import Path

from textwrap import dedent

from .local import (generate_GitHub_token, encrypt_variable, encrypt_file,
    upload_GitHub_deploy_key, generate_ssh_key, check_repo_exists,
    GitHub_login, guess_github_repo, AuthenticationFailed)
from .travis import (setup_GitHub_push, commit_docs, push_docs,
    get_current_repo, sync_from_log, find_sphinx_build_dir, run,
    get_travis_branch, copy_to_tmp, checkout_deploy_branch)

from .common import red, green, blue, bold_black, BOLD_BLACK, BOLD_MAGENTA, RESET

from . import __version__

def make_parser_with_config_adder(parser, config):
    """factory function for a smarter parser:

    return an utility function that pull default from the config as well.

    Pull the default for parser not only from the ``default`` kwarg,
    but also if an identical value is find in ``config`` where leading
    ``--`` or ``--no`` is removed.

    If the option is a boolean flag, automatically register an opposite,
    exclusive option by prepending or removing the `--no-`. This is useful
    to overwrite config in ``.travis.yml``

    Mutate the config object and remove know keys in order to detect unused
    options afterwoard.
    """

    def internal(arg, **kwargs):
        invert = {
            'store_true':'store_false',
            'store_false':'store_true',
        }
        if arg.startswith('--no-'):
            key = arg[5:]
        else:
            key = arg[2:]
        if 'default' in kwargs:
            if key in config:
                kwargs['default'] = config[key]
                del config[key]
        action = kwargs.get('action')
        if action in invert:
            exclusive_grp = parser.add_mutually_exclusive_group()
            exclusive_grp.add_argument(arg, **kwargs)
            kwargs['action'] = invert[action]
            kwargs['help'] = 'Inverse of "%s"' % arg
            if arg.startswith('--no-'):
                arg = '--%s' % arg[5:]
            else:
                arg = '--no-%s' % arg[2:]
            exclusive_grp.add_argument(arg, **kwargs)
        else:
            parser.add_argument(arg, **kwargs)

    return internal


def get_parser(config=None):
    """
    return a parser suitable to parse CL arguments.

    Parameters
    ----------

    config: dict
        Default values to fall back on, if not given.

    Returns
    -------

        An argparse parser configured to parse the command lines arguments of
        sys.argv which will default on values present in ``config``.
    """
    # This uses RawTextHelpFormatter so that the description (the docstring of
    # this module) is formatted correctly. Unfortunately, that means that
    # parser help is not text wrapped (but all other help is).
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter, epilog="""
Run --help on the subcommands like 'doctr deploy --help' to see the
options available.
        """,
        )

    if not config:
        config={}
    parser.add_argument('-V', '--version', action='version', version='doctr ' + __version__)

    subcommand = parser.add_subparsers(title='subcommand', dest='subcommand')

    deploy_parser = subcommand.add_parser('deploy', help="""Deploy the docs to GitHub from Travis.""")
    deploy_parser.set_defaults(func=deploy)
    deploy_parser_add_argument = make_parser_with_config_adder(deploy_parser, config)
    deploy_parser_add_argument('--force', action='store_true', help="""Run the deploy command even
    if we do not appear to be on Travis.""")
    deploy_parser_add_argument('deploy_directory', type=str, nargs='?',
        help="""Directory to deploy the html documentation to on gh-pages.""")
    deploy_parser_add_argument('--token', action='store_true', default=False,
        help="""Push to GitHub using a personal access token. Use this if you
        used 'doctr configure --token'.""")
    deploy_parser_add_argument('--key-path', default=None,
        help="""Path of the encrypted GitHub deploy key. The default is github_deploy_key_+
        deploy respository name + .enc.""")
    deploy_parser_add_argument('--built-docs', default=None,
        help="""Location of the built html documentation to be deployed to gh-pages. If not
        specified, Doctr will try to automatically detect build location
        (right now only works for Sphinx docs).""")
    deploy_parser.add_argument('--deploy-branch-name', default=None,
                               help="""Name of the branch to deploy to (default: 'master' for ``*.github.io``
                               and wiki repos, 'gh-pages' otherwise)""")
    deploy_parser_add_argument('--tmp-dir', default=None,
        help=argparse.SUPPRESS)
    deploy_parser_add_argument('--deploy-repo', default=None, help="""Repo to
        deploy the docs to. By default, it deploys to the repo Doctr is run from.""")
    deploy_parser_add_argument('--branch-whitelist', default=None, nargs='*',
        help="""Branches to deploy from. Pass no arguments to not build on any branch
        (typically used in conjunction with --build-tags). Note that you can
        deploy from every branch with --no-require-master.""", metavar="BRANCH")
    deploy_parser_add_argument('--no-require-master', dest='require_master', action='store_false',
        default=True, help="""Allow docs to be pushed from a branch other than master""")
    deploy_parser_add_argument('--command', default=None,
        help="""Command to be run before committing and pushing. This command
        will be run from the deploy repository/branch. If the command creates
        additional files that should be deployed, they should be added to the
        index.""")
    deploy_parser_add_argument('--no-sync', dest='sync', action='store_false',
        default=True, help="""Don't sync any files. This is generally used in
        conjunction with the --command flag, for instance, if the command syncs
        the files for you. Any files you wish to commit should be added to the
        index.""")
    deploy_parser.add_argument('--no-temp-dir', dest='temp_dir',
        action='store_false', default=True, help="""Don't copy the
        --built-docs directory to a temporary directory.""")
    deploy_parser_add_argument('--no-push', dest='push', action='store_false',
        default=True, help="Run all the steps except the last push step. "
        "Useful for debugging")
    deploy_parser_add_argument('--build-tags', action='store_true',
        default=False, help="""Deploy on tag builds. On a tag build,
        $TRAVIS_TAG is set to the name of the tag. The default is to not
        deploy on tag builds. Note that this will still build on a branch,
        unless --branch-whitelist (with no arguments) is passed.""")
    deploy_parser_add_argument('--gh-pages-docs', default=None,
        help="""!!DEPRECATED!! Directory to deploy the html documentation to on gh-pages.
        The default is %(default)r. The deploy directory should be passed as
        the first argument to 'doctr deploy'. This flag is kept for backwards
        compatibility.""")
    deploy_parser_add_argument('--exclude', nargs='+', default=(), help="""Files and
        directories from --built-docs that are not copied.""")

    if config:
        print('Warning, The following options in `.travis.yml` were not recognized:\n%s' % json.dumps(config, indent=2))

    configure_parser = subcommand.add_parser('configure', help="Configure doctr. This command should be run locally (not on Travis).")
    configure_parser.set_defaults(func=configure)
    configure_parser.add_argument('--force', action='store_true', help="""Run the configure command even
    if we appear to be on Travis.""")
    configure_parser.add_argument('--token', action="store_true", default=False,
        help="""Generate a personal access token to push to GitHub. The default is to use a
        deploy key. WARNING: This will grant read/write access to all the
        public repositories for the user. This option is not recommended
        unless you are using a separate GitHub user for deploying.""")
    configure_parser.add_argument("--no-upload-key", action="store_false", default=True,
        dest="upload_key", help="""Don't automatically upload the deploy key to GitHub. If you select this
        option, you will not be prompted for your GitHub credentials, so this option is not compatible with
        private repositories.""")
    configure_parser.add_argument('--key-path', default=None,
        help="""Path to save the encrypted GitHub deploy key. The default is github_deploy_key_+
        deploy respository name. The .enc extension is added to the file automatically.""")

    return parser

def get_config():
    """
    This load some configuration from the ``.travis.yml``, if file is present,
    ``doctr`` key if present.
    """
    p = Path('.travis.yml')
    if not p.exists():
        return {}
    with p.open() as f:
        travis_config = yaml.safe_load(f.read())

    config = travis_config.get('doctr', {})

    if not isinstance(config, dict):
        raise ValueError('config is not a dict: {}'.format(config))
    return config

def get_deploy_key_repo(deploy_repo, keypath, key_ext=''):
    """
    Return (repository of which deploy key is used, environment variable to store
    the encryption key of deploy key, path of deploy key file)
    """
    # deploy key of the original repo has write access to the wiki
    deploy_key_repo = deploy_repo[:-5] if deploy_repo.endswith('.wiki') else deploy_repo

    # Automatically determine environment variable and key file name from deploy repo name
    # Special characters are substituted with a hyphen(-) by GitHub
    snake_case_name = deploy_key_repo.replace('-', '_').replace('.', '_').replace('/', '_').lower()
    env_name = 'DOCTR_DEPLOY_ENCRYPTION_KEY_' + snake_case_name.upper()
    keypath = keypath or 'github_deploy_key_' + snake_case_name + key_ext

    return (deploy_key_repo, env_name, keypath)

def process_args(parser):
    args = parser.parse_args()

    if not args.subcommand:
        parser.print_usage()
        parser.exit(1)

    try:
        return args.func(args, parser)
    except RuntimeError as e:
        sys.exit("Error: " + e.args[0])

def on_travis():
    return os.environ.get("TRAVIS_JOB_NUMBER", '')

def deploy(args, parser):
    if not args.force and not on_travis():
        parser.error("doctr does not appear to be running on Travis. Use "
                     "doctr deploy <target-dir> --force to run anyway.")

    config = get_config()

    if args.tmp_dir:
        parser.error("The --tmp-dir flag has been removed (doctr no longer uses a temporary directory when deploying).")

    if args.gh_pages_docs:
        print("The --gh-pages-docs flag is deprecated and will be removed in the next release. Instead pass the deploy directory as an argument, e.g. `doctr deploy .`")

    if args.gh_pages_docs and args.deploy_directory:
        parser.error("The --gh-pages-docs flag is deprecated. Specify the directory to deploy to using `doctr deploy <dir>`")

    if not args.gh_pages_docs and not args.deploy_directory:
        parser.error("No deploy directory specified. Specify the directory to deploy to using `doctr deploy <dir>`")

    deploy_dir = args.gh_pages_docs or args.deploy_directory

    build_repo = get_current_repo()
    deploy_repo = args.deploy_repo or build_repo

    if args.deploy_branch_name:
        deploy_branch = args.deploy_branch_name
    else:
        deploy_branch = 'master' if deploy_repo.endswith(('.github.io', '.github.com', '.wiki')) else 'gh-pages'

    _, env_name, keypath = get_deploy_key_repo(deploy_repo, args.key_path, key_ext='.enc')

    current_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    try:
        branch_whitelist = set() if args.require_master else set(get_travis_branch())
        branch_whitelist.update(set(config.get('branches',set({}))))
        if args.branch_whitelist is not None:
            branch_whitelist.update(set(args.branch_whitelist))
            if not args.branch_whitelist:
                branch_whitelist = {'master'}

        canpush = setup_GitHub_push(deploy_repo, deploy_branch=deploy_branch,
                                     auth_type='token' if args.token else 'deploy_key',
                                     full_key_path=keypath,
                                     branch_whitelist=branch_whitelist,
                                     build_tags=args.build_tags,
                                     env_name=env_name)

        if args.sync:
            built_docs = args.built_docs or find_sphinx_build_dir()
            exclude = [os.path.relpath(i, built_docs) for i in args.exclude]
            if args.temp_dir:
                built_docs = copy_to_tmp(built_docs)
            exclude = [os.path.normpath(os.path.join(built_docs, i)) for i in exclude]

        # Reset in case there are modified files that are tracked in the
        # deploy branch.
        run(['git', 'stash', '--all'])
        checkout_deploy_branch(deploy_branch, canpush=canpush)

        if args.sync:
            log_file = os.path.join(deploy_dir, '.doctr-files')

            print("Moving built docs into place")
            added, removed = sync_from_log(src=built_docs,
                dst=deploy_dir, log_file=log_file, exclude=exclude)

        else:
            added, removed = [], []

        if args.command:
            run(args.command, shell=True)

        changes = commit_docs(added=added, removed=removed)
        if changes:
            if canpush and args.push:
                push_docs(deploy_branch)
            else:
                print("Don't have permission to push. Not trying.")
        else:
            print("The docs have not changed. Not updating")
    except BaseException as e:
        DOCTR_COMMAND = ' '.join(map(shlex.quote, sys.argv))
        print(red("ERROR: The doctr command %r failed: %r" % (DOCTR_COMMAND, e)),
            file=sys.stderr)
        raise
    finally:
        run(['git', 'checkout', current_commit])
        # Ignore error, won't do anything if there was nothing to stash
        run(['git', 'stash', 'pop'], exit=False)

class IncrementingInt:
    def __init__(self, i=0):
        self.i = i

    def __repr__(self):
        ret = repr(self.i)
        self.i += 1
        return ret

    __str__ = __repr__

def configure(args, parser):
    """
    Color guide

    - red: Error and warning messages
    - green: Welcome messages (use sparingly)
    - blue: Default values
    - bold_magenta: Action items
    - bold_black: Parts of code to be run or copied that should be modified
    """
    if not args.force and on_travis():
        parser.error(red("doctr appears to be running on Travis. Use "
            "doctr configure --force to run anyway."))


    print(green(dedent("""\
    Welcome to Doctr.

    We need to ask you a few questions to get you on your way to automatically
    deploying from Travis CI to GitHub pages.
    """)))

    login_kwargs = {}
    if args.upload_key:
        while not login_kwargs:
            try:
                login_kwargs = GitHub_login()
            except AuthenticationFailed as e:
                print(red(e))
    else:
        login_kwargs = {'auth': None, 'headers': None}

    get_build_repo = False
    default_repo = guess_github_repo()
    while not get_build_repo:
        try:
            if default_repo:
                build_repo = input("What repo do you want to build the docs for [{default_repo}]? ".format(default_repo=blue(default_repo)))
                if not build_repo:
                    build_repo = default_repo
            else:
                build_repo = input("What repo do you want to build the docs for (org/reponame, like 'drdoctr/doctr')? ")
            is_private = check_repo_exists(build_repo, service='github', **login_kwargs)
            check_repo_exists(build_repo, service='travis')
            get_build_repo = True
        except RuntimeError as e:
            print(red('\n{!s:-^{}}\n'.format(e, 70)))

    get_deploy_repo = False
    while not get_deploy_repo:
        try:
            deploy_repo = input("What repo do you want to deploy the docs to? [{build_repo}] ".format(build_repo=blue(build_repo)))
            if not deploy_repo:
                deploy_repo = build_repo

            if deploy_repo != build_repo:
                check_repo_exists(deploy_repo, service='github', **login_kwargs)

            get_deploy_repo = True
        except RuntimeError as e:
            print(red('\n{!s:-^{}}\n'.format(e, 70)))

    N = IncrementingInt(1)

    header = green("\n================== You should now do the following ==================\n")

    if args.token:
        token = generate_GitHub_token(**login_kwargs)['token']
        encrypted_variable = encrypt_variable("GH_TOKEN={token}".format(token=token).encode('utf-8'),
            build_repo=build_repo, is_private=is_private, **login_kwargs)
        print(dedent("""
        A personal access token for doctr has been created.

        You can go to https://github.com/settings/tokens to revoke it."""))

        print(header)
    else:
        deploy_key_repo, env_name, keypath = get_deploy_key_repo(deploy_repo, args.key_path)

        ssh_key = generate_ssh_key("doctr deploy key for {deploy_repo}".format(
            deploy_repo=deploy_key_repo), keypath=keypath)
        key = encrypt_file(keypath, delete=True)
        encrypted_variable = encrypt_variable(env_name.encode('utf-8') + b"=" + key,
            build_repo=build_repo, is_private=is_private, **login_kwargs)

        deploy_keys_url = 'https://github.com/{deploy_repo}/settings/keys'.format(deploy_repo=deploy_key_repo)

        if args.upload_key:

            upload_GitHub_deploy_key(deploy_key_repo, ssh_key, **login_kwargs)

            print(dedent("""
            The deploy key has been added for {deploy_repo}.

            You can go to {deploy_keys_url} to revoke the deploy key.\
            """.format(deploy_repo=deploy_key_repo, deploy_keys_url=deploy_keys_url, keypath=keypath)))
            print(header)
        else:
            print(header)
            print(dedent("""\
            {N}. {BOLD_MAGENTA}Go to {deploy_keys_url}
               and add the following as a new key:{RESET}

                {ssh_key}
               {BOLD_MAGENTA}Be sure to allow write access for the key.{RESET}
            """.format(ssh_key=ssh_key, deploy_keys_url=deploy_keys_url, N=N,
                BOLD_MAGENTA=BOLD_MAGENTA, RESET=RESET)))


        print(dedent("""\
        {N}. {BOLD_MAGENTA}Add the file {keypath}.enc to be staged for commit:{RESET}

            git add {keypath}.enc
        """.format(keypath=keypath, N=N, BOLD_MAGENTA=BOLD_MAGENTA, RESET=RESET)))

    options = '--built-docs ' + bold_black('<path/to/built/html/>')
    if args.key_path:
        options += ' --key-path {keypath}.enc'.format(keypath=keypath)
    if deploy_repo != build_repo:
        options += ' --deploy-repo {deploy_repo}'.format(deploy_repo=deploy_repo)

    print(dedent("""\
    {N}. {BOLD_MAGENTA}Add these lines to your `.travis.yml` file:{RESET}

        env:
          global:
            # Doctr deploy key for {deploy_repo}
            - secure: "{encrypted_variable}"

        script:
          - set -e
          - {BOLD_BLACK}<Command to build your docs>{RESET}
          - pip install doctr
          - doctr deploy {options} {BOLD_BLACK}<target-directory>{RESET}
    """.format(options=options, N=N,
        encrypted_variable=encrypted_variable.decode('utf-8'),
        deploy_repo=deploy_repo, BOLD_MAGENTA=BOLD_MAGENTA,
        BOLD_BLACK=BOLD_BLACK, RESET=RESET)))

    print(dedent("""\
    Replace the text in {BOLD_BLACK}<angle brackets>{RESET} with the relevant
    things for your repository.
    """.format(BOLD_BLACK=BOLD_BLACK, RESET=RESET)))

    print(dedent("""\
    Note: the `set -e` prevents doctr from running when the docs build fails.
    We put this code under `script:` so that if doctr fails it causes the
    build to fail.
    """))

    print(dedent("""\
    {N}. {BOLD_MAGENTA}Commit and push these changes to your GitHub repository.{RESET}
       The docs should now build automatically on Travis.
    """.format(N=N, BOLD_MAGENTA=BOLD_MAGENTA, RESET=RESET)))

    print("See the documentation at https://drdoctr.github.io/ for more information.")

def main():
    config = get_config()
    return process_args(get_parser(config=config))

if __name__ == '__main__':
    sys.exit(main())
