# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='tawnycalc',
    version='0.1.0',
    description='Python wrappers for THERMOCALC software for phase equilibrium modelling.',
    long_description=readme,
    author='John Mansour',
    author_email='mansourjohn@gmail.com',
    url='https://github.com/underworldcode/tawnycalc',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

