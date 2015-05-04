#!/usr/bin/env python

from distutils.core import setup

setup(name='ration',
      version='0.1.3',
      description='Civilized window management',
      author='Christopher Groskopf',
      author_email='staringmonkey@gmail.com',
      url='http://github.com/bouvard/ration',
      license='MIT',

      classifiers=[
                     'Development Status :: 3 - Alpha',
                     'Environment :: X11 Applications :: Gnome',
                     'Intended Audience :: End Users/Desktop',
                     'License :: OSI Approved :: MIT License',
                     'Natural Language :: English',
                     'Operating System :: POSIX :: Linux',
                     'Programming Language :: Python :: 2.6',
                     'Topic :: Desktop Environment :: Gnome',
                     'Topic :: Utilities'
                    ],

      long_description='A Divvy-like application for quickly arranging and resizing windows in GTK-based Linux distributions.',

      packages=['ration'],
      scripts=['scripts/ration'],
      data_files=[('share/applications', ['data/ration.desktop'])]
     )

