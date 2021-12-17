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

"""Get and read cloudiness and map to a region masking out for a swath outline in the near future.

 1) Read a cloud analysis. Either
    * Mesan cloud amount (coarse superobs - ascii file)
    * Mesan cloud composite
    * A past SEVIRI NWCSAF cloud mask/type
    * A past polar NWCSAF cloud mask/type product
 2) Derive a swath outline
 3) Create a raster mask with the swath outline
 4) Mask out the cloud analysis from point 1) for the swath 
 
Possible test Cases:
afimg_20210619_113811.geojson
afimg_20210611_114138.geojson

"""

from glob import glob
import os

from fires_and_clouds.cloud_utils import get_cloudmask_scene
from fires_and_clouds.cloud_utils import get_satname_from_files

from fires_and_clouds.utils import find_actual_tlefile
from fires_and_clouds.utils import create_pass

from pyresample import load_area

from datetime import datetime, timedelta
import numpy as np
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

import rasterio.features
import pyproj
import rasterio
import rasterio.mask
from rasterio.features import rasterize
from shapely.ops import transform
from shapely.geometry import Polygon
from shapely.ops import cascaded_union

# Polar cloud products:
VIIRS_DATADIR = "/data/lang/satellit2/polar/pps/2021/06/11"
AVHRR_MODIS_DATADIR = "/data/lang/satellit/polar/PPS_products/satproj/2021/06/11"

TESTIMG = "/home/a000680/data/msb_proj2021/metop02_20211109_0809_78133_euron1_rgb_02b.tif"
AREA_DEF_FILE = '/home/a000680/usr/src/pytroll-config/etc/areas.yaml'

SMHILOGO = "/home/a000680/data/logos/SMHIlogotypevitRGB8mm.png"
SMHILOGO_BLACK = "/home/a000680/data/logos/SMHIlogotypesvartRGB8mm.png"
FONTS = "/usr/share/fonts/dejavu/DejaVuSerif.ttf"


def get_polygon_from_contour(contour_poly):
    """From a pytroll-schedule contour-poly return a shapely Polygon."""

    geodata = np.vstack((contour_poly.lon, contour_poly.lat)).T
    return Polygon(np.rad2deg(geodata))


def get_swathoutline_as_shape(start_time, end_time, satname, sensor, areaid):
    """Get a swath outline for a given time interval as a polygon from a shapefile."""

    tle_filename = find_actual_tlefile(start_time)
    mypass = create_pass(satname, sensor, start_time, end_time, tle_filename)

    mypoly = get_polygon_from_contour(mypass.boundary.contour_poly)
    areadef = load_area(AREA_DEF_FILE, areaid)

    wgs84 = pyproj.CRS('EPSG:4326')
    mycrs = areadef.crs

    project = pyproj.Transformer.from_crs(wgs84, mycrs, always_xy=True).transform
    new_shapes = transform(project, mypoly)

    shape_path = "/tmp/poly2.shp"
    gpd.GeoDataFrame(pd.DataFrame(['p1'], columns=['geom']),
                     crs=mycrs,
                     geometry=[new_shapes]).to_file(shape_path)

    return gpd.read_file(shape_path)


def get_mask_from_shape(poly_shape, areaid):
    """From a shapefile polygon object and area id create a binary mask."""

    # Here we should extract the tiff-metadata corresponding to the area:
    if areaid not in ['euron1', 'eurol']:
        print("No support for this area id yet...")
        return None

    if areaid == "eurol":
        raster_path = '/home/a000680/data/msb_proj2021/met09_20211102_0900.eurol.cloudtype_standard.tif'
    else:
        raster_path = "/home/a000680/data/msb_proj2021/metop02_20211109_0809_78133_euron1_rgb_02b.tif"

    with rasterio.open(raster_path, "r") as src:
        raster_img = src.read()
        raster_meta = src.meta

    print("CRS Raster: {}".format(poly_shape.crs))
    print("CRS Vector {}".format(src.crs))

    poly_shp = []
    im_size = (raster_meta['height'], raster_meta['width'])
    for num, row in poly_shape.iterrows():
        if row['geometry'].geom_type == 'Polygon':
            poly = poly_from_utm(row['geometry'], raster_meta['transform'])
            poly_shp.append(poly)
        else:
            for p in row['geometry']:
                poly = poly_from_utm(p, raster_meta['transform'])
                poly_shp.append(poly)

    mask = rasterize(shapes=poly_shp, out_shape=im_size)
    # Maybe a need to do more with the mask before return? FIXME!

    return mask


def poly_from_utm(polygon, transform_method):
    poly_pts = []

    poly = cascaded_union(polygon)
    for i in np.array(poly.exterior.coords):

        # Convert polygons to the image CRS
        poly_pts.append(~transform_method * tuple(i))

    # Generate a polygon object
    new_poly = Polygon(poly_pts)
    return new_poly


if __name__ == "__main__":

    #ppsfiles = glob(os.path.join(VIIRS_DATADIR, "S_NWC_CMA_*20210611T10*nc"))
    ppsfiles = glob(os.path.join(AVHRR_MODIS_DATADIR, "S_NWC_CMA_*20210611T10*nc"))

    platform_name = get_satname_from_files(ppsfiles)

    areaid = "euron1"
    #areaid = "eurol"
    start_time = datetime(2021, 6, 11, 11, 31)
    end_time = start_time + timedelta(minutes=16)
    future_time = start_time + timedelta(minutes=6)
    ftime_str = future_time.strftime('%Y%m%d_%H%M')

    scn = get_cloudmask_scene(ppsfiles)
    local_scn = scn.resample(areaid, radius_of_influence=8000)

    swath_df = get_swathoutline_as_shape(start_time, end_time, 'NOAA-20', 'viirs', areaid)

    swath_mask = get_mask_from_shape(swath_df, areaid)

    cma = local_scn['cma'] * 255
    local_scn['cma'] = cma.where(swath_mask == 1)
    local_scn['cma'].attrs['area'] = local_scn['cloudmask'].area
    # local_scn.show('cma')

    start_time_txt = platform_name + ': ' + local_scn.start_time.strftime('%Y-%m-%d %H:%M')
    stime_fname = local_scn.start_time.strftime('%Y%m%d_%H%M')
    output_filename = './cloudmask_on_future_swath_{time}_{area}_{future}.png'.format(time=stime_fname,
                                                                                      area=areaid,
                                                                                      future=ftime_str)

    local_scn.save_dataset('cma', filename=output_filename,
                           overlay={'coast_dir': '/home/a000680/data/shapes/', 'color': 'red'},
                           decorate={'decorate': [
                               {'logo': {'logo_path': SMHILOGO_BLACK,
                                         'height': 90, 'bg': 'white', 'bg_opacity': 120}},
                               {'text': {'txt': start_time_txt,
                                         'align': {'top_bottom': 'top', 'left_right': 'left'},
                                         'font': FONTS,
                                         'font_size': 56,
                                         'height': 90,
                                         'bg': 'black',
                                         'bg_opacity': 120,
                                         'line': 'white'}}]})
