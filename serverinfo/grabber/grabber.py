from __future__ import unicode_literals

from serverinfo.grabber import buildout
from serverinfo.grabber import nginx
from serverinfo import utils


def main():
    utils.setup_logging()
    utils.clear_directory_contents(utils.grabber_dir())
    buildout.grab_all()
    nginx.grab_all()
