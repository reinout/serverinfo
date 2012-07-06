from __future__ import unicode_literals
import os
import sys


def buildout_dir():
    """Return buildout directory (for finding the var dirs)."""
    the_script_in_bin = sys.argv[0]
    bin_dir = os.path.dirname(the_script_in_bin)
    one_level_up = os.path.join(bin_dir, '..')
    return os.path.abspath(one_level_up)


def grabber_dir():
    """Return output directory for data we grab."""
    return os.path.join(buildout_dir(), 'var', 'grabber')
