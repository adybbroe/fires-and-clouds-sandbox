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

"""
"""

from glob import glob
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

from fires_and_clouds.cloud_utils import get_cloudmask_scene
from fires_and_clouds.cloud_utils import create_clfree_freshness_from_cloudmask
from fires_and_clouds.cloud_utils import generate_cloudmask_image

from pyresample import load_area
from pyresample import kd_tree, geometry
from trollsift.parser import Parser


# S_NWC_CMA_npp_50192_20210705T0323237Z_20210705T0324479Z.nc
PATTERN = 'S_NWC_CMA_{platform_name:s}_{orbit_number:5d}_{start_time:%Y%m%dT%H%M%S%f}Z_{endtime:%Y%m%dT%H%M%S%f}Z.nc'
PPS_DIR = "/data/lang/satellit2/polar/pps/2021/07/05"

AREAID = 'euron1'
AREA_DEF_FILE = "/home/a000680/usr/src/pytroll-config/etc/areas.yaml"


def map_data(lons, lats, time_data):
    """Remap the data to projected area."""

    swath_def = geometry.SwathDefinition(lons=lons, lats=lats)

    area_def = load_area(AREA_DEF_FILE, AREAID)
    result = kd_tree.resample_nearest(swath_def, time_data,
                                      area_def, radius_of_influence=10000)
    crs = area_def.to_cartopy_crs()

    return result, crs


def plot_data(data, crs, filename):

    cmap = cm.YlGn
    cmaplist = [cmap(i) for i in range(cmap.N)]
    # force the first color entry to be grey
    cmaplist[0] = (.5, .5, .5, 1.0)
    # create the new map
    mycmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)

    # Plot the data with Cartopy:
    plt.figure(figsize=(16, 12))
    plt.title('Freshness of cloudfree view')
    ax = plt.axes(projection=crs)
    ax.coastlines()
    ax.gridlines()
    ax.set_global()
    plt.imshow(data, transform=crs, extent=crs.bounds, interpolation='nearest',
               origin='upper', cmap=mycmap)
    cbar = plt.colorbar()
    cbar.set_label("Freshness of cloudfree view")
    plt.savefig(filename)
    plt.clf()


if __name__ == "__main__":

    # PPS_FILES = (glob(os.path.join(PPS_DIR, "S_NWC_CMA_noaa20*nc")) +
    #             glob(os.path.join(PPS_DIR, "S_NWC_CMA_npp*nc")))

    PPS_FILES = glob(os.path.join(PPS_DIR, "S_NWC_CMA_noaa20_18794*nc"))

    p__ = Parser(PATTERN)
    for ppsfile in PPS_FILES:
        res = p__.parse(os.path.basename(ppsfile))
        break

    this_scn = get_cloudmask_scene(PPS_FILES)
    # generate_cloudmask_image(scn)

    lons, lats, time_data1 = create_clfree_freshness_from_cloudmask(this_scn)

    # cmap = cm.YlGn
    # cmaplist = [cmap(i) for i in range(cmap.N)]
    # # force the first color entry to be grey
    # cmaplist[0] = (.5, .5, .5, 1.0)
    # # create the new map
    # mycmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)

    # # Plot the data with Cartopy:
    # plt.figure(figsize=(16, 12))
    # plt.title('Freshness of cloudfree view')

    # extent = 0, time_data.shape[1], 0, time_data.shape[0]
    # plt.imshow(time_data, extent=extent, origin='upper',
    #            interpolation='nearest', cmap=mycmap)
    # cbar = plt.colorbar()
    # cbar.set_label("Freshness of cloudfree view")
    # plt.show()

    result, crs = map_data(lons, lats, time_data1)
    plot_data(result, crs, './freshness_of_cloudfree_view_1.png')

    #
    PPS_FILES2 = glob(os.path.join(PPS_DIR, "S_NWC_CMA_npp_50197*nc"))

    this_scn = get_cloudmask_scene(PPS_FILES2)
    # generate_cloudmask_image(scn)
    lons2, lats2, time_data2 = create_clfree_freshness_from_cloudmask(this_scn)

    result2, crs = map_data(lons2, lats2, time_data2)
    plot_data(result2, crs, './freshness_of_cloudfree_view_2.png')

    # The assumption is that scene-2 is later than scene-1:
    newres = np.where(np.greater(result2, result), result2, result)

    #result = np.maximum(result, result2)
    plot_data(newres, crs, './freshness_of_cloudfree_view.png')
