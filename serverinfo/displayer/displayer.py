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
data['apache'] = {}
data['buildout'] = {}
data['nginx'] = {}
data['egg'] = {}


class Common(object):
    template_name = None
    subdir = None
    simple_fields = []
    link_attributes = []
    title_prefix = ''
    title_postfix = ''

    def __init__(self, the_json):
        self.json = the_json
        self.data = json.loads(self.json)
        self.id = self.data['id']
        self.prepare()

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    @property
    def title(self):
        return ' '.join([self.title_prefix,
                         self.id,
                         self.title_postfix])

    def prepare(self):
        pass

    @property
    def link(self):
        return "../%s/%s.html" % (self.subdir, self.id)

    @property
    def links(self):
        for link_attribute in self.link_attributes:
            obj = getattr(self, link_attribute, None)
            if obj is None:
                continue
            yield obj.link, obj.title

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
    simple_fields = ['hostname',
                     'buildout_directory',
                     'configfile',
                     'server_names',
                     'proxy_port',
                     ]
    buildout = None
    server = None
    link_attributes = ['buildout',
                       'server',
                       ]

    def _splitted_for_sort(self):
        parts = self.id.split('.')
        parts.reverse()
        return parts

    def __cmp__(self, other):
        return cmp(self._splitted_for_sort(), other._splitted_for_sort())

    @property
    def raw_contents(self):
        return '\n'.join(self.data['contents'])


class Apache(Nginx):
    title_prefix = 'Apache configuration of'


class CodeLink(object):

    def __init__(self, vcs, url):
        self.vcs = vcs
        self.url = url

    @property
    def title(self):
        return "Browse the %s code" % self.vcs

    @property
    def link(self):
        if self.vcs == 'svn':
            return self.url.replace('svn/Products', 'trac/browser/Products')
        return self.url


class AuthorSuggestionLink(object):
    title = "Who worked on this?"

    def __init__(self, vcs, url):
        assert(vcs == 'git')
        self.url = url

    @property
    def link(self):
        return self.url + '/graphs/contributors'


class Buildout(Common):
    subdir = 'buildouts'
    template_name = 'buildout.html'
    title_prefix = 'Buildout directory'
    simple_fields = ['hostname',
                     'directory',
                     'extends',  # TODO: fix this: missing KGS here.
                     'version_control_system',
                     'version_control_url',
                     ]
    site = None
    code_url = None
    server = None
    link_attributes = ['site', 'code_url', 'server', 'author_suggestion']
    # TODO: KGS handling, just like eggs.

    def prepare(self):
        if ('vcs' in self.data) and self.data['vcs']:
            vcs = self.data['vcs']['vcs']
            vcs_url = self.data['vcs']['url']
            self.data['version_control_system'] = vcs
            self.data['version_control_url'] = vcs_url
            # https://office.lizard.net/trac/browser/Products
            # https://office.lizard.net/svn/Products/sites/demo/tags/3.0.11/
            self.code_url = CodeLink(vcs, vcs_url)
            self.author_suggestion = None
            if vcs == 'git':
                self.author_suggestion = AuthorSuggestionLink(vcs, vcs_url)

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

    @property
    def title_postfix(self):
        """Warn if there's no site pointing at us."""
        if not self.site:
            logger.warn("No site: %r", self.site)
            return "(not linked into a site!)"
        return ''


class Server(Common):
    subdir = 'servers'
    template_name = 'server.html'
    title_prefix = 'Linux server'
    simple_fields = ['hostname',
                     'users',
                     'backup_jobs',
                     ]

    def prepare(self):
        self.sites = []
        self.buildouts = []
        self.ports = {}

    @property
    def sites_for_display(self):
        return sorted(self.sites)

    @property
    def buildouts_for_display(self):
        return sorted(self.buildouts)

    @property
    def ports_for_display(self):
        for key in sorted(self.ports.keys()):
            yield key, self.ports[key]


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
               'apache': Apache,
               'server': Server,
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
                data[kind][obj.id.lower()] = obj
    # Link buildouts and nginx sites.
    for nginx in data['nginx'].values():
        buildout_id = nginx.data.get('buildout_id')
        if buildout_id is not None:
            buildout = data['buildout'].get(buildout_id)
            if buildout is not None:
                nginx.buildout = buildout
                buildout.site = nginx
    # Link buildouts and apache sites.
    for apache in data['apache'].values():
        buildout_id = apache.data.get('buildout_id')
        if buildout_id is not None:
            buildout = data['buildout'].get(buildout_id)
            if buildout is not None:
                apache.buildout = buildout
                buildout.site = apache
    # Link buildouts+sites with servers.
    for kind in ['nginx', 'apache', 'buildout']:
        for obj in data[kind].values():
            hostname = obj.data.get('hostname')
            if hostname is not None:
                hostname = hostname.lower()
                server = data['server'].get(hostname)
                if server is None:
                    logger.error("Server with hostname %s not found.",
                                 hostname)
                else:
                    obj.server = server
                    if kind == 'nginx' or kind == 'apache':
                        server.sites.append(obj)
                    elif kind == 'buildout':
                        server.buildouts.append(obj)
    # Link nginx gunicorn ports with servers.
    for kind in ['nginx']:
        for obj in data[kind].values():
            hostname = obj.data.get('hostname')
            port = obj.data.get('proxy_port')
            try:
                port = int(port)
            except:
                pass
            if hostname is not None and port is not None:
                hostname = hostname.lower()
                server = data['server'].get(hostname)
                if server is None:
                    logger.error("Server with hostname %s not found.",
                                 hostname)
                    continue
                server.ports[port] = obj


def generate_html():
    index_subdirs = {'site': 'sites',
                     'buildout': 'buildouts',
                     'server': 'servers',
                     'egg': 'eggs'}
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    data['site'] = data['apache']
    data['site'].update(data['nginx'])
    for kind in ['buildout', 'server', 'egg', 'site']:
        for obj in data[kind].values():
            obj.write()
        # Overview.
        subdir = index_subdirs[kind]
        outfile = os.path.join(utils.html_dir(),
                               subdir,
                               'index.html')
        template = jinja_env.get_template('index.html')
        open(outfile, 'w').write(template.render(
                view={'title': 'Overview of %s' % subdir,
                      'objs': sorted(data[kind].values()),
                      'generated_on': now}))
        logger.info("Wrote %s", outfile)

    outfile = os.path.join(utils.html_dir(), 'index.html')
    template = jinja_env.get_template('root.html')
    open(outfile, 'w').write(template.render(
            view={'title': 'Root overview',
                  'subitems': index_subdirs.values(),
                  'generated_on': now}))
    logger.info("Wrote %s", outfile)


def main():
    utils.setup_logging()
    for subdir in ['eggs', 'servers', 'buildouts', 'sites']:
        utils.clear_directory_contents(os.path.join(
                utils.html_dir(), subdir))
    collect_data()
    generate_html()
