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

"""Read NWCSAF/PPS cloud product and output a shapefile for cloud cover
"""

from glob import glob
import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

import rasterio
from rasterio.features import shapes
import fiona
from shapely.geometry import mapping
from shapely.geometry import shape


from pyresample import load_area
from pyresample import kd_tree, geometry
from satpy import Scene
from satpy.utils import debug_on
from datetime import datetime, timedelta
from trollsift.parser import parse, globify, Parser

debug_on()

# S_NWC_CMA_npp_50192_20210705T0323237Z_20210705T0324479Z.nc
PATTERN = 'S_NWC_CMA_{platform_name:s}_{orbit_number:5d}_{start_time:%Y%m%dT%H%M%S%f}Z_{endtime:%Y%m%dT%H%M%S%f}Z.nc'
PPS_DIR = "/data/lang/satellit2/polar/pps/2021/07/05"

#AREAID = 'scan2'
AREAID = 'euron1'
AREA_DEF_FILE = "/home/a000680/usr/src/pytroll-config/etc/areas.yaml"


def get_cloudmask_scene(ppsfiles):
    """Get a cloudmask scene from a set of files."""

    filenames = {'nwcsaf-pps_nc': ppsfiles}
    scn = Scene(filenames=filenames)
    scn.load(['cma', 'cloudmask'])

    return scn


if __name__ == "__main__":

    PPS_FILES = glob(os.path.join(PPS_DIR, "S_NWC_CMA_noaa20_18794*nc"))

    p__ = Parser(PATTERN)
    for ppsfile in PPS_FILES:
        res = p__.parse(os.path.basename(ppsfile))
        break

    this_scn = get_cloudmask_scene(PPS_FILES)

    local_scn = this_scn.resample(AREAID, radius_of_influence=5000)
    myarea = local_scn['cma'].area
    crs = myarea.to_cartopy_crs()
    data = local_scn['cma'].data.compute()

    local_scn.save_dataset('cloudmask', '/tmp/mycmask.tiff')
    mask = (data != 255)

    data = np.where(np.equal(data, 255), 0, data)
    src = rasterio.open('/tmp/mycmask.tiff')
    this = rasterio.features.shapes(data, mask=mask, transform=src.transform)

    geoms = list(this)
    #geoms = list(results)
    # first feature
    # print(geoms[0])
    # print(shape(geoms[0]['geometry']))

    # Define a polygon feature geometry with one attribute
    schema = {
        'geometry': 'Polygon',
        'properties': {'raster_val': 'int'},
    }

    pause

    # Write a new Shapefile
    with fiona.open('my_shapefile.shp', 'w', crs=myarea.proj4_string,
                    driver='ESRI Shapefile', schema=schema) as fpt:
        for geom in geoms:
            fpt.write({
                'geometry': geom[0],
                'properties': {'raster_val': geom[1]},
            })
