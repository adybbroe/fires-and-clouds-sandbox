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

import os

import rasterio
from rasterio.plot import reshape_as_image
import rasterio.mask
from rasterio.features import rasterize

import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping, Point, Polygon
from shapely.ops import cascaded_union

import numpy as np
import matplotlib.pyplot as plt

SHOW_MASK = True


def poly_from_utm(polygon, transform):
    poly_pts = []

    poly = cascaded_union(polygon)
    for i in np.array(poly.exterior.coords):

        # Convert polygons to the image CRS
        poly_pts.append(~transform * tuple(i))

    # Generate a polygon object
    new_poly = Polygon(poly_pts)
    return new_poly


if __name__ == "__main__":

    raster_path = '/home/a000680/data/msb_proj2021/met09_20211102_0900.eurol.cloudtype_standard.tif'
    with rasterio.open(raster_path, "r") as src:
        raster_img = src.read()
        raster_meta = src.meta

    #shape_path = "/home/a000680/dev/0b0262aeabc29c590ba29015550c2fd2/poly.shp"
    shape_path = "/tmp/poly.shp"
    swath_df = gpd.read_file(shape_path)

    print("CRS Raster: {}".format(swath_df.crs))
    print("CRS Vector {}".format(src.crs))

    poly_shp = []
    im_size = (src.meta['height'], src.meta['width'])
    for num, row in swath_df.iterrows():
        if row['geometry'].geom_type == 'Polygon':
            poly = poly_from_utm(row['geometry'], src.meta['transform'])
            poly_shp.append(poly)
        else:
            for p in row['geometry']:
                poly = poly_from_utm(p, src.meta['transform'])
                poly_shp.append(poly)

    mask = rasterize(shapes=poly_shp,
                     out_shape=im_size)

    if SHOW_MASK:
        # Plot the mask
        plt.figure(figsize=(15, 15))
        plt.imshow(mask)
        plt.show()

    mask = mask.astype("uint16")
    save_path = "./myswath.tif"
    bin_mask_meta = src.meta.copy()
    bin_mask_meta.update({'count': 1})
    with rasterio.open(save_path, 'w', **bin_mask_meta) as dst:
        dst.write(mask * 255, 1)
