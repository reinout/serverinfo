from __future__ import unicode_literals
from contextlib import contextmanager
import logging
import os
import sys


logger = logging.getLogger(__name__)


@contextmanager
def cd(path):
    """Context manager around os.chdir.

    See http://lateral.netmanagers.com.ar/weblog/posts/BB963.html.
    """
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


def buildout_dir():
    """Return buildout directory (for finding the var dirs)."""
    the_script_in_bin = sys.argv[0]
    bin_dir = os.path.dirname(the_script_in_bin)
    one_level_up = os.path.join(bin_dir, '..')
    return os.path.abspath(one_level_up)


def grabber_dir():
    """Return output directory for data we grab."""
    return os.path.join(buildout_dir(), 'var', 'grabber')


def displayer_dir():
    """Return input directory for data we want to display."""
    return os.path.join(buildout_dir(), 'var', 'displayer')


def html_dir():
    """Return output directory for the html we generate."""
    return os.path.join(buildout_dir(), 'var', 'html')


def clear_directory_contents(directory):
    """Clear a directory of files.

    Assumption: there are just files in there.
    """
    with cd(directory):
        for filename in os.listdir('.'):
            os.remove(filename)
    logger.debug("Cleared files out of %s", directory)


def setup_logging():
    """Configure console logging."""
    if '-v' in sys.argv:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel,
                        format="%(levelname)s: %(message)s")
