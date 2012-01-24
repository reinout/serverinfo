import argparse
import json
import logging
import os

import serverinfo.construct

logger = logging.getLogger(__name__)


def construct():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', nargs='?', default=os.curdir)

    args = parser.parse_args()

    result = serverinfo.construct.construct(args.directory)
    print json.dumps(result, sort_keys=True, indent=4)


def construct_all():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument('root', nargs='?', default='/srv')

    args = parser.parse_args()

    collection = {}
    for dir_ in os.listdir(args.root):
        fullpath = os.path.join(args.root, dir_)
        if not os.path.exists(os.path.join(fullpath, 'buildout.cfg')):
            continue
        if os.path.isdir(fullpath):
            collection[fullpath] = serverinfo.construct.construct(fullpath)
    print json.dumps(collection, sort_keys=True, indent=4)


def collect():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument('jsondir', nargs='?', default='reports')

    args = parser.parse_args()

    import serverinfo.collect
    print serverinfo.collect.collect(args.jsondir)
