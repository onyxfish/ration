#!/usr/bin/env python

from distutils.core import setup

setup(name='ration',
      version='0.1',
      description='Civilized window management',
      author='Christopher Groskopf',
      author_email='staringmonkey@gmail.com',
      url='http://github.com/bouvard/ration',
      license='MIT',
      packages=['ration', 'src'],
      package_dir={'ration': ''},
      package_data={'ration': []},
      scripts=['ration'],
      data_files=[('share/applications', ['data/ration.desktop'])]
     )

