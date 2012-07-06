"""Extract information from nginx files.
"""
from __future__ import unicode_literals
import json
import logging
import os

from serverinfo import utils

FILENAME = 'nginx___{id}.json'
NGINX_DIR = '/etc/nginx/sites-enabled/'

logger = logging.getLogger(__name__)


def id(server_names):
    """Return id based on first server name."""
    return server_names[0]


def grab_one(configfile):
    """Grab and write info on one nginx config."""
    logger.info("Grabbing nginx info from %s", configfile)
    result = {}
    result['configfile'] = configfile
    contents = open(configfile).readlines()
    result['contents'] = [line.rstrip() for line in contents]
    settings = {}
    for line in contents:
        line = line.strip()
        parts = line.split(' ', 1)
        if len(parts) == 1:
            continue
        # We treat the first word on the line as a setting name. Good enough
        # for our purpose.
        settings[parts[0]] = parts[1].rstrip(';')
    server_names = settings['server_name']
    server_names = server_names.split()
    server_names = [name for name in server_names if name]
    result['server_names'] = server_names
    # Assumption: access log is in the buildout directory where our site is,
    # so something like /srv/DIRNAME/var/log/access.log.
    logfile = settings['access_log']
    parts = logfile.split('/')
    result['buildout_id'] = parts[2]
    result['buildout_directory'] = '/srv/%s' % parts[2]
    if 'proxy_pass' in settings:
        proxy_pass = settings['proxy_pass']
        result['proxy_pass'] = proxy_pass
        # Looks like 'proxy_pass http://localhost:9000'.
        parts = proxy_pass.split(':')
        port = parts[-1]
        result['proxy_port'] = port
    result['id'] = id(server_names)
    outfile = os.path.join(utils.grabber_dir(),
                           FILENAME.format(id=id(server_names)))
    open(outfile, 'w').write(
        json.dumps(result, sort_keys=True, indent=4))
    logger.debug("Wrote info to %s", outfile)


def grab_all():
    """Grab and write info on all the ngnix configs."""
    config_files = [f for f in os.listdir(NGINX_DIR)
                    if f != 'default' and not f.startswith('.')]
    config_files = [os.path.join(NGINX_DIR, d) for d in config_files]
    for config_file in config_files:
        grab_one(config_file)
