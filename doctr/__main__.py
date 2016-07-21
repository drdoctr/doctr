import sys
import os

from .local import generate_GitHub_token, encrypt_variable
from .travis import setup_GitHub_push, commit_docs, push_docs

def main():
    on_travis = os.environ.get("TRAVIS_JOB_NUMBER", '')

    if on_travis:
        # TODO: Get this automatically
        repo = sys.argv[1]
        if setup_GitHub_push(repo):
            commit_docs()
            push_docs()
    else:
        username = input("What is your GitHub username? ")
        token = generate_GitHub_token(username)

        repo = input("What repo to you want to build the docs for? ")
        encrypted_variable = encrypt_variable("GH_TOKEN={token}".format(token=token).encode('utf-8'), repo=repo)
        travis_content = """
env:
  global:
    secure: "{encrypted_variable}"

""".format(encrypted_variable=encrypted_variable.decode('utf-8'))

        print("Put\n", travis_content, "in your .travis.yml.\n",
            "Also make sure to create an empty gh-pages branch on GitHub, and "
            "enable it at https://github.com/{repo}/settings".format(repo=repo), sep='')

if __name__ == '__main__':
    sys.exit(main())
