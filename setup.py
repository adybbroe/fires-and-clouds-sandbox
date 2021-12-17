#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2021 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c21856.ad.smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""A sandbox for working with cloud cover in relation to fire detection from satellite
"""

import sys
from setuptools import setup, find_packages
import os.path


try:
    # HACK: https://github.com/pypa/setuptools_scm/issues/190#issuecomment-351181286
    # Stop setuptools_scm from including all repository files
    import setuptools_scm.integration
    setuptools_scm.integration.find_files = lambda _: []
except ImportError:
    pass


description = ('Sandbox code for manipulating cloud cover products for fire detection')

try:
    with open('./README.md', 'r') as fd:
        long_description = fd.read()
except IOError:
    long_description = ''

requires = ['docutils>=0.3', 'numpy', 'scipy', 'trollsift',
            'pytroll-schedule', 'pyorbital',
            'geopandas', 'rasterio', 'shapely', 'pyproj']


NAME = "fires_and_clouds"

setup(name=NAME,
      description=description,
      author='Adam Dybbroe',
      author_email='adam.dybbroe@smhi.se',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Science/Research',
                   'License :: OSI Approved :: GNU General Public License v3 ' +
                   'or later (GPLv3+)',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Scientific/Engineering'],
      url='https://gitlab.smhi.se/satsa/fires-and-clouds-sandbox',
      long_description=long_description,
      license='GPLv3',

      packages=find_packages(),
      install_requires=requires,
      scripts=['bin/map_cloudiness_on_swath.py',
               'bin/make_accumulated_cloudcover_from_viirs.py'],
      python_requires='>=3.8',
      zip_safe=False,
      use_scm_version=True
      )
