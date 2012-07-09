"""Extract information about a linux server.
"""
from __future__ import unicode_literals
import json
import logging
import os

from serverinfo import utils

FILENAME = 'server___{id}.json'

logger = logging.getLogger(__name__)


def grab_all():
    """Grab and write info on the whole server."""
    logger.info("Grabbing info for whole server.")
    result = {}
    hostname = utils.hostname()
    result['id'] = hostname
    result['hostname'] = hostname
    result['users'] = [d for d in os.listdir('/home')
                       if not d.startswith('.')]
    backupninja_dir = '/etc/backup.d/'
    try:
        if os.path.exists(backupninja_dir):
            result['backup_jobs'] = os.listdir(backupninja_dir)
    except OSError, e:
        logger.warn(e)
        result['backup_jobs'] = (
            '/etc/backup.d is not accessible to the serverinfo script.')

    outfile = os.path.join(utils.grabber_dir(),
                           FILENAME.format(id=hostname))
    open(outfile, 'w').write(
        json.dumps(result, sort_keys=True, indent=4))
    logger.debug("Wrote info to %s", outfile)
