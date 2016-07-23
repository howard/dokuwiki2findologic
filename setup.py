#!/usr/bin/env python

from setuptools import setup

setup(name='dokuwiki2findologic',
      version='1.0.0',
      description='Converts DokuWiki pages to FINDOLOGIC XML export.',
      author='Chris Ortner',
      author_email='chris@codexfons.com',
      url='https://github.com/howard/dokuwiki2findologic',
      packages=['dokuwiki2findologic'],
      entry_points={
        'console_scripts': [
            'dokuwiki2findologic=dokuwiki2findologic:do_export'
        ],
      })
