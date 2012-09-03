# coding: utf-8 -*-
from setuptools import setup, find_packages
from mongotor import version

setup(
    name = 'mongotor',
    version = version,
    description = "(MONGO + TORnado) is an asynchronous toolkit for accessing mongo with tornado",
    long_description = open("README.md").read(),
    keywords = ['mongo','tornado'],
    author = 'Marcel Nicolay',
    author_email = 'marcel.nicolay@gmail.com',
    url = 'http://github.com/marcelnicolay/mongotor',
    license = 'OSI',
    classifiers = ['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved',
                   'Natural Language :: English',
                   'Natural Language :: Portuguese (Brazilian)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Software Development :: Libraries :: Application Frameworks',
                   ],
    install_requires = open("requirements.txt").read().split("\n"),
    packages = ['mongotor'],
    test_suite="nose.collector"
)