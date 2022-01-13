#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2021, 2022 Adam.Dybbroe

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

"""Go through the archive of VIIRS AF EDRs and do the post-processing and output in Geojson.
"""

import os
from glob import glob
from datetime import datetime
from trollsift import Parser, globify
import pytz

from activefires_pp.post_processing import store_geojson
from activefires_pp.utils import get_geometry_from_shapefile
from activefires_pp.post_processing import ActiveFiresShapefileFiltering

from fires_and_clouds.utils import get_af_files


TESTFILE = "/data/lang/satellit2/polar/viirs_active_fires/2021/04/AFIMG_j01_d20210407_t1158114_e1159359_b17538_c20210407121305204588_cspp_dev.txt"

INFILE_PATTERN = 'AFIMG_{platform:s}_d{start_time:%Y%m%d_t%H%M%S%f}_e{end_hour:%H%M%S%f}_b{orbit:s}_c{processing_time:%Y%m%d%H%M%S%f}_cspp_dev.txt'

SHP_BOARDERS = "/home/a000680/data/shapes/Sverige/Sverige.shp"
SHP_FILTERMASK = "/home/a000680/Satsa/Skogsbrander/tatorter/tatort_mb_ind_dissolve_man_edit.shp"

BASEDIR = "/data/lang/satellit2/polar/viirs_active_fires/"

PLATFORMS = {'j01': 'NOAA-20',
             'npp': 'Suomi-NPP'}


def viirs_afedr2geojson(edr_filepath, platform_name, outfile_pattern):
    """Read EDR file, filter for fires in Sweden and write to Geojson."""
    fmda = {}
    af_shapeff = ActiveFiresShapefileFiltering(edr_filepath,
                                               platform_name=platform_name,
                                               timezone='Europe/Stockholm')

    afdata = af_shapeff.get_af_data(INFILE_PATTERN)

    af_shapeff.fires_filtering(SHP_BOARDERS)
    #afdata_sweden = af_shapeff.get_af_data()

    af_shapeff.fires_filtering(SHP_FILTERMASK, start_geometries_index=0, inside=False)
    afdata_ff = af_shapeff.get_af_data()

    platform_name = af_shapeff.platform_name

    fmda['start_time'] = af_shapeff.metadata['start_time']
    fmda['platform'] = platform_name
    pout = Parser(outfile_pattern)
    output_dir = './'
    out_filepath = os.path.join(output_dir, pout.compose(fmda))

    return store_geojson(out_filepath, afdata_ff, platform_name=platform_name)


if __name__ == "__main__":

    outfile_pattern_national = 'AFIMG_{platform:s}_{start_time:%Y%m%d_%H%M%S}_sweden.geojson'
    #fmda = {}
    #platform_name = 'NOAA-20'
    #fmda['platform'] = platform_name
    #filepath = viirs_afedr2geojson(TESTFILE, platform_name)

    TSTART = datetime(2022, 1, 10, 0)
    TEND = datetime(2022, 1, 13, 0)
    edrlist = get_af_files(BASEDIR, TSTART, TEND, INFILE_PATTERN)

    p__ = Parser(INFILE_PATTERN)
    for edrfile in edrlist:
        print(edrfile)
        res = p__.parse(os.path.basename(edrfile))
        platform_name = PLATFORMS.get(res['platform'])
        try:
            filepath = viirs_afedr2geojson(edrfile, platform_name, outfile_pattern_national)
        except pytz.exceptions.AmbiguousTimeError:
            print("Could not convert file. Continue")

        if filepath:
            print("File created: %s" % filepath)
