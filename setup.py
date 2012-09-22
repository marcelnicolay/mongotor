# coding: utf-8 -*-
from setuptools import setup
from mongotor import version
import os


def get_packages():
    # setuptools can't do the job :(
    packages = []
    for root, dirnames, filenames in os.walk('mongotor'):
        if '__init__.py' in filenames:
            packages.append(".".join(os.path.split(root)).strip("."))

    return packages

setup(
    name = 'mongotor',
    version = version,
    description = "(MongoDB + Tornado) is an asynchronous driver and toolkit for accessing MongoDB with Tornado",
    long_description = open("README.md").read(),
    keywords = ['mongo','tornado'],
    author = 'Marcel Nicolay',
    author_email = 'marcel.nicolay@gmail.com',
    url = 'http://marcelnicolay.github.com/mongotor/',
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
    packages = get_packages(),
    test_suite="nose.collector"
)