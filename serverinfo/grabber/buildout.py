"""Extract information from a buildout with python/zope/django.

A buildout should be inside ``/srv/``, the id of a buildout is the directory
name. So ``/srv/reinout.vanrees.org/`` has the id ``reinout.vanrees.org``.

"""
from __future__ import unicode_literals
from xml.etree import ElementTree
import ConfigParser
import copy
import json
import logging
import os
import subprocess
import sys

import pkg_resources

from serverinfo import utils

FILENAME = 'buildout___{id}.json'
SRV_DIR = '/srv/'

logger = logging.getLogger(__name__)


def id(directory):
    """Return id of buildout based on the directory name."""
    directory = directory.rstrip('/')
    parts = directory.split('/')
    return parts[-1]


def extends_info(directory):
    parser = ConfigParser.RawConfigParser()
    parser.read(os.path.join(directory, 'buildout.cfg'))
    try:
        return parser.get('buildout', 'extends')
    except ConfigParser.NoOptionError:
        return


def vcs_info(directory):
    data = {}
    dir_contents = os.listdir(directory)
    if '.hg' in dir_contents:
        data['vcs'] = 'hg'
    elif '.svn' in dir_contents:
        data['vcs'] = 'svn'
    else:
        return data

    # find the url and revision
    if data['vcs'] == 'hg':
        sub = subprocess.Popen('hg path', cwd=directory, shell=True,
                               stdout=subprocess.PIPE)
        data['url'] = sub.communicate()[0].strip().replace('default = ', '')
        sub = subprocess.Popen('hg id -t', cwd=directory, shell=True,
                               stdout=subprocess.PIPE)
        data['release'] = sub.communicate()[0].strip()
    if data['vcs'] == 'svn':
        sub = subprocess.Popen('svn info --xml', cwd=directory, shell=True,
                               stdout=subprocess.PIPE)
        svn_info = sub.communicate()[0]
        data['url'] = ElementTree.fromstring(svn_info).find('.//url').text
    return data


def eggs_info(directory):
    files_of_interest = ['python', 'zopectl', 'django', 'test', 'paster']
    possible_egg_dirs = set()
    before = copy.copy(sys.path)
    bin_dir = os.path.join(directory, 'bin')
    if not os.path.exists(bin_dir):
        return

    for file_ in os.listdir(bin_dir):
        if file_ not in files_of_interest:
            continue
        new_contents = []
        for line in open(os.path.join(directory, 'bin', file_)):
            # Skipping imports that may be unavailable in the current path.
            if line.strip() != 'import sys':
                # When we see these lines we have past the sys.path:
                if 'import ' in line or 'os.chdir' in line or\
                    '__import__' in line or '_interactive = True' in line:
                    break
            new_contents.append(line)
        # This is very evil, but cool! Because the __name__ != main the
        # remainder of the script is not executed.
        exec ''.join(new_contents)
        possible_egg_dirs.update(sys.path)
    # reset sys.path
    sys.path = before

    eggs = {}
    for dir_ in possible_egg_dirs:
        info = list(pkg_resources.find_distributions(dir_, only=True))
        if len(info) == 0:
            continue
        info = info[0]
        eggs[info.project_name] = info.version
    return eggs


def grab_one(directory):
    """Grab and write info on one buildout."""
    logger.info("Grabbing buildout info from %s", directory)
    result = {}
    result['directory'] = directory
    result['extends'] = extends_info(directory)
    result['eggs'] = eggs_info(directory)
    result['vcs'] = vcs_info(directory)
    result['id'] = id(directory)
    result['hostname'] = utils.hostname()

    outfile = os.path.join(utils.grabber_dir(),
                           FILENAME.format(id=id(directory)))
    open(outfile, 'w').write(
        json.dumps(result, sort_keys=True, indent=4))
    logger.debug("Wrote info to %s", outfile)


def grab_all():
    """Grab and write info on all the buildouts."""
    buildout_dirs = [os.path.join(SRV_DIR, d)
                     for d in os.listdir(SRV_DIR)]
    buildout_dirs = [d for d in buildout_dirs
                     if os.path.exists(os.path.join(d, 'buildout.cfg'))]
    for buildout_dir in buildout_dirs:
        grab_one(buildout_dir)


