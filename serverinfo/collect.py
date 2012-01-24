import datetime
import json
import logging
import os

from jinja2 import Environment, PackageLoader

jinja_env = Environment(loader=PackageLoader('serverinfo', 'templates'))
logger = logging.getLogger(__name__)

PREFIX = 'serverinfo.'
SUFFIX = '.json'


def collect(jsondir):
    logging.basicConfig(level=logging.DEBUG,
                        format="%(levelname)s: %(message)s")
    servers = {}
    packages = {}
    for file_ in os.listdir(jsondir):
        if file_.startswith(PREFIX):
            if file_.endswith(SUFFIX):
                try:
                    servers[file_.replace(PREFIX, '').replace(
                            SUFFIX, '')] = json.load(open(
                            os.path.join(jsondir, file_)))
                except ValueError:
                    # Empty json file
                    pass

    for server, sites in sorted(servers.items()):
        for site, site_info in sites.items():

            # Make a reverse mapping of eggs.
            pkg_info = site_info['eggs']
            if not pkg_info:
                continue
            for pkg, version in pkg_info.items():
                packages.setdefault(pkg, {}).setdefault(
                    version, []).append((server, site))

    template = jinja_env.get_template('index.html')
    return template.render(date=datetime.datetime.now(),
                           servers=servers,
                           packages=packages)
