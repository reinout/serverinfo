from xml.etree import ElementTree
import ConfigParser
import copy
import logging
import os
import re
import subprocess
import sys

import pkg_resources

APACHE_CONF_DIR = '/etc/apache2/sites-enabled'

logger = logging.getLogger(__name__)


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


def apache_info(directory):
    if not os.path.exists(APACHE_CONF_DIR):
        logger.debug("No apache config dir found.")
        return {}
    conflines = []
    potential_locations = ['etc', 'parts/etc']
    for location in potential_locations:
        for root, _, files in os.walk(os.path.join(directory, location)):
            for file_ in files:
                if file_.endswith('apache.conf'):
                    file_path = os.path.join(root, file_)
                    if file_ in os.listdir(APACHE_CONF_DIR):
                        conflines += open(file_path).readlines()
                        logger.debug("Looking at contents of %s", file_path)
                    else:
                        logger.warn("%s is not symlinked, ignoring.",
                                     file_path)

    servername_regex = re.compile(r'^[^#]*ServerName ([a-z0-9\.\-]+)')
    serveralias_regex = re.compile(r'^[^#]*ServerAlias ([a-z0-9\.\-]+)')
    ip_regex = re.compile((r'^[^#]*VirtualHost '
        r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):'))
    port_regex = re.compile(r'^[^#]*http://[locahst127\.0]+:([0-9]+)/')

    servernames = set()
    ips = set()
    ports = set()

    # There should be only one conf per deployment, but we check anyway.
    for confline in conflines:
        servernames.update(servername_regex.findall(confline))
        servernames.update(serveralias_regex.findall(confline))
        ips.update(ip_regex.findall(confline))
        ports.update(port_regex.findall(confline))
    logger.debug("Servernames/aliases found: %s", servernames)
    logger.debug("IP addresses we listen to found: %s", ips)
    logger.debug("Local ports we redirect to found: %s", ports)
    result = {
        'servernames': list(servernames),
        'ips': list(ips),
        'ports': list(ports),
    }
    return result


def extends_info(directory):
    parser = ConfigParser.RawConfigParser()
    parser.read(os.path.join(directory, 'buildout.cfg'))

    try:
        return parser.get('buildout', 'extends')
    except ConfigParser.NoOptionError:
        return


def construct(directory):
    return {
        'apache': apache_info(directory),
        'eggs': eggs_info(directory),
        'vcs': vcs_info(directory),
        'extends': extends_info(directory),
    }
