from setuptools import setup

version = '0.1'

long_description = '\n\n'.join([
    open('README.txt').read(),
    open('CHANGES.txt').read(),
    ])


setup(name='serverinfo',
      version=version,
      long_description=long_description,
      author='Reinout van Rees',
      author_email='reinout@vanrees.org',
      license='Unclear at the moment',
      packages=['serverinfo'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'argparse',
                        'Jinja2',
                        ],
      entry_points={
          'console_scripts': [
              'construct = serverinfo.scripts:construct',
              'construct_all = serverinfo.scripts:construct_all',
              'collect = serverinfo.scripts:collect',
          ]},
      )
