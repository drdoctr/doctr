"""
Code used for both Travis and local (deploy and configure)
"""

# Color guide
#
# - red: Error and warning messages
# - green: Welcome messages (use sparingly)
# - yellow: warning message (only use on Travis)
# - blue: Default values
# - bold_magenta: Action items
# - bold_black: Parts of code to be run or copied that should be modified


def red(text):
    return "\033[31m%s\033[0m" % text

def green(text):
    return "\033[32m%s\033[0m" % text

def yellow(text):
    return "\033[33m%s\033[0m" % text

def blue(text):
    return "\033[34m%s\033[0m" % text

def bold_black(text):
    return "\033[1;30m%s\033[0m" % text

def bold_magenta(text):
    return "\033[1;35m%s\033[0m" % text

def bold(text):
    return "\033[1m%s\033[0m" % text

# Use these when coloring individual parts of a larger string, e.g.,
# "{BOLD_MAGENTA}Bright text{RESET} normal text".format(BOLD_MAGENTA=BOLD_MAGENTA, RESET=RESET)
BOLD_BLACK = "\033[1;30m"
BOLD_MAGENTA = "\033[1;35m"
RESET = "\033[0m"

# Remove whitespace on inputs
_input = input
def input(prompt=None):
    res = _input(prompt)
    return res.strip()
