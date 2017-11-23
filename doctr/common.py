"""
Code used for both Travis and local (deploy and configure)
"""

def red(text):
    return "\033[31m%s\033[0m" % text

def green(text):
    return "\033[32m%s\033[0m" % text

def blue(text):
    return "\033[34m%s\033[0m" % text


def bold_magenta(text):
    return "\033[1;35m%s\033[0m" % text

BOLD_MAGENTA = "\033[1;35m"
RESET = "\033[0m"
