#!/usr/bin/env python2
# coding: utf-8

import sys
import os
from os.path import dirname, join
from setuptools import setup, find_packages
from pip.req import parse_requirements

NAME = "rosbridge_pyclient"
VERSION = "0.4.0"
DESCRIPTION = "This module provides a python client for rosbridge to publish, subscribe topics, call services and use action client"

#  install_reqs = parse_requirements(join(dirname(__file__), "requirements.txt"))
#  reqs = [str(ir.req) for ir in install_reqs]
REQUIRES = []
with open(join(dirname(__file__), 'requirements.txt')) as f:
    REQUIRES = f.read().splitlines()

def read(fname):
    return open(join(dirname(__file__), fname)).read()

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author="Konstantinos Panayiotou",
    author_email="klpanagi@gmail.com",
    maintainer='Konstantinos Panayiotou',
    url="",
    keywords=[],
    install_requires=REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    long_description=read('README.md') if os.path.exists('README.md') else ""
)
