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


class Common(object):
    template_name = None
    subdir = None
    simple_fields = ['buildout_directory',
                     'configfile',
                     'server_names',
                     'proxy_port',
                     ]

    def __init__(self, the_json):
        self.json = the_json
        self.data = json.loads(self.json)
        self.id = self.data['id']

    @property
    def generated_on(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    def write(self):
        outfile = os.path.join(utils.html_dir(),
                               self.subdir,
                               '%s.html' % self.id)
        template = jinja_env.get_template(self.template_name)
        open(outfile, 'w').write(template.render(view=self))
        logger.info("Wrote %s", outfile)

    @property
    def fields(self):
        result = []
        for simple_field in self.simple_fields:
            value = self.data.get(simple_field)
            if value is None:
                continue
            if isinstance(value, list):
                value = ', '.join(value)
            name = simple_field.replace('_', ' ').capitalize()
            result.append([name, value])
        return result


class Site(Common):
    subdir = 'sites'
    template_name = 'nginx.html'

    @property
    def raw_contents(self):
        return '\n'.join(self.data['contents'])

    @property
    def links(self):
        result = []
        buildout_id = self.data.get('buildout_id')
        if buildout_id is not None:
            link = '../buildouts/%s.html' % buildout_id
            title = 'Buildout site info'
            result.append([link, title])
        return result


def collect_data():
    """Collect all the json data and load it in memory."""
    with utils.cd(utils.displayer_dir()):
        for dirpath, dirnames, filenames in os.walk('.'):
            # server_id = dirpath
            for json_file in [f for f in filenames if f.endswith('.json')]:
                kind = json_file.split('___')[0]
                filepath = os.path.join(dirpath, json_file)
                json_content = open(filepath).read()
                site = Site(json_content)
                data[kind][site.id] = site
                logger.debug("Loaded info from %s", filepath)


def generate_html():
    for site in data['nginx'].values():
        site.write()


def main():
    utils.setup_logging()
    for subdir in ['servers', 'buildouts', 'sites']:
        utils.clear_directory_contents(os.path.join(
                utils.html_dir(), subdir))
    collect_data()
    generate_html()
