# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

version = {}
with open("tawnycalc/_version.py") as fp:
    exec(fp.read(), version)

with open('README.rst') as f:
    readme = f.read()

setup(
    name='tawnycalc',
    version=version['__version__'],
    description='Python wrappers for THERMOCALC software for phase equilibrium modelling.',
    long_description=readme,
    author='John Mansour',
    author_email='mansourjohn@gmail.com',
    url='https://github.com/underworldcode/tawnycalc',
    license='LGPL-3',
    include_package_data=True,
    packages=find_packages(exclude=('tests', 'docs')),
    provides=['tawnycalc'],
    install_requires=['tabulate',])

