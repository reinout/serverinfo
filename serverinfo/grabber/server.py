"""Extract information about a linux server.
"""
from __future__ import unicode_literals
import json
import logging
import os
import socket

from serverinfo import utils

FILENAME = 'server___{id}.json'

logger = logging.getLogger(__name__)


def id():
    """Return id based on first server name."""
    return socket.gethostname()


def grab_all():
    """Grab and write info on the whole server."""
    logger.info("Grabbing info for whole server.")
    result = {}
    hostname = id()
    result['id'] = hostname
    result['hostname'] = hostname
    result['users'] = os.listdir('/home')
    backupninja_dir = '/etc/backup.d/'
    if os.path.exists(backupninja_dir):
        result['backup_jobs'] = [d for d in os.listdir(backupninja_dir)
                                 if not d.startswith('.')]

    outfile = os.path.join(utils.grabber_dir(),
                           FILENAME.format(id=hostname))
    open(outfile, 'w').write(
        json.dumps(result, sort_keys=True, indent=4))
    logger.debug("Wrote info to %s", outfile)
