from __future__ import unicode_literals

from serverinfo.grabber import buildout
from serverinfo import utils


def main():
    utils.setup_logging()
    buildout.grab_all()
