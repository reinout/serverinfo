import logging
import os
import re

APACHE_CONF_DIR = '/etc/apache2/sites-enabled'

logger = logging.getLogger(__name__)


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


def construct(directory):
    return {
        'apache': apache_info(directory),
    }
