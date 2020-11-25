#!/usr/bin/env python

from setuptools import setup

setup(name='tikka',
    version='1.0',
    author='Daniel Lovette',
    author_email='dfunklove@gmail.com',
    url='https://github.com/dfunklove/tikka',
    license='LICENSE.txt',
    description='Provide real time financial information over websockets.',
    long_description=open('README.md').read(),
    packages=['tikka'],
    scripts=['tikka/bin/tikka_server.py', 'tikka/bin/transform.py'],
    install_requires=['websockets']
    )
