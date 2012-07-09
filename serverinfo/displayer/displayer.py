from __future__ import unicode_literals
import datetime
import json
import logging
import os
import collections

from jinja2 import Environment, PackageLoader

jinja_env = Environment(loader=PackageLoader('serverinfo', 'templates'))
logger = logging.getLogger(__name__)

from serverinfo import utils

data = {}
data['server'] = {}
data['buildout'] = {}
data['nginx'] = {}
data['egg'] = {}


class Common(object):
    template_name = None
    subdir = None
    simple_fields = []
    title_prefix = ''

    def __init__(self, the_json):
        self.json = the_json
        self.data = json.loads(self.json)
        self.id = self.data['id']
        self.prepare()
        self.title = ' '.join([self.title_prefix, self.id])

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def prepare(self):
        pass

    @property
    def link(self):
        return "../%s/%s.html" % (self.subdir, self.id)

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


class Nginx(Common):
    subdir = 'sites'
    template_name = 'nginx.html'
    title_prefix = 'NGINX configuration of'
    simple_fields = ['buildout_directory',
                     'configfile',
                     'server_names',
                     'proxy_port',
                     ]

    @property
    def raw_contents(self):
        return '\n'.join(self.data['contents'])

    @property
    def links(self):
        result = []
        buildout_id = self.data.get('buildout_id')
        if buildout_id is not None:
            link = '../buildouts/%s.html' % buildout_id
            title = 'Buildout directory info'
            result.append([link, title])
        return result


class Buildout(Common):
    subdir = 'buildouts'
    template_name = 'buildout.html'
    title_prefix = 'Buildout directory'
    simple_fields = ['directory',
                     'extends',  # TODO: fix this: missing KGS here.
                     'version_control_system',
                     'version_control_url',
                     ]
    # TODO: KGS handling, just like eggs.

    def prepare(self):
        if ('vcs' in self.data) and self.data['vcs']:
            vcs = self.data['vcs']['vcs']
            vcs_url = self.data['vcs']['url']
            self.data['version_control_system'] = vcs
            self.data['version_control_url'] = vcs_url
        self.eggs = {}
        for egg_name, version in self.data['eggs'].items():
            if egg_name not in data['egg']:
                data['egg'][egg_name] = Egg(egg_name)
            egg = data['egg'][egg_name]
            egg.add_usage(self, version)
            self.eggs[egg] = version

    @property
    def eggs_for_display(self):
        for key in sorted(self.eggs.keys()):
            yield key, self.eggs[key]


class Egg(Common):
    # Well, it is not actually that common...
    subdir = 'eggs'
    template_name = 'egg.html'
    title_prefix = 'Egg'
    simple_fields = ['directory',
                     'extends',  # TODO: fix this: missing KGS here.
                     'version_control_system',
                     'version_control_url',
                     ]

    def __init__(self, egg_name):
        self.id = egg_name
        self.title = ' '.join([self.title_prefix, self.id])
        self.versions = collections.defaultdict(list)

    def add_usage(self, buildout, version):
        self.versions[version].append(buildout)

    @property
    def versions_for_display(self):
        for key in sorted(self.versions.keys()):
            yield key, self.versions[key]



def collect_data():
    """Collect all the json data and load it in memory."""
    mapping = {'nginx': Nginx,
               'buildout': Buildout}
    with utils.cd(utils.displayer_dir()):
        for dirpath, dirnames, filenames in os.walk('.'):
            # server_id = dirpath
            for json_file in [f for f in filenames if f.endswith('.json')]:
                kind = json_file.split('___')[0]
                filepath = os.path.join(dirpath, json_file)
                logger.debug("Loading info from %s",
                             os.path.abspath(filepath))
                json_content = open(filepath).read()
                klass = mapping[kind]
                obj = klass(json_content)
                data[kind][obj.id] = obj


def generate_html():
    for nginx in data['nginx'].values():
        nginx.write()
    for buildout in data['buildout'].values():
        buildout.write()
    for egg in data['egg'].values():
        egg.write()


def main():
    utils.setup_logging()
    for subdir in ['servers', 'buildouts', 'sites']:
        utils.clear_directory_contents(os.path.join(
                utils.html_dir(), subdir))
    collect_data()
    generate_html()
