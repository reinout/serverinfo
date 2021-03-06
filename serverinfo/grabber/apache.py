"""Extract information from apache files.
"""
from __future__ import unicode_literals
import json
import logging
import os
import re

from serverinfo import utils

FILENAME = 'apache___{id}.json'
APACHE_DIR = '/etc/apache2/sites-enabled/'

logger = logging.getLogger(__name__)
servername_regex = re.compile(r'^[^#]*ServerName ([a-z0-9\.\-]+)')
serveralias_regex = re.compile(r'^[^#]*ServerAlias ([a-z0-9\.\-]+)')
ip_regex = re.compile((r'^[^#]*VirtualHost '
                       r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):'))
port_regex = re.compile(r'^[^#]*http://[locahst127\.0]+:([0-9]+)/')
directory_regex = re.compile(r'/srv/([a-z0-9\.\-_/]+)/var/log')


def id(server_names):
    """Return id based on first server name."""
    return server_names[0]


def grab_one(configfile):
    """Grab and write info on one apache config."""
    logger.info("Grabbing apache info from %s", configfile)
    result = {}
    result['configfile'] = configfile
    contents = open(configfile).readlines()
    result['contents'] = [line.rstrip() for line in contents]
    result['hostname'] = utils.hostname()

    servernames = set()
    ips = set()
    ports = set()
    directories = set()

    # There should be only one conf per deployment, but we check anyway.
    for confline in contents:
        servernames.update(servername_regex.findall(confline))
        servernames.update(serveralias_regex.findall(confline))
        ips.update(ip_regex.findall(confline))
        ports.update(port_regex.findall(confline))
        directories.update(directory_regex.findall(confline))
    if not servernames:
        logger.info("No servernames found, probably empty default config.")
        return
    logger.debug("Servernames/aliases found: %s", servernames)
    logger.debug("IP addresses we listen to found: %s", ips)
    logger.debug("Local ports we redirect to found: %s", ports)
    result['server_names'] = list(servernames)
    result['ips'] = list(ips)
    result['ports'] = list(ports)

    result['id'] = id(result['server_names'])
    if directories:
        directory = list(directories)[0]
        result['buildout_id'] = directory
        result['buildout_directory'] = '/srv/' + directory

    outfile = os.path.join(utils.grabber_dir(),
                           FILENAME.format(id=result['id']))
    open(outfile, 'w').write(
        json.dumps(result, sort_keys=True, indent=4))
    logger.debug("Wrote info to %s", outfile)


def grab_all():
    """Grab and write info on all the apache configs."""
    if not os.path.exists(APACHE_DIR):
        return
    config_files = [f for f in os.listdir(APACHE_DIR)
                    if f != 'default' and not f.startswith('.')]
    config_files = [os.path.join(APACHE_DIR, d) for d in config_files]
    for config_file in config_files:
        grab_one(config_file)
