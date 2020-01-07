#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Christian Karrié <christian@karrie.info>'

from distutils.core import setup

# Dynamically calculate the version based on ccm.VERSION
version_tuple = __import__('csgomatches').VERSION
version = ".".join([str(v) for v in version_tuple])

setup(
    name='ckw_csgomatches',
    description='Django CS:GO Matches Manager',
    version=version,
    author='Christian Karrie',
    author_email='ckarrie@gmail.com',
    url='http://ccm.app/',
    packages=['csgomatches'],
    install_requires=[
        'django',
        'requests',
        'psycopg2-binary', 'bs4', 'python-dateutil', 'python-memcached',
        'django_ical', 'websocket_client', 'djangorestframework', 'websockets',
        'python-twitter'
    ]
)
