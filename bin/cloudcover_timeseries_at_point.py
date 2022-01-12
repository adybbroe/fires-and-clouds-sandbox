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

"""Make a timeseries of the cloud cover at a given point.

Tasks:

 * Find NWCSAF/PPS cloud products on the disk and gather (VIIRS) granules belonging to the same pass

 * For a lon,lat, extract the cloud parameter(s) at that point


"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

import numpy as np
from datetime import datetime
from fires_and_clouds.cloud_utils import PPSFilesGetter
from fires_and_clouds.cloud_utils import get_cloudfraction
from fires_and_clouds.utils import NRK

AVHRR_MODIS_PPS_PATH = "/data/lang/satellit/polar/PPS_products/satproj/"
VIIRS_PPS_PATH = "/data/lang/satellit2/polar/pps/"

if __name__ == "__main__":

    START = datetime(2021, 6, 11, 0)
    END = datetime(2021, 6, 12, 0)

    pps_file_getter = PPSFilesGetter(VIIRS_PPS_PATH, START, END)
    #pps_file_getter.collect_product_files(platforms=['NOAA-20', 'Suomi-NPP'], product_name='CMA')
    #pps_file_getter = PPSFilesGetter(AVHRR_MODIS_PPS_PATH, START, END)
    pps_file_getter.collect_product_files(product_name='CMA')
    total_num_of_files = len(pps_file_getter.pps_files['CMA'])

    # pps_file_getter.gather_granules('CMA')

    #LONS = [22.897562, ]
    #LATS = [66.573494, ]
    LONS = [NRK[0], ]
    LATS = [NRK[1], ]

    results = []
    nfiles_read = 0
    if pps_file_getter.granules:
        for granule_collection in pps_file_getter.pps_files['CMA']:
            for cmafile in pps_file_getter.pps_files['CMA'][granule_collection]:

                cloud_cover, otimes = get_cloudfraction(LONS, LATS, cmafile)
                nfiles_read = nfiles_read + 1
                if not np.isnan(cloud_cover[0]):
                    results.append((cloud_cover[0], otimes[0]))
                    print("===> Result found: %f %s" % (cloud_cover[0], str(otimes[0])))
                    break
    else:
        for cmafile in pps_file_getter.pps_files['CMA']:
            cloud_cover, otimes = get_cloudfraction(LONS, LATS, cmafile)
            nfiles_read = nfiles_read + 1
            if not np.isnan(cloud_cover[0]):
                results.append((cloud_cover[0], otimes[0]))
                print("===> Result found: %f %s" % (cloud_cover[0], str(otimes[0])))

    print("%d files read out of %d" % (nfiles_read, total_num_of_files))

    dtimes = [t[1] for t in results]
    clcov = [t[0] for t in results]

    filename = './cloud_cover_timeseries_viirs_norrkoping.csv'
    #filename = './cloud_cover_timeseries_avhrr_modis.csv'
    with open(filename, 'w') as fpt:
        for res in results:
            fpt.write('%s, %f, %f\n' % (res[1], res[0], 1.0-res[0]))
