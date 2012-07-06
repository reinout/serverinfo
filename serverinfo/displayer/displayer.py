from __future__ import unicode_literals
import datetime
import json
import logging
import os

from jinja2 import Environment, PackageLoader

jinja_env = Environment(loader=PackageLoader('serverinfo', 'templates'))
logger = logging.getLogger(__name__)

from serverinfo import utils

data = {}
data['server'] = {}
data['buildout'] = {}
data['nginx'] = {}


def collect_data():
    """Collect all the json data and load it in memory."""
    with utils.cd(utils.displayer_dir()):
        for dirpath, dirnames, filenames in os.walk('.'):
            # server_id = dirpath
            for json_file in [f for f in filenames if f.endswith('.json')]:
                kind = json_file.split('___')[0]
                filepath = os.path.join(dirpath, json_file)
                json_content = open(filepath).read()
                json_data = json.loads(json_content)
                data[kind][json_data['id']] = json_data
                logger.debug("Loaded info from %s", filepath)


def generate_html():
    for nginx_id, nginx in data['nginx'].items():
        outfile = os.path.join(utils.html_dir(),
                               'sites',
                               '%s.html' % nginx_id)
        template = jinja_env.get_template('nginx.html')
        nginx['generated_on'] = datetime.datetime.now()
        open(outfile, 'w').write(template.render(**nginx))
        logger.info("Wrote %s", outfile)



def main():
    utils.setup_logging()
    for subdir in ['servers', 'buildouts', 'sites']:
        utils.clear_directory_contents(os.path.join(
                utils.html_dir(), subdir))
    collect_data()
    generate_html()
