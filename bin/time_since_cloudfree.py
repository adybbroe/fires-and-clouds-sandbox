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

"""From a set of historic VIIRS NWCSAF/PPS cloud cover scenes create a map
showing the time since most recent cloudfree view

"""

from datetime import datetime
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np
import os
from glob import glob

from trollsift.parser import Parser
from pyresample import kd_tree, geometry
from pyresample import load_area
from fires_and_clouds.cloud_utils import generate_cloudmask_image
from fires_and_clouds.cloud_utils import create_clfree_freshness_from_cloudmask
from fires_and_clouds.cloud_utils import get_cloudmask_scene
from fires_and_clouds.cloud_utils import PPSFilesGetter
from fires_and_clouds.cloud_utils import get_cloudfraction
from fires_and_clouds.cloud_utils import LastCloudfreeView

from trollimage.colormap import rdbu, ylgnbu
from trollimage.image import Image


"""
    1) Find the most recent cloud product and read and remap to area of interest
    2) Create a dataset with the time in seconds from "now" back to observation time for all cloud free views
    3) Take an older cloud cover dataset on the area and find new cloudfree views where cloudy until now, and again update the dataset with new times.
    4) Repeat...


"""


# S_NWC_CMA_npp_50192_20210705T0323237Z_20210705T0324479Z.nc
PATTERN = 'S_NWC_CMA_{platform_name:s}_{orbit_number:5d}_{start_time:%Y%m%dT%H%M%S%f}Z_{endtime:%Y%m%dT%H%M%S%f}Z.nc'
PPS_DIR = "/data/lang/satellit2/polar/pps/"

AREAID = 'euron1'
AREAID = 'sweden'
AREA_DEF_FILE = "/home/a000680/usr/src/pytroll-config/etc/areas.yaml"


if __name__ == "__main__":

    # START = datetime(2021, 6, 11, 0)
    # END = datetime(2021, 6, 11, 12)
    START = datetime(2021, 7, 26, 0)
    END = datetime(2021, 7, 28, 12)

    pps_file_getter = PPSFilesGetter(PPS_DIR, START, END)
    pps_file_getter.collect_product_files(product_name='CMA')
    pps_file_getter.gather_granules('CMA')

    sceneslist = list(pps_file_getter.pps_files['CMA'].keys())

    # start_time = datetime(2021, 6, 11, 12, 0)
    start_time = END

    myobj = LastCloudfreeView(AREAID, start_time)

    sorted_scenes = sceneslist[::-1]
    for nscene, pps_scene in enumerate(sorted_scenes):
        print(nscene, pps_scene)

        PPS_FILES = pps_file_getter.pps_files['CMA'][pps_scene]
        # Get satellite and orbit number and add to scenes-id list
        #
        cmask = myobj.get_cloudmask(PPS_FILES)
        print(myobj.scene_ids[-1])

        lon, lat, time_data = myobj.get_scene_times_cloudfree_view(cmask)
        result = myobj.map_data(lon, lat, time_data)
        myobj.set_time_dataset(result)
        filename = './minutes_since_last_cloudfree_view_from_{starttime}_{scene}.png'.format(starttime=start_time.strftime('%Y%m%d_%H%M'),
                                                                                             scene=pps_scene)

        # myobj.plot_data(filename, max_minutes=60*60)  # 60 hours = 2.5 days
        myobj.plot_data(filename, max_minutes=60*24)  # 24 hours

    # img = Image(myobj.relative_obstimes, mode="L", fill_value=None)
    # ylgnbu.set_range(32, 42)
    # img.colorize(ylgnbu)
    # img.show()

    # plot_data(myobj.relative_obstimes, myobj._crs, './minutes_since_last_cloudfree_view_1.png')

    # img = myobj.create_image()
    # img.show()
