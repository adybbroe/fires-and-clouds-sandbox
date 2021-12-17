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

# def bbox(lat,lng, margin):
#     return Polygon([[lng-margin, lat-margin],[lng-margin, lat+margin],
#     [lng+margin,lat+margin],[lng+margin,lat-margin]])

# gpd.GeoDataFrame(pd.DataFrame(['p1'], columns = ['geom']),
#      crs = {'init':'epsg:4326'},
#      geometry = [bbox(10,10, 0.25)]).to_file('poly.shp')


from fires_and_clouds.utils import find_actual_tlefile
from fires_and_clouds.utils import create_pass

from pyresample.boundary import AreaDefBoundary
from pyresample import load_area
from trollsched.drawing import save_fig
from datetime import datetime, timedelta
import scipy.ndimage as ndimage
import numpy as np
from pyresample import kd_tree, geometry
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import rasterio.features
import rasterio.mask
import pyproj
from shapely.ops import transform

AREA_DEF_FILE = '/home/a000680/usr/src/pytroll-config/etc/areas.yaml'
AREAID = 'eurol'

#TESTIMG = "/home/a000680/data/msb_proj2021/metop02_20211109_0809_78133_euron1_rgb_02b.tif"
TESTIMG = "/home/a000680/data/msb_proj2021/met09_20211102_0900.eurol.cloudtype_standard.tif"


def get_polygon_from_contour(contour_poly):
    """From a pytroll-schedule contour-poly return a shapely Polygon."""

    geodata = np.vstack((contour_poly.lon, contour_poly.lat)).T
    return Polygon(np.rad2deg(geodata))


if __name__ == "__main__":

    sensor = 'viirs'
    satname = 'NOAA-20'

    #start_time = datetime(2021, 11, 1, 11, 54)
    start_time = datetime(2021, 6, 11, 11, 31)
    end_time = start_time + timedelta(minutes=14)

    tle_filename = find_actual_tlefile(start_time)
    mypass = create_pass(satname, sensor, start_time, end_time, tle_filename)

    mypoly = get_polygon_from_contour(mypass.boundary.contour_poly)

    areadef = load_area(AREA_DEF_FILE, AREAID)

    wgs84 = pyproj.CRS('EPSG:4326')
    #mycrs = areadef.to_cartopy_crs()
    mycrs = areadef.crs

    project = pyproj.Transformer.from_crs(wgs84, mycrs, always_xy=True).transform
    new_shapes = transform(project, mypoly)

    shape_path = "/tmp/poly.shp"
    gpd.GeoDataFrame(pd.DataFrame(['p1'], columns=['geom']),
                     crs=mycrs,
                     geometry=[new_shapes]).to_file(shape_path)

    #
    #
    #mycrs = {'init': 'epsg:4326'}
    #mycrs = areadef.crs
    # gpd.GeoDataFrame(pd.DataFrame(['p1'], columns=['geom']),
    #                 crs=mycrs,
    #                 geometry=[mypoly]).to_file('poly.shp')
    # OK, this created a shapefile - it can be viewed with QGis
    # AD, 2021-11-02

    # rst = rasterio.open('/home/a000680/data/met09_20211102_0900.eurol.cloudtype_standard.tif')
    # meta = rst.meta.copy()
    # # meta.update(compress='lzw')

    # shapes = [mypoly]
    # with rasterio.open("./myrastertest.tif", 'w', **meta) as src:
    #     out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)  # , transform=src.transform)
    #     out_meta = src.meta

    # with rasterio.open(out_fn, 'w+', **meta) as out:
    #     out_arr = out.read(1)

    #     burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
    #     out.write_band(1, burned)

    #img = rasterio.features.rasterize([mypoly], out_shape=(1024, 1024), transform=areadef.crs)
    # plt.imshow(img)
    # plt.show()
